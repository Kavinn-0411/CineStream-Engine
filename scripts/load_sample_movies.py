#!/usr/bin/env python3
"""
Script to load first 1000 movies from CSV file into MySQL database.
Prompts for database connection details interactively.
"""

import csv
import sys
import mysql.connector
from mysql.connector import Error
import getpass


def get_db_connection_interactive():
    """Prompt user for database connection details."""
    print("\n=== MySQL Database Connection ===")
    host = "localhost"
    port = "3306"
    database = "cinestream"
    user = "Cinestream"
    password = "password"
    
    try:
        connection = mysql.connector.connect(
            host=host,
            port=int(port),
            database=database,
            user=user,
            password=password
        )
        print(f"✓ Connected to MySQL database '{database}' at {host}:{port}\n")
        return connection
    except Error as e:
        print(f"✗ Error connecting to MySQL: {e}")
        return None


def parse_csv_columns(header_row: list) -> dict:
    """
    Parse CSV header to find column indices.
    Returns dict with keys: id, title, imdb_rating, genres
    """
    header_lower = [col.strip().lower() for col in header_row]
    
    column_map = {}
    
    # Find ID column
    for idx, col in enumerate(header_lower):
        if col in ['id', 'movie_id', 'movieid']:
            column_map['id'] = idx
            break
    
    # Find title column
    for idx, col in enumerate(header_lower):
        if col in ['title', 'movie_title', 'name']:
            column_map['title'] = idx
            break
    
    # Find imdb_rating column
    for idx, col in enumerate(header_lower):
        if col in ['imdb_rating', 'imdbrating', 'rating', 'imdb rating']:
            column_map['imdb_rating'] = idx
            break
    
    # Find genres column
    for idx, col in enumerate(header_lower):
        if col in ['genres', 'genre', 'genres_list']:
            column_map['genres'] = idx
            break
    
    # Verify all required columns are found
    required = ['id', 'title', 'imdb_rating', 'genres']
    missing = [col for col in required if col not in column_map]
    if missing:
        raise ValueError(f"Missing required columns: {missing}. Found columns: {header_row}")
    
    return column_map


def load_sample_movies(csv_path: str, max_records: int = 1000):
    """Load first N movies from CSV file into MySQL database."""
    
    # Get database connection
    connection = get_db_connection_interactive()
    if not connection:
        return False
    
    cursor = connection.cursor()
    success_count = 0
    error_count = 0
    
    try:
        print(f"Reading CSV file: {csv_path}")
        print(f"Loading first {max_records} records...\n")
        
        # Read CSV file
        with open(csv_path, 'r', encoding='utf-8', errors='ignore') as csvfile:
            # Try to detect delimiter
            sample = csvfile.read(1024)
            csvfile.seek(0)
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
            
            reader = csv.reader(csvfile, delimiter=delimiter)
            
            # Read header
            header = next(reader)
            column_map = parse_csv_columns(header)
            
            print(f"Found columns:")
            print(f"  - ID: column {column_map['id']} ({header[column_map['id']]})")
            print(f"  - Title: column {column_map['title']} ({header[column_map['title']]})")
            print(f"  - IMDb Rating: column {column_map['imdb_rating']} ({header[column_map['imdb_rating']]})")
            print(f"  - Genres: column {column_map['genres']} ({header[column_map['genres']]})")
            print()
            
            # Prepare insert query
            insert_query = """
                INSERT INTO movies (movie_id, title, imdb_rating, genres)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    title = VALUES(title),
                    imdb_rating = VALUES(imdb_rating),
                    genres = VALUES(genres),
                    updated_at = CURRENT_TIMESTAMP
            """
            
            batch = []
            records_processed = 0
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
                # Stop after max_records
                if records_processed >= max_records:
                    break
                
                try:
                    # Extract values based on column mapping
                    movie_id = int(row[column_map['id']])
                    title = row[column_map['title']].strip()
                    imdb_rating_str = row[column_map['imdb_rating']].strip()
                    genres = row[column_map['genres']].strip()
                    
                    # Convert imdb_rating to float, handle empty values
                    imdb_rating = None
                    if imdb_rating_str:
                        try:
                            imdb_rating = float(imdb_rating_str)
                            # Validate rating range (0-10)
                            if imdb_rating < 0 or imdb_rating > 10:
                                imdb_rating = None
                        except ValueError:
                            pass
                    
                    # Validate required fields
                    if not title:
                        print(f"Warning: Row {row_num} - Empty title, skipping")
                        error_count += 1
                        continue
                    
                    batch.append((movie_id, title, imdb_rating, genres))
                    records_processed += 1
                    
                    # Insert in batches of 100
                    if len(batch) >= 100:
                        cursor.executemany(insert_query, batch)
                        connection.commit()
                        success_count += len(batch)
                        print(f"  Loaded {success_count}/{max_records} movies...", end='\r')
                        batch = []
                
                except (ValueError, IndexError) as e:
                    print(f"\nWarning: Row {row_num} - Error: {e}, skipping")
                    error_count += 1
                    continue
            
            # Insert remaining batch
            if batch:
                cursor.executemany(insert_query, batch)
                connection.commit()
                success_count += len(batch)
        
        print()  # New line after progress updates
        print(f"\n{'='*50}")
        print(f"✓ Successfully loaded {success_count} movies")
        if error_count > 0:
            print(f"⚠ Skipped {error_count} rows due to errors")
        print(f"{'='*50}\n")
        
        # Show sample of loaded data
        cursor.execute("SELECT COUNT(*) FROM movies")
        total_in_db = cursor.fetchone()[0]
        print(f"Total movies in database: {total_in_db}")
        
        cursor.execute("SELECT movie_id, title, imdb_rating, genres FROM movies LIMIT 5")
        sample = cursor.fetchall()
        if sample:
            print("\nSample of loaded movies:")
            print("-" * 80)
            for movie_id, title, rating, genres in sample:
                rating_str = f"{rating:.1f}" if rating else "N/A"
                genres_str = genres[:50] + "..." if genres and len(genres) > 50 else (genres or "N/A")
                print(f"ID: {movie_id:5} | {title[:40]:40} | Rating: {rating_str:4} | {genres_str}")
            print("-" * 80)
        
        return True
    
    except FileNotFoundError:
        print(f"\n✗ Error: CSV file not found: {csv_path}")
        return False
    except Exception as e:
        print(f"\n✗ Error loading movies: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        cursor.close()
        connection.close()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Load first 1000 movies from CSV into MySQL database'
    )
    parser.add_argument(
        '--csv',
        type=str,
        default='data/movies.csv',
        help='Path to movies CSV file (default: data/movies.csv)'
    )
    parser.add_argument(
        '--max-records',
        type=int,
        default=1000,
        help='Maximum number of records to load (default: 1000)'
    )
    
    args = parser.parse_args()
    
    import os
    if not os.path.exists(args.csv):
        print(f"\n✗ Error: CSV file not found: {args.csv}")
        print(f"\nPlease provide the path to your movies CSV file:")
        print(f"  python scripts/load_sample_movies.py --csv <path_to_your_csv_file>")
        sys.exit(1)
    
    print("="*50)
    print("CineStream - Sample Movie Data Loader")
    print("="*50)
    
    success = load_sample_movies(args.csv, args.max_records)
    
    if success:
        print("\n✓ Sample data loaded successfully!")
        sys.exit(0)
    else:
        print("\n✗ Failed to load sample data")
        sys.exit(1)


if __name__ == '__main__':
    main()


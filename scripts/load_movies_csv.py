#!/usr/bin/env python3
"""
Script to load movies from CSV file into MySQL database.
Expects CSV with columns: id, title, imdb_rating, genres
"""

import csv
import os
import sys
import mysql.connector
from mysql.connector import Error
from typing import Optional
import argparse


def get_db_connection() -> Optional[mysql.connector.MySQLConnection]:
    """Create and return MySQL database connection."""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            port=int(os.getenv('MYSQL_PORT', 3306)),
            database=os.getenv('MYSQL_DB', 'cinestream'),
            user=os.getenv('MYSQL_USER', 'cinestream_user'),
            password=os.getenv('MYSQL_PASSWORD', 'cinestream_password')
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None


def parse_csv_columns(header_row: list) -> dict:
    """
    Parse CSV header to find column indices.
    Returns dict with keys: id, title, imdb_rating, genres
    """
    header_lower = [col.strip().lower() for col in header_row]
    
    # Try to find columns with various possible names
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


def load_movies_from_csv(csv_path: str, batch_size: int = 1000) -> tuple[int, int]:
    """
    Load movies from CSV file into MySQL database.
    Returns (success_count, error_count)
    """
    connection = get_db_connection()
    if not connection:
        return 0, 0
    
    cursor = connection.cursor()
    success_count = 0
    error_count = 0
    
    try:
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
            
            print(f"Found columns: id={column_map['id']}, title={column_map['title']}, "
                  f"imdb_rating={column_map['imdb_rating']}, genres={column_map['genres']}")
            
            # Prepare insert/update query
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
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
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
                        except ValueError:
                            pass
                    
                    # Validate required fields
                    if not title:
                        print(f"Warning: Row {row_num} - Empty title, skipping")
                        error_count += 1
                        continue
                    
                    batch.append((movie_id, title, imdb_rating, genres))
                    
                    # Insert in batches for better performance
                    if len(batch) >= batch_size:
                        cursor.executemany(insert_query, batch)
                        connection.commit()
                        success_count += len(batch)
                        print(f"Loaded {success_count} movies...")
                        batch = []
                
                except (ValueError, IndexError) as e:
                    print(f"Error processing row {row_num}: {e}")
                    error_count += 1
                    continue
            
            # Insert remaining batch
            if batch:
                cursor.executemany(insert_query, batch)
                connection.commit()
                success_count += len(batch)
        
        print(f"\nSuccessfully loaded {success_count} movies")
        if error_count > 0:
            print(f"Skipped {error_count} rows due to errors")
    
    except FileNotFoundError:
        print(f"Error: CSV file not found: {csv_path}")
        error_count = 1
    except Exception as e:
        print(f"Error loading movies: {e}")
        error_count += 1
    finally:
        cursor.close()
        connection.close()
    
    return success_count, error_count


def main():
    parser = argparse.ArgumentParser(description='Load movies from CSV into MySQL database')
    parser.add_argument('--csv', type=str, required=True,
                       help='Path to movies CSV file')
    parser.add_argument('--batch-size', type=int, default=1000,
                       help='Batch size for database inserts (default: 1000)')
    parser.add_argument('--host', type=str,
                       help='MySQL host (default: from env or localhost)')
    parser.add_argument('--port', type=int,
                       help='MySQL port (default: from env or 3306)')
    parser.add_argument('--user', type=str,
                       help='MySQL user (default: from env or cinestream_user)')
    parser.add_argument('--password', type=str,
                       help='MySQL password (default: from env or cinestream_password)')
    parser.add_argument('--database', type=str,
                       help='MySQL database (default: from env or cinestream)')
    
    args = parser.parse_args()
    
    # Override env vars if CLI args provided
    if args.host:
        os.environ['MYSQL_HOST'] = args.host
    if args.port:
        os.environ['MYSQL_PORT'] = str(args.port)
    if args.user:
        os.environ['MYSQL_USER'] = args.user
    if args.password:
        os.environ['MYSQL_PASSWORD'] = args.password
    if args.database:
        os.environ['MYSQL_DB'] = args.database
    
    if not os.path.exists(args.csv):
        print(f"Error: CSV file not found: {args.csv}")
        sys.exit(1)
    
    print(f"Loading movies from {args.csv}...")
    success, errors = load_movies_from_csv(args.csv, args.batch_size)
    
    if success > 0:
        print(f"\n✓ Successfully loaded {success} movies into database")
        sys.exit(0)
    else:
        print("\n✗ Failed to load any movies")
        sys.exit(1)


if __name__ == '__main__':
    main()


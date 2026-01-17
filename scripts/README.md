# Scripts

Utility scripts for CineStream operations.

## load_sample_movies.py

Quick script to load the first 1000 movies from CSV into MySQL database with interactive database connection prompts.

### Usage

```bash
# Default: loads first 1000 records from data/movies.csv
python scripts/load_sample_movies.py

# Custom CSV file path
python scripts/load_sample_movies.py --csv /path/to/your/movies.csv

# Load custom number of records
python scripts/load_sample_movies.py --csv data/movies.csv --max-records 500
```

### Interactive Prompts

The script will prompt you for:
- MySQL Host (default: localhost)
- MySQL Port (default: 3306)
- Database name (default: cinestream)
- Username (default: cinestream_user)
- Password (hidden input)

### Example

```bash
$ python scripts/load_sample_movies.py --csv data/movies.csv

=== MySQL Database Connection ===
Host [localhost]: localhost
Port [3306]: 3306
Database [cinestream]: cinestream
Username [cinestream_user]: root
Password for root: ****

✓ Connected to MySQL database 'cinestream' at localhost:3306
Reading CSV file: data/movies.csv
Loading first 1000 records...

Found columns:
  - ID: column 0 (id)
  - Title: column 1 (title)
  - IMDb Rating: column 2 (imdb_rating)
  - Genres: column 3 (genres)

  Loaded 1000/1000 movies...

==================================================
✓ Successfully loaded 1000 movies
==================================================
```

## load_movies_csv.py

Loads movies from CSV file into MySQL database.

### Prerequisites

1. MySQL database must be running (via docker-compose)
2. Database schema must be initialized
3. Required Python packages: `mysql-connector-python`

### Installation

```bash
pip install mysql-connector-python
```

Or install all dependencies:
```bash
pip install -r requirements.txt
```

### Usage

```bash
# Load movies from CSV
python scripts/load_movies_csv.py --csv data/movies.csv

# Check database connection first (ensure docker-compose is running)
docker-compose ps
```

### Options

- `--csv`: Path to CSV file (required)
- `--batch-size`: Number of records per batch (default: 1000)
- `--host`: MySQL host (overrides environment variable)
- `--port`: MySQL port (overrides environment variable)
- `--user`: MySQL username (overrides environment variable)
- `--password`: MySQL password (overrides environment variable)
- `--database`: MySQL database name (overrides environment variable)

### Example

```bash
# Using environment variables
python scripts/load_movies_csv.py --csv data/movies.csv

# With explicit credentials
python scripts/load_movies_csv.py \
  --csv data/movies.csv \
  --host localhost \
  --user cinestream_user \
  --password cinestream_password \
  --database cinestream
```


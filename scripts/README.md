# Scripts

Utility scripts for CineStream operations.

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


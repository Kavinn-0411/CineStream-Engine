# CineStream Engine

A real-time movie recommendation engine that personalizes suggestions based on user reviews and sentiment analysis.

## Overview

CineStream processes user movie reviews in real-time using Apache Kafka and PySpark streaming. It uses sentiment analysis to understand user preferences and generates personalized movie recommendations through collaborative filtering.

## Tech Stack

- **Backend**: FastAPI (Python)
- **Databases**: MySQL (structured data) + MongoDB (logs)
- **Streaming**: Apache Kafka + PySpark
- **ML**: Sentiment Analysis + Collaborative Filtering
- **Infrastructure**: Docker Compose

## Architecture

```
User Reviews → FastAPI → Kafka → PySpark → Sentiment Analysis → Recommendations
                ↓                              ↓
            MongoDB Logs                   MySQL Database
```

## Quick Start

### Prerequisites
- Docker Desktop
- Python 3.8+
- Movie dataset CSV (place in `data/movies.csv`)

### 1. Start Infrastructure
```bash
# Start all services (Kafka, MySQL, MongoDB)
docker-compose up -d

# Wait 60 seconds for services to initialize

# Create Kafka topics
docker exec cinestream-kafka kafka-topics --create --bootstrap-server localhost:9092 --topic reviews --partitions 3 --replication-factor 1 --if-not-exists
docker exec cinestream-kafka kafka-topics --create --bootstrap-server localhost:9092 --topic movie-logs --partitions 3 --replication-factor 1 --if-not-exists
```

### 2. Load Movie Data
```bash
# Load sample 1000 movies
python scripts/load_sample_movies.py --csv data/movies.csv
```

### 3. Start API Server
```bash
# Install dependencies
pip install -r requirements.txt

# Run API
python -m uvicorn api.main:app --reload --port 8000
```

### 4. Access Services
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Kafka UI**: http://localhost:8080
- **MySQL**: localhost:3307
- **MongoDB**: localhost:27017

## Project Status

✅ **Completed**
- Infrastructure setup (Docker Compose)
- Database schemas (MySQL + MongoDB)
- Data loading scripts
- FastAPI foundation with health checks

🚧 **In Progress**
- Movie API endpoints
- User management
- Review submission with Kafka
- PySpark streaming job
- ML models (Sentiment Analysis + Collaborative Filtering)

## Project Structure

```
CineStream-Engine/
├── api/                      # FastAPI backend
│   ├── main.py              # API entry point
│   ├── config.py            # Configuration
│   ├── database/            # Database connections
│   └── utils/               # Utilities
├── data/                     # Movie dataset (CSV)
├── infrastructure/           # Docker & DB initialization
│   ├── init_db/             # SQL/MongoDB init scripts
│   └── kafka/               # Kafka setup
├── scripts/                  # Utility scripts
├── docker-compose.yml       # Infrastructure orchestration
└── requirements.txt         # Python dependencies
```

## Documentation

- [QUICKSTART.md](QUICKSTART.md) - Detailed setup guide
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [ROADMAP.md](ROADMAP.md) - Development roadmap
- [API_DEVELOPMENT_PLAN.md](API_DEVELOPMENT_PLAN.md) - API development phases

## Development

```bash
# Check service health
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## License

This project is for educational purposes.

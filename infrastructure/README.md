# CineStream Infrastructure Setup

This directory contains infrastructure configuration for the CineStream recommendation engine.

## Prerequisites

- Docker Desktop (or Docker + Docker Compose)
- Ports available: 9092 (Kafka), 3306 (MySQL), 27017 (MongoDB), 2181 (Zookeeper), 8080 (Kafka UI)

## Quick Start

1. **Start all services:**
   ```bash
   docker-compose up -d
   ```

2. **Check service health:**
   ```bash
   docker-compose ps
   ```

3. **Create Kafka topics:**
   ```bash
   chmod +x infrastructure/kafka/topics_setup.sh
   ./infrastructure/kafka/topics_setup.sh
   ```

4. **View Kafka UI:**
   Open http://localhost:8080 in your browser

5. **Stop services:**
   ```bash
   docker-compose down
   ```

## Services

### Kafka (Port 9092)
- Message broker for streaming movie logs and reviews
- Accessible at `localhost:9092`

### Zookeeper (Port 2181)
- Required by Kafka for coordination
- Internal service only

### MySQL (Port 3306)
- Main database for movies, users, preferences, and recommendations
- Database: `cinestream`
- User: `cinestream_user`
- Password: `cinestream_password`
- Root Password: `root_password`

### MongoDB (Port 27017)
- Document store for review logs and streaming logs
- Database: `cinestream_logs`
- Admin User: `cinestream_admin`
- Admin Password: `cinestream_admin_password`
- App User: `cinestream_app`
- App Password: `cinestream_app_password`

### Kafka UI (Port 8080)
- Web interface for monitoring Kafka topics and messages
- Accessible at http://localhost:8080

## Database Connections

### MySQL
```
Host: localhost
Port: 3306
Database: cinestream
Username: cinestream_user
Password: cinestream_password
Root Password: root_password
```

### MongoDB
```
Host: localhost
Port: 27017
Database: cinestream_logs
Username: cinestream_app
Password: cinestream_app_password
Auth Source: cinestream_logs
```

## Kafka Topics

- `movie-logs`: User movie viewing events
- `reviews`: User text reviews

## Troubleshooting

1. **Port conflicts:** Ensure ports 9092, 3306, 27017, 2181, and 8080 are not in use
2. **Kafka not starting:** Wait a few seconds for Zookeeper to be fully ready
3. **Database connection issues:** Wait for health checks to pass before connecting


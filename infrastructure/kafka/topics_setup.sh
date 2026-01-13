#!/bin/bash

# Script to create Kafka topics for CineStream
# This can be run manually or executed as part of the setup

KAFKA_BOOTSTRAP_SERVER="localhost:9092"

echo "Waiting for Kafka to be ready..."
sleep 10

# Create movie-logs topic
echo "Creating movie-logs topic..."
docker exec cinestream-kafka kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic movie-logs \
  --partitions 3 \
  --replication-factor 1 \
  --if-not-exists

# Create reviews topic
echo "Creating reviews topic..."
docker exec cinestream-kafka kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic reviews \
  --partitions 3 \
  --replication-factor 1 \
  --if-not-exists

echo "Kafka topics created successfully!"
echo "Listing all topics:"
docker exec cinestream-kafka kafka-topics --list --bootstrap-server localhost:9092


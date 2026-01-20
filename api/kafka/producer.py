"""Kafka producer for review events."""

import json
import logging

from kafka import KafkaProducer

from api.config import settings

logger = logging.getLogger(__name__)

_producer: KafkaProducer | None = None


def get_kafka_producer() -> KafkaProducer:
    global _producer
    if _producer is None:
        _producer = KafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda v: v.encode("utf-8") if v else None,
            retries=3,
        )
        logger.info("Kafka producer initialized.")
    return _producer


def publish_review_event(payload: dict) -> None:
    producer = get_kafka_producer()
    future = producer.send(
        topic=settings.KAFKA_TOPIC_REVIEWS,
        key=str(payload.get("user_id", "")),
        value=payload,
    )
    # Wait for broker ack to treat as published
    future.get(timeout=10)
    producer.flush()


def close_kafka_producer() -> None:
    global _producer
    if _producer is not None:
        _producer.close()
        _producer = None
        logger.info("Kafka producer closed.")

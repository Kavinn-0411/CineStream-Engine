"""Configuration loader for streaming job."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _default_sentiment_nb_path() -> str:
    root = Path(__file__).resolve().parents[1]
    return str(root / "models" / "artifacts" / "sentiment_mnb.joblib")


@dataclass
class StreamingConfig:
    app_name: str = os.getenv("SPARK_APP_NAME", "CineStream-Streaming")
    spark_master: str = os.getenv("SPARK_MASTER", "local[*]")
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    kafka_topic_reviews: str = os.getenv("KAFKA_TOPIC_REVIEWS", "reviews")
    checkpoint_location: str = os.getenv("SPARK_CHECKPOINT_LOCATION", "./checkpoints/reviews_stream")
    trigger_seconds: int = int(os.getenv("SPARK_BATCH_INTERVAL", "10"))
    # mapInPandas: one sklearn load per partition (default 1 for local).
    sentiment_inference_partitions: int = int(os.getenv("SENTIMENT_INFERENCE_PARTITIONS", "1"))
    spark_packages: str = os.getenv(
        "SPARK_PACKAGES",
        "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,com.mysql:mysql-connector-j:8.3.0",
    )

    mysql_host: str = os.getenv("MYSQL_HOST", "localhost")
    mysql_port: int = int(os.getenv("MYSQL_PORT", "3307"))
    mysql_db: str = os.getenv("MYSQL_DB", "cinestream")
    mysql_user: str = os.getenv("MYSQL_USER", "cinestream_user")
    mysql_password: str = os.getenv("MYSQL_PASSWORD", "cinestream_password")

    # Sentiment: train with scripts/train_sentiment_nb.py --data your.csv
    sentiment_nb_model_path: str = os.getenv(
        "SENTIMENT_MNB_MODEL_PATH",
        _default_sentiment_nb_path(),
    )

    @property
    def mysql_jdbc_url(self) -> str:
        return f"jdbc:mysql://{self.mysql_host}:{self.mysql_port}/{self.mysql_db}"

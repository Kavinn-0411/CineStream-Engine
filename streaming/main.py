"""PySpark streaming job:
reviews topic -> Multinomial NB sentiment -> MySQL user_preferences + heuristic recommendations.
"""

import logging
from pathlib import Path

import pyarrow  # noqa: F401 — required for mapInPandas / Arrow (pip install pyarrow)

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructField, StructType, StringType, IntegerType

from streaming.config import StreamingConfig
from streaming.processors.sentiment_processor import add_sentiment_columns
from streaming.processors.recommendation_processor import build_candidate_recommendations
from streaming.writers.mysql_writer import write_feedback_batch, write_recommendations_batch

logger = logging.getLogger(__name__)


def build_spark_session(cfg: StreamingConfig) -> SparkSession:
    return (
        SparkSession.builder.appName(cfg.app_name)
        .master(cfg.spark_master)
        .config("spark.jars.packages", cfg.spark_packages)
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.sql.execution.arrow.pyspark.enabled", "true")
        .config("spark.sql.execution.arrow.maxRecordsPerBatch", "1000")
        .getOrCreate()
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    cfg = StreamingConfig()
    sent_path = Path(cfg.sentiment_nb_model_path)
    if not sent_path.is_file():
        raise SystemExit(
            f"Sentiment model not found: {sent_path}\n"
            "Train from your labeled CSV:\n"
            "  python scripts/train_sentiment_nb.py --data path/to/your_download.csv\n"
            "Or set SENTIMENT_MNB_MODEL_PATH to an existing joblib pipeline."
        )
    logger.info("Sentiment model: Multinomial NB (%s)", sent_path)

    spark = build_spark_session(cfg)
    spark.sparkContext.setLogLevel("WARN")

    schema = StructType(
        [
            StructField("event_id", StringType(), True),
            StructField("user_id", IntegerType(), True),
            StructField("movie_id", IntegerType(), True),
            StructField("review_text", StringType(), True),
            StructField("event_time", StringType(), True),
            StructField("source", StringType(), True),
        ]
    )

    kafka_stream = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", cfg.kafka_bootstrap_servers)
        .option("subscribe", cfg.kafka_topic_reviews)
        .option("startingOffsets", "latest")
        .load()
    )

    parsed = (
        kafka_stream.selectExpr("CAST(value AS STRING) AS json_value")
        .select(F.from_json(F.col("json_value"), schema).alias("data"))
        .select("data.*")
        .withColumn("event_time", F.to_timestamp("event_time"))
        .filter(F.col("user_id").isNotNull() & F.col("movie_id").isNotNull() & F.col("review_text").isNotNull())
    )

    scored = add_sentiment_columns(
        parsed,
        cfg,
        sentiment_partitions=cfg.sentiment_inference_partitions,
    )

    def _foreach_batch(df, _batch_id):
        if df.count() == 0:
            return
        write_feedback_batch(df, cfg)
        recommendations_df = build_candidate_recommendations(
            scored_reviews_df=df, cfg=cfg, top_n=10
        )
        write_recommendations_batch(recommendations_df, cfg)

    query = (
        scored.writeStream.outputMode("update")
        .trigger(processingTime=f"{cfg.trigger_seconds} seconds")
        .option("checkpointLocation", cfg.checkpoint_location)
        .foreachBatch(_foreach_batch)
        .start()
    )

    print("Streaming job started. Press Ctrl+C to stop.")
    print(f"Kafka topic: {cfg.kafka_topic_reviews}")
    print(f"Checkpoint: {cfg.checkpoint_location}")
    query.awaitTermination()


if __name__ == "__main__":
    main()

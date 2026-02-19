"""MySQL sink helpers for Spark foreachBatch."""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
import mysql.connector

from streaming.config import StreamingConfig


def _upsert_partition(rows, cfg: StreamingConfig) -> None:
    conn = mysql.connector.connect(
        host=cfg.mysql_host,
        port=cfg.mysql_port,
        database=cfg.mysql_db,
        user=cfg.mysql_user,
        password=cfg.mysql_password,
    )
    cursor = conn.cursor()
    try:
        query = """
            INSERT INTO user_preferences (
                user_id, movie_id, rating, sentiment_score, last_review_text, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE
                rating = VALUES(rating),
                sentiment_score = VALUES(sentiment_score),
                last_review_text = VALUES(last_review_text),
                updated_at = NOW()
        """
        values = []
        for r in rows:
            values.append(
                (
                    int(r["user_id"]),
                    int(r["movie_id"]),
                    float(r["rating"]),
                    float(r["sentiment_score"]),
                    r["last_review_text"],
                )
            )
        if values:
            cursor.executemany(query, values)
            conn.commit()
    finally:
        cursor.close()
        conn.close()


def write_feedback_batch(batch_df: DataFrame, cfg: StreamingConfig) -> None:
    # Keep latest review per user/movie in this micro-batch.
    latest_df = (
        batch_df.groupBy("user_id", "movie_id")
        .agg(
            F.max("event_time").alias("event_time"),
            F.last("review_text", ignorenulls=True).alias("last_review_text"),
            F.last("sentiment_score", ignorenulls=True).alias("sentiment_score"),
            F.last("derived_rating", ignorenulls=True).alias("rating"),
        )
        .drop("event_time")
    )

    latest_df.foreachPartition(lambda rows: _upsert_partition(rows, cfg))


def _upsert_recommendations_partition(rows, cfg: StreamingConfig) -> None:
    conn = mysql.connector.connect(
        host=cfg.mysql_host,
        port=cfg.mysql_port,
        database=cfg.mysql_db,
        user=cfg.mysql_user,
        password=cfg.mysql_password,
    )
    cursor = conn.cursor()
    try:
        query = """
            INSERT INTO recommendations (user_id, movie_id, score, generated_at)
            VALUES (%s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE
                score = VALUES(score),
                generated_at = NOW()
        """
        values = []
        for r in rows:
            values.append((int(r["user_id"]), int(r["movie_id"]), float(r["score"])))
        if values:
            cursor.executemany(query, values)
            conn.commit()
    finally:
        cursor.close()
        conn.close()


def write_recommendations_batch(recommendations_df: DataFrame, cfg: StreamingConfig) -> None:
    recommendations_df.foreachPartition(lambda rows: _upsert_recommendations_partition(rows, cfg))

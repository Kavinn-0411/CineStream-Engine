"""Low-level review CRUD queries for MySQL ingestion."""

from typing import Any, Optional


def user_exists(conn, user_id: int) -> bool:
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM users WHERE user_id = %s LIMIT 1", (user_id,))
        return cursor.fetchone() is not None
    finally:
        cursor.close()


def movie_exists(conn, movie_id: int) -> bool:
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM movies WHERE movie_id = %s LIMIT 1", (movie_id,))
        return cursor.fetchone() is not None
    finally:
        cursor.close()


def insert_review_raw(conn, payload: dict[str, Any]) -> Optional[dict[str, Any]]:
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO reviews_raw (
                event_id, user_id, movie_id, review_text, event_time, kafka_topic, kafka_published
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                payload["event_id"],
                payload["user_id"],
                payload["movie_id"],
                payload["review_text"],
                payload["event_time"],
                payload.get("kafka_topic"),
                payload.get("kafka_published", 0),
            ),
        )
        conn.commit()
    finally:
        cursor.close()

    return get_review_by_event_id(conn, payload["event_id"])


def get_review_by_event_id(conn, event_id: str) -> Optional[dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT event_id, user_id, movie_id, kafka_topic, kafka_published, created_at
            FROM reviews_raw
            WHERE event_id = %s
            LIMIT 1
            """,
            (event_id,),
        )
        return cursor.fetchone()
    finally:
        cursor.close()

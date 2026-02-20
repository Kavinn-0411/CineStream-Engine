"""Read recommendations joined with movie metadata."""

from typing import Any


def list_recommendations_for_user(
    conn, user_id: int, limit: int = 20
) -> list[dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT
                r.movie_id,
                m.title,
                m.imdb_rating,
                m.genres,
                r.score,
                r.generated_at
            FROM recommendations r
            INNER JOIN movies m ON m.movie_id = r.movie_id
            WHERE r.user_id = %s
            ORDER BY r.score DESC, r.generated_at DESC
            LIMIT %s
            """,
            (user_id, limit),
        )
        return cursor.fetchall()
    finally:
        cursor.close()

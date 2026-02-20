"""Low-level movie CRUD queries for MySQL."""

from typing import Any, Optional


def create_movie(conn, movie_data: dict[str, Any]) -> dict[str, Any]:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            INSERT INTO movies (movie_id, title, imdb_rating, genres)
            VALUES (%s, %s, %s, %s)
            """,
            (
                movie_data["movie_id"],
                movie_data["title"],
                movie_data.get("imdb_rating"),
                movie_data.get("genres"),
            ),
        )
        conn.commit()
        return get_movie_by_id(conn, movie_data["movie_id"])
    finally:
        cursor.close()


def get_movie_by_id(conn, movie_id: int) -> Optional[dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT movie_id, title, imdb_rating, genres, created_at, updated_at
            FROM movies
            WHERE movie_id = %s
            """,
            (movie_id,),
        )
        return cursor.fetchone()
    finally:
        cursor.close()


def list_movies(
    conn,
    page: int,
    size: int,
    search: Optional[str] = None,
    genre: Optional[str] = None,
) -> tuple[list[dict[str, Any]], int]:
    offset = (page - 1) * size
    conditions = []
    params: list[Any] = []

    if search:
        conditions.append("title LIKE %s")
        params.append(f"%{search}%")
    if genre:
        conditions.append("genres LIKE %s")
        params.append(f"%{genre}%")

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(f"SELECT COUNT(*) AS total FROM movies {where_clause}", tuple(params))
        total = cursor.fetchone()["total"]

        cursor.execute(
            f"""
            SELECT movie_id, title, imdb_rating, genres, created_at, updated_at
            FROM movies
            {where_clause}
            ORDER BY movie_id ASC
            LIMIT %s OFFSET %s
            """,
            tuple(params + [size, offset]),
        )
        rows = cursor.fetchall()
        return rows, total
    finally:
        cursor.close()


def update_movie(conn, movie_id: int, updates: dict[str, Any]) -> Optional[dict[str, Any]]:
    if not updates:
        return get_movie_by_id(conn, movie_id)

    set_clause = ", ".join([f"{field} = %s" for field in updates.keys()])
    params = list(updates.values()) + [movie_id]

    cursor = conn.cursor()
    try:
        cursor.execute(f"UPDATE movies SET {set_clause} WHERE movie_id = %s", tuple(params))
        conn.commit()
        if cursor.rowcount == 0:
            return None
        return get_movie_by_id(conn, movie_id)
    finally:
        cursor.close()


def delete_movie(conn, movie_id: int) -> bool:
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM movies WHERE movie_id = %s", (movie_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()

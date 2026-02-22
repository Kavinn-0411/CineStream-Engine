"""User CRUD for MySQL."""

from typing import Any, Optional

_PUBLIC_FIELDS = "user_id, username, email, created_at"


def create_user(conn, username: str, email: str, password_hash: str) -> dict[str, Any]:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            INSERT INTO users (username, email, password_hash)
            VALUES (%s, %s, %s)
            """,
            (username, email, password_hash),
        )
        conn.commit()
        uid = cursor.lastrowid
        return get_user_by_id(conn, uid)
    finally:
        cursor.close()


def get_user_by_id(conn, user_id: int) -> Optional[dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            f"""
            SELECT {_PUBLIC_FIELDS}
            FROM users WHERE user_id = %s
            """,
            (user_id,),
        )
        return cursor.fetchone()
    finally:
        cursor.close()


def get_user_by_username(conn, username: str) -> Optional[dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            f"""
            SELECT {_PUBLIC_FIELDS}
            FROM users WHERE username = %s
            """,
            (username,),
        )
        return cursor.fetchone()
    finally:
        cursor.close()


def get_user_with_password_by_username(conn, username: str) -> Optional[dict[str, Any]]:
    """Includes password_hash — for authentication only."""
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT user_id, username, email, password_hash, created_at
            FROM users WHERE username = %s
            """,
            (username,),
        )
        return cursor.fetchone()
    finally:
        cursor.close()


def get_user_by_email(conn, email: str) -> Optional[dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            f"""
            SELECT {_PUBLIC_FIELDS}
            FROM users WHERE email = %s
            """,
            (email,),
        )
        return cursor.fetchone()
    finally:
        cursor.close()


def list_users(conn, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            f"""
            SELECT {_PUBLIC_FIELDS}
            FROM users
            ORDER BY user_id ASC
            LIMIT %s OFFSET %s
            """,
            (limit, offset),
        )
        return cursor.fetchall()
    finally:
        cursor.close()


def count_users(conn) -> int:
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM users")
        return int(cursor.fetchone()[0])
    finally:
        cursor.close()

"""Processor layer for API business logic."""

from math import ceil
from datetime import datetime, timezone
import uuid

from fastapi import HTTPException, status
from mysql.connector import Error as MySQLError

from api.crud.movie_crud import (
    create_movie,
    delete_movie,
    get_movie_by_id,
    list_movies,
    update_movie,
)
from api.crud.review_crud import insert_review_raw, movie_exists, user_exists
from api.database.connection import get_mysql_connection
from api.schemas.movie import MovieCreate, MovieListResponse, MovieResponse, MovieUpdate
from api.schemas.review import ReviewCreate, ReviewCreateResponse
from api.kafka.producer import publish_review_event


def create_movie_processor(payload: MovieCreate) -> MovieResponse:
    conn = get_mysql_connection()
    try:
        try:
            created = create_movie(conn, payload.model_dump())
        except MySQLError as exc:
            if "Duplicate entry" in str(exc):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Movie with id {payload.movie_id} already exists.",
                ) from exc
            raise
        return MovieResponse(**created)
    finally:
        conn.close()


def get_movie_processor(movie_id: int) -> MovieResponse:
    conn = get_mysql_connection()
    try:
        movie = get_movie_by_id(conn, movie_id)
        if not movie:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Movie with id {movie_id} not found.",
            )
        return MovieResponse(**movie)
    finally:
        conn.close()


def list_movies_processor(
    page: int,
    size: int,
    search: str | None = None,
    genre: str | None = None,
) -> MovieListResponse:
    conn = get_mysql_connection()
    try:
        rows, total = list_movies(conn, page=page, size=size, search=search, genre=genre)
        pages = ceil(total / size) if total else 0
        return MovieListResponse(
            items=[MovieResponse(**row) for row in rows],
            total=total,
            page=page,
            size=size,
            pages=pages,
        )
    finally:
        conn.close()


def update_movie_processor(movie_id: int, payload: MovieUpdate) -> MovieResponse:
    conn = get_mysql_connection()
    try:
        updates = payload.model_dump(exclude_none=True)
        updated = update_movie(conn, movie_id, updates)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Movie with id {movie_id} not found.",
            )
        return MovieResponse(**updated)
    finally:
        conn.close()


def delete_movie_processor(movie_id: int) -> dict[str, str]:
    conn = get_mysql_connection()
    try:
        deleted = delete_movie(conn, movie_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Movie with id {movie_id} not found.",
            )
        return {"message": f"Movie {movie_id} deleted successfully."}
    finally:
        conn.close()


def create_review_processor(payload: ReviewCreate) -> ReviewCreateResponse:
    conn = get_mysql_connection()
    event_id = str(uuid.uuid4())
    event_time = datetime.now(timezone.utc)

    review_event = {
        "event_id": event_id,
        "user_id": payload.user_id,
        "movie_id": payload.movie_id,
        "review_text": payload.review_text,
        "event_time": event_time.isoformat(),
        "source": "api",
    }

    try:
        if not user_exists(conn, payload.user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {payload.user_id} not found.",
            )
        if not movie_exists(conn, payload.movie_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Movie with id {payload.movie_id} not found.",
            )

        try:
            publish_review_event(review_event)
            kafka_published = 1
        except Exception as exc:
            kafka_published = 0
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to publish review to Kafka: {exc}",
            ) from exc

        row = insert_review_raw(
            conn,
            {
                "event_id": event_id,
                "user_id": payload.user_id,
                "movie_id": payload.movie_id,
                "review_text": payload.review_text,
                "event_time": event_time.replace(tzinfo=None),
                "kafka_topic": "reviews",
                "kafka_published": kafka_published,
            },
        )
        return ReviewCreateResponse(**row)
    finally:
        conn.close()

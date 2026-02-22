"""Review schemas used for review ingestion APIs."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    """Authenticated review body — user_id comes from the JWT."""

    movie_id: int = Field(..., gt=0, description="Movie id from movies table")
    review_text: str = Field(..., min_length=3, max_length=5000)


class ReviewCreateResponse(BaseModel):
    event_id: str
    user_id: int
    movie_id: int
    kafka_topic: str
    kafka_published: bool
    created_at: Optional[datetime] = None

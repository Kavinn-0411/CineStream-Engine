"""Recommendation response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RecommendationItem(BaseModel):
    movie_id: int
    title: str
    imdb_rating: Optional[float] = None
    genres: Optional[str] = None
    score: float = Field(..., description="Recommendation rank score")
    generated_at: Optional[datetime] = None


class RecommendationListResponse(BaseModel):
    user_id: int
    items: list[RecommendationItem]
    total: int

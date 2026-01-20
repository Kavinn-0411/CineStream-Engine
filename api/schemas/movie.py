"""Movie schemas used by Phase 2 CRUD endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MovieCreate(BaseModel):
    movie_id: int = Field(..., gt=0, description="Unique movie id")
    title: str = Field(..., min_length=1, max_length=500)
    imdb_rating: Optional[float] = Field(None, ge=0.0, le=10.0)
    genres: Optional[str] = Field(None, max_length=500)


class MovieUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    imdb_rating: Optional[float] = Field(None, ge=0.0, le=10.0)
    genres: Optional[str] = Field(None, max_length=500)


class MovieResponse(BaseModel):
    movie_id: int
    title: str
    imdb_rating: Optional[float] = None
    genres: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MovieListResponse(BaseModel):
    items: list[MovieResponse]
    total: int
    page: int
    size: int
    pages: int

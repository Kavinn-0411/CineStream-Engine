"""User schemas for registration and profile."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=100, description="Unique display name")
    email: EmailStr = Field(..., description="Unique email")


class UserResponse(BaseModel):
    user_id: int
    username: str
    email: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int

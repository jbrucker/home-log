"""Pydantic schemas for type validation, serialization, and deserialization.
These schemas are used in API endpoints.
"""

from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import datetime, timezone


class UserCreate(BaseModel):
    """User attributes that are given to a service endpoint to create a new User entity."""
    email: EmailStr
    username: Optional[str] = None


class User(UserCreate):
    """The complete User schema."""
    # id: int
    # In model classes, these default to current time
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)
    # model_config replaces the Config inner-class in Pydantic 2.0
    model_config = ConfigDict(from_attributes=True)

"""Authentication-related Schemas"""
class Token(BaseModel):
    """The fields in a JWT access token."""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """The fields in the token payload.
        These can be anything you want.
    """
    id: Optional[str] = None
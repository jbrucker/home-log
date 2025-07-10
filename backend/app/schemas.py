"""Pydantic schemas for type validation, serialization, and deserialization.
These schemas are used in API endpoints.
"""

from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from datetime import datetime, timezone
from app.core.config import MAX_DESC, MAX_EMAIL, MAX_NAME, MAX_UNIT_NAME


class UserCreate(BaseModel):
    """User attributes that are given to a service endpoint to create a new User entity."""
    # RFC 5321: max length of an email address is 254 chars
    email: EmailStr = Field(..., max_length=MAX_EMAIL)
    username: Optional[str] = Field(None, max_length=MAX_NAME)


class User(UserCreate):
    """The complete User schema."""
    # For testing include id, for security omit it.
    id: Optional[int] = None
    # In model classes, these default to current time
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)
    # computed variable
    #password: Optional[str] = None
    # model_config replaces the Config inner-class in Pydantic 2.0
    model_config = ConfigDict(from_attributes=True)


class DataSourceCreate(BaseModel):
    """Schema for creating a new DataSource."""
    name: str = Field(..., max_length=MAX_NAME)
    description: Optional[str] = Field(None, max_length=MAX_DESC)
    unit: Optional[str] = Field(None, max_length=MAX_UNIT_NAME)
    # Need to be able to specify owner when source is created
    owner_id: Optional[int] = None


class DataSource(DataSourceCreate):
    """Schema for validating and returning a DataSource."""
    id: int
    owner_id: int
    created_at: datetime = datetime.now(timezone.utc)
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
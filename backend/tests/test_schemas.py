import pytest
from pydantic import ValidationError, EmailStr
from datetime import datetime, timezone
from app.schemas import UserCreate, User

def test_user_create_valid_email():
    """can create a user with valid email and username"""
    user = UserCreate(email="test@example.com", username="tester")
    assert user.email == "test@example.com"
    assert user.username == "tester"

def test_user_invalid_email():
    """email is required and must be a string having valid email syntax"""
    for bad_email in [2.5, "jomzap", "jim@foo", "@foo.com"]:
        with pytest.raises(ValidationError):
            user = User(email=bad_email, username="bad_email")

def test_user_create_optional_username():
    """username is optional and default value is None"""
    user = UserCreate(email="test@example.com")
    assert user.username is None

def test_user_model_fields():
    """test that programmer is not incompetent"""
    now = datetime(2025, 1, 31, 12, 0, 0, tzinfo=timezone.utc)
    user = User(
        id=1,
        email="user@example.com",
        username="user1",
        created_at=now,
        updated_at=now
    )
    assert user.id == 1
    assert user.email == "user@example.com"
    assert user.username == "user1"
    assert user.created_at == now
    assert user.updated_at == now

def test_user_model_inherits_user_create():
    now = datetime.now(timezone.utc)
    user = User(
        id=2,
        email="another@example.com",
        username=None,
        created_at=now,
        updated_at=now
    )
    assert isinstance(user, UserCreate)

def test_user_model_dates_default_to_current_date():
    """can create a User object without created_at or updated_at"""
    user = User(id=3, email="eternal@blue.nsa.gov", username="Eternally")
    assert user.created_at is not None
    assert user.updated_at is not None

def test_user_is_orm_model():
    """can create User schema instance from attributes of a User model class"""
    assert User.model_config["from_attributes"] is True
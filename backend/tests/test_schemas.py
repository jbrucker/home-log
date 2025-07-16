import pytest
from pydantic import ValidationError
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

def test_user_schema_fields():
    """test that programmer is not incompetent"""
    now = datetime(2025, 1, 31, 12, 0, 0, tzinfo=timezone.utc)
    user = User(
        email="user@example.com",
        username="user1",
        created_at=now,
        updated_at=now
    )
    # Schema may not have an id field, so don't verify that
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

def test_validators_accept_non_latin_chars():
    """Validators should allow name and email to contain non-latin characters."""
    my_name = "กำโด่่ฑ้อยใเยิ็นให้ผูฟอห์ กำโด่่ฑ้อยใเยิ็นให้ผูฟอห์"
    my_email = "กำโด่่ฑ้อยใเยิ็นให้ผูฟอห์กำโด่่ฑ้อยใเยิ็นให้ผูฟอห์@foomail.co.uk"
    user = User(username = my_name, email=my_email)
    assert user.username == my_name
    assert user.email == my_email

def test_invalid_email_address():
    """Validator rejects invalid email addresses."""
    for bogus_mail in ["foobar@gmail", "no space@gmail.com", "nospace @gmail.com",
                       "<specialchars>@gmail.com",
                       r"escape\\me@gmail.com", r"[brackets]for-all@gmail.com"]:
        with pytest.raises(ValidationError):
            user = User(username="Bad User", email=bogus_mail)
            pytest.fail(reason=f"User schema accepted email={bogus_mail}")

def test_validators_enforce_length_limit():
    """string fields all have length limits"""
    # email should never exceed 160 chars total length
    long_email = f"{'a123456789'*16}@gmail.com"
    assert len(long_email) > 160
    with pytest.raises(ValidationError):
        user = User(
                email=long_email,
                username="user1"
                )
        pytest.fail(reason=f"Schema accepted too long email (len(long_email) chars)")
    # Username should be < config.MAX_NAME which is certainly <= 200
    long_username = "Buffer Overruns for Fun " * 10
    with pytest.raises(ValidationError):
        user = User(
                email="harryhacker@hackers.com",
                username=long_username
                )
        assert len(user.username) < 200, "Schema accepted too long username"


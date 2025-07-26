"""Unit tests of persistenc operations for models.User."""
import asyncio
from datetime import datetime
import pytest, pytest_asyncio
from sqlalchemy.exc import IntegrityError
from app.models import User
from .utils import as_utc_time, is_timezone_aware
# Import of session fixture is necessary
from .fixtures import db, session

# Ignore F811 Parameter name shadows import
# flake8: noqa: F811


@pytest.fixture
def user_data() -> dict:
    """inject a dict of user attributes for create-user-myself tests."""
    return {
        "username": "testuser",
        "email": "testuser@example.com"
    }


@pytest_asyncio.fixture()
async def user(session, user_data) -> User:
    """Inject a persisted user model into the session"""
    user = User(**user_data)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_create_user(session, user_data: dict):
    user = User(**user_data)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    assert user.id is not None
    assert user.username == user_data["username"]
    assert isinstance(user.created_at, datetime)


@pytest.mark.asyncio
async def test_create_and_update_dates(session, user):
    """created_at and updated_at are automatically set and updated."""
    assert isinstance(user.created_at, datetime), "user.created_at should be datetime but is {type(user.created_at).__name__}"
    assert isinstance(user.updated_at, datetime), "user.created_at should be datetime but is {type(user.updated_at).__name__}"
    # initially both dates should be nearly the same
    delta = user.updated_at - user.created_at
    assert abs(delta.microseconds <= 500000)  # allow for imprecise timestamps
    # update some attribute and retest create & update times
    last_update = user.updated_at
    user.username = "Born again user"
    session.add(user)
    await session.commit()
    await session.refresh(user)
    new_update = user.updated_at
    assert as_utc_time(new_update) > as_utc_time(last_update), "user.updated_at not modified by update"


@pytest.mark.skipif(str(db.engine.url).startswith("sqlite"),
                    reason="SQLite does not return timezone aware datetime")
@pytest.mark.asyncio
async def test_dates_are_timezone_aware(session, user):
    """created_at and updated_at should return timezone-aware datetime instances."""
    assert is_timezone_aware(user.created_at), "user.created_at is not timezone aware"
    assert is_timezone_aware(user.updated_at), "user.updated_at is not timezone aware"
    # update the user and recheck `updated_at` is still timezone aware
    user.username = "Anonymous"
    session.add(user)
    await session.commit()
    await session.refresh(user)
    assert is_timezone_aware(user.updated_at), "after update, user.updated_at is not timezone-aware"


@pytest.mark.asyncio
async def test_unique_email(session, user_data: dict):
    """User's email must be unique."""
    user1 = User(**user_data)
    session.add(user1)
    await session.commit()
    # another user with same email
    user_data["username"] = "User 2. We try harder"
    user2 = User(**user_data)
    session.add(user2)
    with pytest.raises(IntegrityError):
        await session.commit()
        await session.rollback()


@pytest.mark.asyncio
async def test_update_user_email(session, user):
    """Can update a user's email and the updated_at timestamp changes."""
    last_update = user.updated_at
    assert last_update is not None, "Create user did not set updated_at"
    new_email = "newemail@example.com"
    user.email = new_email
    await asyncio.sleep(0.5)  # seconds, to ensure updated_at > last_update
    session.add(user)
    await session.commit()
    updated_user = await session.get(User, user.id)
    assert updated_user.email == new_email
    assert as_utc_time(updated_user.updated_at) > as_utc_time(last_update)


@pytest.mark.asyncio
async def test_delete_user(session, user):
    """We can delete a user using the session."""
    # user is already persisted
    assert user.id > 0
    user_id = user.id
    await session.delete(user)
    await session.commit()
    deleted_user = await session.get(User, user_id)
    assert deleted_user is None


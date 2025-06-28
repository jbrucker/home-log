"""Unit tests of persistenc operations for models.User."""
import pytest
from sqlalchemy.exc import IntegrityError
from app.models import User


@pytest.fixture
def user_data() -> dict:
    return {
        "username": "testuser",
        "email": "testuser@example.com"
    }

@pytest.mark.skip("Not finished. Not async")
def test_create_user(session, user_data):
    user = User(**user_data)
    session.add(user)
    session.commit()
    assert user.id is not None
    assert user.username == user_data["username"]

@pytest.mark.skip("Not finished. Not async")
def test_unique_username(session, user_data):
    user1 = User(**user_data)
    session.add(user1)
    session.commit()
    user2 = User(**user_data)
    session.add(user2)
    with pytest.raises(IntegrityError):
        session.commit()
        session.rollback()

@pytest.mark.skip("Not finished. Not async")
def test_update_user_email(session, user):
    new_email = "newemail@example.com"
    user.email = new_email
    session.commit()
    updated_user = session.get(User, user.id)
    assert updated_user.email == new_email

@pytest.mark.skip("Not finished. Not async")
def test_delete_user(session, user):
    session.delete(user)
    session.commit()
    deleted = session.get(User, user.id)
    assert deleted is None

@pytest.mark.skip("Not implemented")
def test_password_is_hashed(user_data):
    user = User(**user_data)
    assert user.password != user_data["password"]

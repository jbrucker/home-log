"""Tests for the user_dao module.

   Requires pytest-asyncio be installed for async support.
"""
import pytest
import sqlalchemy

from app import models, schemas
from app.data_access import user_dao
from .fixtures import session
from .utils import EMAIL_DOMAIN, create_users

# Ignore F811 Parameter name shadows import
# flake8: noqa: F811


@pytest.mark.asyncio
async def test_create_user(session):
    """Can add a user to database using dao.create_user with UserCreate schema object."""
    new_user = schemas.UserCreate(email="anonymous@hackers.com", username="Hacker")
    # my DAO return model objects, not schema objects
    user = await user_dao.create(session, new_user)
    assert isinstance(user, models.User)
    # model should be fully populated
    assert user.id > 0
    assert user.username == "Hacker"
    assert user.email == "anonymous@hackers.com"
    assert user.created_at is not None

@pytest.mark.asyncio
async def test_get_user_by_id(session):
    """get_user_by_id returns a User or None."""
    new_user = schemas.UserCreate(email="anonymous@hackers.com", username="Hacker")
    # my DAO return model objects, not schema objects
    user = await user_dao.create(session, new_user)
    assert isinstance(user, models.User)
    # model should be fully populated
    assert user.id > 0
    # get Hacker again
    result = await user_dao.get(session, user.id)
    assert result.email == user.email
    assert result.username == user.username
    # get non-existent user
    result = await user_dao.get(session, 999999)
    assert result is None

@pytest.mark.asyncio
async def test_get_user_by_email(session):
    """get_user_by_email returns a User or None."""
    await create_users(session, 5)  # "User1", "User2", ...
    # get each user
    for user_num in range(1,6):
        email = f"user{user_num}@{EMAIL_DOMAIN}"
        result = await user_dao.get_by_email(session, email=email)
        assert result is not None, f"Failed to get User for email {email}"
        assert isinstance(result, models.User), f"get_user_by_email returned a {type(result).__name__}"
        assert result.email == email
    # non-existent user
    result = await user_dao.get_by_email(session, "completely-bogus-user@bitnet")
    assert result is None


@pytest.mark.asyncio
async def test_email_must_be_unique(session):
    """Cannot add 2 users with the same email."""
    new_user1 = schemas.UserCreate(email="testhacker@hackers.com", username="Hacker")
    # my DAO return model objects, not schema objects
    user1 = await user_dao.create(session, new_user1)
    assert isinstance(user1, models.User)
    # Need to put `pytest.raises` outside the session context
    # because it will rollback the session if an exception occurs.
    # If the exception occurs inside the session context, it will not be caught.
    with pytest.raises(sqlalchemy.exc.SQLAlchemyError):
        #async for session in db.get_session():
        # should fail
        new_user2 = schemas.UserCreate(email=user1.email, username="Duplicate User")
        user2 = await user_dao.create(session, new_user2)
        assert user2 is None


@pytest.mark.asyncio
async def test_update_user_success(session):
    """Can update an existing user's email and username; updated_at is updated automatically."""
    # Create a user first
    new_user = schemas.UserCreate(email="oldself@email.com", username="Old Self")
    user = await user_dao.create(session, new_user)
    user_id = user.id

    #async with db.get_session() as session:
    updated_data = schemas.UserCreate(email="renamed@email.com", username="NewName")
    updated_user = await user_dao.update(session, user_id, updated_data)
    assert updated_user is not None
    assert updated_user.id == user_id
    assert updated_user.email == "renamed@email.com"
    assert updated_user.username == "NewName"
    assert updated_user.updated_at is not None
    assert updated_user.created_at == user.created_at  # created_at should not change
    # this could fail. Timestamp granularity depends on database
    assert updated_user.updated_at > user.created_at


@pytest.mark.asyncio
async def test_update_user_nonexistent(session):
    """Updating a non-existent user returns None."""
    #async with db.get_session() as session:
    updated_data = schemas.UserCreate(email="doesnot@exist.com", username="Nobody")
    with pytest.raises(ValueError):
        updated_user = await user_dao.update(session, 99999, updated_data)
        assert updated_user is None


@pytest.mark.asyncio
async def test_update_user_email_unique_constraint(session):
    """Updating a user to an email that already exists should raise an IntegrityError."""
    await create_users(session, 2)
    # Get both users
    #async with db.get_session() as session:
    users = await user_dao.get_users(session)
    user1, user2 = users[0], users[1]
    # Try to update user2's email to user1's email
    with pytest.raises(sqlalchemy.exc.SQLAlchemyError):
        #async with db.get_session() as session:
        updated_data = schemas.UserCreate(email=user1.email, username="NewName")
        await user_dao.update(session, user2.id, updated_data)


@pytest.mark.asyncio
async def test_get_all_users(session):
    """get_users should return all users in the database, ordered by id."""
    await create_users(session, 3)
    #async with db.get_session() as session:
    users = await user_dao.get_users(session)
    assert len(users) == 3
    assert users[0].username == "User1"
    assert users[1].username == "User2"
    assert users[2].username == "User3"
    # Ensure results are ordered by id
    ids = [user.id for user in users]
    assert ids == sorted(ids)


@pytest.mark.asyncio
async def test_get_users_with_limit(session):
    """get_users should respect the limit parameter."""
    await create_users(session, 10)
    #async with db.get_session() as session:
    users = await user_dao.get_users(session, limit=4)
    assert len(users) == 4
    assert users[0].username == "User1"
    assert users[1].username == "User2"
    assert users[2].username == "User3"
    assert users[3].username == "User4"


@pytest.mark.asyncio
async def test_get_users_with_offset_and_limit(session):
    """get_users should respect the offset and limit parameters."""
    await create_users(session, 20)
    #async with db.get_session() as session:
    users = await user_dao.get_users(session, offset=0, limit=2)
    assert len(users) == 2
    assert users[0].username == "User1"
    assert users[1].username == "User2"
    users = await user_dao.get_users(session, offset=5, limit=1)
    assert len(users) == 1
    assert users[0].username == "User6"
    users = await user_dao.get_users(session, offset=10, limit=5)
    assert len(users) == 5
    assert users[0].username == "User11"
    assert users[1].username == "User12"
    assert users[2].username == "User13"
    assert users[3].username == "User14"
    assert users[4].username == "User15"


@pytest.mark.asyncio
async def test_get_users_may_be_empty(session):
    """get_users should return an empty list if there are no users."""
    users = await user_dao.get_users(session)
    assert users == []


@pytest.mark.asyncio
async def test_find_users_with_condition(session):
    """find_users with a specified condition."""
    domain_to_find = "noway.org.no"
    await create_users(session, 15)
    # more users with a different domain
    await create_users(session, 20, email_domain=domain_to_find)
    users = await user_dao.find(session, models.User.email.contains(domain_to_find), offset=10, limit=5)
    assert len(users) == 5
    for user in users:
        # We created 15 users with default domain first + skip 10 matching specific domain -> min id should be 26
        assert user.id > 25, f"find_users didn't skip first 10 matching users, returned user with id {user.id}"
        assert domain_to_find in user.email, f"find_users returned non-matching result: {str(user)}"


@pytest.mark.asyncio
async def test_find_users_with_offset_and_limit(session):
    """find_users applies limit and offset."""
    await create_users(session, 50)
    users = await user_dao.find(session, offset=12, limit=7)
    assert len(users) == 7, f"Specified limit=7 but got {len(users)} results"
    for user in users:
        assert user.id > 12, f"Specified offset=12, returned find_users returned user with id {user.id}"


@pytest.mark.asyncio
async def test_delete_user(session):
    """Can delete a user by id."""
    await create_users(session, 10)
    users = await user_dao.get_users(session)
    # delete user #2
    user_to_delete = users[1]
    assert user_to_delete.id > 0, "User does not have id"
    # delete_user returns the deleted user on success, None otherwise
    deleted = await user_dao.delete_user(session, user_to_delete.id)
    assert deleted is not None
    assert deleted.email == user_to_delete.email, "Deleted wrong user."
    # Verify user is *really* deleted
    deleted_user = await user_dao.get(session, user_to_delete.id)
    assert deleted_user is None
    # Did not delete adjacent user
    other_user = await user_dao.get(session, users[0].id)
    assert other_user.email == users[0].email

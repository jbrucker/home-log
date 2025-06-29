"""Tests for the user_dao module.
   Requires pytest-asyncio be installed for async support.
"""
import pytest
# TODO  Eliminate Framework dependency by defining generic Exceptions
import sqlalchemy
from app import models, schemas
from app.data_access import user_dao
from .fixtures import db, session


async def create_users(howmany: int):
    """Create multiple users.  Assumes database and User table already initialized."""
    # TODO: Use same Session as the test method, or a separate Session?
    async for session in db.get_session():
        for n in range(1, howmany+1):
            username = f"Tester{n}"
            email = f"{username.lower()}@yahoo.com"
            session.add(models.User(username=username, email=email))
        await session.commit()
    print(f"Added {n} users")

@pytest.mark.asyncio
async def test_create_user(session):
    """Can add a user to database using dao.create_user with UserCreate schema object"""
    new_user = schemas.UserCreate(email="anonymous@hackers.com", username="Hacker")
    # my DAO return model objects, not schema objects
    user = await user_dao.create_user(session, new_user)
    assert isinstance(user, models.User)
    # model should be fully populated
    assert user.id > 0
    assert user.username == "Hacker"
    assert user.email == "anonymous@hackers.com"
    assert user.created_at is not None

@pytest.mark.asyncio
async def test_email_must_be_unique(session):
    """Cannot add 2 users with the same email"""
    new_user1 = schemas.UserCreate(email="tester@hackers.com", username="Tester")
    # my DAO return model objects, not schema objects
    user1 = await user_dao.create_user(session, new_user1)
    assert isinstance(user1, models.User)
    # Need to put `pytest.raises` outside the session context
    # because it will rollback the session if an exception occurs.
    # If the exception occurs inside the session context, it will not be caught.
    with pytest.raises(sqlalchemy.exc.SQLAlchemyError):
        #async for session in db.get_session():   
        # should fail
        new_user2 = schemas.UserCreate(email=user1.email, username="Duplicate User")
        user2 = await user_dao.create_user(session, new_user2)
        assert user2 is None
    
@pytest.mark.asyncio
async def test_update_user_success(session):
    """Can update an existing user's email and username; updated_at is updated automatically."""
    # Create a user first
    new_user = schemas.UserCreate(email="oldself@email.com", username="Old Self")
    user = await user_dao.create_user(session, new_user)
    user_id = user.id

    #async with db.get_session() as session:
    updated_data = schemas.UserCreate(email="renamed@email.com", username="NewName")
    updated_user = await user_dao.update_user(session, user_id, updated_data)
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
    updated_user = await user_dao.update_user(session, 9999, updated_data)
    assert updated_user is None

@pytest.mark.asyncio
async def test_update_user_email_unique_constraint(session):
    """Updating a user to an email that already exists should raise an IntegrityError."""
    await create_users(2)
    # Get both users
    #async with db.get_session() as session:
    users = await user_dao.get_users(session)
    user1, user2 = users[0], users[1]
    # Try to update user2's email to user1's email
    with pytest.raises(sqlalchemy.exc.SQLAlchemyError):
        #async with db.get_session() as session:
        updated_data = schemas.UserCreate(email=user1.email, username="NewName")
        await user_dao.update_user(session, user2.id, updated_data)


@pytest.mark.asyncio
async def test_get_all_users(session):
    """get_users should return all users in the database, ordered by id."""
    await create_users(3)
    #async with db.get_session() as session:
    users = await user_dao.get_users(session)
    assert len(users) == 3
    assert users[0].username == "Tester1"
    assert users[1].username == "Tester2"
    assert users[2].username == "Tester3"
    # Ensure results are ordered by id
    ids = [user.id for user in users]
    assert ids == sorted(ids)

@pytest.mark.asyncio
async def test_get_users_with_limit(session):
    """get_users should respect the limit parameter."""
    await create_users(10)
    #async with db.get_session() as session:
    users = await user_dao.get_users(session, limit=3)
    assert len(users) == 3
    assert users[0].username == "Tester1"
    assert users[1].username == "Tester2"
    assert users[2].username == "Tester3"

@pytest.mark.asyncio
async def test_get_users_may_be_empty(session):
    """get_users should return an empty list if there are no users."""
    users = await user_dao.get_users(session)
    assert users == []

@pytest.mark.asyncio
async def test_delete_user(session):
    """Can delete a user by id."""
    await create_users(10)
    users = await user_dao.get_users(session)
    # delete user #2
    user_to_delete = users[1]
    # delete_user returns the deleted user on success, None otherwise
    deleted = await user_dao.delete_user(session, user_to_delete.id)
    assert deleted is not None
    assert deleted.email == user_to_delete.email, "Deleted wrong user."
    # Verify user is deleted
    ghost_user = await user_dao.get_user_by_id(session, user_to_delete.id)
    assert ghost_user is None


@pytest.mark.asyncio
async def test_set_user_password(session):
    """Can set a password for a user and it is saved in hashed form."""
    pass

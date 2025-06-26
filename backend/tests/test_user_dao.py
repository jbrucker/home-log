"""Tests for the user_dao module.
   Requires pytest-asyncio be installed for async support.
"""
import pytest, pytest_asyncio
from app.core.database import db, Base
from app import models, schemas
from app.data_access import user_dao
# TODO  Eliminate Framework dependency by defining generic Exceptions
import sqlalchemy

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture() # fixture(autouse=True)
async def setUp():
    """Use a temporary in-memory database for tests"""
    db.create_engine(TEST_DATABASE_URL)
    assert db.database_url == TEST_DATABASE_URL
    print("Database engine url", str(db.engine.url))
    assert str(db.engine.url) == TEST_DATABASE_URL
    await db.create_tables()  # Create tables before each test
    # Optionally, you can add code to insert sample data here
    try:
        yield
    finally:
        await db.destroy_tables()
        print("Destroy database tables")
        

async def create_users(howmany: int):
    """Create multiple users.  Requires database and table already initialized."""
    async with db.get_session() as session:
        for n in range(1,howmany+1):
            username = f"Tester{n}"
            email = f"{username.lower()}@yahoo.com"
            session.add(models.User(username=username, email=email))
        await session.commit()
    print(f"Added {n} users")

@pytest.mark.asyncio
async def test_create_user(setUp):
    """Can add a user to database using dao.create_user with UserCreate schema object"""
    async with db.get_session() as session:
        new_user = schemas.UserCreate(email="tester@hackers.com", username="Tester")
        # my DAO return model objects, not schema objects
        user = await user_dao.create_user(session, new_user)
        assert isinstance(user, models.User)
        # model should be fully populated
        assert user.id > 0
        assert user.username == "Tester"
        assert user.email == "tester@hackers.com"
        assert user.created_at is not None

@pytest.mark.asyncio
async def test_email_must_be_unique(setUp):
    """Cannot add 2 users with the same email"""
    async with db.get_session() as session:
        new_user1 = schemas.UserCreate(email="tester@hackers.com", username="Tester")
        # my DAO return model objects, not schema objects
        user1 = await user_dao.create_user(session, new_user1)
        assert isinstance(user1, models.User)
        # should fail
        new_user2 = schemas.UserCreate(email=user1.email, username="Duplicate User")
        # TODO check for specific exception. sqlalchemy.exc.IntegrityError didn't work
        with pytest.raises(sqlalchemy.exc.SQLAlchemyError):
            user2 = await user_dao.create_user(session, new_user2)
            assert user2 is None

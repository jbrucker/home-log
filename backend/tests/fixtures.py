"""Fixtures for unit testing.

   To verify fixtures are found use:  pytest --fixtures

"""

#from sqlalchemy.ext.asyncio import AsyncSession
import logging
import pytest, pytest_asyncio
from fastapi.testclient import TestClient
import pytest, pytest_asyncio
from app.core import security
from app.core.database import db
# Must import models so that db.create_tables() can create the table schema
from app import main, models

AUTH_USER_EMAIL = "admin@localhost.com"
AUTH_USER_PASSWORD = "MakeMyDay"

"""Use a temporary database for tests"""
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# db = Database()
db.create_engine(TEST_DATABASE_URL)
print("Database engine url", str(db.engine.url))
assert str(db.engine.url) == TEST_DATABASE_URL


# A session-level "fixture" for logging. scope="session" means it is used only once.
@pytest.fixture(scope="session", autouse=True)
def setup():
    from .conftest import configure_logging
    configure_logging()
    logging.getLogger("fixtures").info("Logging initialized")
    file = open("/tmp/pytest_config.txt", mode="a")
    file.write("Running pytest session fixture 'setup'")
    file.close()

@pytest_asyncio.fixture()
async def session():
    """Test fixture that yields an AsyncSession for use in a test."""
    # Create tables before each test
    await db.destroy_tables()
    await db.create_tables()  
    try:
        async for session in db.get_session():
            yield session
    finally:
        await session.close()

@pytest_asyncio.fixture()
async def auth_user(session):
    """Create a user for use in other tests."""
    user = models.User(username="admin", email=AUTH_USER_EMAIL)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    user_password = models.UserPassword(
                        hashed_password=security.hash_password(AUTH_USER_PASSWORD),
                        user_id=user.id
                    )
    session.add(user_password)
    await session.commit()
    return user

@pytest.fixture()
async def async_client():
    """Async test fixture for client -- doesn't work as FastAPI test client.
       Use the `client` fixture instead.
    """
    from httpx import AsyncClient
    async with AsyncClient(app=main.app) as client:
        yield client

@pytest.fixture()
def client():
    """Test fixture for calls to FastAPI route endpoints."""
    #main.app.dependency_overrides[get_session] = db.get_session
    yield TestClient(main.app)

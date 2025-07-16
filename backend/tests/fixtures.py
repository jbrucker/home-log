"""Fixtures for unit testing.

   To verify fixtures are found use:  pytest --fixtures

   A test database is configured in conftest.py, pytest_sessionstart().
"""

import logging
import pytest, pytest_asyncio
from fastapi.testclient import TestClient
from app.core import security
from app.core.database import db
# Must import models so that db.create_tables() can create the table schema
from app import main, models, schemas
from app.data_access import user_dao
from .conftest import TEST_DATABASE_URL

AUTH_USER_EMAIL = "admin@localhost.com"
AUTH_USER_PASSWORD = "MakeMyDay"


# A session-level "fixture" for logging. scope="session" means it is used only once.
# BUG: pytest_asyncio.fixture does not honor the `scope=` parameter.
# @pytest_asyncio.fixture(scope="session")
# PROBLEM: You can't use a synchronous fixture as a fixture parameter in an async fixture.
# WORK-AROUND: Put all session-level test configuration in conftext.py
@pytest.fixture(scope="session")
def globalsetup():
    """Perform global configuration, but this is never invoked."""
    from .conftest import configure_logging, event_log
    event_log("Run fixtures.globalsetup()")
    configure_logging()
    logging.getLogger("fixtures").info(f"Logging initialized by {__name__} fixture")
    yield
    # run after all tests
    event_log("Finish fixtures.globalsetup() after yield")


@pytest_asyncio.fixture()
async def session():
    """Test fixture that yields an AsyncSession for use in a test."""
    # Create tables before each test?
    assert str(db.engine.url) == TEST_DATABASE_URL, \
           f"Are you using a test database? Got db URL {str(db.engine.url)}"
    await db.destroy_tables()
    await db.create_tables()
    # Or delete data from tables? Should be faster and less I/O.
    # await db.delete_all_data2(models.Base)
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
    """Async test fixture for client, DOES NOT WORK as FastAPI test client.
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


@pytest_asyncio.fixture()
async def alexa(session):
    """Test fixture for a user entity named Alexa."""
    new_user = schemas.UserCreate(email="alexa@amazon.com", username="Alexa")
    user = await user_dao.create(session, new_user)
    assert user.id > 0, "Persisted user should have id > 0"
    return user


@pytest_asyncio.fixture()
async def sally(session):
    """Test fixture for a user entity named Sally."""
    new_user = schemas.UserCreate(email="sally@yahoo.com", username="Sally")
    user = await user_dao.create(session, new_user)
    assert user.id > 0, "Persisted user should have id > 0"
    return user

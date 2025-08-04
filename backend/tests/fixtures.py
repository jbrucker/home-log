"""Fixtures for unit testing.

   To verify the fixtures are found use:  pytest --fixtures

   A test database is configured in conftest.py: pytest_sessionstart().

   I removed the "globalsetup" fixture because it was not being invoked:
   @pytest.fixture(scope="session")
   def globalsetup(session):
       configure_logging()
       logging.getLogger("fixtures").info(f"Logging initialized by {__name__}")
       yield
       # run this after all tests
       event_log("Finish fixtures.globalsetup() after yield")

   Instead, do session-level initialization and teardown in conftest.py

   Another BUG: pytest_asyncio.fixture does not honor the `scope=` parameter.
   Problem:  You can't use a synchronous fixture as a fixture parameter
             in an async fixture.
   This doesn't work:
   @pytest_asyncio.fixture(scope="session")
   def myfixture(session):
"""
# flake8: noqa: D401 First line should be in imperative mood

from typing import Generator
import pytest, pytest_asyncio
import fastapi.testclient
from app.core import security
from app.core.database import db
# Must import models so that db.create_tables() can create the table schema
from app import main, models, schemas
from app.data_access import user_dao
from .conftest import TEST_DATABASE_URL

AUTH_USER_EMAIL = "admin@localhost.com"
AUTH_USER_PASSWORD = "MakeMyDay"


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
async def auth_user(session) -> models.User:
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
def client(): # -> Generator[fastapi.testclient.TestClient]
    """Test fixture for calls to FastAPI route endpoints."""
    # main.app.dependency_overrides[get_session] = db.get_session
    yield fastapi.testclient.TestClient(main.app)


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


@pytest_asyncio.fixture()
async def user1(session) -> models.User:
    """Fixture to inject a User model that is owner of DataSource 1 (ds1)."""
    user = models.User(username="User 1", email="user1@mydomain.com")
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest_asyncio.fixture()
async def user2(session) -> models.User:
    """Fixture to inject a User model that is owner of DataSource 2 (ds2)."""
    user = models.User(username="User 2", email="user2@mydomain.com")
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest_asyncio.fixture()
async def ds1(session, user1: models.User) -> models.DataSource:
    """A DataSource owned by user1."""
    ds = models.DataSource(
        name="Data Source 1",
        description="A data source with 1 component",
        metrics={"Energy": "kWh"},
        owner_id=user1.id
    )
    session.add(ds)
    await session.commit()
    await session.refresh(ds)
    return ds


@pytest_asyncio.fixture()
async def ds2(session, user2: models.User) -> models.DataSource:
    """A DataSource owned by user2 with 2 data components."""
    ds = models.DataSource(
        name="Data Source 2",
        description="A data source with 2 component",
        metrics={"first": "unit1", "second": "unit2"},
        owner_id=user2.id
    )
    session.add(ds)
    await session.commit()
    await session.refresh(ds)
    return ds

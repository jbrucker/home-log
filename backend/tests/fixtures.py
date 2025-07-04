"""Fixtures for testing database and routers."""

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient
import pytest, pytest_asyncio
from app.core import security
from app.core.database import db
# Must import models so that db.create_tables() can create the table schema
from app import main, models, schemas


"""Use a temporary database for tests"""
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
db.create_engine(TEST_DATABASE_URL)
assert db.database_url == TEST_DATABASE_URL
print("Database engine url", str(db.engine.url))
assert str(db.engine.url) == TEST_DATABASE_URL

AUTH_PASSWORD = "Make My Day"

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
    user = models.User(username="admin", email="root@localhost.com")
    session.add(user)
    await session.commit()
    await session.refresh(user)
    user_password = models.UserPassword(
                        hashed_password=security.hash_password(AUTH_PASSWORD),
                        user_id=user.id
                    )
    session.add(user_password)
    await session.commit()
    return user

@pytest.fixture()
def client():
    """Test fixture for calls to FastAPI route endpoints."""
    #app.dependency_overrides[get_session] = override_get_session
    yield TestClient(main.app)
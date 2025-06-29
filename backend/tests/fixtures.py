"""Fixtures for testing database and routers."""

from fastapi.testclient import TestClient
import pytest, pytest_asyncio
from app.core.database import db
# Must import models so that db.create_tables() can create the table schema
from app import main, models, schemas


"""Use a temporary database for tests"""
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
db.create_engine(TEST_DATABASE_URL)
assert db.database_url == TEST_DATABASE_URL
print("Database engine url", str(db.engine.url))
assert str(db.engine.url) == TEST_DATABASE_URL

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


@pytest.fixture()
def client():
    """Test fixture for calls to FastAPI route endpoints."""
    #app.dependency_overrides[get_session] = override_get_session
    yield TestClient(main.app)
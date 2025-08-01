"""Test that the database connection is available and async works.

   Test overriding values in .env by setting an envvar in code.
"""
import os
from typing import AsyncGenerator
from app.core.database import db


def test_env_vars():
    """Cannot set environment vars from within a test (different shell)."""
    old_database_url = os.getenv("DATABASE_URL", "")
    db_url = "sqlite:///localhost/fake.sqlite"
    # Doesn't work!  Each system() command is a separate process?
    os.system(f"export DATABASE_URL={db_url}")
    assert os.getenv("DATABASE_URL", "") == old_database_url, "Database URL changed by os.system!"
    # attempt to restore old database url
    if old_database_url:
        os.system(f"export DATABASE_URL={old_database_url}")


def test_database_connection():
    """`database` module provides access to a possibly async database connection."""
    print("Database engine is", type(db.engine))
    print("Database URL is", db.engine.url)
    session = db.get_session()
    print("db.get_session returned", type(session))
    assert isinstance(session, AsyncGenerator)


def test_create_engine():
    """We can change the database engine, database connection, and session maker."""
    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
    database_url = "sqlite+aiosqlite:///:memory:"  # in-memory SQLite database
    db.create_engine(database_url)
    print("New database engine is", type(db.engine))
    print("New database URL is", db.engine.url)
    assert db.database_url == database_url
    # strings look same, but are not the same object
    assert str(db.engine.url) == database_url
    assert isinstance(db.engine, AsyncEngine)
    session = db.get_session()
    print("db.get_session returned", type(session))
    assert not isinstance(session, AsyncSession), "session is not an AsyncSession"
    assert isinstance(session, AsyncGenerator), "session is not an AsyncGenerator"


if __name__ == '__main__':
    test_env_vars()
    test_database_connection()

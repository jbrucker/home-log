"""Test that the database connection is available and async works.

   Test overriding values in .env by setting an envvar in code.
"""
import os
from typing import AsyncGenerator
from decouple import config

def test_env_vars():
    #os.setenv("DATABASE_URL", "sqlite:///localhost/test.sqlite")
    print("Set DATABASE_URL envvar")
    # Doesn't work!  Each system() command is a separate process?
    os.system("DATABASE_URL=sqlite:///localhost/test.sqlite")
    database_url = config("DATABASE_URL", default="No database URL set!")
    print(f"DATABASE_URL = {database_url}")

from app.core.database import db

def test_database_connection():
    """`database` module provides access to a possibly async database connection"""
    print("Database engine is", type(db.engine))
    print("Database URL is", db.engine.url)
    session = db.get_session()
    print("db.get_session returned", type(session))

def test_create_engine():
    """We can change the database engine, database connection, and session maker."""
    from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncEngine, AsyncSession
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

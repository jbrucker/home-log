"""A globally accessible connection to the database.

    db - a shared instance of database.
    db.get_session() - get an async session object for the database
    db.create_tables - create table schema using SqlAlchemy ORM model classes 
       defined using `Base` from this module.
       This is optional -- you can create schema in many ways.
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings


class Base(AsyncAttrs, DeclarativeBase):
    """
    SqlAlchemy 2.0 recommended style for the ORM base class used in database models.
    `AsyncAttrs` is necessary to support async operations like:
     - await user.refresh() or await user.load()
    `AsyncAttrs` does *NOT* make your model classes async, it makes
    model instances support async operations like async_session.
    """
    pass


class Database:
    """A globally accessible database connection manager."""

    engine: AsyncEngine

    def __init__(self) -> None:
        if not settings.database_url:
            raise ValueError("database_url is not set in config.Settings.")
        self.create_engine(settings.database_url)

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Async context manager that yields a generator for creating an AsyncSession,
          and ensures it's closed after commit.

        :returns: async_sessionmaker[AsyncSession]
        """
        async with self.asyncSessionMaker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    def create_engine(self, database_url: str) -> None:
        """Create an async engine and async sessionmaker and save as attributes.

           :param database_url: URL of an async database.
           :raises Exception: If the engine creation fails.
        """
        try:
            self.engine: AsyncEngine = create_async_engine(
                database_url,
                echo=True,   # Log SQL queries (useful for development)
                future=True  # Use SQLAlchemy 2.0 style APIs
            )
            # if that worked, set the database_url
            self.database_url = database_url
        except Exception as ex:
            logging.error(f"Failed to create async engine for {database_url}: {ex}")
            raise ex

        self.asyncSessionMaker = async_sessionmaker(
            self.engine,
            # class_=AsyncSession,
            expire_on_commit=False,  # SqlAlchemy recommends avoid expire on commit for async
            future=True              # Use SqlAlchemy 2.0 style API?
        )

    async def create_tables(self):
        """Create all tables in the database. Used for testing."""
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

# Shared database instance 
db = Database()

"""A globally accessible connection to the database.

    db - a shared instance of database.
    db.get_session() - get an async session object for the database
    db.create_tables - create table schema using SqlAlchemy ORM model classes 
       defined using `Base` from this module.
       This is optional -- you can create schema in many ways.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# SqlAlchemy 2.0 recommended style for defining ORM base class.
# AsyncAttrs is necessary to support async operations like:
# .await user.refresh() or .await user.load()
# AsyncAttrs does *NOT* make your model classes async, it makes
# model instances support async operations like async_session.

class Base(AsyncAttrs, DeclarativeBase):
    pass

class Database:
    def __init__(self) -> None:
        self.database_url = settings.database_url
        
        # Create async engine
        self.engine: AsyncEngine = create_async_engine(
            self.database_url,
            echo=True,   # Log SQL queries (useful for development)
            future=True  # Use SQLAlchemy 2.0 style APIs
        )

        self.AsyncSessionLocal = async_sessionmaker(
            self.engine,
            # class_=AsyncSession,
            expire_on_commit=False,  # SqlAlchemy recommends avoid expire on commit
            future=True              # Use SqlAlchemy 2.0 style API?
        )

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Async context manager that yields a session and ensures it's closed after commit."""
        async with self.AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def create_tables(self):
        """Create all tables in the database. Used for testing."""
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)


# Shared database instance 
db = Database()

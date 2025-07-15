"""A globally accessible connection to the database.

    db                 a shared instance of the Database class.
    db.create_engine(url) change the URL of the database engine and connection.
                       This is intended for running tests.
    db.get_session() - an async generator for AsyncSession objects
    db.create_tables - create table schema using SqlAlchemy ORM model classes 
                       defined using `Base` from this module.
    db.delete_tables - delete table schema

    Use of `db.create_tables` is optional -- you can create schema in many ways.
"""
import asyncio
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

    def __init__(self, database_url: str = None) -> None:
        if database_url:
            settings.database_url = database_url
        elif not settings.database_url:
            raise ValueError("database_url is not set in config.Settings.")
        self.create_engine(settings.database_url)

    # The asynccontextmanager annotation causes an error 
    # with FastAPI's `Depends(...)` because FastAPI expects  
    # a callable returning `Awaitable` or `AsyncGenerator`,
    # not a context manager function.
    ##@asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Yields a generator for creating AsyncSession
          and ensures it's closed after commit.

        :returns: AsyncGenerator[AsyncSession]
        """
        async with self.async_sessionmaker() as session:
            try:
                yield session
                # code using the session calls session.commit() itself, if needed.
                # await session.commit()
            except Exception as ex:
                await session.rollback()
                raise
                # Or wrap the exception (abstraction):
                # raise Exception(f"Database operation failed: {ex}")
            finally:
                await session.close()

    def create_engine(self, database_url: str) -> None:
        """Create an async engine and async sessionmaker as attributes.

           :param database_url: URL of an async database.
           :raises Exception: If the engine creation fails.
        """
        try:
            self.engine: AsyncEngine = create_async_engine(
                database_url,
                echo=False,   # Log SQL queries (useful for development)
                future=True   # Use SQLAlchemy 2.0 style APIs
            )
            # if that worked, set the database_url
            self.database_url = database_url
        except Exception as ex:
            logging.error(f"Failed to create async engine for {database_url}: {ex}")
            raise ex

        self.async_sessionmaker = async_sessionmaker(
            self.engine,
            expire_on_commit=False,   # SqlAlchemy recommends avoid expire on commit for async
            autoflush=False,          # Default is False (I think). Not recommended for async.
            class_=AsyncSession,
        )

    async def create_tables(self):
        """Create all tables in the database. Used for testing."""
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    async def destroy_tables(self):
        """Destroy tables. Intended for testing using in-memory database."""
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)

    async def delete_all_data(self, Base):
        """Delete all records from all tables in dependency order.
           For running tests this may be faster and use less I/O than
           creating tables before each test and dropping them later.

           :param Base: the declarative Base class used to create the models.
        """
        # Get all model classes
        models = [cls for cls in Base.__subclasses__()
                  if hasattr(cls, '__tablename__')]
        
        # Sort models by dependency (simple approach - may need adjustment)
        # This is to avoid ForeignKey constraint violations during delete.
        models.sort(key=lambda x: len(x.__table__.foreign_keys), reverse=True)
        async for session in self.get_session():
            for model in models:
                await session.query(model).delete()
            await session.commit()

    async def delete_all_data2(self, Base):
        """Use metadate to delete all table data, in reverse order that
           the tables were created.

           :param Base: the declarative Base class used to create the models.
        """
        async for session in self.get_session():
            for table in reversed(Base.metadata.sorted_tables):
                await session.execute(table.delete())
            await session.commit()     

# Shared database instance 
db = Database()


async def session_tests():
    """Some tests of the use of db.get_session()."""
    whatis = lambda session: print("          session is", type(session).__name__)

    # Can we use `async for` to get a session?
    # Answer: YES.  It yields only 1 session not an infinite loop.
    print("\nMethod 1: async for session in db.get_session()")
    print("          It yields only 1 session not an infinite loop.")
    async for session in db.get_session():
        whatis(session)
        # You can use the session here, e.g., to query or add data.
        await session.commit()  # Nothing to commit.
        await session.close()

    # Can we use db.asyncSessionMaker in a "with" clause?
    # Answer: YES. But you must close the session in code.
    print("\nMethod 2: async with db.async_sessionmaker()  as session")
    print("          Works, but you must issue session.close() in code.")
    async with db.async_sessionmaker() as session:
        whatis(session)
        # You can use the session here, e.g., to query or add data.
        await session.commit()  # Nothing to commit.
        await session.close()

    # Can we use "with db.get_session()" to get a session?
    # Answer: NO, "async_generator object is not an async context manager protocol""
    print("\nMethod 3: async with db.get_session() as session")
    print("          Doesn't work.")
    print("          async_generator object is not an async context manager")
    try:
        async with db.get_session() as session:
            whatis(session)
            # You can use the session here, e.g., to query or add data.
            await session.commit()  # Nothing to commit.
            await session.close()
    except Exception as ex:
        print("Exception:", ex)


if __name__ == '__main__':
    db.create_engine("sqlite+aiosqlite:///:memory:")
    asyncio.run(session_tests())

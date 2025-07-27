"""Create a sample database and some users. """

import asyncio
from typing import Type
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import security
from app.data_access import user_dao
from app import models

# Import ORM models
from app.models import User, UserPassword
from app.core.database import db

# Database URL is defined in config.py
# Override it here (before creating any async sessions) using:
# from app.core.database import db
# db.create_engine(new_database_url)
#
# Example:
# DATABASE_URL = "sqlite+aiosqlite:///./test.sqlite3"
# DATABASE_URL = "sqlite+aiosqlite:///:memory:"
# DATABASE_URL = "postgresql+asyncpg://user:password@localhost/mydatabase"
DATABASE_URL = "sqlite+aiosqlite:///./dev.sqlite3"


async def insert_sample_users(users: list[User] = None):
    """Insert sample users into the database."""
    # Sample users
    if not users:
        users = [User(email="jim@hackers.com", username="Jim"),
                 User(email="harry@hackers.com", username="Harry"),
                 User(email="sally@hackers.com", username="Sally")
                ]  # noqa: E124
    password = "hackme2"
    
    async for session in db.get_session():
        # Use the session to add the user
        await session.begin()
        assert session is not None, "No session"
        # Ensure the session is an AsyncSession
        if not isinstance(session, AsyncSession):
            print("Session is not an AsyncSession")
        for user in users:
            session.add(user)
        await session.commit()
        for user in users:
            await session.refresh(user)
            print(f"Inserted user id {user.id} {user.username} <{user.email}> at {user.created_at}")
        # Set passwords
        for user in users:
            user_password = UserPassword(
                    user_id=user.id,
                    hashed_password=security.hash_password(password)
                    )
            session.add(user_password)
            await session.commit()
            await session.refresh(user_password)

            print(f"Password for {user.username} (id {user.id}) "
                  "is {user_password.hashed_password}")


async def assign_user_password(email: str, password: str) -> bool:
    """Assign a password to a user, selected by email."""
    async for session in db.get_session():
        user = await user_dao.get_by_email(session, email)
        if not user:
            return False
        await user_dao.set_password(session, user, password=password)
        hashed = await user_dao.get_password(session, user)
        print(f"Set password for {email} to {password}. Hash = {hashed}")
    return True


async def create_tables():
    """Drop and recreate tables."""
    await db.destroy_tables()
    # Create tables if they don't exist
    await db.create_tables()
    print("Created tables")


async def create_table(table: Type[models.Base]):
    """Create specific table(s)."""
    async with db.engine.begin() as connection:
        # This creates all tables
        # await connection.run_sync(Base.metadata.create_all)
        # Create a specific table
        await connection.run_sync(table.__table__.create, checkfirst=True)


async def get_table_names():
    """Return a list(?) of table names."""
    async with db.engine.begin() as conn:
        table_names = inspect(conn).get_table_names()
    print(table_names)
    return table_names


async def main():
    """Perform sample actions.  Create tables, insert users."""
    database_url = DATABASE_URL
    db.create_engine(database_url)
    print("Database engine url", str(db.engine.url))

    #await create_tables()
    await create_table(models.Reading)
    await get_table_names()

    # Insert sample data
    # await insert_sample_users()

    # Setting passwords is done in insert_sample_users()
    # emails = ["tester@hackers.com", "jim@yahoo.com", "harry@hackerone.com"]
    # await assign_user_passwords(emails, "hackme2")


if __name__ == "__main__":
    asyncio.run(main())

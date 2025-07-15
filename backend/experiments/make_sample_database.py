# experiments/users_sample.py

import asyncio
from collections.abc import Collection
from datetime import datetime, timezone
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import security
from app.data_access import user_dao

# Database URL is defined in config.py
# Override it here (before creating any async sessions) using:
# from app.core.database import db
# db.create_engine(new_database_url)
#
# Example urls:
# DATABASE_URL = "sqlite+aiosqlite:///test.sqlite3"
# DATABASE_URL = "postgresql+asyncpg://user:password@localhost/mydatabase"

# Import ORM models
from app.models import User, UserPassword
from app.core.database import db 


async def insert_sample_users():
    """Insert sample users into the database."""

    # Sample users
    users = [User(email="jim@hackers.com", username="Jim"),
             User(email="harry@hackers.com", username="Harry"),
             User(email="sally@hackers.com", username="Sally")
             ]
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
                    user_id = user.id,
                    hashed_password = security.hash_password(password)
                    )
            session.add(user_password)
            await session.commit()
            await session.refresh(user_password)

            print(f"Password for id {user_password.user_id} ({user.username}) is {user_password.hashed_password}")


async def assign_user_passwords(emails: Collection[EmailStr], password: str) -> int:
    """assign same password to several users, selected by email."""
    change_count = 0
    async for session in db.get_session():
        for email in emails:
            user = await user_dao.get_user_by_email(session, email)
            if not user:
                continue
            await user_dao.set_password(session, user, password=password)
            hashed = await user_dao.get_password(session, user)
            print(f"Set password for {email} to {password}. Hash = {hashed}")
            change_count += 1
    return change_count    



async def main():
    # use an in-memory SQLite database for testing
    #database_url = "sqlite+aiosqlite:///:memory:"
    database_url = "sqlite+aiosqlite:///./test.sqlite3"
    db.create_engine(database_url)
    print("Database engine url", str(db.engine.url))
    await db.destroy_tables()
    # Create tables if they don't exist
    await db.create_tables()
    print("Created tables")
    
    # Insert sample data
    await insert_sample_users()
    #emails = ["tester@hackers.com", "jim@yahoo.com", "harry@hackerone.com"]
    #await assign_user_passwords(emails, "hackme2")


if __name__ == "__main__":
    asyncio.run(main())
    #emails = ["tester@hackers.com", "jim@yahoo.com", "harry@hackerone.com"]
    #asyncio.run(assign_user_passwords(emails, "hackme2"))
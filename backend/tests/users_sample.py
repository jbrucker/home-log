# experiments/users_sample.py

import asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

# Database URL is defined in config.py
# Example alternatives:
# DATABASE_URL = "sqlite:///test_homelog.db"
# DATABASE_URL = "postgresql://user:password@localhost/mydatabase"
# DATABASE_URL = "mysql+pymysql://user:password@localhost/mydatabase"

# Import your models (assuming they're in models.py)
from app.models import User, UserPassword
from app.core.database import db 

async def get_session() -> AsyncSession | None:
    """Get a database session."""
    # db.get_session() is an async generator that yields a session
    async for session in db.get_session():
        return session

async def insert_sample_users():
    """Insert sample users into the database."""
    session_generator = db.get_session()

    # Sample user 1
    user1 = User(
        email="user1@example.com",
        username="user1"
    )
    async for session in db.get_session():
        # Use the session to add the user
        await session.begin()
        assert session is not None, "No session"
        # Ensure the session is an AsyncSession
        if not isinstance(session, AsyncSession):
            print("Session is not an AsyncSession")
        session.add(user1)
        await session.commit()
        await session.refresh(user1)
        print(f"Inserted user #{user1.id} {user1.username} <{user1.email}> at {user1.created_at}")

        # Can we do more work in session?
        user1_password = UserPassword(
            user_id=user1.id,
            hashed_password="hashed_password_123"  # In real usage, use proper password hashing
        )
        session.add(user1_password)
        await session.commit()
        await session.refresh(user1_password)
        print(f"Password for {user1.username} is {user1_password.hashed_password}")

    # Apparently session is automatically closed after async for

    session = db.async_sessionmaker()
    if session:
        # Sample user 2
        user2 = User(
            email="user2@hackers.com",
            username="Harry Hacker",
            created_at=datetime.utcnow()
        )
        session.add(user2)
        await session.commit()
        await session.refresh(user2)
        # MUST close the session in code!!!
        await session.close()
        print(f"Inserted user #{user2.id} {user2.username} <{user2.email}> at {user2.created_at}")


async def main():
    # use an in-memory SQLite database for testing
    db.create_engine("sqlite+aiosqlite:///:memory:")
    print("Database engine url", str(db.engine.url))
    # Create tables if they don't exist
    await db.create_tables()
    print("Created tables")
    
    # Insert sample data
    await insert_sample_users()

if __name__ == "__main__":
    asyncio.run(main())
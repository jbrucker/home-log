# experiments/users_sample.py

import asyncio
from dataclasses import dataclass
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import db
from app.data_access import user_dao

# Database URL is defined in app/core/config.py
# Override it here (before creating any async sessions) using:
# from app.core.database import db
# db.create_engine(new_database_url)
#
# Example urls:
# DATABASE_URL = "sqlite+aiosqlite:///test.sqlite3"
# DATABASE_URL = "postgresql+asyncpg://user:password@localhost/mydatabase"

# Import ORM models
from app.models import User, UserPassword
from app import schemas
from app.core.database import db 
from app.data_access import user_dao


async def insert_sample_users(user_data: list[dict[str,Any]]):
    """Insert sample users into the database."""
    
    async for session in db.get_session():
        assert session is not None, "No session"

        for new_user_data in user_data:
            plain_password = new_user_data.get('password')
            # 'password' is not part of the schema
            del new_user_data['password']
            new_user = schemas.UserCreate(**new_user_data)

            user = await user_dao.get_by_email(session, new_user.email)
            if user:
                print(f"User {user.username} <{user.email}> already exists in database")
            else:
                print(f"Add {new_user.username} <{new_user.email}> to Users")
                user = await user_dao.create(session, new_user)
                print(f"Added {user} at {user.created_at}")
            # Set password
            try:
                # returns a UserPassword instance
                user_password = await user_dao.set_password(session, user, plain_password)
                hashed_password = user_password.hashed_password
                print(f'{user.email} has password "{plain_password}" hash "{hashed_password[:40]}..."')
            except Exception as ex:
                print(f"Exception setting password for {user.email}", ex)
    

async def assign_user_password(email: str, password: str):
    """Assign a password to a user by email."""
    async for session in db.get_session():
        user = await user_dao.get_by_email(session, email)
        if not user:
            print(f"No user with email {email}")
            return
        await user_dao.set_password(session, user, password=password)
        hashed = await user_dao.get_password(session, user)
        print(f"Password for {email} is {password}. Hash {hashed}")


async def create_tables():
    """Drop and recreate database tables."""
    await db.destroy_tables()
    # Create tables if they don't exist
    await db.create_tables()
    print("Created tables")


async def main():
    # use an in-memory SQLite database for testing
    #database_url = "sqlite+aiosqlite:///:memory:"
    #db.create_engine(database_url)
    print("Database engine url", str(db.engine.url))

    user_data = [{'email': "jim@hackers.com", 'username': "Jim", 'password': "hackme2"},
                {'email': "harry@hackers.com", 'username': "Harry", 'password': "hackme2"},
                {'email': "sally@hackers.com", 'username': "Sally", 'password': "hackme2"},
                {'email': "admin@localhost.com",'username': "admin", 'password': "MakeMyDay"}
            ]
    
    # Insert sample users
    await insert_sample_users(user_data)


@dataclass
class Person:
    """A lame person model."""
    name: str
    email: str
    id: int


def make_people(user_data: list[dict[str, Any]]):
    """Experiment how to pass a dict to constructor or function as name=value pairs?
       Answer:  use **data where data is the dict of params.
    """
    for data in user_data:
        p = Person(**data)
        print(p)


if __name__ == "__main__":
    asyncio.run(main())
    # make_people{user_data)

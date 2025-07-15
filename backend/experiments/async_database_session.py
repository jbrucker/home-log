"""Experiment with async database sessionmaker and session."""
import asyncio

from sqlalchemy import select
from app.core.database import db, Base
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker


# Switch to a temporary in-memory SQLite database
database_url = "sqlite+aiosqlite:///:memory:" 
db.create_engine(database_url)

from app.models import User

# What is this?
# The name used in documentation is misleading.
# async_session_factory() returns a sqlalchemy.ext.asyncio.session.AsyncSession
async_session_factory = async_sessionmaker(
        db.engine,
        expire_on_commit=False
)

async def create_tables():
    """Create tables in the database."""
    async with db.engine.begin() as conn:
        # Create all tables defined in the models
        await conn.run_sync(Base.metadata.create_all)

 
async def create_users():
    async with async_session_factory() as session:
        user1 = User(email="rangjut@yahoo.com", username="Rangjut")
        user2 = User(email="fatalaijon@gmail.com", username="Fatalai")
        session.add(user1)
        session.add(user2)
        await session.commit()
        await session.refresh(user1)
        await session.refresh(user2)
        print(f"Created {user1.username} with id {user1.id} at {user1.created_at}")
        print(f"Created {user2.username} with id {user2.id} at {user2.created_at}")


async def get_user(username: str) -> User | None:
    """Get a user by username."""
    async with async_session_factory() as session:
        stmt = select(User).where(User.username == username)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
    # should be inside with block?
    return user    


async def what_the_hell_are_these():
    print("async_sessionmaker returns a", type(async_session_factory))
    print("async_session_factory() return", type(async_session_factory()))
    session = async_session_factory()
    print("session = async_session_factory() is", type(session))
    print("session.begin() is", type(await session.begin()))
    print("session.commit() is", type(await session.commit()))
    print("")

def print_user(user: User | None) -> None:
    if user:
        print(f"Found user {user.username} <{user.email}> with id {user.id}")
    else:
        print("No user")

async def main():
    await what_the_hell_are_these()
    input("Press Enter to continue...")
    await create_tables()
    await create_users()

    input("Get user Rangjut")
    user = await get_user("Rangjut")
    print_user(user)
    input("Get user Santa")
    user = await get_user("Santa")
    print_user(user)

if __name__ == "__main__":
    asyncio.run(main())

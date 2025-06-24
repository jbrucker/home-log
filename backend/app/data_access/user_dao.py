"""ORM operations for user objects."""
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
# select is now asynchronous by default, so don't need to import from sqlachemy.future
from sqlalchemy import select

from app import models, schemas
# from app.core.security import hash_password


async def create_user(session: AsyncSession, user: schemas.UserCreate) -> models.User:
    user = models.User(email=user.email, username=user.username)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_user_by_id(session: AsyncSession, user_id: int) -> models.User | None:
    """Get a user from database using the primary key (id)."""
    if not isinstance(user_id, int) or user_id <= 0:
        return None
    stmt = select(models.User).where(models.User.id == user_id)
    result = await session.execute(stmt)
    # Return the first result or None if no match.
    return result.scalar_one_or_none()


async def get_user_by_email(session: AsyncSession, email: str) -> models.User | None:
    stmt = select(models.User).where(models.User.email == email)
    result = await session.execute(stmt)
    # Return the first result or None if no match.
    return result.scalar_one_or_none()

async def get_user_by_id(session: AsyncSession, user_id: int) -> models.User | None:
    stmt = select(models.User).where(models.User.id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def create_user(session: AsyncSession, user_data: schemas.UserCreate) -> models.User:
    user = models.User(email=user_data.email, username=user_data.username)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def update_user(session: AsyncSession, user_id: int, user_data: schemas.UserCreate) -> models.User | None:
    user = await get_user_by_id(session, user_id)
    if user:
        user.email = user_data.email
        user.username = user_data.username
        user.updated_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(user)
    return user


async def delete_user(session: AsyncSession, user_id: int) -> bool:
    user = await get_user_by_id(session, user_id)
    if user:
        await session.delete(user)
        await session.commit()
        return True
    return False
"""ORM operations for user objects.


TODO:
   Encapsulate sqlalchemy exceptions in framework-independent exceptions.
   sqlalchemy.exc.IntegrityError -> IntegrityError or ValueError
"""

from datetime import datetime, timezone
from typing import Collection
from sqlalchemy.ext.asyncio import AsyncSession
# select is now asynchronous by default, so don't need to import from sqlachemy.future
from sqlalchemy import select

from app import models, schemas
# from app.core.security import hash_password


async def create_user(session: AsyncSession, user_data: schemas.UserCreate) -> models.User:
    """Add a new user to persistent storage, assigning a user.id and creation date.

    :param session: database connection "session" object
    :param user_data: schema object containing attributes for a new user entity
    :returns: a User model object populated with values of corresponding entity
    :raises IntegrityError: if uniqueness constraint(s) violated
    :raises ValueError: if any required values are missing or invalid (Note)

    Note: the Schema object should perform data validation, so a ValueError on
          save indicates an inconsistency between schema validators and 
          database requirements.
    """
    user = models.User(email=user_data.email, username=user_data.username)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_user_by_id(session: AsyncSession, user_id: int) -> models.User | None:
    """Get a user from database using the primary key (id)."""
    if not isinstance(user_id, int) or user_id <= 0:
        return None
    #stmt = select(models.User).where(models.User.id == user_id)
    #result = await session.execute(stmt)
    user_result = await session.get(models.User, user_id)
    # Return the first result or None if no match.
    return user_result


async def get_user_by_email(session: AsyncSession, email: str) -> models.User | None:
    stmt = select(models.User).where(models.User.email == email)
    result = await session.execute(stmt)
    # Return the first result or None if no match.
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> models.User | None:
    stmt = select(models.User).where(models.User.id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_users(session: AsyncSession, limit: int = 0) -> Collection[models.User]:
    """Get all users, ordered by user.id.

    :param limit: max number of values to return, default is unlimited
    :returns: collection of user objects. May be empty.
    """
    stmt = select(models.User).order_by(models.User.id)
    if limit > 0:
        stmt = stmt.limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


async def create_user(session: AsyncSession, user_data: schemas.UserCreate) -> models.User:
    """Persist a user object, with auto-assigned creation date/time.

    :param user_data: data for the user, as a schemas object
    :returns: User model with persisted values.
    """
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


async def delete_user(session: AsyncSession, user_id: int) -> models.User | None:
    """Delete a user by id.

    :returns: data for the deleted user or None if no matching user.
    """
    user = await get_user_by_id(session, user_id)
    if user:
        await session.delete(user)
        await session.commit()
        return user
    return None

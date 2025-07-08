"""ORM operations for user objects.

TODO:
   Encapsulate sqlalchemy exceptions in framework-independent exceptions.
   sqlalchemy.exc.IntegrityError -> IntegrityError or ValueError
"""

from datetime import datetime, timezone
from typing import Collection
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
# select is now asynchronous by default, so don't need to import from sqlachemy.future
from sqlalchemy import select, and_

from app import models, schemas
from app.core import security


async def create_user(session: AsyncSession, user_data: schemas.UserCreate) -> models.User:
    """Add a new user to persistent storage, assigning a user.id and creation date.

    :param session: database connection "session" object
    :param user_data: schema object containing attributes for a new user entity
    :returns: a User model instance with persisted values
    :raises IntegrityError: if uniqueness constraint(s) violated
    :raises ValueError: if any required values are missing or invalid (Note)

    Note: the Schema object should perform data validation, so a ValueError on
          save indicates an inconsistency between schema validators and 
          database requirements.
    """
    user = models.User(**user_data.model_dump())  # **user_data.dict() is deprecated
    session.add(user)
    await session.commit()
    await session.refresh(user)     # update the user.id and user.created_at
    return user


async def get_user_by_id(session: AsyncSession, user_id: int) -> models.User | None:
    """Get a user from database using his id (primary key).
    
    :returns: models.User instance or None if no match for `user_id`
    """
    if not isinstance(user_id, int) or user_id <= 0:
        return None
    # Another way:
    # stmt = select(models.User).where(models.User.id == user_id)
    # result = await session.execute(stmt)
    # Return the first result or None if no match.
    result = await session.get(models.User, user_id, 
                               options=[joinedload(models.User.user_password)])
    return result


async def get_user_by_email(session: AsyncSession, email: str) -> models.User | None:
    stmt = select(models.User).options(joinedload(models.User.user_password)).where(models.User.email == email)
    result = await session.execute(stmt)
    # Return the first result or None if no match.
    # .scalar_one_or_none() raises sqlalchemy.exc.MultipleResultsFound if more than one match.
    # Use result.first() if email may not be unique, but first() returns a Row not a User.
    return result.scalar_one_or_none()


async def get_users_by(session: AsyncSession, **filters) -> list[models.User]:
    """
    Get users matching arbitrary filter criteria.
    Usage: await get_users_by(session, email="foo@bar.com", username="Foo")
    
    :param filters: dict of User attribute to arbitrary values
    :returns: list of matching entities, may be empty
    """
    stmt = select(models.User)
    if filters:
        conditions = [getattr(models.User, key) == value for key, value in filters.items()]
        stmt = stmt.where(and_(*conditions))
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_users(session: AsyncSession, limit: int = 0) -> Collection[models.User]:
    """Get all users, ordered by user.id.

    This method does **not** eagerly load user_password relations. 
    For access to a user's password use `get_user_by_id` or `get_user_password`.

    :param limit: max number of values to return, default is unlimited
    :returns: collection of user objects. May be empty.
    """
    stmt = select(models.User).order_by(models.User.id)
    if limit > 0:
        stmt = stmt.limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


async def update_user(session: AsyncSession, user_id: int, user_data: schemas.UserCreate) -> models.User | None:
    """Update the data for an existing user, identified by `user_id`.

       :param user_id: id (primary key) of User to update
       :param user_data: new data for the user. All fields are in user_data are used.
       :raises ValueError: if no persisted User with the given `user_id`
    """
    user = await get_user_by_id(session, user_id)
    if not user:
        raise ValueError(f"No user found with id {user_id}")
    # TODO Should we exclude unset fields?  It could make it impossible to "unset" an optional attribute.
    #update_data = user_data.model_dump(exclude_unset=True)
    #for field, value in update_data.items():
    #    setattr(user, field, value)
    # Old:
    user.email = user_data.email
    user.username = user_data.username
    # updated_at is updated automatically by SqlAlchemy. See models.User
    user.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(user)
    return user

async def get_user_password(session: AsyncSession, 
                            user: models.User | int
                            ) -> models.UserPassword | None:
    """Get a user's related UserPassword instance, which may be None.
    If you only want the user's hashed password, use @get_password instead.
    
    :param user: a User model instance or the id (int) of user
    :returns: UserPassword of the requested user
    :raises ValueError: If no User with the given user_id value
    """
    user_id = user if isinstance(user, int) else user.id
    stmt = select(models.UserPassword).where(models.UserPassword.user_id == user_id)
    user_password: models.UserPassword = await session.execute(stmt)
    return user_password.scalar_one_or_none()


async def get_password(session: AsyncSession, 
                       user: models.User | int
                       ) -> str | None:
    """Get a user's hashed password or None if no password.
    
    :param user: an instance of models.User or a user id value
    :returns: hashed password of the requested user, which may be None
    :raises ValueError: If no User with the given user_id value
    """
    user_id = user if isinstance(user, int) else user.id
    stmt = select(models.UserPassword).where(models.UserPassword.user_id == user_id)
    result = await session.execute(stmt)
    # raises sqlalchemy.exc.MultipleResultsFound if more than one match
    if user_password := result.scalar_one_or_none():
        return user_password.hashed_password 
    else:
        None

async def set_password(session: AsyncSession, 
                            user: models.User | int, 
                            password: str) -> models.UserPassword | None:
    """Set or update a user's password.

    :param user: a models.User or user id (int) of a User 
    :param password: plain text of the new password
    :returns: UserPassword of the updated or added password
    :raises ValueError: If no User with the given user_id value
    """
    user_id = user if isinstance(user, int) else user.id
    stmt = select(models.UserPassword).where(models.UserPassword.user_id == user_id)
    result = await session.execute(stmt)
    # this raises sqlalchemy.exc.MultipleResultsFound if more than one match
    user_password = result.scalar_one_or_none()

    hashed_password = security.hash_password(password)
    if user_password:
        # update password of an existing user
        user_password.hashed_password = hashed_password
    else:
        # create a new UserPassword referencing the user
        user_password = models.UserPassword(
                            user_id=user_id,
                            hashed_password=hashed_password
                        )
    # updated_at is updated automatically by SqlAlchemy. See models.UserPassword
    user_password.updated_at = datetime.now(timezone.utc)
    session.add(user_password)
    await session.commit()
    await session.refresh(user_password)
    return user_password


async def delete_user(session: AsyncSession, user_id: int) -> models.User | None:
    """Delete a user by id.

    :returns: data for the deleted user or None if no matching user.
    """
    user = await get_user_by_id(session, user_id)
    if user:
        await session.delete(user)
        await session.commit()
        # set user.id= 0 to indicate not persisted
        # but must also update test_user_dao
        return user
    return None


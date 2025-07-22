"""Persistence operations for User objects.

TODO:
   Encapsulate sqlalchemy exceptions in framework-independent exceptions.
   sqlalchemy.exc.IntegrityError -> IntegrityError or ValueError
"""

from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
# select is now asynchronous by default, so don't need to import from sqlachemy.future
from sqlalchemy import select

from app import models, schemas
from app.core import security
from app.data_access import base_dao


async def create(session: AsyncSession, user_data: schemas.UserCreate) -> models.User:
    """Add a new user to persistent storage, assigning a user id and creation date.

    :param session: database connection "session" object
    :param user_data: schema object containing attributes for a new user entity
    :returns: a User model instance with persisted values
    :raises IntegrityError: if uniqueness constraint(s) violated
    :raises ValueError: if any required values are missing or invalid (Note)

    Note: the Schema object should perform data validation, so a ValueError on
          save indicates an inconsistency between schema validators and 
          database requirements.
    """
    return await base_dao.create(models.User, session, user_data)


async def get(session: AsyncSession, user_id: int) -> models.User | None:
    """Get a user using his id (primary key), and pre-fetched user_password relationship.

    :returns: models.User instance or None if no match for `user_id`
    """
    if not isinstance(user_id, int) or user_id <= 0:
        return None
    options = [joinedload(models.User.user_password)]
    return await base_dao.get_by_id(models.User, session, user_id, options=options)


async def get_by_email(session: AsyncSession, email: str) -> models.User | None:
    """Get a user from database using his email, and pre-fetched user_password relationship.

    :returns: models.User instance or None if no match for `user_id`
    """
    options = joinedload(models.User.user_password)
    stmt = select(models.User).options(options).where(models.User.email == email)
    result = await session.execute(stmt)
    # Return the first result or None if no match.
    # .scalar_one_or_none() raises sqlalchemy.exc.MultipleResultsFound if more than one match.
    # Use result.first() if email may not be unique, but first() returns a Row not a User.
    return result.scalar_one_or_none()


async def get_users(session: AsyncSession, limit: int = 0, offset: int = 0) -> list[models.User]:
    """Get all users, ordered by user.id.

    This method does **not** eagerly load user_password relations. 
    For access to a user's password use `get_user_by_id` or `get_user_password`.

    :param limit: max number of values to return, default is unlimited
    :param offset: start returning users after skipping this many initial records
    :returns: list of user objects. May be empty.
    """
    return await base_dao.get_all(models.User, session, offset=offset, limit=limit)


async def find(session: AsyncSession, *conditions, **filters) -> list[models.User]:
    """
    Get users matching arbitrary conditions and filter criteria.

    :param conditions: SqlAlchemy filter expressions (e.g. models.User.id > 1000).
    :param filters: dict of User attribute to arbitrary values (e.g. email="foo@bar.com")
    `filters` may include `limit=n` and `offset=m` to limit and paginate results (see get_users)
    :returns: list of matching entities, may be empty

    Example usage:
    await find_users(session, models.User.is_active == True, email="foo@bar.com")
    """
    return await base_dao.find_by(models.User, session, *conditions, **filters)


async def update(session: AsyncSession,
                 user_id: int,
                 user_data: schemas.UserCreate) -> models.User | None:
    """Update the data for an existing user, identified by `user_id`.

    :param user_id: id (primary key) of User to update
    :param user_data: new data for the user. All fields are in user_data are used.
    :raises ValueError: if no persisted User with the given `user_id`
    :raises IntegrityError: if uniqueness constraint(s) violated
    :raises ValueError: if any required values are invalid
    """
    user = await get(session, user_id)
    if not user:
        raise ValueError(f"No user found with id {user_id}")
    # TODO Should we exclude unset fields?  It could make it impossible to "unset" an optional attribute.
    # update_data = user_data.model_dump(exclude_unset=True)
    # for field, value in update_data.items():
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

    If you only want the user's hashed password, use `get_password` instead. 
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
                       password: str
                       ) -> models.UserPassword | None:
    """Set or update a user's password.

    :param user: a models.User or user id (int) of a User 
    :param password: plain text of the new password
    :returns: UserPassword with the updated password
    :raises ValueError: If no User with the given user_id value
    """
    user_id = user if isinstance(user, int) else user.id
    stmt = select(models.UserPassword).where(models.UserPassword.user_id == user_id)
    result = await session.execute(stmt)
    # this raises sqlalchemy.exc.MultipleResultsFound if more than one match
    user_password = result.scalar_one_or_none()

    hashed_password = security.hash_password(password)
    if user_password:
        # update existing password
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
    return await base_dao.delete_by_id(models.User, session, user_id)

"""Test of hashed passwords in User and UserPassword."""

from datetime import datetime, timezone
import pytest
from app.core import security
from app.data_access import user_dao
from app import schemas, models
# VS Code thinks the 'session' import is unused, but it is needed as fixture
from .fixtures import session  # noqa: F401
from . import utils

# Ignore F811 "Redefinition of unused import" for test fixtures used as parameters
# flake8: noqa: F811


@pytest.mark.asyncio
async def test_new_user_password(session):
    """A newly created user does not have a password."""
    new_user = schemas.UserCreate(email="harry@hackers.com", username="Harry")
    user = await user_dao.create(session, new_user)
    # verify user was persisted
    assert isinstance(user, models.User)
    # model should be fully populated
    assert user.id > 0
    assert user.username == "Harry"
    password = await user_dao.get_password(session, user.id)
    # Does not have a password yet
    assert password is None
    # Can also get password using User instance as parameter value
    password = await user_dao.get_password(session, user)
    # Does not have a password yet
    assert password is None


@pytest.mark.asyncio
async def test_set_password(session):
    """Can set the password for a user in database and hashed password passes verification."""
    new_user = schemas.UserCreate(email="harry@hackers.com", username="Harry")
    user = await user_dao.create(session, new_user)
    # verify user was persisted
    assert isinstance(user, models.User)
    assert user.id > 0
    # set a password and then get the hashed password
    plain_password = utils.make_password()
    await user_dao.set_password(session, user.id, plain_password)
    hashed_password = await user_dao.get_password(session, user.id)
    assert hashed_password is not None, "User should have a password!"
    assert security.verify_password(plain_password, hashed_password) is True,\
        f"Passwords don't match. Hashed = {hashed_password}"

@pytest.mark.asyncio
async def test_set_password_updates_date(session):
    """Setting (changing) a password updates the `updated_at` attr in UserPassword."""
    start_time = datetime.now(timezone.utc)
    new_user = schemas.UserCreate(email="harry@hackers.com", username="Harry")
    user = await user_dao.create(session, new_user)
    # set a password and then get the hashed password
    plain_password = utils.make_password()
    await user_dao.set_password(session, user.id, plain_password)
    user_password = await user_dao.get_user_password(session, user.id)
    assert isinstance(user_password, models.UserPassword)
    update_time = utils.as_utc_time(user_password.updated_at)
    assert update_time > start_time
    # Change password and check again
    plain_password = utils.make_password()
    await user_dao.set_password(session, user.id, plain_password)
    await session.refresh(user_password)
    new_update_time = utils.as_utc_time(user_password.updated_at)
    assert new_update_time > update_time


@pytest.mark.asyncio
async def test_get_user_password(session):
    """Can get the UserPassword object for a User by doing a query."""
    new_user = schemas.UserCreate(email="sally@hackers.com", username="Sally")
    user = await user_dao.create(session, new_user)
    # set a password and then get the hashed password
    plain_password = utils.make_password()
    await user_dao.set_password(session, user.id, plain_password)
    # password is saved in a UserPassword object
    user_password = await user_dao.get_user_password(session, user)
    assert isinstance(user_password, models.UserPassword), f"get_user_password return a {type(user_password).__name__}"
    hashed_password = user_password.hashed_password
    assert security.verify_password(plain_password, hashed_password) is True,\
        f"Passwords don't match. Hashed = {hashed_password}"
    # we can also get the hashed password w/o UserPassword object by calling user_dao.get_password
    hashed_password2 = await user_dao.get_password(session, user)
    assert hashed_password2 == hashed_password, "user_dao.get_password() didn't return userPassword.hashed_password"


@pytest.mark.skip("Accessing a relationship field in user model doesn't work with async Postgresql")
@pytest.mark.asyncio
async def test_user_password_property(session):
    """Can get the UserPassword for a User using a relationship field defined in User model."""
    new_user = schemas.UserCreate(email="sally@hackers.com", username="Sally")
    user = await user_dao.create(session, new_user)
    # set a password and then get the hashed password
    plain_password = utils.make_password()
    await user_dao.set_password(session, user.id, plain_password)
    # Important! Get the user by id to force eager loading of relationship.
    user = await user_dao.get(session, user.id)
    # user.user_password refers to the related UserPassword object
    assert user.user_password is not None
    assert isinstance(user.user_password, models.UserPassword), f"get_user_password return a {type(user.user_password).__name__}"
    hashed_password = user.user_password.hashed_password
    assert security.verify_password(plain_password, hashed_password) is True,\
        f"Passwords don't match. Hashed = {hashed_password}"

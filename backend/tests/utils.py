"""Some utility functions for use in tests."""
from datetime import datetime, timezone
from app import models
from app.core import security
from app.utils import jwt

# Email domain for users created by create_users()
EMAIL_DOMAIN = "test.doma.in"


def auth_header(arg: models.User | str) -> dict:
    """Create an auth token for a user (if arg is User model) or containing arg (str)
       as a token, and return an authorization header containing the token.
    """
    if isinstance(arg, models.User):
        token = jwt.create_access_token(data={"user_id": arg.id}, expires=30)
    else:
        token = arg  # assume string is a token
    return {"Authorization": f"Bearer {token}"}


def is_timezone_aware(dt: datetime) -> bool:
    """Return True if argument is a datetime instance AND is timezone aware."""
    if not isinstance(dt, datetime):
        raise TypeError(f"{str(dt)} is not a datetime, it's a {type(dt).__name__}")
    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None


def as_utc_time(dt: datetime) -> datetime:
    """Convert a datetime instance to UTC time, if and only if it is timezone unaware."""
    if is_timezone_aware(dt):
        return dt
    return dt.replace(tzinfo=timezone.utc)


def make_password() -> str:
    """Make a random password that will probably pass password validation.

    The custom validator rules are in app.schemas.PasswordStr.
    """
    from random import randint
    LOWERCASE = "abcdefghijklmnopqrstuvwxyz"
    UPPERCASE = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    SPECIALS = "!@#$%^&*+-."
    min_length = 12
    password: str = ""
    while len(password) < min_length:
        password += LOWERCASE[randint(0, 25)]
        password += UPPERCASE[randint(0, 25)]
        password += str(randint(0, 9))
        password += SPECIALS[randint(0, len(SPECIALS)-1)]  # noqa: E226
    return password


async def create_users(session, howmany: int, email_domain: str = EMAIL_DOMAIN):
    """Create multiple users.  Assumes database and User table already initialized."""
    # TODO: Use same Session as the test method, or a separate Session?
    for n in range(1, howmany + 1):
        username = f"User{n}"
        email = f"{username.lower()}@{email_domain}"
        session.add(models.User(username=username, email=email))
    await session.commit()
    print(f"Added {n} users")


async def create_user(session, username: str, email: str, password: str = None):
    """Create a user with given username, email, and optional password.
    
    :returns: User model with given username, email, and optional password
    """
    user = models.User(username=username, email=email)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    # set a password?
    if password:
        user_pass = models.UserPassword(
                            user_id=user.id,
                            hashed_password=security.hash_password(password),
                            updated_at=datetime.now(timezone.utc)
                            )  # noqa: E124
        session.add(user_pass)
        await session.commit()
    return user

async def create_data_source(session, owner: models.User = None, **data) -> models.DataSource:
    """
    Create a DataSource instance using the provided by key-value parameters (**data).
    Assumes the 'models.DataSource' fields match keys in 'data'.
    """
    if owner:
        data["owner_id"] = owner.id
    data_source = models.DataSource(**data)
    session.add(data_source)
    await session.commit()
    return data_source

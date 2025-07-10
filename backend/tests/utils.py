"""Some utility functions for use in tests."""
from datetime import datetime, timezone
from app import models

# Email domain for users created by create_users()
EMAIL_DOMAIN = "yahoo.com"

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


async def create_users(session, howmany: int):
    """Create multiple users.  Assumes database and User table already initialized."""
    # TODO: Use same Session as the test method, or a separate Session?
    
    for n in range(1, howmany+1):
        username = f"User{n}"
        email = f"{username.lower()}@{EMAIL_DOMAIN}"
        session.add(models.User(username=username, email=email))
    await session.commit()
    print(f"Added {n} users")
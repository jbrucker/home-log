"""Some utility functions for use in tests."""
from datetime import datetime, timezone

def is_timezone_aware(dt: datetime) -> bool:
    """Return True if argument is a datetime instance AND is timezone aware."""
    assert isinstance(dt, datetime), "arg is not a datetime, it's a {type(dt).__name__}" 
    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None

def as_utc_time(dt: datetime) -> datetime:
    """Convert datetime object to UTC time, if and only if it is timezone unaware."""
    if is_timezone_aware(dt):
        return dt
    return dt.replace(tzinfo=timezone.utc)
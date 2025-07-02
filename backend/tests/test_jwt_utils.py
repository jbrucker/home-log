"""Test the functions in utils.jwt"""
from datetime import datetime, timedelta, timezone
import os
import pytest
import jose.exceptions
from app.core.config import settings

from app.utils.jwt import create_access_token, verify_access_token

@pytest.fixture()
def setup():
    # create a new secret_key to avoid exposing env var
    settings.secret_key = os.urandom(32)
    

def test_valid_token(setup):
    """token with valid expiry and the required data"""
    expires = 1
    data = {"user_id": 999, "email": "santa@northpole.org"}
    token = create_access_token(data, expires=expires)
    created_utc = datetime.now(timezone.utc)
    payload = verify_access_token(token)
    assert data["user_id"] == payload["user_id"]
    assert data["email"] == payload["email"]
    exp = data["exp"]
    assert isinstance(exp, int)
    expires_time = datetime.fromtimestamp(exp, tz=timezone.utc)
    assert created_utc <= expires_time <= created_utc + timedelta(minutes=expires)

def test_invalid_token(setup):
    """token missing required user_id in payload."""
    expires = 1  # in minutes
    data = {"id": 999, "email": "santa@northpole.org"}
    token = create_access_token(data, expires=expires)
    assert token is not None
    with pytest.raises(jose.exceptions.JWTError):
        payload = verify_access_token(token)
    # should not be present
    user_id = payload["user_id"]
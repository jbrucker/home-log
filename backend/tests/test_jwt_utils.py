"""Test the functions in utils.jwt"""
from datetime import datetime, timedelta, timezone
import os
import pytest
import jose.exceptions
from app.core.config import settings

from app.utils.jwt import create_access_token, verify_access_token

@pytest.fixture()
def setup():
    # Create a new secret_key to avoid exposing env var
    # This assumes that the jwt functions get secret key from settings.secret_key
    # (tested below)
    settings.secret_key = os.urandom(32)

@pytest.fixture()
def data():
    # Inject some data to use as payload in the JWT token
    return {"user_id": 999, "email": "santa@northpole.org"}


def test_valid_token(setup, data):
    """token with valid expiry and the required data"""
    expires = 1
    token = create_access_token(data, expires=expires)
    created_time = datetime.now(timezone.utc)
    payload = verify_access_token(token)
    for key in data.keys():
        assert payload[key] == data[key]
    exp = payload["exp"]
    assert isinstance(exp, int)
    expires_time = datetime.fromtimestamp(exp, tz=timezone.utc)
    assert created_time <= expires_time <= created_time + timedelta(minutes=expires)


def test_expired_token(setup, data):
    """verify token should raise exception if token has expired."""
    expires = -1  # in minutes
    token = create_access_token(data, expires=expires)
    assert token is not None
    with pytest.raises(jose.exceptions.ExpiredSignatureError):
        payload = verify_access_token(token)
    # how about expiry in 0 minutes?
    expires = 0
    token = create_access_token(data, expires=expires)
    assert token is not None
    with pytest.raises(jose.exceptions.ExpiredSignatureError):
        payload = verify_access_token(token)


def test_invalid_token(setup, data):
    """token with invalid syntax or non-matching SECRET_KEY."""
    expires = 1
    token = create_access_token(data, expires=expires)
    assert token is not None
    # bogus token
    with pytest.raises(jose.exceptions.JWTError):
        payload = verify_access_token(token[0:-1])+"$"  # '$' char never used in base64 encoding
    with pytest.raises(jose.exceptions.JWTError):
        payload = verify_access_token(token.replace(".", ","))
    # bogus secret key
    old_secret_key = settings.secret_key
    settings.secret_key = os.urandom(32)
    with pytest.raises(jose.exceptions.JWTError):
        payload = verify_access_token(token)
    # valid token & matching secret_key
    settings.secret_key = old_secret_key
    payload = verify_access_token(token)
    for key in data.keys():
        assert payload[key] == data[key]


@pytest.mark.skip(reason="verify_access_token does not verify keys in payload. Token consumer should do that.")
def test_token_with_bad_payload(setup):
    """token missing required user_id in payload."""
    expires = 1
    # create test payload w/o 'user_id'
    data = {"email": "santa@northpole.org"}
    token = create_access_token(data, expires=expires)
    assert token is not None
    with pytest.raises(jose.exceptions.JWTError):
        payload = verify_access_token(token)
    # user_id is not present
    with pytest.raises(KeyError):
        user_id = payload["user_id"]
        print("payload['user_id'] =", user_id)
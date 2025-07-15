"""Create and decode JWT tokens.

This module is independent of SqlAlchemy and Pydantic."""
from datetime import datetime, timedelta, timezone
import logging
from typing import Any
from jose import jwt
import jose.exceptions
from app.core.config import settings

# Data required to create token
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
# Name of the expiry field in JWT.  Appears that 'exp' is required name.
EXPIRY = "exp"


def create_access_token(data: dict, expires: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    """Create a JWT token containing the `data` dict as payload, 
    along with an expiry datetime.  If `expires` is not given then
    a default from app settings (created from env vars) is used.
    
    :param data: dict of values for payload
    :param expires: (optional) number of minutes after which token expires
    """
    SECRET_KEY = settings.secret_key
    JWT_ALGORITHM = settings.jwt_algorithm
    payload = data.copy()
    expires = datetime.now(timezone.utc) + timedelta(minutes=expires)
    expire_timestamp = int(expires.timestamp())
    payload.update({EXPIRY: expire_timestamp})
    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str) -> dict[str, Any]:
    """Verify an access token.

    :returns: the token payload
    :raises JWTClaimsError: any of the claims in token is invalid
    :raises ExpiredSignatureError: the `exp` value has already past (expired)
    :raises JWTError: the signature is invalid
    """
    SECRET_KEY = settings.secret_key
    JWT_ALGORITHM = settings.jwt_algorithm
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        # Check for required fields
        #user_id: str = payload.get("user_id")
        expiry = payload.get(EXPIRY)
        print(f"{EXPIRY}: ", expiry)
    #except jose.exceptions.JWTError as ex:
    except Exception as ex:
        # includes ExpiredSignatureError, JWTClaimsError
        logging.error(f"JWT decoding error: {ex}")
        raise ex

    # Verify token not expired. This is also done be jwt.decode
    # The expiry (`exp`) is stored in token as an int timestamp.
    # datetime.fromtimestamp(exp) works in my experiments
    
    expiry_datetime = datetime.fromtimestamp(expiry, tz=timezone.utc)
    if expiry_datetime < datetime.now(timezone.utc):
        # millisecond-granularity check for expiry (jwt uses seconds)
        logging.error("JWT decoding error: Signature has expired.")
        raise jose.exceptions.ExpiredSignatureError("Signature has expired.")
    return payload


def test_tokens(expires: int = 1):
    payload = {"user_id": 999, "email": "santa@northpole.org", "junk": "no"}
    token = create_access_token(payload, expires=expires)

    print("token =", token)
    print()
    data = verify_access_token(token)
    print("data in token =", data)
    expiry = data["exp"]
    assert isinstance(expiry, int), "'exp' payload should be int"
    print("expiry    ", expiry)
    expires_time = datetime.fromtimestamp(expiry, tz=timezone.utc)
    print("UTC Time  ", expires_time)
    local_tz = datetime.now().astimezone().tzinfo  # = ZoneInfo("Asia/Bangkok")
    local_time = datetime.fromtimestamp(expiry, tz=local_tz)
    print("Local Time", local_time)

if __name__ == '__main__':
    for expires_in in [1, 0, -1]:
        input(f"\nCREATE TOKEN EXPIRING IN {expires_in} MINUTES")
        try:
            test_tokens(expires_in)
        except Exception as ex:
            print(f" {type(ex).__name__}:", str(ex))
"""Password hashing using Argon2."""

import logging
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
# Uncomment the following lines if you want to use Passlib instead of argon2-cffi
# from passlib.hash import argon2
# from passlib.context import CryptContext
# from passlib.exceptions import PasslibHashingError, VerifyMismatchError

pwd_context = PasswordHasher()


def hash_password(password: str | bytes) -> str:
    """Hash a password using Argon2.

       :returns: hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str|bytes, hashed_password: str|bytes) -> bool:
    """Verify a password against its Argon2 hash."""
    try:
        # argon2.verify expects hashed_password to be the first argument
        return pwd_context.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False
    except Exception as e:
        # Handle other exceptions as needed
        logging.error(f"An error occurred during password verification: {e}")
        return False

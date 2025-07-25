"""Global settings and app configuration."""

import os
from decouple import config


# Maximum length for some string fields
MAX_NAME = 60       # A descriptive name can be a bit long
MAX_DESC = 80       # descriptions. For TEXT fields length is unlimited.
MAX_EMAIL = 160     # Email address. Pydantic limit is 64+1+67 chars.
MAX_ADDRESS = 160   # address or location
MAX_UNIT_NAME = 20  # unit names like 'kWhr', 'deg-C', 'meters'

# Clean way to create a database URL for Postgres
"""
from sqlalchemy.engine import URL
url = URL.create(
        drivername="postgresql+async",
        username="postgres",
        password="FatChance",
        host="db",  # for Docker container
        database="homelog"
        )
"""

class Settings:
    """Globally available constants based on environment variables
       or specified values (for testing).
    """

    def __init__(self, database_url:str = None):
        """Create application settings using environment vars or hardcoded values."""
        self.database_url = database_url if database_url else config("DATABASE_URL")

        # Hashing algorithm for JWT tokens. Prefer "HS256" = HMAC + SHA256 Symmetric key algorithm
        self.jwt_algorithm = config("JWT_ALGORITHM", default="HS256")
        # For "HS256" - generate secret key (str) using one of these:
        # os.urandom(32).hex()
        # secrets.token_hex(32)  -- a wrapper for os.urandom(n).hex()
        # Shell: `openssl rand --hex 32`
        self.secret_key = config("SECRET_KEY", default=os.urandom(32).hex())
        # Use short expiry on tokens
        self.access_token_expire_minutes = config("ACCESS_TOKEN_EXPIRE_MINUTES", default=60, cast=int)


# For production
# settings = Settings()

# A lightweight database for development use
# Note the async SQLite URL uses aiosqlite
DEV_DATABASE_URL = "sqlite+aiosqlite:///./dev.sqlite3"

# Run using a light-weight development database.
# For unit testing, the database URL is overridden in tests/conftest.py (TEST_DATABASE_URL)
settings = Settings(DEV_DATABASE_URL)

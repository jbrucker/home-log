from decouple import config

# Note the async SQLite URL uses aiosqlite
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.sqlite3"

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
        self.database_url = database_url if database_url else config("DATABASE_URL")

        # for JWT tokens
        # Recommended algorithms
        # "HS256" - HMAC + SHA256 - Symmetric key algorithm
        # "ES256" - Asymmetric, elliptic curve algorithm (faster than RSA)
        self.jwt_algorithm = config("JWT_ALGORITHM", default="HS256")
        # "HS256" - generate secret key using one of these:
        # os.urandom(32) 
        # secrets.token_hex(32)
        # Shell: `openssl rand --hex 32`
        self.secret_key = config("SECRET_KEY")
        # Use short expiry on tokens
        self.access_token_expire_minutes = config("ACCESS_TOKEN_EXPIRE_MINUTES", default=180, cast=int)

# For production
#settings = Settings()

# Run tests using a test database (Sqlite)
settings = Settings(TEST_DATABASE_URL)
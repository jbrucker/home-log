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
    def __init__(self,database_url:str = config("DATABASE_URL")):
        self.database_url = database_url

# Use Postgres
#settings = Settings()

# Run tests using Sqlite
settings = Settings(TEST_DATABASE_URL)
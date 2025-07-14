"""Configure Pytest test environment.

   These functions are called once per session in this order:
   1. pytest_configure(config)
   2. pytest_sessionstart(session)
   ...
   N. pytest_sessionfinish(session)

   In my tests, a fixture annotated with @fixture(scope="session")
   was never executed.
   
   To verify that this file is found by pytest, use:  pytest --trace-config
"""
import asyncio
from datetime import datetime
import logging
import os
from app.core.database import db
from app.core.config import settings

"""Use a temporary database for tests"""
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


def event_log(message: str):
    """Write a timestamped message to a file to record pytest events.
       This is so I can what setup & teardown functions are executed, and the order.
    """
    with open("event_log.txt", mode="a") as file:
        file.write(f"{datetime.now():%Y-%m-%d %T} {message}\n")


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(name)s: %(message)s",
        filename="./testing.log"
        )


def pytest_configure(config):
    """Configure logging once for the entire test session."""
    configure_logging()
    logging.getLogger("conftest").info("Logging initialized")
    event_log(f"Run pytest_config(config={str(config)})")
    # Create a new secret_key to avoid exposing the env var value
    # This assumes that the jwt functions get the secret key from settings.secret_key
    settings.secret_key = os.urandom(32)


def pytest_sessionstart(session):
    """Runs once before all tests."""
    event_log(f"Run pytest_sessionstart(session={str(session)})")
    # Connect to testing database
    db.create_engine(TEST_DATABASE_URL)
    print("Database engine url", str(db.engine.url))
    assert str(db.engine.url) == TEST_DATABASE_URL
    # destroy and recreate tables (one time) -- See also the "session" fixture in fixtures.py
    #asyncio.run(db.destroy_tables())
    #asyncio.run(db.create_tables())


def pytest_sessionfinish(session, exitstatus):
    """Runs once after all tests."""
    event_log(f"Run pytest_sessionfinish(session={str(session)})")
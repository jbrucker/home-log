"""Configure Pytest test environment.

   These functions are called once per session in this order:
   1. pytest_configure(config)
   2. pytest_sessionstart(session)
   Last. pytest_sessionfinish(session)

   In my tests, the fixture annotated with @fixture(scope="session")
   was never executed.

   To verify that this file is found by pytest, use:  pytest --trace-config
"""
from datetime import datetime
import logging
import os
from app.core.database import db
from app.core.config import settings

"""Use a temporary database for tests"""
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

EVENT_LOG = "pytest.log"


def event_log(message: str):
    """Write a timestamped message to a file to record pytest events.

       This records what setup & teardown functions are executed, and the order.
    """
    with open(EVENT_LOG, mode="a") as file:
        file.write(f"{datetime.now():%Y-%m-%d %T} {message}\n")


def configure_logging():
    """Configure Python logging to use a testing log file and threshold INFO."""
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(name)s: %(message)s",
        filename="./testing.log"
        )


def pytest_configure(config):
    """Configure logging once for the entire test session."""
    event_log(f"Run pytest_configure(config), config={str(config)}")
    configure_logging()
    logging.getLogger(__name__).info("Logging initialized")
    # Create a new secret_key to avoid exposing the env var value.
    # This assumes that the jwt functions use the key in settings.secret_key
    settings.secret_key = os.urandom(32)


def pytest_sessionstart(session):
    """Run once before all tests, but after `pytest_configure`."""
    event_log("Run pytest_sessionstart(session)")
    logging.getLogger(__name__).info("Run pytest_sessionstart(session)")
    # Connect to testing database
    db.create_engine(TEST_DATABASE_URL)
    logging.getLogger(__name__).info(f"db.engine.url = {db.engine.url}")
    assert str(db.engine.url) == TEST_DATABASE_URL
    # Destroy and recreate tables (one time)?
    # -- See also the "session" fixture in fixtures.py
    # asyncio.run(db.destroy_tables())
    # asyncio.run(db.create_tables())


def pytest_sessionfinish(session, exitstatus):
    """Run once after all tests."""
    event_log("Run pytest_sessionfinish(session)")
    logging.getLogger(__name__).info("Run pytest_sessionfinish(session)")

"""Configure Pytest test environmentg.

   To verify that this file is found by pytest, use:  pytest --trace-config
"""
from datetime import datetime
import logging


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
    file = open("/tmp/pytest_config.txt", mode="a")
    file.write(f"Running pytest_configure at {datetime.now()}\n.")
    file.write(f"config={str(config)} is a {type(config).__name__}\n")
    file.close()

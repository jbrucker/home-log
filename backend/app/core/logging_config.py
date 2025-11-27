"""Configure application log formats and streams.

For a containerized app, the recommended approach is to log
everything to stdout and use an external logging collector
to forward and aggregate logs.
"""
import logging
from decouple import config
from pythonjsonlogger import jsonlogger


def create_logging_config():
    """Return a logging configuration in Python dictConfig format."""
    log_level = config("LOG_LEVEL", default="INFO")

    # Common JSON formatter
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )

    # Shared handler for all loggers
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "()": jsonlogger.JsonFormatter,
                "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s",
            },
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            }
        },
        "loggers": {
            # Application logger
            "app": {
                "handlers": ["default"],
                "level": log_level,
                "propagate": False,
            },
            # Uvicorn logger
            "uvicorn": {
                "handlers": ["default"],
                "level": log_level,
            },
            # Uvicorn access logs (HTTP requests)
            "uvicorn.access": {
                "handlers": ["default"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["default"],
                "level": log_level,
                "propagate": False,
            },
        },
        "root": {
            "handlers": ["default"],
            "level": log_level,
        },
    }

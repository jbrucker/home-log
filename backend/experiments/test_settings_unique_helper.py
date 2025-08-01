"""Does "import config" create a new settings instance?."""
import config


def get_settings():
    """Return the settings, of course."""
    return config.settings


def get_counter():
    """Return the settings instance counter."""
    return config.settings.counter

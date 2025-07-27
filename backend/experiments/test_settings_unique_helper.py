"""Import config. Does it create a new settings instance?"""
import config


def get_settings():
    return config.settings


def get_counter():
    return config.settings.counter

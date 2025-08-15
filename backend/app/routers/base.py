"""Base configuration for multiple routers."""

# Path prefix for API routes, but maybe not for "/login" or "/logout".
# Set to an empty string (not "/") if no prefix. Do not include trailing /.
API_PREFIX = "/api"


def path(path: str) -> str:
    """Add any needed prefix to path for API call, for example '/sources' returns '/api/sources'."""
    return API_PREFIX + path

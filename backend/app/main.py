"""Initialize the application.

- define log format, log handlers, and custom logging
- add CORS Middleware to permit SPA's to work correctly
- normalize URLs by removing trailing "/" and NOT send 307 Redirect in this case
- add routes
"""

import logging
from contextlib import asynccontextmanager
import time
import uuid
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter
from app.core.database import db
from app.routers import auth, data_source, health, login, reading, user

# flake8: noqa: D401 First line of docstring must be imperitive.

console_handler = logging.StreamHandler()
# Initialize log format
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(module)s.%(name)s: %(message)s",
    handlers=[console_handler]
)
logger = logging.getLogger("main")
logger.info(f"Database URL is {str(db.engine.url)}")


@asynccontextmanager
async def lifecycle(app: FastAPI):
    """Perform FastAPI lifecycle event hook for start-up and shutdown."""
    logger.info("Starting lifecycle(app). Invoke on_startup()...")
    await on_startup()
    yield
    logger.info("Finishing lifecycle(app). Shutting down...")


# redirect_slashes=False disables automatic redirects in case of missing trailing "/"
app = FastAPI(lifespan=lifecycle, redirect_slashes=False)

# Instrument for Prometheus using pre-defined metrics from Instrumentator.
# The Instrumentator provides built-in metrics for request count, duration, and in-progress.
# We only add custom metrics for exception tracking which the Instrumentator doesn't provide.
instrumenter = Instrumentator(
    should_group_status_codes=True,           # optionally group 2xx/4xx/5xx
    should_ignore_untemplated=True,           # avoid high-cardinality paths where available
    should_instrument_requests_inprogress=True  # track in-progress requests
)
# Attach Instrumentator before the app starts
logger.info("Instrumenting app for Prometheus")
instrumenter.instrument(app)
instrumenter.expose(app, include_in_schema=False)
logger.info("Done instrumenting app")


# Custom metric for exception tracking (not provided by Instrumentator)
EXCEPTIONS = Counter(
    'http_request_exceptions_total',
    'Total exceptions during request processing',
    ['method', 'endpoint', 'exception_type']
)


# Optional: initialize schema on startup
# Deprecated: @app.on_event("startup")
async def on_startup():
    """Run FastAPI lifecycle event hook for start-up."""
    logger.info("Executing on_startup()")
    async with db.engine.begin() as connection:  # noqa: F841
        # await conn.run_sync(Base.metadata.create_all)
        # Create specific table
        # logger.info("Creating DataSource table")
        # await connection.run_sync(models.DataSource.__table__.create, checkfirst=True)
        pass

# Middleware order: normalize first, then monitoring, then logging

@app.middleware("http")
async def strip_trailing_slash(request: Request, call_next):
    """Remove trailing / from URLs for consistency."""
    if request.url.path.endswith("/") and request.url.path != "/":
        request.scope["path"] = request.url.path.rstrip("/")
    return await call_next(request)


@app.middleware("http")
async def track_exceptions(request: Request, call_next):
    """Track exceptions in Prometheus.

    The Instrumentator handles request count, latency, and in-progress tracking.
    This middleware only tracks exceptions by type, which the Instrumentator doesn't provide.
    """
    endpoint = request.url.path

    # Skip metrics endpoint
    if endpoint.startswith("/metrics"):
        return await call_next(request)

    method = request.method.upper()
    # Prefer route template over request path if available
    # This avoids endpoint explosion in metrics
    route = request.scope.get("route")
    try:
        if route is not None:
            endpoint = route.path
    except Exception:
        endpoint = request.url.path

    # Avoid extremely long endpoint labels
    MAX_ENDPOINT_LENGTH = 200
    if len(endpoint) > MAX_ENDPOINT_LENGTH:
        endpoint = endpoint[:MAX_ENDPOINT_LENGTH]

    try:
        response = await call_next(request)
    except Exception as ex:
        EXCEPTIONS.labels(method=method, endpoint=endpoint, exception_type=ex.__class__.__name__).inc()
        # Re-raise exception so FastAPI can handle it
        raise

    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Custom logging includes auth headers, or whatever.
    
       - Add a request id header if not provided
       - Mask sensitive headers such as authentication
       - Log after response to include status/time
    """
    req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    auth = request.headers.get("authorization")

    # Attach req_id to scope so downstream handlers can use it (and to response)
    request.state.request_id = req_id
    start_time = time.perf_counter()
    # Exclude some requests?
    # Use request.url.path not in ["/favicon.ico", "/health", ...]
    logger.info(f"{request.method.upper()} {request.url.path}?{request.query_params} req_id={req_id}")
    logger.debug(f"Authorization: {request.headers.get('authorization','')}")

    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Request failed (req_id={req_id}): {str(e)}")
        raise

    # Calculate response time in milliseconds
    process_time = (time.perf_counter() - start_time) * 1000

    # Log response
    logger.info(
        f"Response: {request.method} {request.url.path} "
        f"{response.status_code} {process_time:.2f}ms"
        f"| req_id={req_id}"
    )
    if isinstance(response, Response):
        response.headers["X-Request-ID"] = req_id
    return response


# Middleware for CORS support
origins = [
    "http://localhost:5173",   # Vue dev server
    "http://www.homelog.com",  # Production server
    "http://localhost:8000"
    ]
# For development only:
# origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Needed?
    allow_headers=["*"],
)


# Finally, register routers
app.include_router(health.router)
app.include_router(user.router)
app.include_router(login.router)
app.include_router(auth.router)
app.include_router(data_source.router)
app.include_router(reading.router)

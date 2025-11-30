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
# For custom metrics
from prometheus_client import Counter, Histogram, Gauge
from app.core import config
from app.core.database import db
from app.routers import auth, data_source, health, login, reading, user

# flake8: noqa: D401 First line of docstring must be imperative.

console_handler = logging.StreamHandler()
# Initialize log format
logging.basicConfig(
    level=config.settings.log_level,
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
app = FastAPI(lifespan=lifecycle, redirect_slashes=True)

# Instrument for Prometheus using pre-defined metrics
# Prefer instrument() + expose() to ensure custom metrics registered before expose
instrumenter = Instrumentator(
    should_group_status_codes=True,  # optionally group 2xx/4xx/5xx
    should_ignore_untemplated=True,  # avoid high-cardinality paths where available
    should_instrument_requests_inprogress=True,
    # should_respect_env_var=True,
    # env_var_name="ENABLE_METRICS",
    excluded_handlers=["/metrics", "/health"],
    inprogress_name="inprogress",
    inprogress_labels=True,
)
# Attach Instrumentator before the app starts
logger.info("Instrumenting app for Prometheus")
instrumenter.instrument(app)
instrumenter.expose(app, include_in_schema=False)
logger.info("Done instrumenting app")


# Additional metrics for Prometheus
# Define metrics for (hopefully) API templated routes
REQUEST_COUNT = Counter(
    'http_request_routes',
    'Total HTTP Requests by Route',
    ['method', 'route', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_routes_duration_seconds',
    'HTTP Request Latency by Route (sec)',
    ['method', 'route'],
    # tunable buckets for web latency (seconds)
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10]
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

# Middleware invocation order: normalize request, monitoring, logging, CORS 
# Middleware are invoked in the **reverse** order they are added to the app.

def write_scope(request: Request):
    """Write request scope to a file, for development to understand FastAPI internals.

    :param request: FastAPI Request object
    """
    FILENAME = "request_scopes.txt"
    with open(FILENAME, "a") as file:
        req_type = type(request).__name__     
        file.write(f"scope for {request.method} {request.url.path}\n")
        for key, value in request.scope.items():
            file.write(f"  {key}: {value}\n")
        file.write("\n")


@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    """Collect Prometheus metrics.

      Request count and latency by endpoint, method, & status code.
      Exceptions by endpoint and method.
      - endpoint: use route template when available (reduces cardinality)
      - method: use request.method
      - status_code: as string
    """
    logger.info(f"monitor_requests: request.url.path={request.url.path}")

    endpoint = request.url.path
    # Normalize: remove trailing slash
    if endpoint.endswith("/") and endpoint != "/":
        endpoint = endpoint[:-1]
    
    # Skip metrics endpoint
    if endpoint.startswith("/metrics"):
        return await call_next(request)
    
    method = request.method.upper()
    # Prefer route template over request path if available 
    # This avoids endpoint explosion in metrics.
    # request.scope.get("route") returns a FastAPI APIRoute object or None.
    # APIRoute has path and methods attributes.
    api_route = request.scope.get("route")
    try:
        if api_route is not None:
            route = api_route.path
        else:
            route = request.url.path
            # This happens a lot, so don't log it.
            #logging.warning(f"monitor_requests: Failed to extract route template for path={request.url.path}")

    except Exception as ex:
        logging.exception(ex)
        route = request.url.path

    # Avoid extremely long endpoint labels
    MAX_ENDPOINT_LENGTH = 100
    if len(route) > MAX_ENDPOINT_LENGTH:
        route = route[:MAX_ENDPOINT_LENGTH]

    # time.perf_counter() is higher resolution than time.time()
    start_time = time.perf_counter()
    
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as ex:
        status_code = 500
        # Re-raise exception so FastAPI can handle it
        raise
    finally:
        latency = time.perf_counter() - start_time
        REQUEST_DURATION.labels(method=method, route=route).observe(latency)
        REQUEST_COUNT.labels(method=method, route=route, status_code=str(status_code)).inc()
    
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Custom logging includes auth headers, or whatever.
    
       - Add a request id header if not provided
       - Mask sensitive headers such as authentication
       - Log after response to include status/time
    """
    req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    # Attach req_id to scope so downstream handlers can use it (and to response)
    request.state.request_id = req_id
    start_time = time.perf_counter()
    # Exclude some requests?
    # Use request.url.path not in ["/favicon.ico", "/health", ...]
    logger.debug(f"{request.method.upper()} {request.url.path}?{request.query_params}")
    auth = request.headers.get("authorization")
    if auth:
        auth = auth[:-8] + '...' if len(auth) > 8 else '...'
        logger.debug(f"Authorization: {request.headers.get('authorization',auth)}")

    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Request failed (req_id={req_id}): {str(e)}")
        raise

    # Calculate response time in milliseconds
    process_time = (time.perf_counter() - start_time) * 1000

    # Log response
    logger.debug(
        f"Response: {request.method} {request.url.path} "
        f"{response.status_code} {process_time:.2f}ms"
        f"| req_id={req_id}"
    )
    if isinstance(response, Response):
        response.headers["X-Request-ID"] = req_id
    return response


# Normalize URLs by removing trailing "/" to avoid 307 Redirects
@app.middleware("http")
async def strip_trailing_slash(request: Request, call_next):
    """Remove trailing / from URLs for consistency."""
    # write_scope(request)
    request_path = request.scope["path"] or request.url.path
    if request_path.endswith("/") and request_path != "/":
        request.scope["path"] = request_path.rstrip("/")

    response = await call_next(request)
    return response


# Middleware for CORS support
origins = [
    "http://localhost:5173",   # Vue dev server
    "http://www.homelog.com",  # Production server
    "http://localhost:8000"
    ]
# For development only:
# origins = ["*"]

# See Wiki page "FastAPI Programming Notes" for why CORS added last
# and invoked first.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Needed?
    allow_headers=["Authorization", "*"],
)


# Finally, register routers
app.include_router(health.router)
app.include_router(user.router)
app.include_router(login.router)
app.include_router(auth.router)
app.include_router(data_source.router)
app.include_router(reading.router)

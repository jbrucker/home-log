"""Initialize the application.

- define log format, log handlers, and custom logging
- add CORS Middleware to permit SPA's to work correctly
- normalize URLs by removing trailing "/" and NOT send 307 Redirect in this case
- add routes
"""

import logging
from contextlib import asynccontextmanager
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import db
from app.routers import account, auth, data_source, reading, user

# flake8: noqa: D401 First line of docstring must be imperitive.

# Initialize log format
logging.basicConfig(
    level=logging.DEBUG,
    format="\033[32m%(levelname)s\033[0m: %(module)s.%(name)s \033[35m%(message)s\033[0m",
    handlers=[
        logging.FileHandler("backend.log", mode="w"),  # "w" = OVERWRITE
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("main")
logger.info(f"Database URL is {str(db.engine.url)}")


@asynccontextmanager
async def lifecycle(app: FastAPI):
    """Perform FastAPI lifecycle event hook for start-up and shutdown."""
    logger.info("Executing lifecycle(app). Invoke on_startup()...")
    await on_startup()
    yield
    logger.info("Finishing lifecycle(app). Shutting down...")


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


# redirect_slashes=False disables automatic redirects in case of missing trailing "/"
app = FastAPI(lifespan=lifecycle, redirect_slashes=False)

# Add middleware for CORS support
origins = [
    "http://localhost:5173",  # Vue dev server
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

app.include_router(user.router)
app.include_router(auth.router)
app.include_router(account.router)
app.include_router(data_source.router)
app.include_router(reading.router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Custom logging includes auth headers, or whatever."""
    start_time = time.time()
    # Exclude some requests?
    # Use request.url.path not in ["/favicon.ico", "/health", ...]

    logger.info(f"{request.method.upper()} {request.url.path}?{request.query_params}")
    logger.debug(f"Authorization: {request.headers.get('authorization','')}")

    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        raise

    # Calculate response time
    process_time = (time.time() - start_time) * 1000
    formatted_time = f"{process_time:.2f}ms"

    # Log response
    logger.info(
        f"Response: {request.method} {request.url.path} "
        f"| Status {response.status_code} "
        f"| Time {formatted_time}"
    )
    return response

@app.middleware("http")
async def strip_trailing_slash(request: Request, call_next):
    """Remove trailing / from URLs for consistency."""
    if request.url.path.endswith("/") and request.url.path != "/":
        request.scope["path"] = request.url.path.rstrip("/")
    return await call_next(request)

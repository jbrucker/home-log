"""Initialize the application, apply routes."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import db
from app.routers import account, auth, data_source, user


# Initialize log format
logging.basicConfig(
    level=logging.INFO,
    format="\033[32m%(levelname)s\033[0m: %(module)s \033[35m%(message)s\033[0m"
)
logger = logging.getLogger("main")
logger.info(f"Database URL {str(db.engine.url)}")


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


app = FastAPI(lifespan=lifecycle)

app.include_router(user.router)
app.include_router(auth.router)
app.include_router(account.router)
app.include_router(data_source.router)

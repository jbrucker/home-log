from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from app import models
from app.routers import account, auth, data_source, user
from app.core.database import Base, db


# TODO: Initialize log format
logging.basicConfig(
    level=logging.INFO,
    format="\033[32m%(levelname)s\033[0m: %(module)s \033[35m%(message)s\033[0m"
)
logger = logging.getLogger("main")
logger.info(f"Database URL {str(db.engine.url)}")

@asynccontextmanager
async def lifecycle(app: FastAPI):
    logger.info("Startup...")
    await on_startup()
    yield
    logger.info("Shutting down...")


# Optional: initialize schema on startup
# Deprecated: @app.on_event("startup")
async def on_startup():
    logger.info("Executing on_startup()")
    async with db.engine.begin() as conn:
        # await conn.run_sync(Base.metadata.create_all)
        # Create specific table
        #logger.info("Creating DataSource table")
        #await conn.run_sync(models.DataSource.__table__.create, checkfirst=True)
        pass


app = FastAPI(lifespan=lifecycle)

app.include_router(user.router)
app.include_router(auth.router)
app.include_router(account.router)
app.include_router(data_source.router)
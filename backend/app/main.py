from fastapi import FastAPI
from app.routers import user
from app.core.database import Base, engine

app = FastAPI(title="HomeLog")

app.include_router(user.router)

# Optional: initialize schema on startup
#@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

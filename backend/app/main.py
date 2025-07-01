from fastapi import FastAPI
from app.routers import auth, user
from app.core.database import Base, db

app = FastAPI(title="HomeLog")

app.include_router(user.router)
app.include_router(auth.router)

# Optional: initialize schema on startup
#@app.on_event("startup")
async def on_startup():
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

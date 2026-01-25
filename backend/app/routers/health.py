"""Application health check, invoked by the container."""
from fastapi import APIRouter

router = APIRouter(tags=['health'])


@router.get("/health")
async def health():
    """Lightweight health endpoint for Docker healthchecks."""
    return {"status": "ok"}

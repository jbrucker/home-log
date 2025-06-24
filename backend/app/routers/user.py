"""REST endpoints for user.

   To declare a response model used to serialize the return value, use a schema class not a model class.
"""

from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app import schemas
from app.data_access import user_dao

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", status_code=HTTPStatus.CREATED, response_model=schemas.User)
async def register_user(user_data: schemas.UserCreate, session: AsyncSession = Depends(get_db)):
    existing_user = await user_dao.get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await user_dao.create_user(db, user_data)


"""REST endpoints for user.

   To declare a response model used to serialize the return value, use a schema class not a model class.
"""

from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import db
from app import models, schemas
from app.data_access import user_dao

router = APIRouter(tags=["users"])  # can use prefix="/users" to factor out path prefix.

@router.get("/users/{user_id}", response_model=schemas.User)
async def get_user(user_id: int, session: AsyncSession = Depends(db.get_session)):
    user = await user_dao.get_user_by_id(session, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user  # FastAPI will use from_attributes=True to convert to schema


@router.post("/users", status_code=HTTPStatus.CREATED, response_model=schemas.User)
async def register_user(user_data: schemas.UserCreate, 
                        session: AsyncSession = Depends(db.get_session)):
    existing_user = await user_dao.get_user_by_email(session, user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await user_dao.create_user(session, user_data)


"""REST endpoints for user.

   To declare a response model used to serialize the return value, use a schema class not a model class.
"""

from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import db
from app import schemas
from app.data_access import user_dao
from app.utils import oauth2


router = APIRouter(tags=["users"])  # can use prefix="/users" to factor out path prefix.

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


@router.get("/users")
async def get_users(limit: int = 20, session: AsyncSession = Depends(db.get_session)) -> list[schemas.User]:
    """Get multiple users.  Limit the number of returned values using `limit=n` query parameter.
    
    :param limit: maximum number of Users to return.  Use 0 for unlimited.
    """
    if not isinstance(limit, int) or limit < 0:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=f"Invalid value of limit")
    users = await user_dao.get_users(session, limit)
    return users


@router.get("/users/{user_id}")
async def get_user(user_id: int, session: AsyncSession = Depends(db.get_session)) -> schemas.User:
    """Get a user with matching `user_id`."""
    user = await user_dao.get_user_by_id(session, user_id)
    if user is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"User id {user_id} not found")
    return user  # FastAPI will use from_attributes=True to convert to schema


@router.post("/users", status_code=HTTPStatus.CREATED, response_model=schemas.User)
async def register_user(user_data: schemas.UserCreate,
                        request: Request,
                        response: Response,
                        session: AsyncSession = Depends(db.get_session),
                        current_user = Depends(oauth2.get_current_user)
                        ):
    """Persist a new user.
       If success, return the user data and a `Location:` header containing the URL of the new entity.
    """
    existing_user = await user_dao.get_user_by_email(session, user_data.email)
    if existing_user:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Email already registered")
    user = await user_dao.create_user(session, user_data)
    # Add Location of new user
    location = request.url_for("get_user", user_id=str(user.id))  # reverse mapping
    response.headers["Location"] = str(location)
    # user is serialized automatically using Schema User (I think)
    return user


@router.put("/users/{user_id}", status_code=status.HTTP_201_CREATED, response_model=schemas.User)
async def update_user(user_id: int, user_data: schemas.UserCreate, 
                      session: AsyncSession = Depends(db.get_session),
                      current_user = Depends(oauth2.get_current_user)
                     ):
    """Update the data for an existing user, using the `user_id` to identify the user to modify."""
    user = await user_dao.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No user with id {user_id}")
    return await user_dao.update_user(session, user_id=user_id, user_data=user_data)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, session: AsyncSession = Depends(db.get_session)):
    """Delete a user by id.  Returns the data for the deleted user."""
    user = await user_dao.delete_user(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No user with id {user_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT, detail=f"Deleted user {user_id}")
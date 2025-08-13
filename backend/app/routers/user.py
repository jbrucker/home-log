"""REST endpoints for a user.

   To declare a response model used to serialize the return value, use a schema class not a model class.
"""
# flake8: noqa: E251
# E251 unexpected space around equals in 'parameter=value'

import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi import status  # for HTTP status codes. Can alternatively use http.HTTPStatus.
import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import db
from app import schemas
from app.data_access import user_dao
from app.routers.base import API_PREFIX, path
from app.utils import oauth2

# can add prefix="/users" option to factor out path prefix. I prefer explicit path for readability.
router = APIRouter(prefix=API_PREFIX, tags=["Users"]) 


@router.post("/users", status_code=status.HTTP_201_CREATED, response_model=schemas.User)
async def create_user(user_data: schemas.UserCreate,
                        request: Request,
                        response: Response,
                        session: AsyncSession = Depends(db.get_session),
                        current_user = Depends(oauth2.get_current_user)
                        ):
    """Persist a new user.

       :returns: the user data and a `Location:` header containing the URL of the new entity.
    """
    existing_user = await user_dao.get_by_email(session, user_data.email)
    if existing_user:
        # 409 CONFLICT is standard response for conflicting data
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, 
                            detail="Email {user_data.email} already registered")
    try:
        result = await user_dao.create(session, user_data)
    except ValueError as ex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail="Invalid data for user. Exception: {ex}")
    # Add Location of new resource - "url_for" performs reverse mapping
    location = request.url_for("get_user", user_id=str(result.id))
    response.headers["Location"] = str(location)
    # result is serialized automatically by FastAPI
    return result


@router.get("/users/{user_id}", response_model=schemas.User, status_code=status.HTTP_200_OK)
async def get_user(user_id: int, session: AsyncSession = Depends(db.get_session)) -> schemas.User:
    """Get a user with matching `user_id`."""
    user = await user_dao.get(session, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User id {user_id} not found")
    return user  # FastAPI will use from_attributes=True to convert to schema


@router.get("/users", status_code=status.HTTP_200_OK)
async def get_users(limit: int = Query(100, ge=1, le=100),
                    offset: int = Query(0, ge=0),
                    session: AsyncSession = Depends(db.get_session),
                    current_user = Depends(oauth2.get_current_user)) -> list[schemas.User]:
    """Get multiple users.  Limit the number of returned values using `limit=n` query parameter.
    
    :param offset: number of users (ordered by id) to skip before first result returned.
    :param limit: maximum number of Users to return.  Use 0 for unlimited.
    """
    if not isinstance(limit, int) or limit < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid value of limit")
    users = await user_dao.get_users(session, limit=limit, offset=offset)
    return users


@router.put("/users/{user_id}", status_code=status.HTTP_200_OK, response_model=schemas.User)
async def update_user(user_id: int, 
                      user_data: schemas.UserCreate, 
                      session: AsyncSession = Depends(db.get_session),
                      current_user = Depends(oauth2.get_current_user)
                     ) -> schemas.User:
    """Update the data for an existing user, using the `user_id` to identify the user to modify.
    
    :returns: 200 after successful update, 400 BAD REQUEST if update data is invalid,
              403 FORBIDDEN if the update is not allowed, e.g. updating a different user,
              409 CONFLICT if update violates database integrity (email already used by another user)
    """
    result = await user_dao.get(session, user_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No user with id {user_id}")
    # User can update only his own data
    if user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    # return the updated user model (without password)
    try:
        updated = await user_dao.update(session, user_id=user_id, user_data=user_data)
        return updated
    except sqlalchemy.exc.IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Data integrity error")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, 
                      session: AsyncSession = Depends(db.get_session),
                      current_user = Depends(oauth2.get_current_user)):
    """Delete a user by id.  Returns the data for the deleted entity."""
    logging.getLogger(__name__).info(f"delete_user user_id {user_id} by {str(current_user)}")
    assert user_id > 0
    result = await user_dao.delete_user(session, user_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No user with id {user_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

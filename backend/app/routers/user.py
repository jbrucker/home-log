"""REST endpoints for user.

   To declare a response model used to serialize the return value, use a schema class not a model class.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi import status  # for HTTP status codes. Can alternatively use http.HTTPStatus.
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import db
from app import schemas
from app.data_access import user_dao
from app.utils import oauth2

# can add prefix="/users" option to factor out path prefix. I prefer explicit path for readability.
router = APIRouter(tags=["users"]) 


@router.get("/users")
async def get_users(limit: int = Query(20, ge=1, le=100),
                    offset: int = Query(0, ge=0),
                    session: AsyncSession = Depends(db.get_session)) -> list[schemas.User]:
    """Get multiple users.  Limit the number of returned values using `limit=n` query parameter.
    
    :param offset: number of users (ordered by id) to skip before first result returned.
    :param limit: maximum number of Users to return.  Use 0 for unlimited.
    """
    if not isinstance(limit, int) or limit < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid value of limit")
    users = await user_dao.get_users(session, limit=limit, offset=offset)
    return users


@router.get("/users/{user_id}", response_model=schemas.User)
async def get_user(user_id: int, session: AsyncSession = Depends(db.get_session)) -> schemas.User:
    """Get a user with matching `user_id`."""
    user = await user_dao.get_user(session, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User id {user_id} not found")
    return user  # FastAPI will use from_attributes=True to convert to schema


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
    existing_user = await user_dao.get_user_by_email(session, user_data.email)
    if existing_user:
        # 409 CONFLICT is standard response for conflicting data
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, 
                            detail="Email {user_data.email} already registered")
    try:
        result = await user_dao.create(session, user_data)
    except ValueError as ex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail="Invalid data for user. Exception: {ex}")

    # Add Location of new user - "url_for" performs reverse mapping
    location = request.url_for("get_user", user_id=str(result.id))
    response.headers["Location"] = str(location)
    # result is serialized automatically by FastAPI
    return result


@router.put("/users/{user_id}", status_code=status.HTTP_201_CREATED, response_model=schemas.User)
async def update_user(user_id: int, 
                      user_data: schemas.UserCreate, 
                      session: AsyncSession = Depends(db.get_session),
                      current_user = Depends(oauth2.get_current_user)
                     ) -> schemas.User:
    """Update the data for an existing user, using the `user_id` to identify the user to modify."""
    result = await user_dao.get_user(session, user_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No user with id {user_id}")
    return await user_dao.update_user(session, user_id=user_id, user_data=user_data)


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
"""Router endpoints for account management, including change password."""

from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException, Response
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core import database
from app.data_access import user_dao
from app.utils import oauth2
from app import models, schemas

router = APIRouter(tags=['Account'])


@router.post('/account/password', status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        session: Session = Depends(database.db.get_session),
        current_user: models.User = Depends(oauth2.get_current_user)
        ):
    """Change password for the currently authenticated user,\
       where the password is submitted as form-data in a field named 'password'.

       The 'username' used in form must be the email of the currently authenticated user.
    """
    try:
        # validate password from form_data
        schemas.PasswordCreate(password=form_data.password)
    except ValueError as ex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ex))
    user_password = await user_dao.set_password(session, current_user, form_data.password)  # noqa: F841
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put('/account/password', status_code=status.HTTP_204_NO_CONTENT)
async def update_password(
        password_request: schemas.PasswordStr,
        session: Session = Depends(database.db.get_session),
        current_user: models.User = Depends(oauth2.get_current_user)
        ):
    """Change password for the authenticated user, for request submitted as JSON data.

    Returns:
    - 204 No Content on success (recommended best practice)
    - 400 Bad Request if request does not contain required data
    - 401 Unauthorized if token invalid
    - 422 Validation Errors if the password does not satisfy validation rules,
    such as at least 1 uppercase letter, 1 lowercase letter, and 1 numeric char
    """
    # Instead of returning status 204, it's acceptable to return 200 OK with a text body such as:
    # { "status": "success", "message": "Password updated" }
    # but do not return the hashed password.
    new_password = password_request.get_secret_value()
    user_password = await user_dao.set_password(session, current_user, new_password)  # noqa: F841
    return Response(status_code=status.HTTP_204_NO_CONTENT)

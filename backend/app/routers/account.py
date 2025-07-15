"""Router endpoints for account management, including change password."""

import logging
from pathlib import Path
from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException, Response
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core import database, security
from app.data_access import user_dao
from app.utils import jwt, oauth2
from app import schemas
from fastapi.responses import HTMLResponse

router = APIRouter(tags=['Account'])

@router.post('/account/password')
async def change_password(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()], 
        session: Session = Depends(database.db.get_session),
        current_user = Depends(oauth2.get_current_user)
    ):
    """Change password for the currently authenticated user,
       where the password is submitted as form-data in a field named 'password'.
       The 'username' must be the email of the currently authenticated user.
    """
    try:
        new_password = schemas.PasswordCreate(password=form_data.password)
    except ValueError as ex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ex))
    user_password = await user_dao.set_password(session, current_user, form_data.password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put('/account/password')
async def update_password(
        password_request: schemas.PasswordStr, 
        session: Session = Depends(database.db.get_session),
        current_user = Depends(oauth2.get_current_user)
    ):
    """Change password for the currently authenticated user,
       where the password is submitted in request as JSON data.
       Returns:
        200 OK on success (with optional success message)
        400 Bad Request for validation errors
        401 Unauthorized if token invalid
        403 Forbidden if new password doesn't meet requirements (?)
    """
    new_password = password_request.get_secret_value()
    user_password = await user_dao.set_password(session, current_user, new_password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


"""Router endpoints for account management, including change password."""

import logging
from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException, Request, Response
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core import database
from app.data_access import user_dao
from app.routers.base import API_PREFIX
from app.routers.login import validate_login
from app.utils import jwt, oauth2
from app import models, schemas

router = APIRouter(prefix=API_PREFIX, tags=['Authentication API for WS'])


@router.post('/auth/password', status_code=status.HTTP_204_NO_CONTENT)
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


@router.put('/auth/password', status_code=status.HTTP_204_NO_CONTENT)
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


@router.post('/auth/login', response_model=schemas.Token)
async def login_json(login_data: schemas.LoginData,
                     request: Request,
                     session: Session = Depends(database.db.get_session)):
    """Authenticate user using JSON input values and return a JWT token.

    :param request: POST request containing username=value, password=value
    :returns: JSON access token. Format of body is:
              {"access_token": "jwt-token-value", "token_type": "bearer" }

    The `grant_type` should always be `password` (the OAuth2 flow).
    """
    content_type = request.headers.get("content-type", "").lower()

    if not content_type.startswith("application/json"):
        logging.warning(f"Login request failed. Content type {content_type} not supported.")
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                            detail="Unsupported Content-Type")
    try:
        # username field value is expected to be an email address
        email = login_data.username
        password = login_data.password
    except Exception:
        logging.warning(f"Login failed. JSON data missing username or password.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid JSON body")
    access_token = await validate_login(email, password, session)
    return {"access_token": access_token, "token_type": "bearer"}


@router.put('/diyvalidate')
async def validate_token_diy(
                     request: Request,
                     response: Response):
    """Verify the the access token in the Authorization header is still valid.
    
    Do It Yourself implementation, w/o oauth2_schema
    """
    token_header: str = request.headers.get("authorization")
    if not token_header:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Missing required Authorization header")
    logging.info(f"Authorization: {token_header}")
    try:
        token = token_header.split()[-1].strip()
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid Authorization header: {token_header}")
    if jwt.verify_access_token(token):
        response.status_code = status.HTTP_200_OK
        return
    # failed validation
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid authentication credentials",
                        headers={"WWW-Authenticate": "Bearer"}
                        )


@router.put('/validate')
async def validate_token(token: str = Depends(oauth2.oauth2_scheme)):
    """Validate the access token."""
    try:
        return jwt.verify_access_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

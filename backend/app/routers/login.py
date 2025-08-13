"""Route handler to authenticate a User."""

import logging
from pathlib import Path
from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core import database, security
from app.data_access import user_dao
from app.utils import jwt
from app import schemas
from fastapi.responses import HTMLResponse

router = APIRouter(tags=['Form-based Authentication for Web Apps'])


@router.get('/login', response_class=HTMLResponse)
async def loginform():
    """Return a login form in html."""
    file_path = Path("app/forms/login.html")
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Login form {str(file_path.absolute())} not found"
                            )
    return file_path.read_text(encoding="utf-8")


@router.post('/login', response_model=schemas.Token)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                session: Session = Depends(database.db.get_session)):
    """Authenticate user using form data and return a JWT token for this session.

    :param form_data: data from login form, containing 'username' and 'password' fields

    `form_data` also has fields for `grant_type`, (optional) `scope`, `client_id`, and `client_secret`
    The `grant_type` should always be `password` (the OAuth2 flow).
    """
    # username is really the email address. In our models, 'username' is arbitrary and not unique.
    try:
        email = form_data.username
        password = form_data.password
    except Exception:
        logging.warning(f"Login failed for {email}. POST form data invalid.")
        # Response should probably be 422 Unprocessable Entity
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Missing user email or password"
                            )
    access_token = await validate_login(email, password, session)
    return {"access_token": access_token, "token_type": "bearer"}


async def validate_login(email: str, password: str, session: Session) -> str:
    """Validate user credentials and return a JWT access token.

    If any errors, raises HTTPException.
    """
    if not email or not password:
        logging.warning(f"Login failed for {email}. Missing username or password.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                      detail="Username and password may not be empty.")
    user = await user_dao.get_by_email(session, email=email)
    if not user:
        logging.warning(f"Login failed for {email}. Unknown user.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Credentials",
            headers={"WWW-Authenticate": "Bearer"}
            )
    hashed_password = await user_dao.get_password(session, user)
    if not hashed_password:
        logging.warning(f"Login failed for {email}. User has no local password.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User does not have local password credential",
            headers={"WWW-Authenticate": "Bearer"}
            )
    if not security.verify_password(hashed_password=hashed_password, plain_password=password):
        logging.warning(f"Login failed for {email} with {password}. Invalid credentials.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Credentials",
            headers={"WWW-Authenticate": "Bearer"}
            )
    # create and return a token
    access_token = jwt.create_access_token(data={"user_id": user.id})
    logging.info(f"Login success for {email} Access token granted.")
    return access_token

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

router = APIRouter(tags=['Authentication'])


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
    """Authenticate user and return a JWT token for this session.

    :param form_data: data from login form, containing 'username' and 'password' fields

    `form_data` also has fields for `grant_type`, (optional) `scope`, `client_id`, and `client_secret`
    The `grant_type` should always be `password` (the OAuth2 flow).
    """
    # username is really the email address. In our models, 'username' is arbitrary and not unique.
    try:
        email = form_data.username
        password = form_data.password
        logging.warning(f"Login for {email} with {password}")
        assert email is not None
        assert password is not None
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Missing user email or password"
                            )
    user = await user_dao.get_by_email(session, email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Credentials",
            headers={"WWW-Authenticate": "Bearer"}
            )
    hashed_password = await user_dao.get_password(session, user)
    if not hashed_password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have local password credential",
            headers={"WWW-Authenticate": "Bearer"}
            )

    if not security.verify_password(hashed_password=hashed_password, plain_password=password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Credentials",
            headers={"WWW-Authenticate": "Bearer"}
            )

    # create and return a token
    access_token = jwt.create_access_token(data={"user_id": user.id})

    return {"access_token": access_token, "token_type": "bearer"}

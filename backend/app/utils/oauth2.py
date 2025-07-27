"""Support for OAuth2 Password flow.

Create a JWT session token, validate a token, extract data from a token.
"""
from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jose.exceptions

from app.core.database import db
from app.data_access import user_dao
from app import models
from app.utils.jwt import verify_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')


async def get_current_user(
                    token: str = Depends(oauth2_scheme),
                    session: Session = Depends(db.get_session),
                    ) -> models.User | None:
    """Verify access token and get the currently authenticated user.

    :returns: User model for user_id in token
    :raises HTTPException: with status 401 if token is invalid, expired,
                        or user_id is missing/not known
    """
    try:
        payload = verify_access_token(token)
        user_id = payload.get("user_id", None)
    except jose.exceptions.ExpiredSignatureError:
        raise credentials_exception(detail="Token Expired",
                            bearer_detail='error="invalid_token" error_description="Token expired"')
    except jose.exceptions.JWTError:
        # this also catches JWTClaimsError
        raise credentials_exception(detail="Invalid token")
    if not user_id:
        raise credentials_exception(detail="Invalid token. Missing user id.")

    user = await user_dao.get(session, user_id=user_id)
    return user


def credentials_exception(detail: str = "Invalid authentication credentials",
                          bearer_detail: str = "") -> HTTPException:
    """Return a custom exception for credentials error.

    :param detail: is added as a 'detail' header field
    :param bearer_detail: string appended to 'WWW-Authenticate' header
    """
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                         detail=detail,
                         headers={"WWW-Authenticate": f"Bearer {bearer_detail}"}
                         )

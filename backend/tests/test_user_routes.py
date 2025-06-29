"""Test the FastAPI routes for /user"""
from fastapi import status
import pytest, pytest_asyncio
from jose import jwt
from app import schemas
from app.data_access import user_dao
# VS Code thinks these fixtures are unused, but they are used & necessary.
from .fixtures import client, session

@pytest.mark.asyncio
async def test_create_user(session, client):
    USER_EMAIL = "sally@hackers.com"
    result = client.post("/users",
                         json={"username": "Sally", "email": USER_EMAIL}
                        )
    new_user = schemas.User(**result.json())
    assert result.status_code == status.HTTP_201_CREATED
    assert new_user.email == USER_EMAIL
    assert new_user.username == "Sally"
    # new user is in database, too
    user = await user_dao.get_user_by_email(session, email=USER_EMAIL)
    assert user is not None
    assert user.username == "Sally"
    # cannot add another user with same email
    result = client.post("/users",
                         json={"username": "Harry", "email": USER_EMAIL}
                        )
    # TODO what should be status code? Check Microsoft Guidance
    assert result.status_code == status.HTTP_400_BAD_REQUEST

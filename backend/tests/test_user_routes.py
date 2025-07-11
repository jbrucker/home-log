"""Test the FastAPI routes for /user"""
from fastapi import status

from fastapi.testclient import TestClient
import pytest, pytest_asyncio
from app import schemas
from app.data_access import user_dao
from app.core import security
from app.utils import jwt
# VS Code thinks these fixtures are unused, but they are used & necessary.
from .fixtures import client, auth_user, session
from .utils import create_users


def auth_headers(token: str) -> dict:
    """Return authorization headers containing the given token."""
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture()
async def alexa(session):
    """Test fixture for a persisted user name Alexa."""
    new_user = schemas.UserCreate(email="alexa@amazon.com", username="Alexa")
    user = await user_dao.create(session, new_user) 
    assert user.id > 0, "Persisted user should have id > 0"
    return user


@pytest_asyncio.fixture()
async def sally(session):
    """Test fixture for a persisted user name Sally."""
    new_user = schemas.UserCreate(email="sally@yahoo.com", username="Sally")
    user = await user_dao.create(session, new_user)
    assert user.id > 0, "Persisted user should have id > 0"
    return user


@pytest.mark.asyncio
async def test_create_user(session, auth_user, client: TestClient):
    """An authorized user can create a new user entity."""
    # add authentication
    token = jwt.create_access_token(data={"user_id": auth_user.id}, expires=30)
    USER_EMAIL = "harry@hackers.com"
    USER_NAME = "Harry Hacker"
    result = client.post("/users",
                         headers=auth_headers(token),
                         json={"username": USER_NAME, "email": USER_EMAIL}
                        )
    new_user = schemas.User(**result.json())
    assert result.status_code == status.HTTP_201_CREATED
    assert new_user.email == USER_EMAIL
    assert new_user.username == USER_NAME
    # new user is in database, too
    user = await user_dao.get_user_by_email(session, email=USER_EMAIL)
    assert user is not None
    assert user.username == USER_NAME
    # cannot add another user with same email
    result = client.post("/users",
                         headers=auth_headers(token),
                         json={"username": "Jone", "email": USER_EMAIL}
                        )
    # TODO what should be status code? Check Microsoft Guidance
    assert result.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_get_user(session, alexa, auth_user, client: TestClient):
    """Router returns a user with matching id, e.g. GET /users/1."""
    # add authentication?
    token = jwt.create_access_token(data={"user_id": auth_user.id}, expires=30)
    # requested user
    user_id = alexa.id
    # Use /users/delete
    result = client.get(f"/users/{user_id}", headers=auth_headers(token))   # auth not really required
    # Should return HTTP 200 OK with data
    assert result.status_code == status.HTTP_200_OK
    # get user data from response body
    user_data = result.json()
    assert user_data["id"] == alexa.id
    assert user_data["email"] == alexa.email
    assert user_data["username"] == alexa.username


@pytest.mark.asyncio
async def test_get_users_returns_all(session, auth_user, client: TestClient):
    """Router returns all users when no limit is specified."""
    await create_users(session, 20)
    token = jwt.create_access_token(data={"user_id": auth_user.id}, expires=30)
    result = client.get("/users/", headers=auth_headers(token))
    assert result.status_code == status.HTTP_200_OK
    user_data = result.json()
    assert isinstance(user_data, list)
    assert len(user_data) == 20


@pytest.mark.asyncio
async def test_get_users_with_limit(session, auth_user, client: TestClient):
    """Router returns specified number of users when limit is provided."""
    await create_users(session, 20)
    token = jwt.create_access_token(data={"user_id": auth_user.id}, expires=30)
    result = client.get("/users/?limit=5", headers=auth_headers(token))
    assert result.status_code == status.HTTP_200_OK
    user_data = result.json()
    assert isinstance(user_data, list)
    assert len(user_data) == 5


@pytest.mark.skip(reason="For debugging allow unauthenticated get all users")
@pytest.mark.asyncio
async def test_get_users_unauthenticated(session, client: TestClient):
    """Unauthenticated request to get all users should be forbidden."""
    await create_users(session, 5)
    result = client.get("/users/")
    assert result.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_delete_user(session, alexa, auth_user, client: TestClient):
    """An authorized user can delete a user. For now, any authenticated user is authorized."""
    # add authentication
    token = jwt.create_access_token(data={"user_id": auth_user.id}, expires=30)
    # injected user
    user_id = alexa.id
    # Use /users/{id}
    result = client.delete(f"/users/{user_id}",
                        headers=auth_headers(token)
                        )
    # Should return HTTP 204
    assert result.status_code == status.HTTP_204_NO_CONTENT
    # user should no longer be fetchable
    token = jwt.create_access_token(data={"user_id": auth_user.id}, expires=30)
    result = client.get(f"/users/{user_id}", headers=auth_headers(token))
    # Should return NOT FOUND
    assert result.status_code == status.HTTP_404_NOT_FOUND, \
          f"GET deleted user {user_id} returned status code {result.status_code}"


@pytest.mark.asyncio
async def test_unauthenticated_delete_user(session, sally, auth_user, client: TestClient):
    """An unauthorized request cannot delete a user."""
    # injected user
    user_id = sally.id
    # Use /users/delete
    result = client.delete(f"/users/{user_id}")
    # Should be either FORBIDDEN or UNAUTHORIZED
    assert result.status_code == status.HTTP_401_UNAUTHORIZED
    # user is still in persistent storage
    user = await user_dao.get_user(session, user_id)
    assert user is not None, f"Unauthorized delete request deleted user {str(sally)}"
    assert user.id == user_id, f"Unauthorized delete request changed user id of {str(sally)}"
    # user is still GET-able
    token = jwt.create_access_token(data={"user_id": auth_user.id}, expires=30)
    result = client.get(f"/users/{user_id}", headers=auth_headers(token))
    # Should return OK
    assert result.status_code == status.HTTP_200_OK
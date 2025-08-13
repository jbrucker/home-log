"""Test the FastAPI routes for /login.

Expected status codes for failed logins:

401 Unauthorized  if unknown email-address sent as 'username' or incorrect password
422 Unprocessable if 'username' field omitted or not a syntactically valide email
422 Unprocessable if 'password' field omitted
"""
from fastapi import Response, status

from fastapi.testclient import TestClient
import pytest
from app.data_access import user_dao
from app.routers.base import path
# VS Code thinks these fixtures are unused, but they are used & necessary.
from .fixtures import client, auth_user, session
from .utils import create_user

# flake8: noqa: F811 Redefinition of import by parameter (fixtures)


@pytest.mark.asyncio
async def test_post_login(session, client: TestClient):
    """User can login using POST request for url-formencoded data."""
    # Need a user with known password
    username = "Jose Hacker"
    email = "jose@hackerone.com"
    password = "Sufficently*Strong?"
    user = await create_user(session, username, email, password)
    # Is user on server-side now?
    response: Response = client.get(path(f"/users/{user.id}"))
    assert response.status_code == status.HTTP_200_OK
    # Does user have a password?
    hashed_password = await user_dao.get_password(session, user.id)
    assert hashed_password is not None, f"User {user.email} has no password"
    # Can we login now?
    response: Response = client.post(
                        "/login",
                        data={"username": email, "password": password},
                        headers={"Content-Type": "application/x-www-form-urlencoded"}
                        )
    assert response.status_code == status.HTTP_200_OK
    # response body should contain access_token in a JSON object
    data = response.json()
    assert "access_token" in data
    # this is not important
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_post_login_invalid_credentials(session, client: TestClient):
    """Cannot login with invalid or missing password."""
    # Need a user with known password
    username = "Jose Hacker"
    email = "jose@hackerone.com"
    password = "Sufficently*Strong?"
    user = await create_user(session, username, email, password)
    # Can we login without a password?
    response: Response = client.post(
                        "/login",
                        data={"username": email},
                        headers={"Content-Type": "application/x-www-form-urlencoded"}
                        )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Try an incorrect or blank password
    bad_password = "FatChance!"
    response: Response = client.post(
                        "/login",
                        # data= specifies FORM data. Explictly setting header maybe not needed.
                        data={"username": email, "password": bad_password},
                        headers={"Content-Type": "application/x-www-form-urlencoded"}
                        )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, f'using password "{bad_password}"'
    # What happens if password is empty?
    bad_password = ""
    response: Response = client.post(
                        "/login",
                        # data= specifies FORM data. Explictly setting header maybe not needed.
                        data={"username": email, "password": bad_password},
                        headers={"Content-Type": "application/x-www-form-urlencoded"}
                        )
    
    # should be 401 UNAUTHORIZED but FastAPI return 400 BAD REQUEST for empty password
    assert response.status_code == status.HTTP_400_BAD_REQUEST, f'using password "{bad_password}"'


@pytest.mark.asyncio
async def test_json_login(session, client: TestClient):
    """User can login using POST request and JSON form request body (hack, hack)."""
    # Need a user with known password
    username = "Jose Hacker"
    email = "jose@hackerone.com"
    password = "Sufficently*Strong?"
    user = await create_user(session, username, email, password)
    # Use the REST API endpoint for login, not html form handler.
    url = path("/auth/login")
    response: Response = client.post(
                        url,
                        json={"username": email, "password": password}
                        )
    assert response.status_code == status.HTTP_200_OK
    # response body should contain access_token in a JSON object
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_invalid_login(session, client: TestClient):
    """User cannot authenticate via REST API with invalid username or password."""
    # Need a user with known password
    username = "Jose Hacker"
    email = "jose@hackerone.com"
    password = "Sufficently*Strong?"
    user = await create_user(session, username, email, password)
    # Try invalid username values
    login_url = path("/auth/login")
    for bad_username in ["unknown@nowhere.com", "jose", ""]:
        response: Response = client.post(
                        login_url,
                        json={"username": bad_username, "password": password}
                        )
        # Response depends on whether "username" is a syntactically valid email address
        if "@" in bad_username:
            assert response.status_code == status.HTTP_401_UNAUTHORIZED, f"username = '{bad_username}'"
        else:
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, f"username = {bad_username}"
    # Try invalid password
    bad_password = "FatChance!"
    response: Response = client.post(
                        login_url,
                        json={"username": email, "password": bad_password}
                        )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, f'using password "{bad_password}"'
    # Empty password - should return 401
    ad_password = ""
    response: Response = client.post(
                        login_url,
                        json={"username": email, "password": bad_password}
                        )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    # Omit password entirely
    response: Response = client.post(
                        login_url,
                        json={"username": email}
                        )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, "Omitted password"

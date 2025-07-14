"""Test the FastAPI routes for /user"""
from fastapi import Response, status

from fastapi.testclient import TestClient
import pytest, pytest_asyncio
from app import schemas
from app.data_access import user_dao
from app.utils import jwt
# VS Code thinks these fixtures are unused, but they are used & necessary.
from .fixtures import client, auth_user, session
# These are User entities for tests
from .fixtures import alexa, sally
from .utils import auth_header, create_users


@pytest.mark.asyncio
async def test_create_user(session, auth_user, client: TestClient):
    """An authorized user can create a new user entity."""
    # add authentication
    
    USER_EMAIL = "harry@hackers.com"
    USER_NAME = "Harry Hacker"
    token = jwt.create_access_token(data={"user_id": auth_user.id}, expires=30)
    result: Response = client.post("/users",
                         headers=auth_header(token),
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
                         headers=auth_header(token),
                         json={"username": "Jone", "email": USER_EMAIL}
                        )
    # 409 CONFLICT is standard response for conflicting data
    assert result.status_code == status.HTTP_409_CONFLICT


@pytest.mark.asyncio
async def test_get_user(session, alexa, auth_user, client: TestClient):
    """Router returns a user with matching id, e.g. GET /users/1."""
    # add authentication?
    # the user to get
    user_id = alexa.id
    result = client.get(f"/users/{user_id}", 
                        headers=auth_header(auth_user))   # auth not really required
    assert result.status_code == status.HTTP_200_OK
    # verify user data from response body
    user_data = result.json()
    assert user_data["id"] == alexa.id
    assert user_data["email"] == alexa.email
    assert user_data["username"] == alexa.username


@pytest.mark.asyncio
async def test_get_users_returns_all(session, auth_user, client: TestClient):
    """Router returns all users when no limit is specified."""
    await create_users(session, 20)
    result = client.get("/users/", headers=auth_header(auth_user))
    assert result.status_code == status.HTTP_200_OK
    user_data = result.json()
    assert isinstance(user_data, list)
    assert len(user_data) == 20


@pytest.mark.asyncio
async def test_get_users_with_limit(session, auth_user, client: TestClient):
    """Router returns specified number of users when limit is provided."""
    await create_users(session, 20)
    result = client.get("/users/?limit=5", headers=auth_header(auth_user))
    assert result.status_code == status.HTTP_200_OK
    users_data = result.json()
    assert isinstance(users_data, list)
    assert len(users_data) == 5


@pytest.mark.asyncio
async def test_get_users_with_limit_and_offset(session, auth_user, client: TestClient):
    """Router returns requested users when limit and offset are given."""
    await create_users(session, 50)
    my_auth_header = auth_header(auth_user)
    # get users in groups of 10. Save the ids so we can verify no repeats.
    seen_ids = []
    for offset in range(0,50,10):
        result = client.get(f"/users/?limit=10&offset={offset}", headers=my_auth_header)
        assert result.status_code == status.HTTP_200_OK
        users_data = result.json()
        assert isinstance(users_data, list)
        assert len(users_data) == 10
        returned_ids = {user["id"] for user in users_data}
        # all the returned values are distinct
        assert len(set(returned_ids)) == len(returned_ids), f"Duplicate returned User ids: {returned_ids}"
        # none of them were returned previously
        assert not any(id in seen_ids for id in returned_ids)
        seen_ids.extend(returned_ids)
    
    # If offset too large, then GET with offset returns an empty result
    offset = 1000
    result = client.get(f"/users/?limit=10&offset={offset}", headers=my_auth_header)
    assert result.status_code == status.HTTP_200_OK
    users_data = result.json()
    assert isinstance(users_data, list)
    assert len(users_data) == 0, f"Expected empty list but got {len(users_data)} results"


@pytest.mark.skip(reason="For debugging allow unauthenticated get all users")
@pytest.mark.asyncio
async def test_get_users_unauthenticated(session, client: TestClient):
    """Unauthenticated request to get all users should be forbidden."""
    await create_users(session, 5)
    result = client.get("/users/")
    assert result.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_update_user(session, alexa, sally, client: TestClient):
    """An authorized user can update his own data."""
    # the user to update
    user_id = alexa.id
    # Update the user's attributes
    update_data = {
                    "username": "Jeff Bezos",
                    "email": "bezos@amazon.com"
                }
    response = client.put(f"/users/{user_id}",
                        # add authentication
                        headers=auth_header(alexa),
                        json=update_data
                        )
    assert response.status_code == status.HTTP_200_OK
    updated = response.json()
    assert updated["id"] == user_id
    assert updated["username"] == update_data["username"]
    assert updated["email"] == update_data["email"]


@pytest.mark.asyncio
async def test_update_user_enforces_data_integrity(session, alexa, sally, client: TestClient):
    """Updates to a user cannot violate database constraints."""
    # the user to update
    user_id = alexa.id
    # Update the user's attributes. Email violates uniqueness constraint.
    update_data = {
                    "username": "Jeff Bezos",
                    "email": sally.email
                }
    response = client.put(f"/users/{user_id}",
                        # add authentication
                        headers=auth_header(alexa),
                        json=update_data
                        )
    assert response.status_code == status.HTTP_409_CONFLICT
    # TODO If a required field is missing, should raise HTTP 400


@pytest.mark.asyncio
async def test_cannot_update_another_user(session, alexa, sally, client: TestClient):
    """A user may update only his/her own data, not someone else's."""
    # the user to update
    user_id = alexa.id
    update_data = {
                    "username": "Jeff Bezos",
                    "email": "bezos@amazon.com"
                }
    response = client.put(f"/users/{user_id}",
                        # add authentication
                        headers=auth_header(sally),  # authenticate as someone else
                        json=update_data
                        )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_delete_user(session, alexa, auth_user, client: TestClient):
    """An authorized user can delete a user. For now, any authenticated user is authorized."""
    # the user to delete
    user_id = alexa.id
    result = client.delete(f"/users/{user_id}",
                        # add authentication
                        headers=auth_header(auth_user)
                        )
    # Should return HTTP 204
    assert result.status_code == status.HTTP_204_NO_CONTENT
    # user should no longer be fetchable
    token = jwt.create_access_token(data={"user_id": auth_user.id}, expires=30)
    result = client.get(f"/users/{user_id}", headers=auth_header(auth_user))
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
    # user should still be GET-able
    result = client.get(f"/users/{user_id}", headers=auth_header(auth_user))
    assert result.status_code == status.HTTP_200_OK
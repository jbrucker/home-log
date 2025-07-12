"""Test the FastAPI routes for /source"""
from datetime import datetime, timezone
from fastapi import status

from fastapi.testclient import TestClient
import pytest, pytest_asyncio
from app import schemas
from app.data_access import data_source_dao
from app.core import security
from app.utils import jwt
# VS Code thinks these fixtures are unused, but they are used & necessary.
from .fixtures import alexa, sally, client, auth_user, session
from .utils import auth_headers, create_users


def test_create_data_source_as_authenticated(session, alexa, client):
    """
    Test the creation of a new data source by an authenticated user.

    This test verifies that an authenticated user can successfully create a data source
    via the POST /source/ endpoint. It checks that the response status code is 201 (Created),
    and that the returned data contains the expected fields and values, including 'id' and 'created_at'.

    Args:
        client: Test client with authentication headers set for the authenticated user.
        alexa: Fixture providing a user entity with 'id' and 'email'.
        session: Database session fixture.

    Asserts:
        - Response status code is 201 (Created).
        - Response JSON contains the correct 'name', 'type', and 'config'.
        - Response JSON includes 'id' and 'created_at' fields.
    """
    # Assume auth_user is a fixture that returns a user dict with 'id' and 'email'
    # and client is a TestClient with authentication headers set for auth_user
    data = {
        "name": "Test Source",
        "unit": "btu",
    }
    token = jwt.create_access_token(data={"user_id": alexa.id}, expires=30)
    create_time = datetime.now(timezone.utc)
    result = client.post("/sources/", 
                           headers=auth_headers(token),
                           json=data)
    assert result.status_code == status.HTTP_201_CREATED
    new_source = schemas.DataSource(**result.json())
    assert new_source.id > 0
    assert new_source.name == data["name"]
    assert new_source.unit == data["unit"]
    assert new_source.owner_id == alexa.id
    assert isinstance(new_source.created_at, datetime)
    assert new_source.created_at.date() >= create_time.date()


def test_unauthenticated_create_data_source_not_allowed(session, client):
    """Cannot create a data source without an authenticated user."""
    data = {
        "name": "Another Test Source",
        "unit": "btu",
    }
    result = client.post("/sources/", 
                          json=data)
    assert result.status_code == status.HTTP_401_UNAUTHORIZED
 

def test_create_data_source_always_owned_by_auth_user(session, alexa, sally, client):
    """The owner of a new data source is always the user authenticated in request header."""
    data = {
        "name": "Another Test Source",
        "unit": "btu",
        "owner_id": sally.id   # this should be ignored
    }
    # authenticate as alexa
    token = jwt.create_access_token(data={"user_id": alexa.id}, expires=30)
    create_time = datetime.now(timezone.utc)
    result = client.post("/sources/", 
                         headers=auth_headers(token),
                         json=data)
    assert result.status_code == status.HTTP_201_CREATED
    new_source = schemas.DataSource(**result.json())
    assert new_source.owner_id == alexa.id
 
    
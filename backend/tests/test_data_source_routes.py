"""Test the FastAPI routes for data sources."""
from datetime import datetime, timezone
from fastapi import status
from fastapi.testclient import TestClient

import pytest
from app import models, schemas
from app.utils import jwt
# VS Code thinks these fixtures are unused, but they are used & necessary.
# MUST import session fixture to force it to be executed, even if 'session' is not injected in any tests
from .fixtures import session, alexa, sally, client
from .utils import auth_header

# flake8: noqa: F811 Parameter name shadows import


def test_create_data_source_as_authenticated(alexa: models.User, client: TestClient):
    """
    Test the creation of a new data source by an authenticated user.

    This test verifies that an authenticated user can successfully create a data source
    via the POST /source/ endpoint. It checks that the response status code is 201 (Created),
    and that the returned data contains the expected fields and values, including 'id' and 'created_at'.

    Args:
        client: FastAPI Test client.
        alexa: Fixture providing a user entity.
        session: Database session fixture.
    """
    data = {
        "name": "Test Source",
        "metrics": {"Energy": "btu"}
    }
    create_time = datetime.now(timezone.utc)
    result = client.post("/sources/",
                           headers=auth_header(alexa),
                           json=data)
    assert result.status_code == status.HTTP_201_CREATED
    new_source = schemas.DataSource(**result.json())
    assert new_source.id > 0
    assert new_source.name == data["name"]
    assert new_source.metrics == data["metrics"]
    assert new_source.metrics["Energy"] == "btu"
    assert new_source.owner_id == alexa.id
    assert isinstance(new_source.created_at, datetime)
    assert new_source.created_at.date() >= create_time.date()


def test_unauthenticated_create_data_source(client: TestClient):
    """Cannot create a data source without an authenticated user."""
    data = {
        "name": "Another Test Source",
        "metrics": {"Temperature": "deg-C"}
    }
    result = client.post("/sources/", json=data)
    assert result.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_data_source_always_owned_by_auth_user(alexa: models.User, sally, client: TestClient):
    """The owner of a new data source is always the user in the authentication request header."""
    data = {
        "name": "Another Test Source",
        "owner_id": sally.id   # sally is not the authorized user, so this id should be ignored
    }
    # authenticate as alexa
    create_time = datetime.now(timezone.utc)
    result = client.post("/sources/",
                         headers=auth_header(alexa),
                         json=data)
    assert result.status_code == status.HTTP_201_CREATED
    new_source = schemas.DataSource(**result.json())
    assert new_source.owner_id == alexa.id


def test_create_data_source_returns_location(client: TestClient, alexa: models.User):
    """Creating a new resource should return a Location header with URL of the created resource."""
    payload = {
        "name": "Test Source",
        "metrics": {"High": "degree", "Low": "degree"}
    }
    result = client.post("/sources/",
                           headers=auth_header(alexa),
                           json=payload)
    assert result.status_code == status.HTTP_201_CREATED
    # FastAPI Client returns header names in lowercase
    location = result.headers.get("location", default=None)
    assert location is not None, "Create a new DataSource should return 'location' header"
    # Get the URL.  Apparently its not necessary to strip off host part ("http://host:port")
    get_result = client.get(location, headers=auth_header(alexa))
    assert get_result.status_code == status.HTTP_200_OK
    ds_data = get_result.json()
    assert ds_data["name"] == payload["name"]


def test_update_data_source_success(alexa: models.User, client: TestClient):
    """Authenticated user can update their own data source."""
    # Create a data source owned by Alexa
    token = jwt.create_access_token(data={"user_id": alexa.id}, expires=30)
    data = {"name": "Original Name", "metrics": {"weight": "lb"}, "description": "Original description"}
    response = client.post(
        "/sources/",
        headers=auth_header(alexa),
        json=data
    )
    assert response.status_code == status.HTTP_201_CREATED
    source_id = response.json()["id"]
    assert source_id > 0

    # Update the data source
    update_data = {
        "name": "Updated Name",
        "metrics": {"weight": "kg"},
        "description": "Updated description"
    }
    update_resp = client.put(
        f"/sources/{source_id}",
        headers=auth_header(alexa),
        json=update_data
    )
    assert update_resp.status_code == status.HTTP_200_OK
    updated = update_resp.json()
    assert updated["id"] == source_id
    assert updated["name"] == update_data["name"]
    assert updated["metrics"] == update_data["metrics"]
    assert updated["description"] == update_data["description"]
    assert updated["owner_id"] == alexa.id


def test_partial_update_preserves_old_data(alexa: models.User, client: TestClient):
    """Fields not specified in an update request are not changed."""
    # Create a data source owned by Alexa
    orig_data = {"name": "Original Name", "description": "Original description"}
    response = client.post("/sources/", headers=auth_header(alexa), json=orig_data)
    assert response.status_code == status.HTTP_201_CREATED
    source_id = response.json()["id"]

    # Update only some fields
    update_data = {
                    "name": "Updated Name",
                    "metrics": {"sys": "mmHg", "dia": "mmHg"}
                  }
    response = client.put(
                    f"/sources/{source_id}",
                    headers=auth_header(alexa),
                    json=update_data
                    )
    assert response.status_code == status.HTTP_200_OK
    updated = response.json()
    updated_ds = schemas.DataSource(**response.json())
    assert updated_ds.name == update_data["name"]
    assert updated_ds.metrics == update_data["metrics"]
    assert updated_ds.metrics["dia"] == "mmHg"
    # still has original description
    assert updated_ds.description == orig_data["description"]


def test_unuathorized_update_data_source(alexa: models.User, sally, client: TestClient):
    """User cannot update a data source they do not own."""
    # Alexa creates a data source
    create_resp = client.post(
                    "/sources/",
                    headers=auth_header(alexa),
                    json={"name": "Alexa's Source"}
                    )
    source_id = create_resp.json()["id"]

    # Sally tries to update Alexa's data source
    update_data = {"name": "Sally's Update"}
    update_resp = client.put(
                    f"/sources/{source_id}",
                    headers=auth_header(sally),
                    json=update_data
                    )
    assert update_resp.status_code == status.HTTP_403_FORBIDDEN


def test_update_data_source_not_found(alexa: models.User, client: TestClient):
    """Returns 404 if attempt to update a data source that does not exist."""
    update_data = {"name": "Doesn't Matter", "metrics": {"Energy": "kWh"}}
    response = client.put(
                    "/sources/99999",
                    headers=auth_header(alexa),
                    json=update_data
                    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_data_source_success(alexa: models.User, client: TestClient):
    """Authenticated user can delete their own data source."""
    # Alexa creates a data source
    auth_header_alexa = auth_header(alexa)
    create_response = client.post(
        "/sources/",
        headers=auth_header_alexa,
        json={"name": "Source to Delete", "unit": "kWh"}
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    source_id = create_response.json()["id"]

    # Alexa deletes the data source
    delete_response = client.delete(f"/sources/{source_id}", headers=auth_header_alexa)
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    # Confirm it's gone
    response = client.get(f"/sources/{source_id}", headers=auth_header_alexa)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_data_source_unauthorized(alexa: models.User, sally, client: TestClient):
    """User cannot delete a data source they do not own."""
    # Alexa creates a data source
    create_resp = client.post(
        "/sources/",
        headers=auth_header(alexa),
        json={"name": "Alexa's Source", "unit": "kWh"}
    )
    source_id = create_resp.json()["id"]

    # Sally tries to delete Alexa's data source
    delete_resp = client.delete(f"/sources/{source_id}", headers=auth_header(sally))
    assert delete_resp.status_code == status.HTTP_403_FORBIDDEN
    # Confirm source is still there
    response = client.get(f"/sources/{source_id}", headers=auth_header(alexa))
    assert response.status_code == status.HTTP_200_OK


def test_delete_data_source_not_found(alexa: models.User, client: TestClient):
    """Returns 404 if attempt to delete a data source that does not exist."""
    delete_resp = client.delete("/sources/99999", headers=auth_header(alexa))
    assert delete_resp.status_code == status.HTTP_404_NOT_FOUND


def test_delete_data_source_unauthenticated(client: TestClient):
    """Cannot delete a data source without authentication."""
    delete_resp = client.delete("/sources/1")
    assert delete_resp.status_code == status.HTTP_401_UNAUTHORIZED

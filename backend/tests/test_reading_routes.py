"""Tests of router endpoints for readings."""

import time
from datetime import datetime, timezone
from numbers import Number
from urllib.parse import urlparse
from fastapi import status
from fastapi.testclient import TestClient
from app import models
# MUST import fixtures.session to force it to be executed, even if 'session' is not injected in any tests
from .fixtures import session
from .fixtures import alexa, client, ds1, ds2, user1, user2
from .utils import auth_header, make_reading_values

# flake8: noqa: F811 Parameter name shadows import


def reading_url(source_id: int, reading_id: int = None) -> str:
    """Construct the URL for a reading route endpoint."""
    url = f"/sources/{source_id}/readings"
    if reading_id:
        url += f"/{reading_id}"
    return url


def test_create_reading_success(client: TestClient, user1: models.User, ds1: models.DataSource):
    """Create a reading with valid data and authorized creator."""
    payload = {
        "values": make_reading_values(ds1.components()),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    response = client.post(
        reading_url(ds1.id),
        json=payload,
        headers=auth_header(user1)
    )
    assert response.status_code == status.HTTP_201_CREATED
    response_body = response.json()
    # This is a wimpy test. Is the data really persisted?
    assert response_body["data_source_id"] == ds1.id
    assert response_body["values"] == payload["values"]
    assert response_body["created_by_id"] == user1.id
    assert "timestamp" in response_body


def test_create_reading_returns_location(client: TestClient, user1: models.User, ds1: models.DataSource):
    """Creating a new reading should return a Location header with URL of the created resource."""
    payload = {
        "values": make_reading_values(ds1.components()),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    response = client.post(
        reading_url(ds1.id),
        json=payload,
        headers=auth_header(user1)
    )
    assert response.status_code == status.HTTP_201_CREATED
    # FastAPI Client returns header names in lowercase
    location = response.headers.get("location", default=None)
    assert location is not None, "POST a new reading should return 'location' header"
    # Get the URL.  Apparently its not necessary to strip off host part ("http://host:port")
    path = urlparse(location).path
    get_response = client.get(location, headers=auth_header(user1))
    assert get_response.status_code == status.HTTP_200_OK
    reading_data = get_response.json()
    # First 18 chars of timestamp are "yyyy-mm-ddTHH:MM:SS". 
    # Remainder may differ due to timezone aware/unaware database semantics.
    assert reading_data["timestamp"][:18] == payload["timestamp"][:18]


def test_create_reading_with_incomplete_timestamp(client: TestClient, 
                                    user1: models.User, ds1: models.DataSource):
    """Create a reading with a timestamp containing only a date or date+time but no timezone."""
    reading_data = {
        "values": make_reading_values(ds1.components()),
        "timestamp": "2025-01-31"
    }
    response = client.post(
        reading_url(ds1.id),
        json=reading_data,
        headers=auth_header(user1)
    )
    assert response.status_code == status.HTTP_201_CREATED
    url = response.headers.get("location")
    # Get the reading from database
    get_response = client.get(url, headers=auth_header(user1))
    response_data = get_response.json()
    assert response_data["data_source_id"] == ds1.id
    assert reading_data["timestamp"] in response_data["timestamp"],\
          f'timestamp should contain {reading_data["timestamp"]}'

    # A timestamp with date and time, but no timezone or milliseconds
    reading_data["timestamp"] = "2025-01-31T12:45:00"  # no millisec or timezone
    response = client.post(
        reading_url(ds1.id),
        json=reading_data,
        headers=auth_header(user1)
    )
    assert response.status_code == status.HTTP_201_CREATED
    url = response.headers.get("location")
    # Get the reading from database
    time.sleep(1)
    get_response = client.get(url, headers=auth_header(user1))
    assert get_response.status_code == status.HTTP_200_OK
    response_data = get_response.json()
    assert "timestamp" in response_data, "Response body missing 'timestamp'"
    assert reading_data["timestamp"] in response_data["timestamp"],\
        f'Persisted timestamp {response_data["timestamp"]} does not match {reading_data["timestamp"]}'



def test_create_reading_missing_field(client: TestClient, user1: models.User, ds1: models.DataSource):
    """Reading creation fails when missing any required field."""
    payload = {
        # "values" is missing
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    response = client.post(
        reading_url(ds1.id),
        json=payload,
        headers=auth_header(user1)
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_reading_invalid_source(client: TestClient, alexa):
    """Reading creation fails if data_source_id is not in database."""
    payload = {
        "values": make_reading_values(["value1", "value2"]),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    response = client.post(
        reading_url(99999),
        json=payload,
        headers=auth_header(alexa)
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_reading_unauthorized(client: TestClient, user1: models.User, ds1: models.DataSource):
    """Reading creation fails without authentication."""
    payload = {
        "values": make_reading_values(ds1.components()),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    response = client.post(
        reading_url(ds1.id),
        json=payload
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_reading_user_is_not_authorized(
        client: TestClient, user1: models.User, user2: models.User, ds1: models.DataSource):
    """Reading creation fails if user is not owner of the data source.
    
       ds1 is owned by user1, not user2.
    """
    payload = {
        "values": make_reading_values(ds1.components()),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    response = client.post(
        reading_url(ds1.id),
        json=payload,
        headers=auth_header(user2)
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_reading_success(client: TestClient, user1: models.User, ds1: models.DataSource):
    """The reading owner can update an existing reading."""
    # First, create a reading
    payload = {
        "values": make_reading_values(ds1.components()),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    create_response = client.post(reading_url(ds1.id), json=payload, headers=auth_header(user1))
    created_url = create_response.headers.get("location")
    reading_id = create_response.json()["id"]
    update_payload = {
        "values": {k: v + 1 for k, v in payload["values"].items()},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    update_response = client.put(
        created_url,
        json=update_payload,
        headers=auth_header(user1)
    )
    assert update_response.status_code == status.HTTP_200_OK
    response_data = update_response.json()
    # Could fail if values are re-ordered on server side
    assert response_data["values"] == update_payload["values"]
    assert response_data["id"] == reading_id
    # Timestamp may be timezone unaware
    assert response_data["timestamp"][:18] == update_payload["timestamp"][:18]


def test_update_reading_not_found(client: TestClient, user1: models.User, ds1: models.DataSource):
    """Updating a non-existent reading returns 404."""
    update_payload = {
        "values": make_reading_values(ds1.components()),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    response = client.put(reading_url(ds1.id, 99999), json=update_payload, headers=auth_header(user1))
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_reading_unauthorized(client: TestClient, user1: models.User, ds1: models.DataSource):
    """Updating a reading without authentication returns 401."""
    # First, create a reading
    payload = {
        "values": make_reading_values(ds1.components()),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    create_response = client.post(reading_url(ds1.id), json=payload, headers=auth_header(user1))
    created_url = create_response.headers.get("location")
    update_payload = {
        "values": {k: v + 1 for k, v in payload["values"].items()},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    response = client.put(
        created_url,
        json=update_payload
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_not_own_reading(client: TestClient, 
                                user1: models.User, ds1: models.DataSource, user2: models.User):
    """Cannot update a reading owned by someone else."""
    # First, create a reading
    payload = {
        "values": make_reading_values(ds1.components()),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    # ds1 and reading are both owned by user1
    create_response = client.post(reading_url(ds1.id), json=payload, headers=auth_header(user1))
    created_url = create_response.headers.get("location")
    update_payload = {
        "values": {k: v + 1 for k, v in payload["values"].items()},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    # attempt to update as user2
    response = client.put(
        created_url,
        json=update_payload,
        headers=auth_header(user2)
    )
    # User is authenticated but does not have permission to do this, so semantics should be 403?
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_reading_success(client: TestClient, user1: models.User, ds1: models.DataSource):
    """An authorized user can delete a reading that he/she created."""
    # First, create a reading
    payload = {
        "values": make_reading_values(ds1.components()),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    response = client.post(reading_url(ds1.id), json=payload, headers=auth_header(user1))
    assert response.status_code == status.HTTP_201_CREATED
    url = response.headers.get("location")
    # Now delete the reading
    delete_response = client.delete(url, headers=auth_header(user1))
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
    # Confirm it is gone
    get_response = client.get(url, headers=auth_header(user1))
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_reading_unauthorized(client: TestClient, user1: models.User, ds1: models.DataSource):
    """An unauthenticated request cannot delete a reading."""
    payload = {
        "values": make_reading_values(ds1.components()),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    response = client.post(reading_url(ds1.id), json=payload, headers=auth_header(user1))
    assert response.status_code == status.HTTP_201_CREATED
    resource_url = response.headers.get("location")
    # Delete without an auth header
    delete_response = client.delete(resource_url)
    assert delete_response.status_code == status.HTTP_401_UNAUTHORIZED


def test_delete_reading_when_not_owner(client: TestClient,
                                       user1: models.User,
                                       user2: models.User,
                                       ds1: models.DataSource):
    """A user cannot delete a reading if he is neither creator nor owner of the data source."""
    # assumes that user1 owns ds1
    assert user1.id == ds1.owner_id
    payload = {
        "values": make_reading_values(ds1.components()),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    response = client.post(reading_url(ds1.id), json=payload, headers=auth_header(user1))
    assert response.status_code == status.HTTP_201_CREATED
    resource_url = response.headers.get("location")
    # Delete as a different user
    delete_response = client.delete(resource_url, headers=auth_header(user2))
    # should be 403: user2 is authorized but does not have permission to do this
    assert delete_response.status_code == status.HTTP_403_FORBIDDEN


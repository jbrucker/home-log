"""The application should handle request paths both with and without trailing /.

   This is configured in main.py.
   It should not return 307 Temporary Redirect in this case.
"""

from datetime import datetime, timedelta, timezone
from fastapi import status
from fastapi.testclient import TestClient
import pytest
from app import main, models
# MUST import fixtures.session to force it to be executed, even if 'session' is not injected in any tests
from .fixtures import session
from .fixtures import alexa, ds1, ds2, user1, user2
from .utils import auth_header, make_reading_values

# flake8: noqa: F811 Parameter name shadows import


@pytest.fixture()
def client(): # -> Generator[fastapi.testclient.TestClient]
    """Test Client instance the does NOT FOLLOW REDIRECTS."""
    # main.app.dependency_overrides[get_session] = db.get_session
    yield TestClient(main.app, follow_redirects=False)


def reading_url(source_id: int, reading_id: int = None) -> str:
    """Construct the URL for a reading route endpoint WITHOUT trailing slash."""
    url = f"/sources/{source_id}/readings"
    if reading_id:
        url += f"/{reading_id}"
    return url


def test_create_reading_location_does_not_end_with_slash(
    client: TestClient, user1: models.User, ds1: models.DataSource):
    """The Location URL returned by POST should not include trailing /."""
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
    url: str = response.headers.get("location")
    assert url is not None, "POST did not return 'location' header"
    assert not url.endswith("/"), f"Location URL ends with slash: {url}"


def test_create_reading_location_is_unique(
    client: TestClient, user1: models.User, ds1: models.DataSource):
    """The Location URL returned by POST should be unique."""
    now = datetime.now(timezone.utc)
    payload = {
        "values": make_reading_values(ds1.components()),
        "timestamp": now.isoformat()
    }
    response = client.post(
        reading_url(ds1.id),
        json=payload,
        headers=auth_header(user1)
    )
    assert response.status_code == status.HTTP_201_CREATED
    url1: str = response.headers.get("location")
    # Another reading, almost identical data
    payload["timestamp"] = (now - timedelta(minutes=1)).isoformat()
    response = client.post(
        reading_url(ds1.id),
        json=payload,
        headers=auth_header(user1)
    )
    assert response.status_code == status.HTTP_201_CREATED
    url2: str = response.headers.get("location")
    assert url1 != url2, f"Separate POSTs returned same location {url1}"


def test_get_reading_path(client: TestClient, 
                          user1: models.User, 
                          ds1: models.DataSource):
    """Can get a reading with or without a trailing "/" in path.
    
    user1 owns the DataSource ds1 and creates the reading.
    """
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
    url: str = response.headers.get("location")
    # Make sure no trailing / unless entire path is "/"
    if len(url) > 1 and url.endswith("/"):
        url = url[:-1]
    # Get it without trailing /
    get_response = client.get(url, headers=auth_header(user1))
    assert get_response.status_code == 200, f"GET {url} failed"
    # Get it with trailing /
    url += "/"
    get_response = client.get(url, headers=auth_header(user1))
    assert get_response.status_code == 200, f"GET {url} failed"


def test_create_data_source_location_does_not_end_with_slash(user1: models.User, client: TestClient):
    """
    Test the creation of a new data source returns a Location url not ending with /."""
    data = {
        "name": "Test Source",
        "metrics": {"Energy": "Astrophage"}
    }
    create_time = datetime.now(timezone.utc)
    response = client.post("/sources/",
                           headers=auth_header(user1),
                           json=data)
    assert response.status_code == status.HTTP_201_CREATED
    url: str = response.headers.get("location")
    assert url is not None, "POST did not return 'location' header"
    assert not url.endswith("/"), f"Location URL ends with slash: {url}"


def test_get_data_source_path(client: TestClient, 
                          user1: models.User, 
                          ds1: models.DataSource):
    """Can get a source using path with or without trailing /.

    This test assumes ds1 is owned by user1.
    """
    url = f"/sources/{ds1.id}"
    response = client.get(url, headers=auth_header(user1))
    assert response.status_code == status.HTTP_200_OK, f"Failed to get {url}"
    url = f"/sources/{ds1.id}/"
    response = client.get(url, headers=auth_header(user1))
    assert response.status_code == status.HTTP_200_OK, f"Failed to get {url}"

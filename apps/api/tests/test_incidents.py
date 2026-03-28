
import pytest
from fastapi.testclient import TestClient

from src.opsmesh.main import app


@pytest.fixture
def client():
    """Synchronous test client for simple endpoint tests."""
    return TestClient(app)


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


# Note: Full async DB tests require a test database.
# For now, test the API contract with the sync client.
# These will be expanded in Week 9 (Testing & Reliability).

def test_create_incident_validation(client):
    """Test that invalid payloads are rejected."""
    # Missing required fields
    response = client.post("/api/v1/incidents", json={})
    assert response.status_code == 422

    # Title too short
    response = client.post(
        "/api/v1/incidents",
        json={"title": "", "source": "test"},
    )
    assert response.status_code == 422

    # Invalid environment
    response = client.post(
        "/api/v1/incidents",
        json={
            "title": "Test incident",
            "source": "test",
            "environment": "invalid-env",
        },
    )
    assert response.status_code == 422


def test_list_incidents_pagination_params(client):
    """Test that pagination query params are accepted."""
    # Invalid page (0 not allowed)
    response = client.get("/api/v1/incidents?page=0")
    assert response.status_code == 422

    # Page size too large
    response = client.get("/api/v1/incidents?page_size=101")
    assert response.status_code == 422


def test_invalid_uuid_returns_422(client):
    """Test that invalid UUID format is rejected."""
    response = client.get("/api/v1/incidents/not-a-uuid")
    assert response.status_code == 422


# The following tests require a test database and will be expanded in Week 9
# test_get_incident_not_found - needs actual DB connection
# test_incident_stats_endpoint - needs actual DB connection
# test_create_and_retrieve_incident - needs actual DB connection
# test_update_incident - needs actual DB connection
# test_delete_incident - needs actual DB connection

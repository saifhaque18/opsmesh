import uuid
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.opsmesh.api.deps import get_current_user
from src.opsmesh.main import app
from src.opsmesh.models.user import User, UserRole


def create_mock_user(role: UserRole = UserRole.ANALYST) -> User:
    """Create a mock user for testing."""
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.email = "test@opsmesh.dev"
    user.name = "Test User"
    user.role = role
    user.is_active = True
    return user


@pytest.fixture
def client():
    """Synchronous test client for simple endpoint tests."""
    return TestClient(app)


@pytest.fixture
def authenticated_client():
    """Test client with auth dependency overridden."""
    mock_user = create_mock_user(UserRole.ANALYST)

    async def override_get_current_user():
        return mock_user

    app.dependency_overrides[get_current_user] = override_get_current_user
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


# Note: Full async DB tests require a test database.
# For now, test the API contract with the sync client.
# These will be expanded in Week 9 (Testing & Reliability).

def test_create_incident_validation(authenticated_client):
    """Test that invalid payloads are rejected."""
    # Missing required fields
    response = authenticated_client.post("/api/v1/incidents", json={})
    assert response.status_code == 422

    # Title too short
    response = authenticated_client.post(
        "/api/v1/incidents",
        json={"title": "", "source": "test"},
    )
    assert response.status_code == 422

    # Invalid environment
    response = authenticated_client.post(
        "/api/v1/incidents",
        json={
            "title": "Test incident",
            "source": "test",
            "environment": "invalid-env",
        },
    )
    assert response.status_code == 422


def test_list_incidents_pagination_params(authenticated_client):
    """Test that pagination query params are accepted."""
    # Invalid page (0 not allowed)
    response = authenticated_client.get("/api/v1/incidents?page=0")
    assert response.status_code == 422

    # Page size too large
    response = authenticated_client.get("/api/v1/incidents?page_size=101")
    assert response.status_code == 422


def test_invalid_uuid_returns_422(authenticated_client):
    """Test that invalid UUID format is rejected."""
    response = authenticated_client.get("/api/v1/incidents/not-a-uuid")
    assert response.status_code == 422


def test_unauthenticated_returns_401(client):
    """Test that unauthenticated requests are rejected."""
    response = client.get("/api/v1/incidents")
    assert response.status_code == 401

    response = client.post(
        "/api/v1/incidents", json={"title": "Test", "source": "test"}
    )
    assert response.status_code == 401


# The following tests require a test database and will be expanded in Week 9
# test_get_incident_not_found - needs actual DB connection
# test_incident_stats_endpoint - needs actual DB connection
# test_create_and_retrieve_incident - needs actual DB connection
# test_update_incident - needs actual DB connection
# test_delete_incident - needs actual DB connection

"""
API integration tests for incident endpoints.

These test the full HTTP request/response cycle including
authentication, validation, serialization, and database operations.
"""

import uuid

import pytest

from src.opsmesh.models.incident import IncidentSeverity
from tests.conftest import make_auth_header


@pytest.mark.integration
class TestCreateIncidentAPI:
    async def test_create_incident(self, client, analyst_user):
        """Authenticated analyst can create an incident."""
        headers = make_auth_header(analyst_user)
        response = await client.post(
            "/api/v1/incidents",
            json={
                "title": "High CPU on payment-service",
                "source": "datadog",
                "severity": "high",
                "service": "payment-service",
                "environment": "prod",
            },
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "High CPU on payment-service"
        assert data["severity"] == "high"
        assert data["status"] == "open"
        assert data["id"] is not None

    async def test_rejects_unauthenticated(self, client):
        """Unauthenticated requests should be rejected."""
        response = await client.post(
            "/api/v1/incidents",
            json={"title": "Test", "source": "test"},
        )
        assert response.status_code == 401

    async def test_rejects_viewer_role(self, client, viewer_user):
        """Viewer role should not be able to create incidents."""
        headers = make_auth_header(viewer_user)
        response = await client.post(
            "/api/v1/incidents",
            json={"title": "Test", "source": "test"},
            headers=headers,
        )
        assert response.status_code == 403

    async def test_validates_required_fields(self, client, analyst_user):
        """Missing required fields should return 422."""
        headers = make_auth_header(analyst_user)
        response = await client.post(
            "/api/v1/incidents",
            json={},
            headers=headers,
        )
        assert response.status_code == 422

    async def test_validates_environment_enum(self, client, analyst_user):
        """Invalid environment value should be rejected."""
        headers = make_auth_header(analyst_user)
        response = await client.post(
            "/api/v1/incidents",
            json={
                "title": "Test",
                "source": "test",
                "environment": "invalid",
            },
            headers=headers,
        )
        assert response.status_code == 422


@pytest.mark.integration
class TestListIncidentsAPI:
    async def test_lists_incidents(self, client, analyst_user, incident_factory):
        """Authenticated user can list incidents."""
        await incident_factory(title="Incident A")
        await incident_factory(title="Incident B")

        headers = make_auth_header(analyst_user)
        response = await client.get("/api/v1/incidents", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["incidents"]) == 2

    async def test_filters_work(self, client, analyst_user, incident_factory):
        """Filtering by severity should work correctly."""
        await incident_factory(severity=IncidentSeverity.CRITICAL)
        await incident_factory(severity=IncidentSeverity.LOW)

        headers = make_auth_header(analyst_user)
        response = await client.get(
            "/api/v1/incidents?severity=critical", headers=headers
        )
        assert response.status_code == 200
        assert response.json()["total"] == 1

    async def test_pagination_params(self, client, analyst_user):
        """Pagination parameters should be accepted and reflected in response."""
        headers = make_auth_header(analyst_user)
        response = await client.get(
            "/api/v1/incidents?page=1&page_size=5", headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5


@pytest.mark.integration
class TestGetIncidentAPI:
    async def test_get_by_id(self, client, analyst_user, incident_factory):
        """Get incident by ID should return the correct incident."""
        incident = await incident_factory(title="Specific Incident")
        headers = make_auth_header(analyst_user)

        response = await client.get(
            f"/api/v1/incidents/{incident.id}", headers=headers
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Specific Incident"

    async def test_404_for_missing(self, client, analyst_user):
        """Missing incident should return 404."""
        headers = make_auth_header(analyst_user)
        response = await client.get(
            f"/api/v1/incidents/{uuid.uuid4()}", headers=headers
        )
        assert response.status_code == 404


@pytest.mark.integration
class TestUpdateIncidentAPI:
    async def test_update_status(self, client, analyst_user, incident_factory):
        """Analyst can update incident status."""
        incident = await incident_factory()
        headers = make_auth_header(analyst_user)

        response = await client.patch(
            f"/api/v1/incidents/{incident.id}",
            json={"status": "investigating"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "investigating"

    async def test_viewer_cannot_update(self, client, viewer_user, incident_factory):
        """Viewer role should not be able to update incidents."""
        incident = await incident_factory()
        headers = make_auth_header(viewer_user)

        response = await client.patch(
            f"/api/v1/incidents/{incident.id}",
            json={"status": "resolved"},
            headers=headers,
        )
        assert response.status_code == 403

    async def test_update_missing_returns_404(self, client, analyst_user):
        """Updating a non-existent incident should return 404."""
        headers = make_auth_header(analyst_user)
        response = await client.patch(
            f"/api/v1/incidents/{uuid.uuid4()}",
            json={"status": "resolved"},
            headers=headers,
        )
        assert response.status_code == 404


@pytest.mark.integration
class TestDeleteIncidentAPI:
    async def test_delete_incident(self, client, analyst_user, incident_factory):
        """Analyst can delete an incident."""
        incident = await incident_factory()
        headers = make_auth_header(analyst_user)

        response = await client.delete(
            f"/api/v1/incidents/{incident.id}", headers=headers
        )
        assert response.status_code == 204

    async def test_viewer_cannot_delete(self, client, viewer_user, incident_factory):
        """Viewer role should not be able to delete incidents."""
        incident = await incident_factory()
        headers = make_auth_header(viewer_user)

        response = await client.delete(
            f"/api/v1/incidents/{incident.id}", headers=headers
        )
        assert response.status_code == 403

    async def test_delete_missing_returns_404(self, client, analyst_user):
        """Deleting a non-existent incident should return 404."""
        headers = make_auth_header(analyst_user)
        response = await client.delete(
            f"/api/v1/incidents/{uuid.uuid4()}", headers=headers
        )
        assert response.status_code == 404


@pytest.mark.integration
class TestStatsAPI:
    async def test_returns_stats_shape(self, client, analyst_user):
        """Stats endpoint should return the expected shape."""
        headers = make_auth_header(analyst_user)
        response = await client.get("/api/v1/incidents/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        for key in [
            "total",
            "open",
            "acknowledged",
            "investigating",
            "resolved",
            "closed",
            "critical",
            "high",
            "medium",
            "low",
        ]:
            assert key in data

    async def test_stats_reflect_data(self, client, analyst_user, incident_factory):
        """Stats should accurately reflect incident counts."""
        await incident_factory(severity=IncidentSeverity.CRITICAL)
        await incident_factory(severity=IncidentSeverity.HIGH)

        headers = make_auth_header(analyst_user)
        response = await client.get("/api/v1/incidents/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["critical"] == 1
        assert data["high"] == 1

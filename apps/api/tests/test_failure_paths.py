"""
Tests for error handling, edge cases, and invalid data.

These verify that the system fails gracefully rather
than crashing or returning corrupted data.
"""

import uuid
from datetime import timedelta

import pytest

from src.opsmesh.services.auth_service import create_access_token, create_refresh_token
from tests.conftest import make_auth_header


@pytest.mark.integration
class TestInvalidInputs:
    async def test_empty_title_rejected(self, client, analyst_user):
        """Empty title should be rejected."""
        headers = make_auth_header(analyst_user)
        response = await client.post(
            "/api/v1/incidents",
            json={"title": "", "source": "test"},
            headers=headers,
        )
        assert response.status_code == 422

    async def test_title_too_long_rejected(self, client, analyst_user):
        """Title exceeding max length should be rejected."""
        headers = make_auth_header(analyst_user)
        response = await client.post(
            "/api/v1/incidents",
            json={"title": "x" * 501, "source": "test"},
            headers=headers,
        )
        assert response.status_code == 422

    async def test_invalid_severity_rejected(self, client, analyst_user):
        """Invalid severity enum value should be rejected."""
        headers = make_auth_header(analyst_user)
        response = await client.post(
            "/api/v1/incidents",
            json={"title": "Test", "source": "test", "severity": "mega-critical"},
            headers=headers,
        )
        assert response.status_code == 422

    async def test_invalid_uuid_in_path(self, client, analyst_user):
        """Invalid UUID format in path should return 422."""
        headers = make_auth_header(analyst_user)
        response = await client.get("/api/v1/incidents/not-a-uuid", headers=headers)
        assert response.status_code == 422

    async def test_negative_page_rejected(self, client, analyst_user):
        """Negative page number should be rejected."""
        headers = make_auth_header(analyst_user)
        response = await client.get("/api/v1/incidents?page=-1", headers=headers)
        assert response.status_code == 422

    async def test_zero_page_rejected(self, client, analyst_user):
        """Page 0 should be rejected (1-indexed)."""
        headers = make_auth_header(analyst_user)
        response = await client.get("/api/v1/incidents?page=0", headers=headers)
        assert response.status_code == 422

    async def test_oversized_page_rejected(self, client, analyst_user):
        """Page size exceeding max should be rejected."""
        headers = make_auth_header(analyst_user)
        response = await client.get("/api/v1/incidents?page_size=999", headers=headers)
        assert response.status_code == 422


@pytest.mark.integration
class TestNotFoundPaths:
    async def test_get_missing_incident(self, client, analyst_user):
        """Getting a non-existent incident should return 404."""
        headers = make_auth_header(analyst_user)
        response = await client.get(
            f"/api/v1/incidents/{uuid.uuid4()}", headers=headers
        )
        assert response.status_code == 404

    async def test_update_missing_incident(self, client, analyst_user):
        """Updating a non-existent incident should return 404."""
        headers = make_auth_header(analyst_user)
        response = await client.patch(
            f"/api/v1/incidents/{uuid.uuid4()}",
            json={"status": "resolved"},
            headers=headers,
        )
        assert response.status_code == 404

    async def test_delete_missing_incident(self, client, analyst_user):
        """Deleting a non-existent incident should return 404."""
        headers = make_auth_header(analyst_user)
        response = await client.delete(
            f"/api/v1/incidents/{uuid.uuid4()}", headers=headers
        )
        assert response.status_code == 404


@pytest.mark.integration
class TestAuthFailurePaths:
    async def test_expired_token_rejected(self, client, analyst_user):
        """Expired tokens should return 401."""
        expired_token = create_access_token(
            user_id=str(analyst_user.id),
            email=analyst_user.email,
            role=analyst_user.role.value,
            expires_delta=timedelta(seconds=-1),
        )
        response = await client.get(
            "/api/v1/incidents",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 401

    async def test_malformed_token_rejected(self, client):
        """Malformed JWT should return 401."""
        response = await client.get(
            "/api/v1/incidents",
            headers={"Authorization": "Bearer not-a-real-jwt"},
        )
        assert response.status_code == 401

    async def test_missing_auth_header_rejected(self, client):
        """Missing Authorization header should return 401."""
        response = await client.get("/api/v1/incidents")
        assert response.status_code == 401

    async def test_wrong_token_type_rejected(self, client, analyst_user):
        """Using a refresh token as access token should fail."""
        refresh = create_refresh_token(user_id=str(analyst_user.id))
        response = await client.get(
            "/api/v1/incidents",
            headers={"Authorization": f"Bearer {refresh}"},
        )
        assert response.status_code == 401

    async def test_invalid_bearer_format_rejected(self, client):
        """Invalid Bearer format should return 401."""
        response = await client.get(
            "/api/v1/incidents",
            headers={"Authorization": "NotBearer sometoken"},
        )
        assert response.status_code == 401


@pytest.mark.integration
class TestEdgeCases:
    async def test_empty_database_returns_zero(self, client, analyst_user):
        """Stats should work on an empty database."""
        headers = make_auth_header(analyst_user)
        response = await client.get("/api/v1/incidents/stats", headers=headers)
        assert response.status_code == 200
        assert response.json()["total"] == 0

    async def test_empty_list_returns_empty_array(self, client, analyst_user):
        """Empty incident list should return empty array."""
        headers = make_auth_header(analyst_user)
        response = await client.get("/api/v1/incidents", headers=headers)
        assert response.status_code == 200
        assert response.json()["incidents"] == []
        assert response.json()["total"] == 0

    async def test_unicode_in_title(self, client, analyst_user):
        """Unicode characters should be handled correctly."""
        headers = make_auth_header(analyst_user)
        response = await client.post(
            "/api/v1/incidents",
            json={
                "title": "Erreur critique sur le systeme test",
                "source": "test",
            },
            headers=headers,
        )
        assert response.status_code == 201
        assert "Erreur" in response.json()["title"]

    async def test_concurrent_status_updates(
        self, client, analyst_user, incident_factory
    ):
        """Multiple rapid status updates should all succeed."""
        incident = await incident_factory()
        headers = make_auth_header(analyst_user)

        statuses = ["acknowledged", "investigating", "resolved"]
        for status in statuses:
            response = await client.patch(
                f"/api/v1/incidents/{incident.id}",
                json={"status": status},
                headers=headers,
            )
            assert response.status_code == 200
            assert response.json()["status"] == status

    async def test_large_description(self, client, analyst_user):
        """Large description should be accepted."""
        headers = make_auth_header(analyst_user)
        large_desc = "x" * 5000
        response = await client.post(
            "/api/v1/incidents",
            json={
                "title": "Test incident",
                "source": "test",
                "description": large_desc,
            },
            headers=headers,
        )
        assert response.status_code == 201

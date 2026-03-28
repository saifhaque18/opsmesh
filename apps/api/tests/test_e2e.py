"""
End-to-end test: full incident lifecycle.

This test walks through the complete journey of an incident
from creation through processing to resolution, verifying
that all systems work together correctly.
"""

import pytest

from tests.conftest import make_auth_header


@pytest.mark.e2e
@pytest.mark.integration
class TestIncidentLifecycle:
    async def test_full_lifecycle(self, client, analyst_user, admin_user):
        """
        Complete incident lifecycle:
        1. Create incident
        2. Verify it appears in the list
        3. View incident details
        4. Update status through the lifecycle
        5. Add a note
        6. Check timeline has all events
        7. View stats
        8. Resolve
        """
        analyst_headers = make_auth_header(analyst_user)

        # ─── Step 1: Create ──────────────────────────
        create_response = await client.post(
            "/api/v1/incidents",
            json={
                "title": "Database connection pool exhausted on order-processor",
                "description": "All connections in use, new requests queuing",
                "source": "prometheus",
                "severity": "critical",
                "service": "order-processor",
                "environment": "prod",
                "region": "us-east-1",
            },
            headers=analyst_headers,
        )
        assert create_response.status_code == 201
        incident = create_response.json()
        incident_id = incident["id"]
        assert incident["status"] == "open"
        assert incident["severity"] == "critical"

        # ─── Step 2: Verify in list ──────────────────
        list_response = await client.get("/api/v1/incidents", headers=analyst_headers)
        assert list_response.status_code == 200
        assert list_response.json()["total"] >= 1
        incident_ids = [i["id"] for i in list_response.json()["incidents"]]
        assert incident_id in incident_ids

        # ─── Step 3: Get details ─────────────────────
        detail_response = await client.get(
            f"/api/v1/incidents/{incident_id}",
            headers=analyst_headers,
        )
        assert detail_response.status_code == 200
        assert detail_response.json()["title"] == incident["title"]

        # ─── Step 4: Acknowledge ─────────────────────
        ack_response = await client.patch(
            f"/api/v1/incidents/{incident_id}",
            json={"status": "acknowledged"},
            headers=analyst_headers,
        )
        assert ack_response.status_code == 200
        assert ack_response.json()["status"] == "acknowledged"
        assert ack_response.json()["acknowledged_at"] is not None

        # ─── Step 5: Investigate ─────────────────────
        inv_response = await client.patch(
            f"/api/v1/incidents/{incident_id}",
            json={"status": "investigating"},
            headers=analyst_headers,
        )
        assert inv_response.status_code == 200
        assert inv_response.json()["status"] == "investigating"

        # ─── Step 6: Assign ──────────────────────────
        assign_response = await client.patch(
            f"/api/v1/incidents/{incident_id}",
            json={"assigned_to": "alice@opsmesh.dev"},
            headers=analyst_headers,
        )
        assert assign_response.status_code == 200
        assert assign_response.json()["assigned_to"] == "alice@opsmesh.dev"

        # ─── Step 7: Add note ────────────────────────
        note_response = await client.post(
            f"/api/v1/incidents/{incident_id}/notes",
            json={
                "content": "Restarted connection pool, monitoring for recurrence",
                "author": analyst_user.email,
            },
            headers=analyst_headers,
        )
        assert note_response.status_code == 201
        assert note_response.json()["author"] == analyst_user.email
        assert "Restarted connection pool" in note_response.json()["content"]

        # ─── Step 8: Resolve ─────────────────────────
        resolve_response = await client.patch(
            f"/api/v1/incidents/{incident_id}",
            json={"status": "resolved"},
            headers=analyst_headers,
        )
        assert resolve_response.status_code == 200
        assert resolve_response.json()["status"] == "resolved"
        assert resolve_response.json()["resolved_at"] is not None

        # ─── Step 9: Check stats ─────────────────────
        stats_response = await client.get(
            "/api/v1/incidents/stats", headers=analyst_headers
        )
        assert stats_response.status_code == 200
        assert stats_response.json()["resolved"] >= 1

        # ─── Step 10: Verify timeline ────────────────
        timeline_response = await client.get(
            f"/api/v1/incidents/{incident_id}/timeline",
            headers=analyst_headers,
        )
        assert timeline_response.status_code == 200
        events = timeline_response.json()["events"]

        # The timeline should contain events for:
        # created, status_changed (x3), note_added
        event_types = [e["event_type"] for e in events]
        assert "created" in event_types
        assert "note_added" in event_types

        # Timeline is ordered by occurred_at DESC, so created is last
        assert events[-1]["event_type"] == "created"


@pytest.mark.e2e
@pytest.mark.integration
class TestAuthLifecycle:
    async def test_register_login_refresh(self, client):
        """
        Complete auth lifecycle:
        1. Register a new user
        2. Login with credentials
        3. Refresh the token
        4. Access a protected resource
        """
        # ─── Step 1: Register ────────────────────────
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "lifecycle@test.com",
                "name": "Lifecycle User",
                "password": "secure-pass-123",
            },
        )
        assert register_response.status_code == 201
        register_data = register_response.json()
        assert register_data["access_token"] is not None

        # ─── Step 2: Login ───────────────────────────
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "lifecycle@test.com",
                "password": "secure-pass-123",
            },
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        access_token = login_data["access_token"]
        refresh_token = login_data["refresh_token"]

        # ─── Step 3: Refresh ─────────────────────────
        refresh_response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_response.status_code == 200
        new_access_token = refresh_response.json()["access_token"]
        assert new_access_token != access_token  # Should be different

        # ─── Step 4: Access protected resource ───────
        me_response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {new_access_token}"},
        )
        assert me_response.status_code == 200
        assert me_response.json()["email"] == "lifecycle@test.com"

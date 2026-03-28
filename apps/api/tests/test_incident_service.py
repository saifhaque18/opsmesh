"""
Integration tests for the incident service layer.

These tests run against a real test database to verify
that all CRUD operations, filtering, and business logic
work correctly with actual SQL queries.
"""

import uuid

import pytest

from src.opsmesh.models.incident import IncidentSeverity, IncidentStatus
from src.opsmesh.schemas.incident import IncidentUpdate
from src.opsmesh.services.incident_service import IncidentService


@pytest.mark.integration
class TestIncidentServiceCreate:
    async def test_creates_incident(self, db, incident_factory):
        """Verify basic incident creation stores all fields."""
        incident = await incident_factory(
            title="CPU spike on api-gateway",
            source="datadog",
            severity=IncidentSeverity.HIGH,
            service="api-gateway",
            environment="prod",
        )
        assert incident.id is not None
        assert incident.title == "CPU spike on api-gateway"
        assert incident.severity == IncidentSeverity.HIGH
        assert incident.processing_status == "pending"

    async def test_defaults_status_to_open(self, db, incident_factory):
        """New incidents should default to OPEN status."""
        incident = await incident_factory()
        assert incident.status == IncidentStatus.OPEN

    async def test_sets_detected_at(self, db, incident_factory):
        """Incidents should have a detection timestamp."""
        incident = await incident_factory()
        assert incident.detected_at is not None


@pytest.mark.integration
class TestIncidentServiceList:
    async def test_lists_all_incidents(self, db, incident_factory):
        """List should return all created incidents."""
        await incident_factory(title="Incident 1")
        await incident_factory(title="Incident 2")
        await incident_factory(title="Incident 3")

        svc = IncidentService(db)
        incidents, total = await svc.list_incidents()
        assert total == 3
        assert len(incidents) == 3

    async def test_filters_by_severity(self, db, incident_factory):
        """Filtering by severity should return only matching incidents."""
        await incident_factory(severity=IncidentSeverity.CRITICAL)
        await incident_factory(severity=IncidentSeverity.LOW)
        await incident_factory(severity=IncidentSeverity.CRITICAL)

        svc = IncidentService(db)
        incidents, total = await svc.list_incidents(severity=IncidentSeverity.CRITICAL)
        assert total == 2

    async def test_filters_by_status(self, db, incident_factory):
        """Filtering by status should return only matching incidents."""
        await incident_factory(status=IncidentStatus.OPEN)
        await incident_factory(status=IncidentStatus.RESOLVED)

        svc = IncidentService(db)
        incidents, total = await svc.list_incidents(status=IncidentStatus.RESOLVED)
        assert total == 1

    async def test_search_by_title(self, db, incident_factory):
        """Search should match partial title text."""
        await incident_factory(title="High CPU on payment-service")
        await incident_factory(title="Disk full on auth-service")

        svc = IncidentService(db)
        incidents, total = await svc.list_incidents(search="CPU")
        assert total == 1
        assert "CPU" in incidents[0].title

    async def test_pagination(self, db, incident_factory):
        """Pagination should return the correct page slice."""
        for i in range(5):
            await incident_factory(title=f"Incident {i}")

        svc = IncidentService(db)
        page1, total = await svc.list_incidents(page=1, page_size=2)
        assert total == 5
        assert len(page1) == 2

        page2, _ = await svc.list_incidents(page=2, page_size=2)
        assert len(page2) == 2

        page3, _ = await svc.list_incidents(page=3, page_size=2)
        assert len(page3) == 1

    async def test_filters_by_service(self, db, incident_factory):
        """Filtering by service should return only matching incidents."""
        await incident_factory(service="payment-service")
        await incident_factory(service="auth-service")

        svc = IncidentService(db)
        incidents, total = await svc.list_incidents(service="payment-service")
        assert total == 1

    async def test_filters_by_environment(self, db, incident_factory):
        """Filtering by environment should return only matching incidents."""
        await incident_factory(environment="prod")
        await incident_factory(environment="dev")

        svc = IncidentService(db)
        incidents, total = await svc.list_incidents(environment="prod")
        assert total == 1


@pytest.mark.integration
class TestIncidentServiceUpdate:
    async def test_updates_status(self, db, incident_factory):
        """Updating status should persist the change."""
        incident = await incident_factory()
        svc = IncidentService(db)

        updated = await svc.update(
            incident.id, IncidentUpdate(status=IncidentStatus.INVESTIGATING)
        )
        assert updated.status == IncidentStatus.INVESTIGATING

    async def test_sets_acknowledged_at_on_acknowledge(self, db, incident_factory):
        """Acknowledging should auto-set the acknowledged_at timestamp."""
        incident = await incident_factory()
        assert incident.acknowledged_at is None

        svc = IncidentService(db)
        updated = await svc.update(
            incident.id, IncidentUpdate(status=IncidentStatus.ACKNOWLEDGED)
        )
        assert updated.acknowledged_at is not None

    async def test_sets_resolved_at_on_resolve(self, db, incident_factory):
        """Resolving should auto-set the resolved_at timestamp."""
        incident = await incident_factory()
        svc = IncidentService(db)

        updated = await svc.update(
            incident.id, IncidentUpdate(status=IncidentStatus.RESOLVED)
        )
        assert updated.resolved_at is not None

    async def test_returns_none_for_missing_incident(self, db):
        """Updating a non-existent incident should return None."""
        svc = IncidentService(db)
        result = await svc.update(
            uuid.uuid4(), IncidentUpdate(status=IncidentStatus.CLOSED)
        )
        assert result is None


@pytest.mark.integration
class TestIncidentServiceDelete:
    async def test_deletes_incident(self, db, incident_factory):
        """Delete should remove the incident from the database."""
        incident = await incident_factory()
        svc = IncidentService(db)

        assert await svc.delete(incident.id) is True

        # Verify it's gone
        assert await svc.get_by_id(incident.id) is None

    async def test_returns_false_for_missing(self, db):
        """Deleting a non-existent incident should return False."""
        svc = IncidentService(db)
        assert await svc.delete(uuid.uuid4()) is False


@pytest.mark.integration
class TestIncidentServiceStats:
    async def test_counts_by_status(self, db, incident_factory):
        """Stats should aggregate counts by status correctly."""
        await incident_factory(status=IncidentStatus.OPEN)
        await incident_factory(status=IncidentStatus.OPEN)
        await incident_factory(status=IncidentStatus.RESOLVED)

        svc = IncidentService(db)
        stats = await svc.get_stats()
        assert stats["total"] == 3
        assert stats["open"] == 2
        assert stats["resolved"] == 1

    async def test_counts_by_severity(self, db, incident_factory):
        """Stats should aggregate counts by severity correctly."""
        await incident_factory(severity=IncidentSeverity.CRITICAL)
        await incident_factory(severity=IncidentSeverity.LOW)

        svc = IncidentService(db)
        stats = await svc.get_stats()
        assert stats["critical"] == 1
        assert stats["low"] == 1

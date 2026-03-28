"""
Tests for timeline events functionality.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from src.opsmesh.models.event import EventType, TimelineEvent
from src.opsmesh.services.event_service import emit_event


class TestEventType:
    """Tests for EventType enum."""

    def test_all_event_types_defined(self):
        """Verify all 20 event types are defined."""
        expected_types = [
            "CREATED",
            "STATUS_CHANGED",
            "SEVERITY_CHANGED",
            "ASSIGNED",
            "UNASSIGNED",
            "PROCESSING_STARTED",
            "PROCESSING_COMPLETED",
            "PROCESSING_FAILED",
            "DUPLICATE_DETECTED",
            "CLUSTER_JOINED",
            "CLUSTER_CREATED",
            "AI_ANALYSIS_COMPLETED",
            "AI_REVIEW_SUBMITTED",
            "SEVERITY_SCORED",
            "SEVERITY_OVERRIDDEN",
            "NOTE_ADDED",
            "ESCALATED",
            "ACKNOWLEDGED",
            "RESOLVED",
            "REOPENED",
        ]
        actual_types = [et.name for et in EventType]
        assert set(actual_types) == set(expected_types)
        assert len(actual_types) == 20

    def test_event_type_values(self):
        """Event types should have lowercase string values."""
        assert EventType.CREATED.value == "created"
        assert EventType.STATUS_CHANGED.value == "status_changed"
        assert EventType.PROCESSING_STARTED.value == "processing_started"
        assert EventType.AI_ANALYSIS_COMPLETED.value == "ai_analysis_completed"

    def test_event_type_is_string(self):
        """EventType should be a StrEnum (can be used as string)."""
        assert EventType.CREATED == "created"
        assert str(EventType.CREATED) == "created"


class TestTimelineEvent:
    """Tests for TimelineEvent model."""

    def test_timeline_event_fields(self):
        """TimelineEvent should have all required fields."""
        event = TimelineEvent(
            id=uuid.uuid4(),
            incident_id=uuid.uuid4(),
            event_type=EventType.CREATED,
            summary="Test incident created",
            detail="Additional details",
            actor="test@example.com",
            event_metadata={"key": "value"},
            occurred_at=datetime.now(timezone.utc),
        )

        assert event.id is not None
        assert event.incident_id is not None
        assert event.event_type == EventType.CREATED
        assert event.summary == "Test incident created"
        assert event.detail == "Additional details"
        assert event.actor == "test@example.com"
        assert event.event_metadata == {"key": "value"}
        assert event.occurred_at is not None

    def test_timeline_event_optional_fields(self):
        """Optional fields should default to None."""
        event = TimelineEvent(
            id=uuid.uuid4(),
            incident_id=uuid.uuid4(),
            event_type=EventType.PROCESSING_STARTED,
            summary="Processing started",
            occurred_at=datetime.now(timezone.utc),
        )

        assert event.detail is None
        assert event.actor is None
        assert event.event_metadata is None


class TestEmitEvent:
    """Tests for emit_event function."""

    def test_emit_event_creates_timeline_event(self):
        """emit_event should create and return a TimelineEvent."""
        mock_db = MagicMock()
        incident_id = uuid.uuid4()

        event = emit_event(
            db=mock_db,
            incident_id=incident_id,
            event_type=EventType.CREATED,
            summary="Test incident created",
        )

        assert event.incident_id == incident_id
        assert event.event_type == EventType.CREATED
        assert event.summary == "Test incident created"
        assert event.actor == "system"  # Default actor
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

    def test_emit_event_with_all_fields(self):
        """emit_event should accept all optional fields."""
        mock_db = MagicMock()
        incident_id = uuid.uuid4()

        event = emit_event(
            db=mock_db,
            incident_id=incident_id,
            event_type=EventType.NOTE_ADDED,
            summary="Note added",
            detail="This is the note content",
            actor="user@example.com",
            metadata={"length": 25},
        )

        assert event.summary == "Note added"
        assert event.detail == "This is the note content"
        assert event.actor == "user@example.com"
        assert event.event_metadata == {"length": 25}

    def test_emit_event_accepts_string_incident_id(self):
        """emit_event should accept incident_id as string."""
        mock_db = MagicMock()
        incident_id = str(uuid.uuid4())

        event = emit_event(
            db=mock_db,
            incident_id=incident_id,
            event_type=EventType.STATUS_CHANGED,
            summary="Status changed",
        )

        assert event.incident_id == uuid.UUID(incident_id)

    def test_emit_event_sets_occurred_at(self):
        """emit_event should set occurred_at timestamp."""
        mock_db = MagicMock()
        before = datetime.now(timezone.utc)

        event = emit_event(
            db=mock_db,
            incident_id=uuid.uuid4(),
            event_type=EventType.PROCESSING_COMPLETED,
            summary="Processing completed",
        )

        after = datetime.now(timezone.utc)
        assert before <= event.occurred_at <= after


class TestEventTypeCategories:
    """Tests for event type categorization."""

    def test_lifecycle_events(self):
        """Lifecycle events should be defined."""
        lifecycle = [
            EventType.CREATED,
            EventType.STATUS_CHANGED,
            EventType.SEVERITY_CHANGED,
            EventType.ASSIGNED,
            EventType.UNASSIGNED,
        ]
        for et in lifecycle:
            assert et in EventType

    def test_pipeline_events(self):
        """Pipeline events should be defined."""
        pipeline = [
            EventType.PROCESSING_STARTED,
            EventType.PROCESSING_COMPLETED,
            EventType.PROCESSING_FAILED,
        ]
        for et in pipeline:
            assert et in EventType

    def test_dedup_events(self):
        """Deduplication events should be defined."""
        dedup = [
            EventType.DUPLICATE_DETECTED,
            EventType.CLUSTER_JOINED,
            EventType.CLUSTER_CREATED,
        ]
        for et in dedup:
            assert et in EventType

    def test_ai_events(self):
        """AI-related events should be defined."""
        ai = [
            EventType.AI_ANALYSIS_COMPLETED,
            EventType.AI_REVIEW_SUBMITTED,
        ]
        for et in ai:
            assert et in EventType

    def test_scoring_events(self):
        """Scoring events should be defined."""
        scoring = [
            EventType.SEVERITY_SCORED,
            EventType.SEVERITY_OVERRIDDEN,
        ]
        for et in scoring:
            assert et in EventType

    def test_manual_events(self):
        """Manual/user-triggered events should be defined."""
        manual = [
            EventType.NOTE_ADDED,
            EventType.ESCALATED,
            EventType.ACKNOWLEDGED,
            EventType.RESOLVED,
            EventType.REOPENED,
        ]
        for et in manual:
            assert et in EventType


class TestEventMetadata:
    """Tests for event metadata structure."""

    def test_status_change_metadata(self):
        """Status change events should have old/new status in metadata."""
        metadata = {
            "old_status": "open",
            "new_status": "acknowledged",
        }
        event = TimelineEvent(
            id=uuid.uuid4(),
            incident_id=uuid.uuid4(),
            event_type=EventType.STATUS_CHANGED,
            summary="Status changed",
            event_metadata=metadata,
            occurred_at=datetime.now(timezone.utc),
        )
        assert event.event_metadata["old_status"] == "open"
        assert event.event_metadata["new_status"] == "acknowledged"

    def test_duplicate_metadata(self):
        """Duplicate events should have match info in metadata."""
        metadata = {
            "duplicate_of": str(uuid.uuid4()),
            "fingerprint": "abc123",
            "match_type": "exact",
        }
        event = TimelineEvent(
            id=uuid.uuid4(),
            incident_id=uuid.uuid4(),
            event_type=EventType.DUPLICATE_DETECTED,
            summary="Duplicate detected",
            event_metadata=metadata,
            occurred_at=datetime.now(timezone.utc),
        )
        assert "duplicate_of" in event.event_metadata
        assert event.event_metadata["match_type"] == "exact"

    def test_ai_analysis_metadata(self):
        """AI analysis events should have model info in metadata."""
        metadata = {
            "model": "gpt-4",
            "confidence": 0.85,
            "actions_count": 3,
            "latency_ms": 1234,
        }
        event = TimelineEvent(
            id=uuid.uuid4(),
            incident_id=uuid.uuid4(),
            event_type=EventType.AI_ANALYSIS_COMPLETED,
            summary="AI analysis completed",
            event_metadata=metadata,
            occurred_at=datetime.now(timezone.utc),
        )
        assert event.event_metadata["model"] == "gpt-4"
        assert event.event_metadata["confidence"] == 0.85

    def test_severity_override_metadata(self):
        """Severity override events should have score info in metadata."""
        metadata = {
            "previous_score": 0.5,
            "new_score": 0.9,
            "severity_label": "critical",
            "reason": "Customer impact assessment",
        }
        event = TimelineEvent(
            id=uuid.uuid4(),
            incident_id=uuid.uuid4(),
            event_type=EventType.SEVERITY_OVERRIDDEN,
            summary="Severity overridden",
            event_metadata=metadata,
            occurred_at=datetime.now(timezone.utc),
        )
        assert event.event_metadata["previous_score"] == 0.5
        assert event.event_metadata["new_score"] == 0.9
        assert "reason" in event.event_metadata

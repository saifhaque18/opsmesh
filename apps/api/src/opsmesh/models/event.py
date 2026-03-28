"""
Timeline event model for incident audit trail.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.opsmesh.models.base import Base


class EventType(enum.StrEnum):
    """All possible timeline event types."""

    # Lifecycle
    CREATED = "created"
    STATUS_CHANGED = "status_changed"
    SEVERITY_CHANGED = "severity_changed"
    ASSIGNED = "assigned"
    UNASSIGNED = "unassigned"

    # Pipeline
    PROCESSING_STARTED = "processing_started"
    PROCESSING_COMPLETED = "processing_completed"
    PROCESSING_FAILED = "processing_failed"

    # Dedup / clustering
    DUPLICATE_DETECTED = "duplicate_detected"
    CLUSTER_JOINED = "cluster_joined"
    CLUSTER_CREATED = "cluster_created"

    # AI
    AI_ANALYSIS_COMPLETED = "ai_analysis_completed"
    AI_REVIEW_SUBMITTED = "ai_review_submitted"

    # Scoring
    SEVERITY_SCORED = "severity_scored"
    SEVERITY_OVERRIDDEN = "severity_overridden"

    # Manual
    NOTE_ADDED = "note_added"
    ESCALATED = "escalated"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    REOPENED = "reopened"


class TimelineEvent(Base):
    """
    A single event in an incident's lifecycle.

    Timeline events are append-only — they are never
    updated or deleted. This guarantees a complete
    audit trail.
    """

    __tablename__ = "timeline_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Event classification
    event_type: Mapped[EventType] = mapped_column(
        Enum(EventType, name="event_type"),
        nullable=False,
        index=True,
    )

    # Human-readable summary
    summary: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="One-line description of what happened",
    )
    detail: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Extended detail or note content",
    )

    # Who triggered this event
    actor: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        doc="system | worker | user email",
    )

    # Structured change data
    event_metadata: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        doc="Structured data: old/new values, scores, etc.",
    )

    # Timestamp
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.opsmesh.models.base import Base, TimestampMixin, UUIDMixin


class IncidentStatus(StrEnum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentSeverity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Incident(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "incidents"

    # Core fields
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)

    # Classification
    status: Mapped[IncidentStatus] = mapped_column(
        Enum(IncidentStatus, name="incident_status"),
        default=IncidentStatus.OPEN,
        nullable=False,
    )
    severity: Mapped[IncidentSeverity] = mapped_column(
        Enum(IncidentSeverity, name="incident_severity"),
        default=IncidentSeverity.MEDIUM,
        nullable=False,
    )
    severity_score: Mapped[float | None] = mapped_column(
        Float, nullable=True, doc="Computed severity score 0.0-1.0"
    )

    # Categorization
    service: Mapped[str | None] = mapped_column(String(200), nullable=True)
    environment: Mapped[str | None] = mapped_column(
        String(50), nullable=True, doc="prod, staging, dev"
    )
    region: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Deduplication
    fingerprint: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True, doc="Hash for dedup clustering"
    )

    # Cluster relationship
    cluster_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("incident_clusters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    cluster: Mapped["IncidentCluster | None"] = relationship(
        "IncidentCluster", back_populates="incidents", lazy="selectin"
    )

    # Dedup metadata
    is_duplicate: Mapped[bool] = mapped_column(default=False, nullable=False)
    duplicate_of: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        doc="ID of the primary incident this is a duplicate of",
    )
    similarity_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        doc="Similarity to the cluster's primary incident (0.0-1.0)",
    )

    # Assignment
    assigned_to: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Timestamps
    detected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # AI fields (populated by worker in later weeks)
    ai_root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_suggested_actions: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_reviewed: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Processing state
    processing_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default="pending",
        doc="pending, processing, completed, failed",
    )

    __table_args__ = (
        Index("ix_incidents_status_severity", "status", "severity"),
        Index("ix_incidents_source", "source"),
        Index("ix_incidents_detected_at", "detected_at"),
    )

    def __repr__(self) -> str:
        return f"<Incident {self.id} [{self.severity.value}] {self.title[:50]}>"


# Import at end to avoid circular imports
from src.opsmesh.models.cluster import IncidentCluster  # noqa: E402, F401

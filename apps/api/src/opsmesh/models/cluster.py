"""
IncidentCluster model.

Clusters group related incidents together for deduplication
and pattern recognition.
"""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.opsmesh.models.base import Base, TimestampMixin, UUIDMixin


class ClusterStatus(StrEnum):
    ACTIVE = "active"
    MERGED = "merged"
    RESOLVED = "resolved"


class IncidentCluster(Base, UUIDMixin, TimestampMixin):
    """
    A cluster groups related incidents together.

    Clusters are formed when:
    - Multiple incidents share the same fingerprint (exact duplicates)
    - Incidents have high similarity scores (fuzzy matches)
    - Incidents affect the same service with the same error pattern
    """

    __tablename__ = "incident_clusters"

    # Cluster metadata
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Auto-generated or manually set cluster title",
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # The canonical fingerprint that defines this cluster
    fingerprint: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        doc="Primary fingerprint for this cluster",
    )

    # Classification
    status: Mapped[str] = mapped_column(
        String(20),
        default=ClusterStatus.ACTIVE,
        nullable=False,
    )

    # Aggregated metrics
    incident_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        doc="Number of incidents in this cluster",
    )
    max_severity_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        doc="Highest severity score among cluster incidents",
    )
    confidence: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        nullable=False,
        doc="Clustering confidence 0.0-1.0. 1.0 = exact fingerprint match",
    )

    # Representative data (from the first or highest-severity incident)
    primary_service: Mapped[str | None] = mapped_column(String(200), nullable=True)
    primary_source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    primary_environment: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Timing
    first_seen: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_seen: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    incidents: Mapped[list["Incident"]] = relationship(
        "Incident", back_populates="cluster", lazy="selectin"
    )

    def __repr__(self) -> str:
        title_short = self.title[:40] if self.title else ""
        return f"<Cluster {self.id} [{self.incident_count}] {title_short}>"


# Import at end to avoid circular imports
from src.opsmesh.models.incident import Incident  # noqa: E402, F401

"""
Score history model for tracking severity score changes.

Records are created when:
- Initial scoring by the worker pipeline
- Re-scoring after rule changes
- Manual override by an analyst
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.opsmesh.models.base import Base


class ScoreHistory(Base):
    """
    Tracks how an incident's severity score changes over time.
    """

    __tablename__ = "score_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Score data
    score: Mapped[float] = mapped_column(Float, nullable=False)
    previous_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    severity_label: Mapped[str] = mapped_column(String(20), nullable=False)

    # How this score was generated
    source: Mapped[str] = mapped_column(
        String(50), nullable=False, doc="engine | manual | rescore"
    )
    scored_by: Mapped[str | None] = mapped_column(
        String(200), nullable=True, doc="User email for manual overrides"
    )

    # Explanation
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    rule_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Override metadata
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamp
    scored_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

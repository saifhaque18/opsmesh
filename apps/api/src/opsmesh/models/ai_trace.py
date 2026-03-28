"""
AI trace model for auditing AI interactions.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.opsmesh.models.base import Base


class AITrace(Base):
    """
    Audit log for AI interactions.

    Records every prompt sent and response received,
    enabling debugging, cost tracking, and quality review.
    """

    __tablename__ = "ai_traces"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Request
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    user_prompt: Mapped[str] = mapped_column(Text, nullable=False)

    # Response
    response_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Quality
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    human_rating: Mapped[str | None] = mapped_column(
        String(20), nullable=True, doc="accepted | rejected | edited"
    )
    human_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Performance
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    tokens_input: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_output: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_total: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

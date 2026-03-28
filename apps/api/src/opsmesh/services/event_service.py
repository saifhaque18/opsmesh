"""
Event recording service.

Provides a single function to emit timeline events
from anywhere in the codebase. Works with both
sync (worker) and async (API) database sessions.
"""

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from src.opsmesh.models.event import EventType, TimelineEvent

logger = logging.getLogger("opsmesh.events")


def emit_event(
    db: Session,
    incident_id: str | uuid.UUID,
    event_type: EventType,
    summary: str,
    detail: str | None = None,
    actor: str | None = None,
    metadata: dict | None = None,
) -> TimelineEvent:
    """
    Record a timeline event.

    This is the single entry point for all event creation.
    Call it from API routes, worker jobs, or services.
    """
    event = TimelineEvent(
        incident_id=uuid.UUID(str(incident_id)),
        event_type=event_type,
        summary=summary,
        detail=detail,
        actor=actor or "system",
        event_metadata=metadata,
        occurred_at=datetime.now(UTC),
    )
    db.add(event)
    db.flush()

    logger.info(
        "Event: [%s] %s — incident=%s actor=%s",
        event_type.value,
        summary,
        incident_id,
        actor or "system",
    )

    return event


async def emit_event_async(
    db,  # AsyncSession
    incident_id: str | uuid.UUID,
    event_type: EventType,
    summary: str,
    detail: str | None = None,
    actor: str | None = None,
    metadata: dict | None = None,
) -> TimelineEvent:
    """Async version for use in FastAPI route handlers."""
    event = TimelineEvent(
        incident_id=uuid.UUID(str(incident_id)),
        event_type=event_type,
        summary=summary,
        detail=detail,
        actor=actor or "system",
        event_metadata=metadata,
        occurred_at=datetime.now(UTC),
    )
    db.add(event)
    await db.flush()

    logger.info(
        "Event: [%s] %s — incident=%s actor=%s",
        event_type.value,
        summary,
        incident_id,
        actor or "system",
    )

    return event

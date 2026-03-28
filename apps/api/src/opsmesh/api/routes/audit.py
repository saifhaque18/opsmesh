"""
Audit log routes.

Provides global access to timeline events across all incidents.
Useful for compliance, debugging, and system-wide event analysis.
"""

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.opsmesh.api.deps import CurrentUser
from src.opsmesh.core.database import get_db
from src.opsmesh.models.event import EventType, TimelineEvent

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])

DB = Annotated[AsyncSession, Depends(get_db)]


class AuditLogResponse:
    """Paginated audit log response."""

    def __init__(
        self,
        events: list[dict],
        total: int,
        page: int,
        page_size: int,
        total_pages: int,
    ):
        self.events = events
        self.total = total
        self.page = page
        self.page_size = page_size
        self.total_pages = total_pages


@router.get("")
async def get_audit_log(
    db: DB,
    user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    event_type: str | None = None,
    actor: str | None = None,
    incident_id: uuid.UUID | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
):
    """
    Get the global audit log with filtering.

    Query parameters:
    - event_type: Filter by event type (e.g., "created", "status_changed")
    - actor: Filter by actor (e.g., "worker", user email)
    - incident_id: Filter by specific incident
    - from_date: Filter events after this date
    - to_date: Filter events before this date
    """
    query = select(TimelineEvent)

    # Apply filters
    if event_type:
        try:
            et = EventType(event_type)
            query = query.where(TimelineEvent.event_type == et)
        except ValueError:
            pass  # Invalid event type, ignore filter

    if actor:
        query = query.where(TimelineEvent.actor == actor)

    if incident_id:
        query = query.where(TimelineEvent.incident_id == incident_id)

    if from_date:
        query = query.where(TimelineEvent.occurred_at >= from_date)

    if to_date:
        query = query.where(TimelineEvent.occurred_at <= to_date)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Apply pagination and ordering
    query = (
        query.order_by(TimelineEvent.occurred_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(query)
    events = list(result.scalars().all())

    total_pages = (total + page_size - 1) // page_size

    return {
        "events": [
            {
                "id": str(e.id),
                "incident_id": str(e.incident_id),
                "event_type": e.event_type.value,
                "summary": e.summary,
                "detail": e.detail,
                "actor": e.actor,
                "event_metadata": e.event_metadata,
                "occurred_at": e.occurred_at.isoformat(),
            }
            for e in events
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get("/event-types")
async def get_event_types(user: CurrentUser):
    """Get all available event types."""
    return {
        "event_types": [
            {"value": et.value, "name": et.name}
            for et in EventType
        ]
    }


@router.get("/stats")
async def get_audit_stats(
    db: DB,
    user: CurrentUser,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
):
    """Get event statistics grouped by type."""
    query = select(
        TimelineEvent.event_type,
        func.count(TimelineEvent.id).label("count"),
    ).group_by(TimelineEvent.event_type)

    if from_date:
        query = query.where(TimelineEvent.occurred_at >= from_date)
    if to_date:
        query = query.where(TimelineEvent.occurred_at <= to_date)

    result = await db.execute(query)
    rows = result.all()

    return {
        "stats": [
            {"event_type": row[0].value, "count": row[1]}
            for row in rows
        ],
        "total": sum(row[1] for row in rows),
    }

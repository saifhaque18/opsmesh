import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.opsmesh.core.database import get_db
from src.opsmesh.models.ai_trace import AITrace
from src.opsmesh.models.event import EventType
from src.opsmesh.models.incident import IncidentSeverity, IncidentStatus
from src.opsmesh.models.score_history import ScoreHistory
from src.opsmesh.schemas.incident import (
    AIAnalysisResponse,
    AIReviewRequest,
    IncidentCreate,
    IncidentListResponse,
    IncidentResponse,
    IncidentStats,
    IncidentUpdate,
    NoteCreate,
    NoteResponse,
    ScoreHistoryEntry,
    ScoreHistoryListResponse,
    ScoringExplanationResponse,
    SeverityOverrideRequest,
    TimelineEventResponse,
    TimelineResponse,
)
from src.opsmesh.services.event_service import emit_event_async
from src.opsmesh.services.incident_service import IncidentService
from src.opsmesh.services.queue_service import (
    get_job_status,
    get_queue_stats,
    requeue_incident,
)

router = APIRouter(prefix="/api/v1/incidents", tags=["incidents"])

DB = Annotated[AsyncSession, Depends(get_db)]


@router.post("", response_model=IncidentResponse, status_code=201)
async def create_incident(data: IncidentCreate, db: DB):
    """Ingest a new incident."""
    service = IncidentService(db)
    incident = await service.create(data)
    return incident


@router.get("", response_model=IncidentListResponse)
async def list_incidents(
    db: DB,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: IncidentStatus | None = None,
    severity: IncidentSeverity | None = None,
    source: str | None = None,
    service: str | None = None,
    environment: str | None = None,
    search: str | None = None,
):
    """List incidents with filtering and pagination."""
    svc = IncidentService(db)
    incidents, total = await svc.list_incidents(
        page=page,
        page_size=page_size,
        status=status,
        severity=severity,
        source=source,
        service=service,
        environment=environment,
        search=search,
    )
    total_pages = (total + page_size - 1) // page_size
    return IncidentListResponse(
        incidents=incidents,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/stats", response_model=IncidentStats)
async def get_incident_stats(db: DB):
    """Get dashboard summary statistics."""
    svc = IncidentService(db)
    stats = await svc.get_stats()
    return stats


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: uuid.UUID, db: DB):
    """Get a single incident by ID."""
    svc = IncidentService(db)
    incident = await svc.get_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.patch("/{incident_id}", response_model=IncidentResponse)
async def update_incident(incident_id: uuid.UUID, data: IncidentUpdate, db: DB):
    """Update an incident."""
    svc = IncidentService(db)
    incident = await svc.update(incident_id, data)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.delete("/{incident_id}", status_code=204)
async def delete_incident(incident_id: uuid.UUID, db: DB):
    """Delete an incident."""
    svc = IncidentService(db)
    deleted = await svc.delete(incident_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Incident not found")


@router.get("/pipeline/stats")
async def get_pipeline_stats():
    """Get pipeline queue statistics."""
    return get_queue_stats()


@router.get("/{incident_id}/job")
async def get_incident_job_status(incident_id: uuid.UUID):
    """Get the processing job status for an incident."""
    status = get_job_status(str(incident_id))
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status


@router.post("/{incident_id}/reprocess")
async def reprocess_incident(incident_id: uuid.UUID, db: DB):
    """Re-enqueue an incident for reprocessing."""
    svc = IncidentService(db)
    incident = await svc.get_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Reset processing status
    incident.processing_status = "pending"
    await db.flush()

    severity = incident.severity or IncidentSeverity.MEDIUM
    job = requeue_incident(str(incident_id), severity)
    if not job:
        raise HTTPException(status_code=500, detail="Failed to enqueue job")

    return {
        "message": "Incident requeued for processing",
        "job_id": job.id,
        "queue": job.origin,
    }


@router.post("/{incident_id}/override-severity", response_model=IncidentResponse)
async def override_severity(
    incident_id: uuid.UUID,
    data: SeverityOverrideRequest,
    db: DB,
    user_email: str = "analyst@example.com",  # TODO: Replace with auth user
):
    """Manually override an incident's severity score."""
    from sqlalchemy import select

    from src.opsmesh.models.incident import Incident
    from src.opsmesh.services.scoring.engine import ScoringEngine

    # Get the incident
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    previous_score = incident.severity_score

    # Determine severity label from score
    severity_label = ScoringEngine.score_to_label(data.score)

    # Update the incident
    incident.severity_score = data.score
    await db.flush()

    # Record in history (sync operation, run in executor)
    import asyncio

    from src.opsmesh.core.sync_database import get_sync_db
    from src.opsmesh.services.scoring.history import record_score

    def _record():
        sync_db = get_sync_db()
        try:
            record_score(
                db=sync_db,
                incident_id=str(incident_id),
                score=data.score,
                severity_label=severity_label,
                source="manual",
                previous_score=previous_score,
                scored_by=user_email,
                override_reason=data.reason,
            )
            sync_db.commit()
        finally:
            sync_db.close()

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _record)

    # Emit severity override event
    await emit_event_async(
        db=db,
        incident_id=incident_id,
        event_type=EventType.SEVERITY_OVERRIDDEN,
        summary=f"Severity overridden: {previous_score:.2f} → {data.score:.2f}",
        actor=user_email,
        metadata={
            "previous_score": previous_score,
            "new_score": data.score,
            "severity_label": severity_label,
            "reason": data.reason,
        },
    )

    await db.commit()
    await db.refresh(incident)
    return incident


@router.get("/{incident_id}/score-history", response_model=ScoreHistoryListResponse)
async def get_score_history(incident_id: uuid.UUID, db: DB):
    """Get the score history for an incident."""
    from sqlalchemy import select

    from src.opsmesh.models.incident import Incident

    # Verify incident exists
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Get history entries
    result = await db.execute(
        select(ScoreHistory)
        .where(ScoreHistory.incident_id == incident_id)
        .order_by(ScoreHistory.scored_at.desc())
    )
    entries = result.scalars().all()

    return ScoreHistoryListResponse(
        incident_id=incident_id,
        entries=[ScoreHistoryEntry.model_validate(e) for e in entries],
        total=len(entries),
    )


@router.get("/{incident_id}/scoring", response_model=ScoringExplanationResponse)
async def get_scoring_explanation(incident_id: uuid.UUID, db: DB):
    """Get the current scoring breakdown for an incident."""
    from sqlalchemy import select

    from src.opsmesh.models.incident import Incident
    from src.opsmesh.services.scoring.engine import ScoringEngine

    # Get the incident
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Build incident dict for scoring
    incident_data = {
        "id": str(incident.id),
        "title": incident.title,
        "description": incident.description,
        "source": incident.source,
        "severity": incident.severity.value if incident.severity else "medium",
        "service": incident.service,
        "environment": incident.environment,
        "region": incident.region,
    }

    # Score and get breakdown
    engine = ScoringEngine.default()
    result = engine.score(incident_data)

    return ScoringExplanationResponse(
        final_score=result.final_score,
        severity_label=result.severity_label,
        explanation=result.explanation,
        rules=[
            {
                "rule": r.rule,
                "score": r.score,
                "weight": r.weight,
                "explanation": r.explanation,
            }
            for r in result.rules
        ],
    )


@router.get("/{incident_id}/ai-analysis", response_model=AIAnalysisResponse)
async def get_ai_analysis(incident_id: uuid.UUID, db: DB):
    """Get AI analysis results for an incident."""
    import json

    from sqlalchemy import select

    from src.opsmesh.models.incident import Incident

    # Get the incident
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    root_cause = None
    if incident.ai_root_cause:
        try:
            root_cause = json.loads(incident.ai_root_cause)
        except json.JSONDecodeError:
            root_cause = {"summary": incident.ai_root_cause}

    actions = None
    if incident.ai_suggested_actions:
        try:
            actions = json.loads(incident.ai_suggested_actions)
        except json.JSONDecodeError:
            actions = []

    # Get latest trace
    from sqlalchemy import select as sql_select

    trace_result = await db.execute(
        sql_select(AITrace)
        .where(AITrace.incident_id == incident_id)
        .order_by(AITrace.created_at.desc())
        .limit(1)
    )
    trace = trace_result.scalar_one_or_none()

    trace_data = None
    if trace:
        trace_data = {
            "model": trace.model,
            "confidence": trace.confidence,
            "latency_ms": trace.latency_ms,
            "tokens_total": trace.tokens_total,
            "human_rating": trace.human_rating,
            "created_at": trace.created_at.isoformat(),
        }

    return AIAnalysisResponse(
        root_cause=root_cause,
        suggested_actions=actions,
        ai_reviewed=incident.ai_reviewed,
        trace=trace_data,
    )


@router.post("/{incident_id}/ai-review")
async def review_ai_analysis(
    incident_id: uuid.UUID, review: AIReviewRequest, db: DB
):
    """Submit a human review of AI suggestions."""
    import json

    from sqlalchemy import select

    from src.opsmesh.models.incident import Incident

    # Get the incident
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Mark as reviewed
    incident.ai_reviewed = True

    # Apply edits if provided
    if review.rating == "edited":
        if review.edited_root_cause:
            try:
                existing = json.loads(incident.ai_root_cause or "{}")
            except json.JSONDecodeError:
                existing = {}
            existing["summary"] = review.edited_root_cause
            existing["human_edited"] = True
            incident.ai_root_cause = json.dumps(existing)

        if review.edited_actions:
            incident.ai_suggested_actions = json.dumps(review.edited_actions)

    # Update the latest trace with review
    from src.opsmesh.core.sync_database import get_sync_db

    sync_db = get_sync_db()
    try:
        trace = (
            sync_db.query(AITrace)
            .filter(AITrace.incident_id == incident_id)
            .order_by(AITrace.created_at.desc())
            .first()
        )
        if trace:
            trace.human_rating = review.rating
            trace.human_feedback = review.feedback
            sync_db.commit()
    finally:
        sync_db.close()

    # Emit AI review submitted event
    await emit_event_async(
        db=db,
        incident_id=incident_id,
        event_type=EventType.AI_REVIEW_SUBMITTED,
        summary=f"AI analysis {review.rating} by {review.reviewed_by}",
        actor=review.reviewed_by,
        metadata={
            "rating": review.rating,
            "feedback": review.feedback,
            "was_edited": review.rating == "edited",
        },
    )

    await db.commit()

    return {
        "status": "reviewed",
        "rating": review.rating,
        "reviewed_by": review.reviewed_by,
    }


# ─── Notes endpoints ──────────────────────────────


@router.post("/{incident_id}/notes", response_model=NoteResponse, status_code=201)
async def add_note(incident_id: uuid.UUID, note: NoteCreate, db: DB):
    """Add a note to an incident."""
    from sqlalchemy import select

    from src.opsmesh.models.incident import Incident

    # Verify incident exists
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Create the note as a timeline event
    event = await emit_event_async(
        db=db,
        incident_id=incident_id,
        event_type=EventType.NOTE_ADDED,
        summary=f"Note added by {note.author}",
        detail=note.content,
        actor=note.author,
    )

    await db.commit()

    return NoteResponse(
        id=event.id,
        content=note.content,
        author=note.author,
        created_at=event.occurred_at,
    )


# ─── Timeline endpoints ───────────────────────────


@router.get("/{incident_id}/timeline", response_model=TimelineResponse)
async def get_incident_timeline(
    incident_id: uuid.UUID,
    db: DB,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Get the event timeline for an incident."""
    from sqlalchemy import func, select

    from src.opsmesh.models.event import TimelineEvent
    from src.opsmesh.models.incident import Incident

    # Verify incident exists
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Get total count
    count_result = await db.execute(
        select(func.count(TimelineEvent.id)).where(
            TimelineEvent.incident_id == incident_id
        )
    )
    total = count_result.scalar() or 0

    # Get events
    events_result = await db.execute(
        select(TimelineEvent)
        .where(TimelineEvent.incident_id == incident_id)
        .order_by(TimelineEvent.occurred_at.desc())
        .offset(offset)
        .limit(limit)
    )
    events = list(events_result.scalars().all())

    return TimelineResponse(
        incident_id=incident_id,
        events=[
            TimelineEventResponse(
                id=e.id,
                event_type=e.event_type.value,
                summary=e.summary,
                detail=e.detail,
                actor=e.actor,
                event_metadata=e.event_metadata,
                occurred_at=e.occurred_at,
            )
            for e in events
        ],
        total=total,
    )

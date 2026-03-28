import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.opsmesh.core.database import get_db
from src.opsmesh.models.incident import IncidentSeverity, IncidentStatus
from src.opsmesh.schemas.incident import (
    IncidentCreate,
    IncidentListResponse,
    IncidentResponse,
    IncidentStats,
    IncidentUpdate,
)
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

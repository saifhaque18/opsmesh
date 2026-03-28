import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from src.opsmesh.models.incident import IncidentSeverity, IncidentStatus

# ─── Request schemas ───────────────────────────────


class IncidentCreate(BaseModel):
    """Schema for creating a new incident via API."""

    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    source: str = Field(..., min_length=1, max_length=100)
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    service: str | None = None
    environment: str | None = Field(None, pattern="^(prod|staging|dev|test)$")
    region: str | None = None
    detected_at: datetime | None = None
    assigned_to: str | None = None

    model_config = {"from_attributes": True}


class IncidentUpdate(BaseModel):
    """Schema for updating an existing incident."""

    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    status: IncidentStatus | None = None
    severity: IncidentSeverity | None = None
    service: str | None = None
    environment: str | None = None
    region: str | None = None
    assigned_to: str | None = None
    ai_reviewed: bool | None = None

    model_config = {"from_attributes": True}


# ─── Response schemas ──────────────────────────────


class IncidentResponse(BaseModel):
    """Full incident response."""

    id: uuid.UUID
    title: str
    description: str | None
    source: str
    status: IncidentStatus
    severity: IncidentSeverity
    severity_score: float | None
    service: str | None
    environment: str | None
    region: str | None
    fingerprint: str | None
    cluster_id: uuid.UUID | None
    assigned_to: str | None
    detected_at: datetime | None
    acknowledged_at: datetime | None
    resolved_at: datetime | None
    ai_root_cause: str | None
    ai_suggested_actions: str | None
    ai_reviewed: bool
    processing_status: str | None
    is_duplicate: bool
    duplicate_of: uuid.UUID | None
    similarity_score: float | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IncidentListResponse(BaseModel):
    """Paginated list of incidents."""

    incidents: list[IncidentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class IncidentStats(BaseModel):
    """Dashboard summary stats."""

    total: int
    open: int
    acknowledged: int
    investigating: int
    resolved: int
    closed: int
    critical: int
    high: int
    medium: int
    low: int

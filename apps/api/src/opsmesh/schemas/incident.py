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


# ─── Scoring schemas ──────────────────────────────


class SeverityOverrideRequest(BaseModel):
    """Request to manually override an incident's severity score."""

    score: float = Field(..., ge=0.0, le=1.0, description="New severity score (0-1)")
    reason: str = Field(..., min_length=5, max_length=500, description="Why override?")


class RuleResultResponse(BaseModel):
    """Individual rule scoring result."""

    rule: str
    score: float
    weight: float
    explanation: str


class ScoringExplanationResponse(BaseModel):
    """Full scoring breakdown for an incident."""

    final_score: float
    severity_label: str
    explanation: str
    rules: list[RuleResultResponse]
    scored_at: datetime | None = None


class ScoreHistoryEntry(BaseModel):
    """Single score history entry."""

    id: uuid.UUID
    score: float
    previous_score: float | None
    severity_label: str
    source: str
    scored_by: str | None
    explanation: str | None
    rule_details: dict | None
    override_reason: str | None
    scored_at: datetime

    model_config = {"from_attributes": True}


class ScoreHistoryListResponse(BaseModel):
    """List of score history entries for an incident."""

    incident_id: uuid.UUID
    entries: list[ScoreHistoryEntry]
    total: int


# ─── AI Analysis schemas ──────────────────────────


class AIAnalysisResponse(BaseModel):
    """AI analysis results for an incident."""

    root_cause: dict | None
    suggested_actions: list[dict] | None
    ai_reviewed: bool
    trace: dict | None = None


class AIReviewRequest(BaseModel):
    """Human review of AI suggestions."""

    rating: str = Field(..., pattern="^(accepted|rejected|edited)$")
    feedback: str | None = Field(None, max_length=2000)
    reviewed_by: str = Field(..., min_length=1, max_length=200)
    edited_root_cause: str | None = None
    edited_actions: list[dict] | None = None


# ─── Notes schemas ────────────────────────────────


class NoteCreate(BaseModel):
    """Request to add a note to an incident."""

    content: str = Field(..., min_length=1, max_length=5000)
    author: str = Field(..., min_length=1, max_length=200)


class NoteResponse(BaseModel):
    """Note added to an incident."""

    id: uuid.UUID
    content: str
    author: str
    created_at: datetime


# ─── Timeline schemas ─────────────────────────────


class TimelineEventResponse(BaseModel):
    """Single timeline event."""

    id: uuid.UUID
    event_type: str
    summary: str
    detail: str | None
    actor: str | None
    event_metadata: dict | None
    occurred_at: datetime

    model_config = {"from_attributes": True}


class TimelineResponse(BaseModel):
    """Timeline of events for an incident."""

    incident_id: uuid.UUID
    events: list[TimelineEventResponse]
    total: int

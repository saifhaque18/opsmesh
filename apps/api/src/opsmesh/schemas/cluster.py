"""Cluster Pydantic schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from src.opsmesh.models.cluster import ClusterStatus
from src.opsmesh.schemas.incident import IncidentResponse


class ClusterResponse(BaseModel):
    """Full cluster response."""

    id: uuid.UUID
    title: str
    description: str | None
    fingerprint: str
    status: ClusterStatus
    incident_count: int
    max_severity_score: float | None
    confidence: float
    primary_service: str | None
    primary_source: str | None
    primary_environment: str | None
    first_seen: datetime | None
    last_seen: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClusterDetailResponse(ClusterResponse):
    """Cluster with its incidents."""

    incidents: list[IncidentResponse]


class ClusterListResponse(BaseModel):
    """Paginated list of clusters."""

    clusters: list[ClusterResponse]
    total: int
    page: int
    page_size: int


class ClusterStats(BaseModel):
    """Cluster summary statistics."""

    total_clusters: int
    active_clusters: int
    total_duplicates: int
    avg_cluster_size: float
    largest_cluster_size: int

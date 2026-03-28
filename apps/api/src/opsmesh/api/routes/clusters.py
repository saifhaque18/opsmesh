"""Cluster API routes."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.opsmesh.api.deps import AnalystUser, CurrentUser
from src.opsmesh.core.database import get_db
from src.opsmesh.models.cluster import ClusterStatus, IncidentCluster
from src.opsmesh.models.incident import Incident
from src.opsmesh.schemas.cluster import (
    ClusterDetailResponse,
    ClusterListResponse,
    ClusterStats,
)

router = APIRouter(prefix="/api/v1/clusters", tags=["clusters"])

DB = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=ClusterListResponse)
async def list_clusters(
    db: DB,
    user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: ClusterStatus | None = None,
    service: str | None = None,
    min_incidents: int | None = None,
):
    """List incident clusters with optional filtering."""
    query = select(IncidentCluster)

    if status:
        query = query.where(IncidentCluster.status == status)
    if service:
        query = query.where(IncidentCluster.primary_service == service)
    if min_incidents:
        query = query.where(IncidentCluster.incident_count >= min_incidents)

    # Count
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    # Paginate, ordered by last_seen desc (most recent activity first)
    query = (
        query.order_by(IncidentCluster.last_seen.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    clusters = list(result.scalars().all())

    return ClusterListResponse(
        clusters=clusters,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/stats", response_model=ClusterStats)
async def get_cluster_stats(db: DB, user: CurrentUser):
    """Get clustering summary statistics."""
    # Total clusters
    total = (
        await db.execute(select(func.count()).select_from(IncidentCluster))
    ).scalar() or 0

    # Active clusters
    active = (
        await db.execute(
            select(func.count())
            .select_from(IncidentCluster)
            .where(IncidentCluster.status == ClusterStatus.ACTIVE)
        )
    ).scalar() or 0

    # Total duplicates
    dupes = (
        await db.execute(
            select(func.count())
            .select_from(Incident)
            .where(Incident.is_duplicate == True)  # noqa: E712
        )
    ).scalar() or 0

    # Average and max cluster size
    avg_size = (
        await db.execute(select(func.avg(IncidentCluster.incident_count)))
    ).scalar() or 0.0

    max_size = (
        await db.execute(select(func.max(IncidentCluster.incident_count)))
    ).scalar() or 0

    return ClusterStats(
        total_clusters=total,
        active_clusters=active,
        total_duplicates=dupes,
        avg_cluster_size=round(float(avg_size), 1),
        largest_cluster_size=max_size,
    )


@router.get("/{cluster_id}", response_model=ClusterDetailResponse)
async def get_cluster(cluster_id: uuid.UUID, db: DB, user: CurrentUser):
    """Get a cluster with all its incidents."""
    result = await db.execute(
        select(IncidentCluster).where(IncidentCluster.id == cluster_id)
    )
    cluster = result.scalar_one_or_none()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return cluster


@router.patch("/{cluster_id}/resolve")
async def resolve_cluster(cluster_id: uuid.UUID, db: DB, user: AnalystUser):
    """Mark a cluster as resolved."""
    result = await db.execute(
        select(IncidentCluster).where(IncidentCluster.id == cluster_id)
    )
    cluster = result.scalar_one_or_none()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")

    cluster.status = ClusterStatus.RESOLVED
    await db.flush()
    return {"status": "resolved", "cluster_id": str(cluster.id)}

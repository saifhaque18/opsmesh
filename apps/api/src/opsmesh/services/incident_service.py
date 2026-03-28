import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.opsmesh.models.event import EventType
from src.opsmesh.models.incident import Incident, IncidentSeverity, IncidentStatus
from src.opsmesh.schemas.incident import IncidentCreate, IncidentUpdate
from src.opsmesh.services.event_service import emit_event_async
from src.opsmesh.services.queue_service import enqueue_incident_processing

logger = logging.getLogger("opsmesh.incident_service")


class IncidentService:
    """Business logic for incident operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: IncidentCreate, auto_enqueue: bool = True) -> Incident:
        incident = Incident(
            **data.model_dump(exclude_unset=True),
            detected_at=data.detected_at or datetime.now(UTC),
            processing_status="pending",
        )
        self.db.add(incident)
        await self.db.flush()
        await self.db.refresh(incident)

        # Emit CREATED event
        await emit_event_async(
            db=self.db,
            incident_id=incident.id,
            event_type=EventType.CREATED,
            summary=f"Incident created from {incident.source}",
            metadata={
                "title": incident.title,
                "source": incident.source,
                "severity": incident.severity.value if incident.severity else None,
            },
        )

        # Auto-enqueue for pipeline processing
        if auto_enqueue:
            job = enqueue_incident_processing(
                str(incident.id),
                severity=incident.severity or IncidentSeverity.MEDIUM,
            )
            if job:
                logger.info("Incident %s queued for processing", incident.id)
            else:
                logger.warning("Failed to queue incident %s", incident.id)

        return incident

    async def get_by_id(self, incident_id: uuid.UUID) -> Incident | None:
        result = await self.db.execute(
            select(Incident).where(Incident.id == incident_id)
        )
        return result.scalar_one_or_none()

    async def list_incidents(
        self,
        page: int = 1,
        page_size: int = 20,
        status: IncidentStatus | None = None,
        severity: IncidentSeverity | None = None,
        source: str | None = None,
        service: str | None = None,
        environment: str | None = None,
        search: str | None = None,
    ) -> tuple[list[Incident], int]:
        query = select(Incident)

        # Apply filters
        if status:
            query = query.where(Incident.status == status)
        if severity:
            query = query.where(Incident.severity == severity)
        if source:
            query = query.where(Incident.source == source)
        if service:
            query = query.where(Incident.service == service)
        if environment:
            query = query.where(Incident.environment == environment)
        if search:
            query = query.where(
                Incident.title.ilike(f"%{search}%")
                | Incident.description.ilike(f"%{search}%")
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Apply pagination and ordering
        query = (
            query.order_by(Incident.detected_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.db.execute(query)
        incidents = list(result.scalars().all())

        return incidents, total

    async def update(
        self, incident_id: uuid.UUID, data: IncidentUpdate, actor: str | None = None
    ) -> Incident | None:
        incident = await self.get_by_id(incident_id)
        if not incident:
            return None

        update_data = data.model_dump(exclude_unset=True)
        old_status = incident.status
        old_severity = incident.severity

        # Auto-set timestamps based on status changes
        if "status" in update_data:
            new_status = update_data["status"]
            now = datetime.now(UTC)
            is_ack = new_status == IncidentStatus.ACKNOWLEDGED
            if is_ack and not incident.acknowledged_at:
                incident.acknowledged_at = now
            elif new_status in (IncidentStatus.RESOLVED, IncidentStatus.CLOSED):
                if not incident.resolved_at:
                    incident.resolved_at = now

        for field, value in update_data.items():
            setattr(incident, field, value)

        await self.db.flush()
        await self.db.refresh(incident)

        # Emit events for status and severity changes
        if "status" in update_data and update_data["status"] != old_status:
            new_status = update_data["status"]
            event_type = EventType.STATUS_CHANGED
            # Use more specific event types for certain transitions
            if new_status == IncidentStatus.ACKNOWLEDGED:
                event_type = EventType.ACKNOWLEDGED
            elif new_status == IncidentStatus.RESOLVED:
                event_type = EventType.RESOLVED

            await emit_event_async(
                db=self.db,
                incident_id=incident.id,
                event_type=event_type,
                summary=f"Status changed from {old_status.value} to {new_status.value}",
                actor=actor,
                metadata={
                    "old_status": old_status.value,
                    "new_status": new_status.value,
                },
            )

        if "severity" in update_data and update_data["severity"] != old_severity:
            await emit_event_async(
                db=self.db,
                incident_id=incident.id,
                event_type=EventType.SEVERITY_CHANGED,
                summary=f"Severity changed to {update_data['severity'].value}",
                actor=actor,
                metadata={
                    "old_severity": old_severity.value if old_severity else None,
                    "new_severity": update_data["severity"].value,
                },
            )

        return incident

    async def delete(self, incident_id: uuid.UUID) -> bool:
        incident = await self.get_by_id(incident_id)
        if not incident:
            return False
        await self.db.delete(incident)
        return True

    async def get_stats(self) -> dict:
        # Status counts
        status_query = select(Incident.status, func.count(Incident.id)).group_by(
            Incident.status
        )
        status_result = await self.db.execute(status_query)
        status_counts = {row[0].value: row[1] for row in status_result.all()}

        # Severity counts
        severity_query = select(Incident.severity, func.count(Incident.id)).group_by(
            Incident.severity
        )
        severity_result = await self.db.execute(severity_query)
        severity_counts = {row[0].value: row[1] for row in severity_result.all()}

        total = sum(status_counts.values())

        return {
            "total": total,
            "open": status_counts.get("open", 0),
            "acknowledged": status_counts.get("acknowledged", 0),
            "investigating": status_counts.get("investigating", 0),
            "resolved": status_counts.get("resolved", 0),
            "closed": status_counts.get("closed", 0),
            "critical": severity_counts.get("critical", 0),
            "high": severity_counts.get("high", 0),
            "medium": severity_counts.get("medium", 0),
            "low": severity_counts.get("low", 0),
        }

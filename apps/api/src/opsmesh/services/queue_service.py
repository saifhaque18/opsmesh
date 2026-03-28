"""
Queue service for dispatching incidents to RQ workers.

Handles:
- Priority-based queue routing
- Job enqueuing with metadata
- Queue statistics
"""

import logging
from typing import Any

from redis import Redis
from rq import Queue
from rq.job import Job

from src.opsmesh.core.config import settings
from src.opsmesh.models.incident import IncidentSeverity

logger = logging.getLogger("opsmesh.queue")

# Queue names by priority
QUEUE_CRITICAL = "opsmesh-critical"
QUEUE_HIGH = "opsmesh-high"
QUEUE_DEFAULT = "opsmesh-default"


def get_redis_connection() -> Redis:
    """Get a sync Redis connection for RQ."""
    return Redis.from_url(settings.redis_url)


def get_queue_for_severity(severity: IncidentSeverity | str) -> str:
    """
    Map incident severity to the appropriate queue.

    Critical/High → critical queue (processed first)
    Medium → high queue
    Low/Info → default queue
    """
    if isinstance(severity, str):
        severity_value = severity.lower()
    else:
        severity_value = severity.value.lower()

    if severity_value in ("critical", "high"):
        return QUEUE_CRITICAL
    elif severity_value == "medium":
        return QUEUE_HIGH
    else:
        return QUEUE_DEFAULT


def enqueue_incident_processing(
    incident_id: str,
    severity: IncidentSeverity | str = "medium",
) -> Job | None:
    """
    Enqueue an incident for processing.

    Args:
        incident_id: The incident UUID
        severity: Incident severity for queue routing

    Returns:
        The RQ Job object, or None if enqueuing failed
    """
    try:
        redis_conn = get_redis_connection()
        queue_name = get_queue_for_severity(severity)
        queue = Queue(queue_name, connection=redis_conn)

        job = queue.enqueue(
            "src.opsmesh.worker.jobs.process_incident",
            incident_id,
            job_id=f"incident-{incident_id}",
            job_timeout="5m",
            result_ttl=86400,  # Keep results for 24 hours
            failure_ttl=604800,  # Keep failed jobs for 7 days
            meta={"incident_id": incident_id, "severity": str(severity)},
        )

        logger.info(
            "Enqueued incident %s to queue %s (job_id=%s)",
            incident_id,
            queue_name,
            job.id,
        )
        return job

    except Exception as e:
        logger.error("Failed to enqueue incident %s: %s", incident_id, e)
        return None


def get_queue_stats() -> dict[str, Any]:
    """
    Get statistics for all processing queues.

    Returns:
        Dict with queue depths, failed counts, and worker info
    """
    try:
        redis_conn = get_redis_connection()

        stats = {
            "queues": {},
            "total_pending": 0,
            "total_failed": 0,
        }

        for queue_name in [QUEUE_CRITICAL, QUEUE_HIGH, QUEUE_DEFAULT]:
            queue = Queue(queue_name, connection=redis_conn)
            failed_queue = Queue(f"{queue_name}:failed", connection=redis_conn)

            pending = len(queue)
            failed = len(failed_queue)

            stats["queues"][queue_name] = {
                "pending": pending,
                "failed": failed,
            }
            stats["total_pending"] += pending
            stats["total_failed"] += failed

        return stats

    except Exception as e:
        logger.error("Failed to get queue stats: %s", e)
        return {
            "queues": {},
            "total_pending": 0,
            "total_failed": 0,
            "error": str(e),
        }


def get_job_status(incident_id: str) -> dict[str, Any] | None:
    """
    Get the processing status of a specific incident job.

    Args:
        incident_id: The incident UUID

    Returns:
        Job status dict or None if not found
    """
    try:
        redis_conn = get_redis_connection()
        job_id = f"incident-{incident_id}"

        job = Job.fetch(job_id, connection=redis_conn)

        return {
            "job_id": job.id,
            "status": job.get_status(),
            "enqueued_at": job.enqueued_at.isoformat() if job.enqueued_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "ended_at": job.ended_at.isoformat() if job.ended_at else None,
            "result": job.result,
            "exc_info": job.exc_info,
        }

    except Exception:
        return None


def requeue_incident(
    incident_id: str, severity: IncidentSeverity | str = "medium"
) -> Job | None:
    """
    Re-enqueue a failed or completed incident for reprocessing.

    Args:
        incident_id: The incident UUID
        severity: Incident severity for queue routing

    Returns:
        The new RQ Job object, or None if failed
    """
    try:
        redis_conn = get_redis_connection()
        job_id = f"incident-{incident_id}"

        # Try to delete existing job first
        try:
            existing_job = Job.fetch(job_id, connection=redis_conn)
            existing_job.delete()
        except Exception:
            pass  # Job doesn't exist, that's fine

        # Enqueue fresh
        return enqueue_incident_processing(incident_id, severity)

    except Exception as e:
        logger.error("Failed to requeue incident %s: %s", incident_id, e)
        return None

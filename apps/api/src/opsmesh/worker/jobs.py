"""
RQ job definitions.

These functions are serialized and executed by the worker process.
Each job receives an incident ID, loads it from the DB, runs the
pipeline, and writes results back.
"""

import logging
import traceback
from datetime import UTC, datetime

from src.opsmesh.core.sync_database import get_sync_db
from src.opsmesh.models.incident import Incident
from src.opsmesh.services.scoring.history import record_score
from src.opsmesh.worker.dedup_step import dedup_and_cluster
from src.opsmesh.worker.pipeline import (
    compute_fingerprint,
    enrich_metadata,
    normalize,
    score_severity,
)

logger = logging.getLogger("opsmesh.jobs")


def process_incident(incident_id: str) -> dict:
    """
    Main job: process a single incident through the full pipeline.

    Pipeline steps:
    1. Normalize — clean fields
    2. Fingerprint — compute dedup hash
    3. Enrich — classify category
    4. Score — compute severity score

    Returns a summary dict for job result tracking.
    """
    logger.info("Processing incident %s", incident_id)
    db = get_sync_db()

    try:
        # Load the incident
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            logger.error("Incident %s not found", incident_id)
            return {"status": "error", "error": "Incident not found"}

        # Update processing state
        incident.processing_status = "processing"
        db.commit()

        # Build a dict representation for pipeline processing
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

        # Run the pipeline
        incident_data = normalize(incident_data)
        incident_data = compute_fingerprint(incident_data)
        incident_data = enrich_metadata(incident_data)
        incident_data = score_severity(incident_data)

        # Write pipeline results back to the database
        incident.title = incident_data["title"]
        incident.source = incident_data["source"]
        if incident_data.get("service"):
            incident.service = incident_data["service"]
        if incident_data.get("environment"):
            incident.environment = incident_data["environment"]
        incident.fingerprint = incident_data.get("fingerprint")
        incident.severity_score = incident_data.get("severity_score")

        # Record score in history
        score_details = incident_data.get("_score_details", {})
        record_score(
            db=db,
            incident_id=str(incident.id),
            score=incident_data.get("severity_score", 0.0),
            severity_label=incident_data.get("_severity_label", "medium"),
            source="engine",
            explanation=incident_data.get("_score_explanation"),
            rule_details=score_details,
        )

        db.commit()

        # Run deduplication and clustering (uses its own DB session)
        dedup_result = dedup_and_cluster(
            incident_id=str(incident.id),
            fingerprint=incident_data.get("fingerprint", ""),
        )

        # Mark as completed
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        incident.processing_status = "completed"
        db.commit()

        result = {
            "status": "completed",
            "incident_id": str(incident.id),
            "fingerprint": incident_data.get("fingerprint"),
            "severity_score": incident_data.get("severity_score"),
            "category": incident_data.get("_category"),
            "score_explanation": incident_data.get("_score_explanation"),
            "dedup": dedup_result,
            "processed_at": datetime.now(UTC).isoformat(),
        }

        logger.info(
            "Incident %s processed: score=%.3f, fingerprint=%s",
            incident_id,
            incident_data.get("severity_score", 0),
            incident_data.get("fingerprint", "n/a"),
        )

        return result

    except Exception as e:
        logger.error(
            "Failed to process incident %s: %s\n%s",
            incident_id,
            str(e),
            traceback.format_exc(),
        )

        # Mark as failed
        try:
            incident = db.query(Incident).filter(Incident.id == incident_id).first()
            if incident:
                incident.processing_status = "failed"
                db.commit()
        except Exception:
            db.rollback()

        return {"status": "failed", "incident_id": incident_id, "error": str(e)}

    finally:
        db.close()

"""
Score history recording.

Called by the worker pipeline after scoring and
by the override endpoint after manual changes.
"""

import logging
import uuid

from sqlalchemy.orm import Session

from src.opsmesh.models.score_history import ScoreHistory

logger = logging.getLogger("opsmesh.scoring.history")


def record_score(
    db: Session,
    incident_id: str | uuid.UUID,
    score: float,
    severity_label: str,
    source: str,
    previous_score: float | None = None,
    explanation: str | None = None,
    rule_details: dict | None = None,
    scored_by: str | None = None,
    override_reason: str | None = None,
) -> ScoreHistory:
    """Record a score event in the history table."""
    entry = ScoreHistory(
        incident_id=uuid.UUID(str(incident_id)),
        score=score,
        previous_score=previous_score,
        severity_label=severity_label,
        source=source,
        scored_by=scored_by,
        explanation=explanation,
        rule_details=rule_details,
        override_reason=override_reason,
    )
    db.add(entry)
    db.flush()

    logger.info(
        "Recorded score: incident=%s score=%.3f source=%s",
        incident_id,
        score,
        source,
    )
    return entry

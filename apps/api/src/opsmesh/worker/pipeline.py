"""
Incident processing pipeline.

Each step is a pure function that takes an incident dict
and returns an enriched version. This makes steps testable
and composable.
"""

import hashlib
import logging
from datetime import UTC, datetime

from src.opsmesh.core.logging import log_step

logger = logging.getLogger("opsmesh.pipeline")


@log_step("normalize")
def normalize(incident: dict) -> dict:
    """
    Step 1: Normalize raw incident data.

    - Strip whitespace from text fields
    - Lowercase source and service names
    - Ensure detected_at is set
    - Standardize environment names
    """
    # Clean text fields
    if incident.get("title"):
        incident["title"] = incident["title"].strip()
    if incident.get("description"):
        incident["description"] = incident["description"].strip()

    # Normalize categorical fields
    if incident.get("source"):
        incident["source"] = incident["source"].lower().strip()
    if incident.get("service"):
        incident["service"] = incident["service"].lower().strip()

    # Standardize environment
    env_map = {
        "production": "prod",
        "develop": "dev",
        "development": "dev",
        "stage": "staging",
    }
    if incident.get("environment"):
        env = incident["environment"].lower().strip()
        incident["environment"] = env_map.get(env, env)

    return incident


@log_step("fingerprint")
def compute_fingerprint(incident: dict) -> dict:
    """
    Step 2: Compute a deduplication fingerprint.

    The fingerprint is a hash of normalized fields that identify
    "the same kind of incident." Two alerts about high CPU on
    payment-service from datadog should have the same fingerprint.

    Fingerprint components:
    - source
    - service
    - title (first 100 chars, lowered)
    """
    components = [
        incident.get("source", ""),
        incident.get("service", ""),
        incident.get("title", "")[:100].lower(),
    ]

    fingerprint_input = "|".join(components)
    fingerprint = hashlib.sha256(fingerprint_input.encode()).hexdigest()[:16]
    incident["fingerprint"] = fingerprint

    logger.info("Fingerprint: %s", fingerprint)
    return incident


@log_step("enrich")
def enrich_metadata(incident: dict) -> dict:
    """
    Step 3: Enrich with derived metadata.

    - Classify the incident type based on title keywords
    - Add processing timestamp
    """
    title = (incident.get("title") or "").lower()

    # Simple keyword-based classification
    if any(kw in title for kw in ["cpu", "memory", "disk", "oom", "resource"]):
        incident["_category"] = "resource"
    elif any(kw in title for kw in ["5xx", "error", "exception", "crash", "failure"]):
        incident["_category"] = "error"
    elif any(kw in title for kw in ["latency", "slow", "timeout", "delay"]):
        incident["_category"] = "performance"
    elif any(kw in title for kw in ["ssl", "cert", "auth", "login", "security"]):
        incident["_category"] = "security"
    elif any(kw in title for kw in ["deploy", "rollback", "release", "ci", "cd"]):
        incident["_category"] = "deployment"
    elif any(kw in title for kw in ["queue", "kafka", "sqs", "rabbitmq"]):
        incident["_category"] = "queue"
    else:
        incident["_category"] = "other"

    incident["_processed_at"] = datetime.now(UTC).isoformat()

    return incident


@log_step("score")
def score_severity(incident: dict) -> dict:
    """
    Step 4: Compute severity score using the rules engine.

    Replaces the inline scorer from Week 3 with the
    configurable, weighted, explainable engine.

    Six rules with weighted averaging:
    - SeverityLevelRule (w=3.0)
    - EnvironmentRule (w=2.0)
    - KeywordUrgencyRule (w=1.5)
    - ServiceCriticalityRule (w=2.0)
    - RepeatOffenderRule (w=1.0)
    - TimeOfDayRule (w=0.5)
    """
    from src.opsmesh.services.scoring.engine import ScoringEngine

    engine = ScoringEngine.default()
    result = engine.score(incident)

    incident["severity_score"] = result.final_score
    incident["_severity_label"] = result.severity_label
    incident["_score_explanation"] = result.explanation
    incident["_score_details"] = result.to_dict()

    logger.info(
        "Severity score: %.3f (%s)", result.final_score, result.severity_label
    )

    return incident

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
    Step 4: Compute a severity score (0.0 to 1.0).

    This is a rules-based scoring engine. It considers:
    - The declared severity level
    - The environment (prod > staging > dev)
    - Category risk weights
    - Keyword urgency signals

    In Week 5, this will be upgraded with ML/embedding scoring.
    """
    score = 0.0

    # Base score from declared severity
    severity_weights = {
        "critical": 0.9,
        "high": 0.7,
        "medium": 0.5,
        "low": 0.3,
        "info": 0.1,
    }
    severity = incident.get("severity", "medium")
    if isinstance(severity, str):
        score = severity_weights.get(severity, 0.5)
    else:
        score = severity_weights.get(severity.value, 0.5)

    # Environment multiplier
    env_multipliers = {
        "prod": 1.0,
        "staging": 0.7,
        "dev": 0.4,
        "test": 0.2,
    }
    env = incident.get("environment", "prod")
    score *= env_multipliers.get(env, 0.8)

    # Category adjustment
    category_boost = {
        "error": 0.1,
        "security": 0.15,
        "deployment": 0.05,
        "resource": 0.05,
        "performance": 0.0,
        "queue": 0.0,
        "other": 0.0,
    }
    category = incident.get("_category", "other")
    score += category_boost.get(category, 0.0)

    # Urgency keywords in title
    title = (incident.get("title") or "").lower()
    if any(kw in title for kw in ["crash", "down", "outage", "data loss"]):
        score += 0.15
    if any(kw in title for kw in ["intermittent", "warning", "minor"]):
        score -= 0.1

    # Clamp to [0.0, 1.0]
    score = max(0.0, min(1.0, round(score, 3)))

    incident["severity_score"] = score
    sev_key = severity if isinstance(severity, str) else severity.value
    base_score = severity_weights.get(sev_key, 0.5)
    incident["_score_explanation"] = (
        f"base={base_score}, "
        f"env={env}({env_multipliers.get(env, 0.8)}x), "
        f"category={category}(+{category_boost.get(category, 0.0)}), "
        f"final={score}"
    )

    logger.info("Severity score: %s", score)
    return incident

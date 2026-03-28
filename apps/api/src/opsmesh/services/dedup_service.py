"""
Deduplication service.

Two strategies:
1. Exact match — same fingerprint = definite duplicate
2. Fuzzy match — similar title + same service = likely duplicate

The fuzzy matcher uses token overlap (Jaccard similarity)
as a lightweight alternative to embeddings. This keeps the
project dependency-free from ML libraries in v1.
"""

import logging
import re
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.opsmesh.models.cluster import ClusterStatus, IncidentCluster
from src.opsmesh.models.incident import Incident

logger = logging.getLogger("opsmesh.dedup")

# Lookback window for dedup matching
DEDUP_WINDOW_HOURS = 72


def tokenize(text: str | None) -> set[str]:
    """
    Tokenize text into lowercase word tokens.
    Strips common ops noise words.
    """
    if not text:
        return set()
    tokens = set(re.findall(r"[a-z0-9]+", text.lower()))
    # Remove stop words that add noise to similarity
    stop_words = {
        "the",
        "a",
        "an",
        "on",
        "in",
        "is",
        "for",
        "to",
        "of",
        "and",
        "or",
        "at",
        "by",
    }
    return tokens - stop_words


def jaccard_similarity(a: set[str], b: set[str]) -> float:
    """Jaccard similarity between two token sets."""
    if not a or not b:
        return 0.0
    intersection = len(a & b)
    union = len(a | b)
    return intersection / union if union > 0 else 0.0


def find_exact_duplicate(
    db: Session,
    fingerprint: str,
    lookback_hours: int = DEDUP_WINDOW_HOURS,
) -> Incident | None:
    """
    Find an existing incident with the same fingerprint
    within the lookback window.
    """
    cutoff = datetime.now(UTC) - timedelta(hours=lookback_hours)

    result = db.execute(
        select(Incident)
        .where(
            Incident.fingerprint == fingerprint,
            Incident.detected_at >= cutoff,
            Incident.is_duplicate == False,  # noqa: E712
        )
        .order_by(Incident.detected_at.asc())
        .limit(1)
    )
    return result.scalar_one_or_none()


def find_fuzzy_matches(
    db: Session,
    title: str,
    service: str | None,
    source: str | None,
    incident_id: str,
    lookback_hours: int = DEDUP_WINDOW_HOURS,
    threshold: float = 0.6,
) -> list[tuple[Incident, float]]:
    """
    Find incidents with similar titles in the same service.

    Returns list of (incident, similarity_score) tuples
    above the threshold, sorted by similarity descending.
    """
    cutoff = datetime.now(UTC) - timedelta(hours=lookback_hours)

    query = select(Incident).where(
        Incident.detected_at >= cutoff,
        Incident.id != incident_id,
        Incident.is_duplicate == False,  # noqa: E712
    )

    # Scope to same service if available
    if service:
        query = query.where(Incident.service == service)

    result = db.execute(query)
    candidates = result.scalars().all()

    if not candidates:
        return []

    target_tokens = tokenize(title)
    if not target_tokens:
        return []

    matches = []
    for candidate in candidates:
        candidate_tokens = tokenize(candidate.title)
        sim = jaccard_similarity(target_tokens, candidate_tokens)

        # Boost similarity if same source
        if source and candidate.source == source:
            sim = min(1.0, sim + 0.1)

        if sim >= threshold:
            matches.append((candidate, round(sim, 3)))

    # Sort by similarity descending
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches[:5]  # Return top 5 matches


def find_or_create_cluster(
    db: Session,
    fingerprint: str,
    incident: Incident,
    confidence: float = 1.0,
) -> IncidentCluster:
    """
    Find an existing cluster for this fingerprint,
    or create a new one.
    """
    # Look for existing cluster
    result = db.execute(
        select(IncidentCluster).where(
            IncidentCluster.fingerprint == fingerprint,
            IncidentCluster.status == ClusterStatus.ACTIVE,
        )
    )
    cluster = result.scalar_one_or_none()

    now = datetime.now(UTC)

    if cluster:
        # Update existing cluster
        cluster.incident_count += 1
        cluster.last_seen = now

        # Update max severity
        if incident.severity_score and (
            cluster.max_severity_score is None
            or incident.severity_score > cluster.max_severity_score
        ):
            cluster.max_severity_score = incident.severity_score

        # Update confidence (average with new match)
        cluster.confidence = round(
            (cluster.confidence * (cluster.incident_count - 1) + confidence)
            / cluster.incident_count,
            3,
        )

        logger.info(
            "Added to cluster %s (now %d incidents, confidence=%.3f)",
            cluster.id,
            cluster.incident_count,
            cluster.confidence,
        )
    else:
        # Create new cluster
        cluster = IncidentCluster(
            title=incident.title,
            fingerprint=fingerprint,
            status=ClusterStatus.ACTIVE,
            incident_count=1,
            max_severity_score=incident.severity_score,
            confidence=confidence,
            primary_service=incident.service,
            primary_source=incident.source,
            primary_environment=incident.environment,
            first_seen=incident.detected_at or now,
            last_seen=now,
        )
        db.add(cluster)
        db.flush()

        logger.info(
            "Created new cluster %s for fingerprint %s", cluster.id, fingerprint
        )

    return cluster

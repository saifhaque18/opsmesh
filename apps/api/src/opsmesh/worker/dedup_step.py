"""
Deduplication and clustering pipeline step.

This runs after fingerprint computation and severity scoring.
It:

1. Checks for exact fingerprint matches
2. Falls back to fuzzy title matching
3. Creates or updates a cluster
4. Marks duplicates
"""

import logging

from src.opsmesh.core.sync_database import get_sync_db
from src.opsmesh.models.incident import Incident
from src.opsmesh.services.dedup_service import (
    find_exact_duplicate,
    find_fuzzy_matches,
    find_or_create_cluster,
)

logger = logging.getLogger("opsmesh.dedup_step")


def dedup_and_cluster(incident_id: str, fingerprint: str) -> dict:
    """
    Run deduplication and clustering for a processed incident.

    Returns a result dict with:
    - is_duplicate: bool
    - duplicate_of: str | None
    - cluster_id: str | None
    - similarity_score: float | None
    - match_type: "exact" | "fuzzy" | "new"
    """
    db = get_sync_db()

    try:
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            return {"error": "Incident not found"}

        result = {
            "is_duplicate": False,
            "duplicate_of": None,
            "cluster_id": None,
            "similarity_score": None,
            "match_type": "new",
        }

        # Strategy 1: Exact fingerprint match
        if fingerprint:
            existing = find_exact_duplicate(db, fingerprint)
            if existing and str(existing.id) != incident_id:
                logger.info(
                    "Exact duplicate: %s matches %s (fingerprint=%s)",
                    incident_id,
                    existing.id,
                    fingerprint,
                )

                incident.is_duplicate = True
                incident.duplicate_of = existing.id
                incident.similarity_score = 1.0

                result["is_duplicate"] = True
                result["duplicate_of"] = str(existing.id)
                result["similarity_score"] = 1.0
                result["match_type"] = "exact"

                # Add to existing cluster or create one
                cluster = find_or_create_cluster(
                    db, fingerprint, incident, confidence=1.0
                )
                incident.cluster_id = cluster.id
                result["cluster_id"] = str(cluster.id)

                db.commit()
                return result

        # Strategy 2: Fuzzy title matching
        fuzzy_matches = find_fuzzy_matches(
            db,
            title=incident.title,
            service=incident.service,
            source=incident.source,
            incident_id=incident_id,
        )

        if fuzzy_matches:
            best_match, best_score = fuzzy_matches[0]
            logger.info(
                "Fuzzy match: %s ~ %s (score=%.3f)",
                incident_id,
                best_match.id,
                best_score,
            )

            incident.similarity_score = best_score

            # High confidence fuzzy match = likely duplicate
            if best_score >= 0.8:
                incident.is_duplicate = True
                incident.duplicate_of = best_match.id
                result["is_duplicate"] = True
                result["duplicate_of"] = str(best_match.id)

            result["similarity_score"] = best_score
            result["match_type"] = "fuzzy"

            # Use the best match's fingerprint for clustering
            cluster_fp = best_match.fingerprint or fingerprint
            if cluster_fp:
                cluster = find_or_create_cluster(
                    db, cluster_fp, incident, confidence=best_score
                )
                incident.cluster_id = cluster.id
                result["cluster_id"] = str(cluster.id)

            db.commit()
            return result

        # Strategy 3: No match — create a new cluster for this fingerprint
        if fingerprint:
            cluster = find_or_create_cluster(db, fingerprint, incident, confidence=1.0)
            incident.cluster_id = cluster.id
            result["cluster_id"] = str(cluster.id)

        db.commit()
        return result

    except Exception as e:
        db.rollback()
        logger.error("Dedup failed for %s: %s", incident_id, e)
        raise
    finally:
        db.close()

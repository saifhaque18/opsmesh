"""
Integration tests for the processing pipeline.

These verify that the pipeline functions work correctly
with real data structures, and that the scoring engine
produces consistent results across different scenarios.
"""

import pytest

from src.opsmesh.services.scoring.engine import ScoringEngine
from src.opsmesh.worker.pipeline import (
    compute_fingerprint,
    enrich_metadata,
    normalize,
    score_severity,
)


class TestFullPipeline:
    """Run the complete pipeline on various incident types."""

    def _make_incident(self, **overrides):
        defaults = {
            "id": "pipeline-test",
            "title": "High CPU usage on payment-service",
            "description": "CPU at 95% for 15 minutes",
            "source": "DataDog",
            "severity": "high",
            "service": "Payment-Service",
            "environment": "production",
            "_cluster_incident_count": 1,
        }
        defaults.update(overrides)
        return defaults

    def test_full_pipeline_produces_all_fields(self):
        """Running all steps should produce fingerprint, category, and score."""
        incident = self._make_incident()
        incident = normalize(incident)
        incident = compute_fingerprint(incident)
        incident = enrich_metadata(incident)
        incident = score_severity(incident)

        assert incident["fingerprint"] is not None
        assert len(incident["fingerprint"]) == 16
        assert incident["_category"] in [
            "resource",
            "error",
            "performance",
            "security",
            "deployment",
            "queue",
            "other",
        ]
        assert 0.0 <= incident["severity_score"] <= 1.0
        assert incident["_score_details"] is not None

    def test_normalize_standardizes_environment(self):
        """'production' should become 'prod' after normalization."""
        incident = self._make_incident(environment="production")
        result = normalize(incident)
        assert result["environment"] == "prod"

    def test_normalize_lowercases_source(self):
        """Source should be lowercased after normalization."""
        incident = self._make_incident(source="DataDog")
        result = normalize(incident)
        assert result["source"] == "datadog"

    def test_normalize_lowercases_service(self):
        """Service should be lowercased after normalization."""
        incident = self._make_incident(service="Payment-Service")
        result = normalize(incident)
        assert result["service"] == "payment-service"

    def test_same_incidents_same_fingerprint(self):
        """Identical incidents should produce identical fingerprints."""
        a = compute_fingerprint(normalize(self._make_incident()))
        b = compute_fingerprint(normalize(self._make_incident()))
        assert a["fingerprint"] == b["fingerprint"]

    def test_different_services_different_fingerprints(self):
        """Different services should produce different fingerprints."""
        a = compute_fingerprint(normalize(self._make_incident(service="svc-a")))
        b = compute_fingerprint(normalize(self._make_incident(service="svc-b")))
        assert a["fingerprint"] != b["fingerprint"]

    def test_different_titles_different_fingerprints(self):
        """Different titles should produce different fingerprints."""
        a = compute_fingerprint(normalize(self._make_incident(title="Error A")))
        b = compute_fingerprint(normalize(self._make_incident(title="Error B")))
        assert a["fingerprint"] != b["fingerprint"]

    def test_critical_prod_scores_higher_than_low_dev(self):
        """A critical prod incident must score higher than a low dev one."""
        critical_prod = self._make_incident(
            severity="critical",
            environment="prod",
            title="Full outage on payment-service",
            service="payment-service",
        )
        for step in [normalize, compute_fingerprint, enrich_metadata, score_severity]:
            critical_prod = step(critical_prod)

        low_dev = self._make_incident(
            severity="low",
            environment="dev",
            title="Minor warning on test-service",
            service="notification-service",
        )
        for step in [normalize, compute_fingerprint, enrich_metadata, score_severity]:
            low_dev = step(low_dev)

        assert critical_prod["severity_score"] > low_dev["severity_score"]


class TestScoringConsistency:
    """Verify scoring engine produces consistent, deterministic results."""

    def test_same_input_same_output(self):
        """Scoring the same incident twice should give identical results."""
        engine = ScoringEngine.default()
        incident = {
            "severity": "high",
            "environment": "prod",
            "title": "CPU spike",
            "service": "payment-service",
            "_cluster_incident_count": 1,
        }
        score1 = engine.score(incident).final_score
        score2 = engine.score(incident).final_score
        assert score1 == score2

    def test_all_rules_contribute(self):
        """Every registered rule should produce a result."""
        engine = ScoringEngine.default()
        result = engine.score(
            {
                "severity": "medium",
                "environment": "prod",
                "title": "Test incident",
                "service": "test-service",
                "_cluster_incident_count": 1,
            }
        )
        assert len(result.rules) == 6
        assert all(r.score >= 0.0 for r in result.rules)
        assert all(r.weight > 0.0 for r in result.rules)

    def test_score_clamped_to_valid_range(self):
        """Final score should always be between 0 and 1."""
        engine = ScoringEngine.default()

        # Test with extreme values
        extreme_high = engine.score(
            {
                "severity": "critical",
                "environment": "prod",
                "title": "OUTAGE DOWN CRASH ERROR",
                "service": "payment-service",
                "_cluster_incident_count": 100,
            }
        )
        assert 0.0 <= extreme_high.final_score <= 1.0

        extreme_low = engine.score(
            {
                "severity": "info",
                "environment": "dev",
                "title": "test log message",
                "service": "debug-service",
                "_cluster_incident_count": 1,
            }
        )
        assert 0.0 <= extreme_low.final_score <= 1.0

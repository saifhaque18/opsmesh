"""
Tests for the incident processing pipeline.

Tests each pipeline step as a pure function and validates
the full pipeline integration.
"""


from src.opsmesh.worker.pipeline import (
    compute_fingerprint,
    enrich_metadata,
    normalize,
    score_severity,
)


class TestNormalize:
    """Tests for the normalize step."""

    def test_strips_whitespace_from_title(self):
        incident = {"id": "1", "title": "  High CPU Alert  "}
        result = normalize(incident)
        assert result["title"] == "High CPU Alert"

    def test_strips_whitespace_from_description(self):
        incident = {"id": "1", "description": "  Server overloaded  "}
        result = normalize(incident)
        assert result["description"] == "Server overloaded"

    def test_lowercases_source(self):
        incident = {"id": "1", "source": "DataDog"}
        result = normalize(incident)
        assert result["source"] == "datadog"

    def test_lowercases_service(self):
        incident = {"id": "1", "service": "Payment-API"}
        result = normalize(incident)
        assert result["service"] == "payment-api"

    def test_standardizes_production_to_prod(self):
        incident = {"id": "1", "environment": "production"}
        result = normalize(incident)
        assert result["environment"] == "prod"

    def test_standardizes_development_to_dev(self):
        incident = {"id": "1", "environment": "development"}
        result = normalize(incident)
        assert result["environment"] == "dev"

    def test_standardizes_stage_to_staging(self):
        incident = {"id": "1", "environment": "stage"}
        result = normalize(incident)
        assert result["environment"] == "staging"

    def test_preserves_unknown_environment(self):
        incident = {"id": "1", "environment": "qa"}
        result = normalize(incident)
        assert result["environment"] == "qa"

    def test_handles_missing_fields(self):
        incident = {"id": "1"}
        result = normalize(incident)
        assert result == {"id": "1"}


class TestComputeFingerprint:
    """Tests for the fingerprint computation."""

    def test_generates_fingerprint(self):
        incident = {
            "id": "1",
            "source": "datadog",
            "service": "api",
            "title": "High CPU on api-server",
        }
        result = compute_fingerprint(incident)
        assert "fingerprint" in result
        assert len(result["fingerprint"]) == 16

    def test_same_inputs_produce_same_fingerprint(self):
        incident1 = {"source": "datadog", "service": "api", "title": "Alert"}
        incident2 = {"source": "datadog", "service": "api", "title": "Alert"}
        result1 = compute_fingerprint(incident1)
        result2 = compute_fingerprint(incident2)
        assert result1["fingerprint"] == result2["fingerprint"]

    def test_different_source_produces_different_fingerprint(self):
        incident1 = {"source": "datadog", "service": "api", "title": "Alert"}
        incident2 = {"source": "pagerduty", "service": "api", "title": "Alert"}
        result1 = compute_fingerprint(incident1)
        result2 = compute_fingerprint(incident2)
        assert result1["fingerprint"] != result2["fingerprint"]

    def test_truncates_long_titles(self):
        long_title = "A" * 200
        incident = {"source": "test", "service": "api", "title": long_title}
        result = compute_fingerprint(incident)
        # Should not raise, fingerprint is based on first 100 chars
        assert "fingerprint" in result

    def test_handles_missing_fields(self):
        incident = {"id": "1"}
        result = compute_fingerprint(incident)
        assert "fingerprint" in result


class TestEnrichMetadata:
    """Tests for the metadata enrichment step."""

    def test_classifies_cpu_as_resource(self):
        incident = {"id": "1", "title": "High CPU on server"}
        result = enrich_metadata(incident)
        assert result["_category"] == "resource"

    def test_classifies_memory_as_resource(self):
        incident = {"id": "1", "title": "Memory exhausted"}
        result = enrich_metadata(incident)
        assert result["_category"] == "resource"

    def test_classifies_5xx_as_error(self):
        incident = {"id": "1", "title": "5xx errors spike"}
        result = enrich_metadata(incident)
        assert result["_category"] == "error"

    def test_classifies_exception_as_error(self):
        incident = {"id": "1", "title": "Unhandled exception in API"}
        result = enrich_metadata(incident)
        assert result["_category"] == "error"

    def test_classifies_latency_as_performance(self):
        incident = {"id": "1", "title": "High latency in checkout"}
        result = enrich_metadata(incident)
        assert result["_category"] == "performance"

    def test_classifies_ssl_as_security(self):
        incident = {"id": "1", "title": "SSL certificate expiring"}
        result = enrich_metadata(incident)
        assert result["_category"] == "security"

    def test_classifies_deploy_as_deployment(self):
        incident = {"id": "1", "title": "Deploy failed for v2.1"}
        result = enrich_metadata(incident)
        assert result["_category"] == "deployment"

    def test_classifies_kafka_as_queue(self):
        incident = {"id": "1", "title": "Kafka consumer lag high"}
        result = enrich_metadata(incident)
        assert result["_category"] == "queue"

    def test_classifies_unknown_as_other(self):
        incident = {"id": "1", "title": "Something happened"}
        result = enrich_metadata(incident)
        assert result["_category"] == "other"

    def test_adds_processed_at_timestamp(self):
        incident = {"id": "1", "title": "Test"}
        result = enrich_metadata(incident)
        assert "_processed_at" in result


class TestScoreSeverity:
    """Tests for the severity scoring step."""

    def test_critical_severity_has_high_score(self):
        incident = {"id": "1", "severity": "critical", "environment": "prod"}
        result = score_severity(incident)
        assert result["severity_score"] >= 0.9

    def test_low_severity_has_low_score(self):
        incident = {"id": "1", "severity": "low", "environment": "prod"}
        result = score_severity(incident)
        assert result["severity_score"] <= 0.4

    def test_prod_environment_multiplier(self):
        incident = {"id": "1", "severity": "medium", "environment": "prod"}
        result = score_severity(incident)
        prod_score = result["severity_score"]

        incident_dev = {"id": "2", "severity": "medium", "environment": "dev"}
        result_dev = score_severity(incident_dev)
        dev_score = result_dev["severity_score"]

        assert prod_score > dev_score

    def test_security_category_boosts_score(self):
        incident = {
            "id": "1",
            "severity": "medium",
            "environment": "prod",
            "_category": "security",
        }
        result = score_severity(incident)
        security_score = result["severity_score"]

        incident_other = {
            "id": "2",
            "severity": "medium",
            "environment": "prod",
            "_category": "other",
        }
        result_other = score_severity(incident_other)
        other_score = result_other["severity_score"]

        assert security_score > other_score

    def test_crash_keyword_boosts_score(self):
        incident = {
            "id": "1",
            "severity": "medium",
            "title": "Server crash detected",
            "environment": "prod",
        }
        result = score_severity(incident)
        crash_score = result["severity_score"]

        incident_normal = {
            "id": "2",
            "severity": "medium",
            "title": "Normal alert",
            "environment": "prod",
        }
        result_normal = score_severity(incident_normal)
        normal_score = result_normal["severity_score"]

        assert crash_score > normal_score

    def test_intermittent_keyword_lowers_score(self):
        incident = {
            "id": "1",
            "severity": "medium",
            "title": "Intermittent network issues",
            "environment": "prod",
        }
        result = score_severity(incident)
        intermittent_score = result["severity_score"]

        incident_normal = {
            "id": "2",
            "severity": "medium",
            "title": "Network issues",
            "environment": "prod",
        }
        result_normal = score_severity(incident_normal)
        normal_score = result_normal["severity_score"]

        assert intermittent_score < normal_score

    def test_score_clamped_to_0_1(self):
        # Very high severity with all boosts
        incident = {
            "id": "1",
            "severity": "critical",
            "environment": "prod",
            "_category": "security",
            "title": "Server crash outage data loss",
        }
        result = score_severity(incident)
        assert 0.0 <= result["severity_score"] <= 1.0

        # Very low with deductions
        incident_low = {
            "id": "2",
            "severity": "info",
            "environment": "test",
            "_category": "other",
            "title": "Minor intermittent warning",
        }
        result_low = score_severity(incident_low)
        assert 0.0 <= result_low["severity_score"] <= 1.0

    def test_adds_score_explanation(self):
        incident = {"id": "1", "severity": "medium", "environment": "prod"}
        result = score_severity(incident)
        assert "_score_explanation" in result
        assert "base=" in result["_score_explanation"]
        assert "env=" in result["_score_explanation"]


class TestFullPipeline:
    """Integration tests for the full pipeline."""

    def test_full_pipeline_execution(self):
        """Test running all pipeline steps in sequence."""
        incident = {
            "id": "test-123",
            "title": "  High CPU on Payment Service  ",
            "description": "CPU at 95%",
            "source": "DataDog",
            "service": "Payment-API",
            "environment": "production",
            "severity": "high",
        }

        # Run full pipeline
        result = normalize(incident)
        result = compute_fingerprint(result)
        result = enrich_metadata(result)
        result = score_severity(result)

        # Verify all steps completed
        assert result["title"] == "High CPU on Payment Service"
        assert result["source"] == "datadog"
        assert result["service"] == "payment-api"
        assert result["environment"] == "prod"
        assert "fingerprint" in result
        assert result["_category"] == "resource"
        assert "severity_score" in result
        assert "_processed_at" in result

    def test_pipeline_handles_minimal_incident(self):
        """Test pipeline with minimal required fields."""
        incident = {"id": "minimal-123"}

        result = normalize(incident)
        result = compute_fingerprint(result)
        result = enrich_metadata(result)
        result = score_severity(result)

        assert "fingerprint" in result
        assert "_category" in result
        assert "severity_score" in result

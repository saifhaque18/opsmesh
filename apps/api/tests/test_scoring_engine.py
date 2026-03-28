"""
Tests for the severity scoring engine.

Tests cover:
- Individual rule scoring behavior
- Weighted average calculation
- Edge cases and boundary conditions
- Score-to-label mapping
- Full pipeline integration
"""

from datetime import UTC, datetime

from src.opsmesh.services.scoring.engine import (
    EnvironmentRule,
    KeywordUrgencyRule,
    RepeatOffenderRule,
    ScoringEngine,
    ServiceCriticalityRule,
    SeverityLevelRule,
    TimeOfDayRule,
)

# ─── SeverityLevelRule Tests ──────────────────────


class TestSeverityLevelRule:
    def test_critical_severity(self):
        rule = SeverityLevelRule()
        result = rule.evaluate({"severity": "critical"})
        assert result.score == 1.0
        assert "critical" in result.explanation

    def test_high_severity(self):
        rule = SeverityLevelRule()
        result = rule.evaluate({"severity": "high"})
        assert result.score == 0.75

    def test_medium_severity(self):
        rule = SeverityLevelRule()
        result = rule.evaluate({"severity": "medium"})
        assert result.score == 0.5

    def test_low_severity(self):
        rule = SeverityLevelRule()
        result = rule.evaluate({"severity": "low"})
        assert result.score == 0.25

    def test_info_severity(self):
        rule = SeverityLevelRule()
        result = rule.evaluate({"severity": "info"})
        assert result.score == 0.1

    def test_missing_severity_defaults_to_medium(self):
        rule = SeverityLevelRule()
        result = rule.evaluate({})
        assert result.score == 0.5

    def test_unknown_severity_defaults_to_medium(self):
        rule = SeverityLevelRule()
        result = rule.evaluate({"severity": "unknown"})
        assert result.score == 0.5


# ─── EnvironmentRule Tests ────────────────────────


class TestEnvironmentRule:
    def test_prod_environment(self):
        rule = EnvironmentRule()
        result = rule.evaluate({"environment": "prod"})
        assert result.score == 1.0
        assert "prod" in result.explanation

    def test_staging_environment(self):
        rule = EnvironmentRule()
        result = rule.evaluate({"environment": "staging"})
        assert result.score == 0.6

    def test_dev_environment(self):
        rule = EnvironmentRule()
        result = rule.evaluate({"environment": "dev"})
        assert result.score == 0.3

    def test_test_environment(self):
        rule = EnvironmentRule()
        result = rule.evaluate({"environment": "test"})
        assert result.score == 0.1

    def test_missing_environment_defaults_to_prod(self):
        rule = EnvironmentRule()
        result = rule.evaluate({})
        assert result.score == 1.0

    def test_null_environment_defaults_to_prod(self):
        rule = EnvironmentRule()
        result = rule.evaluate({"environment": None})
        assert result.score == 1.0


# ─── KeywordUrgencyRule Tests ─────────────────────


class TestKeywordUrgencyRule:
    def test_outage_keyword(self):
        rule = KeywordUrgencyRule()
        result = rule.evaluate({"title": "Production outage detected"})
        assert result.score == 1.0
        assert "outage" in result.explanation

    def test_down_keyword(self):
        rule = KeywordUrgencyRule()
        result = rule.evaluate({"title": "Service is down"})
        assert result.score == 1.0

    def test_crash_keyword(self):
        rule = KeywordUrgencyRule()
        result = rule.evaluate({"title": "App crash on startup"})
        assert result.score == 0.9

    def test_5xx_keyword(self):
        rule = KeywordUrgencyRule()
        result = rule.evaluate({"title": "5xx error rate spiking"})
        assert result.score == 0.8

    def test_warning_keyword(self):
        rule = KeywordUrgencyRule()
        result = rule.evaluate({"title": "Warning: disk usage high"})
        assert result.score == 0.3

    def test_no_keywords(self):
        rule = KeywordUrgencyRule()
        result = rule.evaluate({"title": "Regular maintenance"})
        assert result.score == 0.5
        assert "neutral" in result.explanation.lower()

    def test_keyword_in_description(self):
        rule = KeywordUrgencyRule()
        result = rule.evaluate({
            "title": "Something happened",
            "description": "There was an outage"
        })
        assert result.score == 1.0

    def test_multiple_keywords_uses_highest(self):
        rule = KeywordUrgencyRule()
        result = rule.evaluate({"title": "Outage causing 5xx errors"})
        assert result.score == 1.0  # outage trumps 5xx


# ─── ServiceCriticalityRule Tests ─────────────────


class TestServiceCriticalityRule:
    def test_critical_service_payment(self):
        rule = ServiceCriticalityRule()
        result = rule.evaluate({"service": "payment-service"})
        assert result.score == 0.9
        assert "critical" in result.explanation

    def test_critical_service_auth(self):
        rule = ServiceCriticalityRule()
        result = rule.evaluate({"service": "auth-service"})
        assert result.score == 0.9

    def test_standard_service(self):
        rule = ServiceCriticalityRule()
        result = rule.evaluate({"service": "notification-service"})
        assert result.score == 0.5
        assert "standard" in result.explanation

    def test_unknown_service(self):
        rule = ServiceCriticalityRule()
        result = rule.evaluate({"service": "some-random-service"})
        assert result.score == 0.6
        assert "unknown" in result.explanation

    def test_no_service(self):
        rule = ServiceCriticalityRule()
        result = rule.evaluate({})
        assert result.score == 0.5


# ─── RepeatOffenderRule Tests ─────────────────────


class TestRepeatOffenderRule:
    def test_first_occurrence(self):
        rule = RepeatOffenderRule()
        result = rule.evaluate({"_cluster_incident_count": 1})
        assert result.score == 0.3
        assert "first" in result.explanation.lower()

    def test_few_occurrences(self):
        rule = RepeatOffenderRule()
        result = rule.evaluate({"_cluster_incident_count": 3})
        assert result.score == 0.55
        assert "repeat" in result.explanation.lower()

    def test_recurring_pattern(self):
        rule = RepeatOffenderRule()
        result = rule.evaluate({"_cluster_incident_count": 7})
        assert result.score == 0.7
        assert "recurring" in result.explanation.lower()

    def test_chronic_issue(self):
        rule = RepeatOffenderRule()
        result = rule.evaluate({"_cluster_incident_count": 15})
        assert result.score == 0.9
        assert "chronic" in result.explanation.lower()

    def test_missing_cluster_count(self):
        rule = RepeatOffenderRule()
        result = rule.evaluate({})
        assert result.score == 0.3


# ─── TimeOfDayRule Tests ──────────────────────────


class TestTimeOfDayRule:
    def test_business_hours_weekday(self):
        rule = TimeOfDayRule()
        dt = datetime(2024, 3, 25, 14, 0, tzinfo=UTC)  # Monday 2pm
        result = rule.evaluate({"detected_at": dt})
        assert result.score == 0.8
        assert "business hours" in result.explanation.lower()

    def test_off_hours_weekday(self):
        rule = TimeOfDayRule()
        dt = datetime(2024, 3, 25, 3, 0, tzinfo=UTC)  # Monday 3am
        result = rule.evaluate({"detected_at": dt})
        assert result.score == 0.5
        assert "outside" in result.explanation.lower()

    def test_weekend(self):
        rule = TimeOfDayRule()
        dt = datetime(2024, 3, 23, 14, 0, tzinfo=UTC)  # Saturday 2pm
        result = rule.evaluate({"detected_at": dt})
        assert result.score == 0.4
        assert "weekend" in result.explanation.lower()

    def test_missing_timestamp(self):
        rule = TimeOfDayRule()
        result = rule.evaluate({})
        assert result.score == 0.5

    def test_iso_string_timestamp(self):
        rule = TimeOfDayRule()
        result = rule.evaluate({"detected_at": "2024-03-25T14:00:00Z"})
        assert result.score == 0.8


# ─── ScoringEngine Tests ──────────────────────────


class TestScoringEngine:
    def test_default_engine_has_all_rules(self):
        engine = ScoringEngine.default()
        assert len(engine.rules) == 6

    def test_empty_engine_returns_neutral(self):
        engine = ScoringEngine(rules=[])
        result = engine.score({})
        assert result.final_score == 0.5

    def test_weighted_average_calculation(self):
        engine = ScoringEngine.default()
        result = engine.score({
            "severity": "critical",
            "environment": "prod",
            "title": "Production outage",
            "service": "payment-service",
        })
        # All rules should push this toward high/critical
        assert result.final_score >= 0.7
        assert result.severity_label in ("critical", "high")

    def test_low_severity_scenario(self):
        engine = ScoringEngine.default()
        result = engine.score({
            "severity": "low",
            "environment": "dev",
            "title": "Minor warning",
            "service": "analytics-pipeline",
        })
        # Should be low
        assert result.final_score < 0.5
        assert result.severity_label in ("low", "medium")

    def test_result_includes_all_rule_results(self):
        engine = ScoringEngine.default()
        result = engine.score({"severity": "medium"})
        assert len(result.rules) == 6

    def test_result_has_explanation(self):
        engine = ScoringEngine.default()
        result = engine.score({"severity": "high"})
        assert result.explanation is not None
        assert "Final score" in result.explanation

    def test_score_to_dict(self):
        engine = ScoringEngine.default()
        result = engine.score({"severity": "medium"})
        d = result.to_dict()
        assert "final_score" in d
        assert "severity_label" in d
        assert "rules" in d
        assert len(d["rules"]) == 6


# ─── Score-to-Label Mapping Tests ─────────────────


class TestScoreToLabel:
    def test_critical_threshold(self):
        assert ScoringEngine.score_to_label(0.85) == "critical"
        assert ScoringEngine.score_to_label(0.95) == "critical"
        assert ScoringEngine.score_to_label(1.0) == "critical"

    def test_high_threshold(self):
        assert ScoringEngine.score_to_label(0.65) == "high"
        assert ScoringEngine.score_to_label(0.75) == "high"
        assert ScoringEngine.score_to_label(0.84) == "high"

    def test_medium_threshold(self):
        assert ScoringEngine.score_to_label(0.40) == "medium"
        assert ScoringEngine.score_to_label(0.50) == "medium"
        assert ScoringEngine.score_to_label(0.64) == "medium"

    def test_low_threshold(self):
        assert ScoringEngine.score_to_label(0.20) == "low"
        assert ScoringEngine.score_to_label(0.30) == "low"
        assert ScoringEngine.score_to_label(0.39) == "low"

    def test_info_threshold(self):
        assert ScoringEngine.score_to_label(0.0) == "info"
        assert ScoringEngine.score_to_label(0.10) == "info"
        assert ScoringEngine.score_to_label(0.19) == "info"


# ─── Integration Tests ────────────────────────────


class TestScoringIntegration:
    def test_real_incident_critical(self):
        """Test a realistic critical incident."""
        engine = ScoringEngine.default()
        incident = {
            "title": "URGENT: Production database outage",
            "description": "Users cannot login, data loss suspected",
            "severity": "critical",
            "service": "auth-service",
            "environment": "prod",
            "detected_at": datetime(2024, 3, 25, 10, 0, tzinfo=UTC),
        }
        result = engine.score(incident)
        assert result.severity_label == "critical"
        assert result.final_score >= 0.85

    def test_real_incident_medium(self):
        """Test a realistic medium-severity incident."""
        engine = ScoringEngine.default()
        incident = {
            "title": "Elevated error rate in analytics pipeline",
            "description": "Some events are being dropped",
            "severity": "medium",
            "service": "analytics-pipeline",
            "environment": "staging",
            "detected_at": datetime(2024, 3, 23, 22, 0, tzinfo=UTC),  # Saturday
        }
        result = engine.score(incident)
        assert result.severity_label in ("medium", "low")
        assert 0.2 <= result.final_score <= 0.6

    def test_real_incident_low(self):
        """Test a realistic low-severity incident."""
        engine = ScoringEngine.default()
        incident = {
            "title": "Scheduled maintenance warning",
            "description": "Informational: dev server reboot scheduled",
            "severity": "low",
            "service": "notification-service",
            "environment": "dev",
        }
        result = engine.score(incident)
        assert result.severity_label in ("low", "info", "medium")
        assert result.final_score <= 0.5

    def test_score_clamped_to_0_1(self):
        """Verify scores are always between 0 and 1."""
        engine = ScoringEngine.default()

        # Even extreme inputs should produce valid scores
        for severity in ["critical", "high", "medium", "low", "info"]:
            for env in ["prod", "staging", "dev", "test"]:
                result = engine.score({
                    "severity": severity,
                    "environment": env,
                })
                assert 0.0 <= result.final_score <= 1.0

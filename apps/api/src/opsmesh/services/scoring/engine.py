"""
Severity scoring engine.

Architecture:
- A ScoringEngine holds a list of ScoringRules
- Each rule evaluates an incident and returns a RuleResult
- The engine combines results using weighted averaging
- Every score comes with a full explanation trace

This is designed to be extensible — add a new rule class,
register it, and it participates in scoring automatically.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger("opsmesh.scoring")


@dataclass
class RuleResult:
    """Output of a single scoring rule."""

    rule_name: str
    score: float  # 0.0 to 1.0
    weight: float  # How much this rule matters
    explanation: str  # Human-readable reasoning
    details: dict = field(default_factory=dict)


@dataclass
class ScoringResult:
    """Combined output of all scoring rules."""

    final_score: float
    severity_label: str
    rules: list[RuleResult]
    explanation: str

    def to_dict(self) -> dict:
        return {
            "final_score": self.final_score,
            "severity_label": self.severity_label,
            "rules": [
                {
                    "rule_name": r.rule_name,
                    "score": r.score,
                    "weight": r.weight,
                    "explanation": r.explanation,
                    "details": r.details,
                }
                for r in self.rules
            ],
            "explanation": self.explanation,
        }


class ScoringRule:
    """Base class for scoring rules."""

    name: str = "base_rule"
    weight: float = 1.0

    def evaluate(self, incident: dict) -> RuleResult:
        raise NotImplementedError


class SeverityLevelRule(ScoringRule):
    """Score based on the declared severity level."""

    name = "severity_level"
    weight = 3.0

    WEIGHTS = {
        "critical": 1.0,
        "high": 0.75,
        "medium": 0.5,
        "low": 0.25,
        "info": 0.1,
    }

    def evaluate(self, incident: dict) -> RuleResult:
        severity = incident.get("severity", "medium")
        if hasattr(severity, "value"):
            severity = severity.value
        score = self.WEIGHTS.get(severity, 0.5)
        return RuleResult(
            rule_name=self.name,
            score=score,
            weight=self.weight,
            explanation=f"Declared severity '{severity}' maps to {score}",
            details={"severity": severity, "mapped_score": score},
        )


class EnvironmentRule(ScoringRule):
    """Score based on the environment (prod > staging > dev)."""

    name = "environment"
    weight = 2.0

    MULTIPLIERS = {
        "prod": 1.0,
        "staging": 0.6,
        "dev": 0.3,
        "test": 0.1,
    }

    def evaluate(self, incident: dict) -> RuleResult:
        env = incident.get("environment", "prod") or "prod"
        score = self.MULTIPLIERS.get(env, 0.7)
        return RuleResult(
            rule_name=self.name,
            score=score,
            weight=self.weight,
            explanation=f"Environment '{env}' has impact factor {score}",
            details={"environment": env, "factor": score},
        )


class KeywordUrgencyRule(ScoringRule):
    """Score based on urgency-signaling keywords in the title."""

    name = "keyword_urgency"
    weight = 1.5

    CRITICAL_KEYWORDS = {
        "outage": 1.0,
        "down": 1.0,
        "data loss": 1.0,
        "security breach": 1.0,
        "crash loop": 0.95,
        "crash": 0.9,
        "oomkilled": 0.9,
        "unresponsive": 0.85,
    }

    HIGH_KEYWORDS = {
        "5xx": 0.8,
        "error rate": 0.75,
        "connection pool": 0.75,
        "memory leak": 0.75,
        "failed deployment": 0.8,
        "rollback": 0.7,
        "timeout": 0.7,
        "latency spike": 0.7,
    }

    LOW_KEYWORDS = {
        "warning": 0.3,
        "minor": 0.2,
        "intermittent": 0.35,
        "scheduled": 0.15,
        "informational": 0.1,
    }

    def evaluate(self, incident: dict) -> RuleResult:
        title = (incident.get("title") or "").lower()
        description = (incident.get("description") or "").lower()
        text = f"{title} {description}"

        matched = []

        # Check critical keywords first
        for keyword, score in self.CRITICAL_KEYWORDS.items():
            if keyword in text:
                matched.append((keyword, score, "critical"))

        for keyword, score in self.HIGH_KEYWORDS.items():
            if keyword in text:
                matched.append((keyword, score, "high"))

        for keyword, score in self.LOW_KEYWORDS.items():
            if keyword in text:
                matched.append((keyword, score, "low"))

        if not matched:
            return RuleResult(
                rule_name=self.name,
                score=0.5,
                weight=self.weight,
                explanation="No urgency keywords detected, neutral score",
                details={"matched_keywords": []},
            )

        # Use the highest-scoring keyword match
        matched.sort(key=lambda x: x[1], reverse=True)
        best_keyword, best_score, best_tier = matched[0]

        return RuleResult(
            rule_name=self.name,
            score=best_score,
            weight=self.weight,
            explanation=f"Keyword '{best_keyword}' ({best_tier} tier) -> {best_score}",
            details={
                "matched_keywords": [
                    {"keyword": k, "score": s, "tier": t} for k, s, t in matched
                ],
                "best_match": best_keyword,
            },
        )


class ServiceCriticalityRule(ScoringRule):
    """Score based on how critical the affected service is."""

    name = "service_criticality"
    weight = 2.0

    # In production, this would come from a config file or DB
    CRITICAL_SERVICES = {
        "payment-service",
        "auth-service",
        "api-gateway",
        "billing-service",
        "order-processor",
    }
    STANDARD_SERVICES = {
        "notification-service",
        "search-indexer",
        "analytics-pipeline",
        "inventory-service",
    }

    def evaluate(self, incident: dict) -> RuleResult:
        service = (incident.get("service") or "").lower()

        if service in self.CRITICAL_SERVICES:
            score = 0.9
            explanation = f"Service '{service}' is business-critical"
        elif service in self.STANDARD_SERVICES:
            score = 0.5
            explanation = f"Service '{service}' has standard criticality"
        elif service:
            score = 0.6
            explanation = f"Service '{service}' has unknown criticality (default)"
        else:
            score = 0.5
            explanation = "No service specified"

        return RuleResult(
            rule_name=self.name,
            score=score,
            weight=self.weight,
            explanation=explanation,
            details={"service": service, "criticality_score": score},
        )


class RepeatOffenderRule(ScoringRule):
    """
    Boost score if this type of incident recurs frequently.
    Uses the cluster's incident_count as a signal.
    """

    name = "repeat_offender"
    weight = 1.0

    def evaluate(self, incident: dict) -> RuleResult:
        cluster_count = incident.get("_cluster_incident_count", 1)

        if cluster_count >= 10:
            score = 0.9
            explanation = f"Cluster has {cluster_count} incidents - chronic issue"
        elif cluster_count >= 5:
            score = 0.7
            explanation = f"Cluster has {cluster_count} incidents - recurring pattern"
        elif cluster_count >= 2:
            score = 0.55
            explanation = f"Cluster has {cluster_count} incidents - repeat occurrence"
        else:
            score = 0.3
            explanation = "First occurrence"

        return RuleResult(
            rule_name=self.name,
            score=score,
            weight=self.weight,
            explanation=explanation,
            details={"cluster_incident_count": cluster_count},
        )


class TimeOfDayRule(ScoringRule):
    """
    Incidents during business hours may be more impactful
    (more users affected). Nights/weekends score lower.
    """

    name = "time_of_day"
    weight = 0.5

    def evaluate(self, incident: dict) -> RuleResult:
        detected_at = incident.get("detected_at")
        if not detected_at:
            return RuleResult(
                rule_name=self.name,
                score=0.5,
                weight=self.weight,
                explanation="No detection time available",
            )

        if isinstance(detected_at, str):
            try:
                detected_at = datetime.fromisoformat(
                    detected_at.replace("Z", "+00:00")
                )
            except ValueError:
                return RuleResult(
                    rule_name=self.name,
                    score=0.5,
                    weight=self.weight,
                    explanation="Could not parse detection time",
                )

        hour = detected_at.hour
        weekday = detected_at.weekday()  # 0=Mon, 6=Sun

        is_business_hours = 9 <= hour <= 17 and weekday < 5

        if is_business_hours:
            score = 0.8
            day_type = "weekday" if weekday < 5 else "weekend"
            explanation = f"Detected during business hours ({hour}:00, {day_type})"
        elif weekday >= 5:
            score = 0.4
            explanation = f"Detected on weekend ({hour}:00)"
        else:
            score = 0.5
            explanation = f"Detected outside business hours ({hour}:00)"

        return RuleResult(
            rule_name=self.name,
            score=score,
            weight=self.weight,
            explanation=explanation,
            details={
                "hour": hour,
                "weekday": weekday,
                "business_hours": is_business_hours,
            },
        )


# ─── Scoring Engine ────────────────────────────────


class ScoringEngine:
    """
    Combines multiple scoring rules into a final severity score.

    Usage:
        engine = ScoringEngine.default()
        result = engine.score(incident_data)
        print(result.final_score)
        print(result.explanation)
    """

    def __init__(self, rules: list[ScoringRule] | None = None):
        self.rules = rules or []

    @classmethod
    def default(cls) -> "ScoringEngine":
        """Create an engine with the standard rule set."""
        return cls(
            rules=[
                SeverityLevelRule(),
                EnvironmentRule(),
                KeywordUrgencyRule(),
                ServiceCriticalityRule(),
                RepeatOffenderRule(),
                TimeOfDayRule(),
            ]
        )

    def score(self, incident: dict) -> ScoringResult:
        """
        Run all rules and compute the weighted average score.
        """
        results = []
        for rule in self.rules:
            try:
                result = rule.evaluate(incident)
                results.append(result)
            except Exception as e:
                logger.warning("Rule %s failed: %s", rule.name, e)
                results.append(
                    RuleResult(
                        rule_name=rule.name,
                        score=0.5,
                        weight=rule.weight,
                        explanation=f"Rule failed: {e}",
                    )
                )

        # Weighted average
        total_weight = sum(r.weight for r in results)
        if total_weight == 0:
            final_score = 0.5
        else:
            weighted_sum = sum(r.score * r.weight for r in results)
            final_score = round(weighted_sum / total_weight, 3)

        # Clamp
        final_score = max(0.0, min(1.0, final_score))

        # Map to severity label
        severity_label = self._score_to_label(final_score)

        # Build explanation
        explanation_parts = [
            f"- {r.rule_name} (w={r.weight}): {r.score:.2f} - {r.explanation}"
            for r in results
        ]
        explanation = (
            f"Final score: {final_score} ({severity_label})\n"
            + "\n".join(explanation_parts)
        )

        return ScoringResult(
            final_score=final_score,
            severity_label=severity_label,
            rules=results,
            explanation=explanation,
        )

    @staticmethod
    def _score_to_label(score: float) -> str:
        if score >= 0.85:
            return "critical"
        elif score >= 0.65:
            return "high"
        elif score >= 0.40:
            return "medium"
        elif score >= 0.20:
            return "low"
        else:
            return "info"

    @staticmethod
    def score_to_label(score: float) -> str:
        """Public method to convert score to severity label."""
        return ScoringEngine._score_to_label(score)

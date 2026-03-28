"""
Incident analyzer — orchestrates AI analysis.

Calls the LLM client with structured prompts,
parses the response, and returns typed results.
"""

import json
import logging
from dataclasses import dataclass

from src.opsmesh.services.ai.client import AIClient
from src.opsmesh.services.ai.prompts import SYSTEM_PROMPT, build_analysis_prompt

logger = logging.getLogger("opsmesh.ai.analyzer")


@dataclass
class AnalysisResult:
    """Parsed AI analysis output."""

    root_cause_summary: str
    root_cause_confidence: float
    contributing_factors: list[str]
    root_cause_category: str
    suggested_actions: list[dict]
    severity_assessment: str
    escalation_needed: bool
    related_systems: list[str]
    prevention_recommendations: list[str]

    # Tracing
    model: str
    latency_ms: float
    tokens_used: int
    raw_prompt: str
    raw_response: str


def analyze_incident(incident: dict) -> AnalysisResult:
    """
    Run AI analysis on an incident.

    Returns structured analysis with root cause,
    suggested actions, and tracing metadata.
    """
    client = AIClient()

    # Build the prompt
    user_prompt = build_analysis_prompt(incident)

    logger.info("Running AI analysis for incident %s", incident.get("id"))

    # Call the LLM
    response = client.chat(
        system=SYSTEM_PROMPT,
        user=user_prompt,
        temperature=0.3,
        max_tokens=1500,
        response_format={"type": "json_object"},
    )

    # Parse the response
    try:
        parsed = json.loads(response.content)
    except json.JSONDecodeError:
        logger.error(
            "Failed to parse AI response as JSON: %s", response.content[:200]
        )
        parsed = _extract_best_effort(response.content)

    root_cause = parsed.get("root_cause", {})
    actions = parsed.get("suggested_actions", [])

    result = AnalysisResult(
        root_cause_summary=root_cause.get("summary", "Analysis unavailable"),
        root_cause_confidence=float(root_cause.get("confidence", 0.0)),
        contributing_factors=root_cause.get("contributing_factors", []),
        root_cause_category=root_cause.get("category", "unknown"),
        suggested_actions=actions,
        severity_assessment=parsed.get("severity_assessment", ""),
        escalation_needed=parsed.get("escalation_needed", False),
        related_systems=parsed.get("related_systems", []),
        prevention_recommendations=parsed.get("prevention_recommendations", []),
        model=response.model,
        latency_ms=response.latency_ms,
        tokens_used=response.usage.get("total_tokens", 0),
        raw_prompt=user_prompt,
        raw_response=response.content,
    )

    logger.info(
        "Analysis complete: confidence=%.2f, actions=%d, model=%s, latency=%sms",
        result.root_cause_confidence,
        len(result.suggested_actions),
        result.model,
        result.latency_ms,
    )

    return result


def _extract_best_effort(text: str) -> dict:
    """Try to extract structured data from a non-JSON response."""
    return {
        "root_cause": {
            "summary": text[:500] if text else "Could not parse AI response",
            "confidence": 0.1,
            "contributing_factors": [],
            "category": "unknown",
        },
        "suggested_actions": [],
        "severity_assessment": "Manual review required — AI response was not parseable",
    }

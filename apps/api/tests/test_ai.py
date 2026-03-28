"""
Tests for AI prompt construction, response parsing, and analysis.
"""

import json

from src.opsmesh.services.ai.analyzer import _extract_best_effort
from src.opsmesh.services.ai.client import AIClient
from src.opsmesh.services.ai.prompts import SYSTEM_PROMPT, build_analysis_prompt


def _incident(**overrides) -> dict:
    defaults = {
        "id": "test-123",
        "title": "High CPU usage on payment-service",
        "description": "CPU consistently above 95% for the last 15 minutes",
        "source": "datadog",
        "severity": "high",
        "service": "payment-service",
        "environment": "prod",
        "region": "us-east-1",
        "severity_score": 0.78,
        "_severity_label": "high",
        "_category": "resource",
        "_cluster_incident_count": 3,
        "detected_at": "2025-01-15T10:30:00Z",
    }
    defaults.update(overrides)
    return defaults


class TestPromptConstruction:
    def test_includes_title(self):
        prompt = build_analysis_prompt(_incident())
        assert "High CPU usage on payment-service" in prompt

    def test_includes_description(self):
        prompt = build_analysis_prompt(_incident())
        assert "95%" in prompt

    def test_includes_service(self):
        prompt = build_analysis_prompt(_incident())
        assert "payment-service" in prompt

    def test_includes_environment(self):
        prompt = build_analysis_prompt(_incident())
        assert "prod" in prompt

    def test_includes_severity_score(self):
        prompt = build_analysis_prompt(_incident())
        assert "0.780" in prompt

    def test_includes_cluster_context(self):
        prompt = build_analysis_prompt(_incident(_cluster_incident_count=5))
        assert "5 times" in prompt

    def test_marks_duplicate(self):
        prompt = build_analysis_prompt(_incident(is_duplicate=True))
        assert "DUPLICATE" in prompt

    def test_handles_missing_fields(self):
        prompt = build_analysis_prompt({"id": "x", "title": "Test"})
        assert "Test" in prompt

    def test_includes_category(self):
        prompt = build_analysis_prompt(_incident(_category="resource"))
        assert "resource" in prompt

    def test_includes_region(self):
        prompt = build_analysis_prompt(_incident(region="us-east-1"))
        assert "us-east-1" in prompt

    def test_includes_severity_label(self):
        prompt = build_analysis_prompt(_incident(_severity_label="high"))
        assert "high" in prompt

    def test_includes_source(self):
        prompt = build_analysis_prompt(_incident(source="prometheus"))
        assert "prometheus" in prompt


class TestSystemPrompt:
    def test_defines_json_schema(self):
        assert "root_cause" in SYSTEM_PROMPT
        assert "suggested_actions" in SYSTEM_PROMPT
        assert "confidence" in SYSTEM_PROMPT

    def test_sets_role(self):
        assert "Site Reliability Engineer" in SYSTEM_PROMPT

    def test_requires_json_response(self):
        assert "JSON" in SYSTEM_PROMPT

    def test_defines_action_structure(self):
        assert "step" in SYSTEM_PROMPT
        assert "action" in SYSTEM_PROMPT
        assert "priority" in SYSTEM_PROMPT
        assert "estimated_time" in SYSTEM_PROMPT

    def test_defines_category_options(self):
        assert "resource" in SYSTEM_PROMPT
        assert "error" in SYSTEM_PROMPT
        assert "performance" in SYSTEM_PROMPT
        assert "security" in SYSTEM_PROMPT

    def test_defines_escalation_field(self):
        assert "escalation_needed" in SYSTEM_PROMPT


class TestBestEffortParsing:
    def test_extracts_text(self):
        result = _extract_best_effort("The CPU is overloaded due to a memory leak")
        assert "CPU is overloaded" in result["root_cause"]["summary"]
        assert result["root_cause"]["confidence"] == 0.1

    def test_handles_empty(self):
        result = _extract_best_effort("")
        assert result["root_cause"]["confidence"] == 0.1
        assert "Could not parse" in result["root_cause"]["summary"]

    def test_truncates_long_text(self):
        long_text = "x" * 1000
        result = _extract_best_effort(long_text)
        assert len(result["root_cause"]["summary"]) <= 500

    def test_returns_unknown_category(self):
        result = _extract_best_effort("Some text")
        assert result["root_cause"]["category"] == "unknown"

    def test_returns_empty_factors(self):
        result = _extract_best_effort("Some text")
        assert result["root_cause"]["contributing_factors"] == []

    def test_returns_empty_actions(self):
        result = _extract_best_effort("Some text")
        assert result["suggested_actions"] == []


class TestMockClient:
    def test_mock_response_without_api_key(self):
        client = AIClient(api_key="")
        response = client.chat(system="test", user="test")
        assert response.model == "mock"
        parsed = json.loads(response.content)
        assert "root_cause" in parsed
        assert "suggested_actions" in parsed

    def test_mock_response_is_valid_json(self):
        client = AIClient(api_key="")
        response = client.chat(system="test", user="test")
        parsed = json.loads(response.content)
        assert isinstance(parsed["root_cause"]["confidence"], float)
        assert isinstance(parsed["suggested_actions"], list)

    def test_mock_response_has_correct_structure(self):
        client = AIClient(api_key="")
        response = client.chat(system="test", user="test")
        parsed = json.loads(response.content)
        assert "summary" in parsed["root_cause"]
        assert "contributing_factors" in parsed["root_cause"]
        assert "category" in parsed["root_cause"]
        assert len(parsed["suggested_actions"]) >= 1

    def test_mock_action_has_required_fields(self):
        client = AIClient(api_key="")
        response = client.chat(system="test", user="test")
        parsed = json.loads(response.content)
        action = parsed["suggested_actions"][0]
        assert "step" in action
        assert "action" in action
        assert "priority" in action
        assert "estimated_time" in action

    def test_fallback_response(self):
        client = AIClient(api_key="")
        response = client._fallback_response("Connection timeout")
        parsed = json.loads(response.content)
        assert "timeout" in parsed["root_cause"]["summary"].lower()
        assert response.model == "fallback"

    def test_fallback_has_actions(self):
        client = AIClient(api_key="")
        response = client._fallback_response("Connection error")
        parsed = json.loads(response.content)
        assert len(parsed["suggested_actions"]) >= 1

    def test_mock_response_zero_tokens(self):
        client = AIClient(api_key="")
        response = client.chat(system="test", user="test")
        assert response.usage["total_tokens"] == 0

    def test_mock_response_zero_latency(self):
        client = AIClient(api_key="")
        response = client.chat(system="test", user="test")
        assert response.latency_ms == 0

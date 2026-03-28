"""
AI client — provider-agnostic LLM interface.

Supports any OpenAI-compatible API:
- OpenAI (gpt-4o-mini, gpt-4o)
- Anthropic (via OpenAI-compatible proxy)
- Ollama (local models)
- Together, Groq, Fireworks, etc.

Configuration via environment variables:
- OPENAI_API_KEY: API key
- OPENAI_MODEL: model name (default: gpt-4o-mini)
- OPENAI_BASE_URL: base URL (default: https://api.openai.com/v1)
"""

import json
import logging
import time
from dataclasses import dataclass

import httpx

from src.opsmesh.core.config import settings

logger = logging.getLogger("opsmesh.ai")


@dataclass
class AIResponse:
    """Structured response from the AI client."""

    content: str
    model: str
    usage: dict
    latency_ms: float
    raw_response: dict


class AIClient:
    """
    OpenAI-compatible API client.

    Usage:
        client = AIClient()
        response = client.chat(
            system="You are an incident response expert.",
            user="Analyze this incident: ...",
        )
        print(response.content)
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 2,
    ):
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model
        self.base_url = (
            base_url or getattr(settings, "openai_base_url", "")
        ).rstrip("/")
        if not self.base_url:
            self.base_url = "https://api.openai.com/v1"
        self.timeout = timeout
        self.max_retries = max_retries

    def chat(
        self,
        system: str,
        user: str,
        temperature: float = 0.3,
        max_tokens: int = 1500,
        response_format: dict | None = None,
    ) -> AIResponse:
        """
        Send a chat completion request.

        Args:
            system: System prompt
            user: User message
            temperature: Sampling temperature (lower = more deterministic)
            max_tokens: Maximum response tokens
            response_format: Optional {"type": "json_object"} for JSON mode

        Returns:
            AIResponse with content, usage, and timing
        """
        if not self.api_key:
            logger.warning("No API key configured — returning mock response")
            return self._mock_response(user)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format:
            payload["response_format"] = response_format

        url = f"{self.base_url}/chat/completions"

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                start = time.monotonic()
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(url, headers=headers, json=payload)
                latency_ms = round((time.monotonic() - start) * 1000, 1)

                if resp.status_code == 429:
                    wait = min(2**attempt, 8)
                    logger.warning("Rate limited, retrying in %ds...", wait)
                    time.sleep(wait)
                    continue

                resp.raise_for_status()
                data = resp.json()

                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})

                logger.info(
                    "AI response: model=%s tokens=%s latency=%sms",
                    self.model,
                    usage.get("total_tokens", "?"),
                    latency_ms,
                )

                return AIResponse(
                    content=content,
                    model=self.model,
                    usage=usage,
                    latency_ms=latency_ms,
                    raw_response=data,
                )

            except httpx.HTTPStatusError as e:
                last_error = e
                logger.error("AI API error (attempt %d): %s", attempt + 1, e)
                if attempt < self.max_retries:
                    time.sleep(2**attempt)

            except Exception as e:
                last_error = e
                logger.error("AI client error (attempt %d): %s", attempt + 1, e)
                if attempt < self.max_retries:
                    time.sleep(1)

        # All retries exhausted — return fallback
        logger.error(
            "AI request failed after %d attempts: %s", self.max_retries + 1, last_error
        )
        return self._fallback_response(str(last_error))

    def _mock_response(self, user_message: str) -> AIResponse:
        """Generate a mock response when no API key is configured."""
        mock_content = json.dumps({
            "root_cause": {
                "summary": (
                    "Mock analysis — configure OPENAI_API_KEY for real AI responses"
                ),
                "confidence": 0.0,
                "contributing_factors": [
                    "No API key configured",
                    "This is a placeholder response",
                ],
                "category": "unknown",
            },
            "suggested_actions": [
                {
                    "step": 1,
                    "action": "Configure OPENAI_API_KEY environment variable",
                    "priority": "high",
                    "estimated_time": "5 minutes",
                    "rationale": "Required for real AI analysis",
                },
                {
                    "step": 2,
                    "action": "Restart the worker to pick up the new configuration",
                    "priority": "medium",
                    "estimated_time": "1 minute",
                    "rationale": "Worker needs to reload environment variables",
                },
            ],
            "severity_assessment": "Unable to assess without real AI",
            "escalation_needed": False,
            "related_systems": [],
            "prevention_recommendations": [],
        })

        return AIResponse(
            content=mock_content,
            model="mock",
            usage={"total_tokens": 0},
            latency_ms=0,
            raw_response={},
        )

    def _fallback_response(self, error: str) -> AIResponse:
        """Generate a fallback when the API is unavailable."""
        fallback = json.dumps({
            "root_cause": {
                "summary": f"AI analysis unavailable: {error}",
                "confidence": 0.0,
                "contributing_factors": ["AI service is currently unreachable"],
                "category": "unknown",
            },
            "suggested_actions": [
                {
                    "step": 1,
                    "action": "Investigate manually using runbook procedures",
                    "priority": "high",
                    "estimated_time": "varies",
                    "rationale": "AI assistance unavailable",
                },
            ],
            "severity_assessment": "Manual assessment required",
            "escalation_needed": False,
            "related_systems": [],
            "prevention_recommendations": [],
            "error": error,
        })

        return AIResponse(
            content=fallback,
            model="fallback",
            usage={"total_tokens": 0},
            latency_ms=0,
            raw_response={"error": error},
        )

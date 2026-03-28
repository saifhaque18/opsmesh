"""
Structured logging configuration for the worker pipeline.

Logs include:
- Incident ID
- Pipeline step name
- Duration
- Success/failure
"""

import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

logger = logging.getLogger("opsmesh.pipeline")


def log_step(step_name: str):
    """Decorator that logs pipeline step execution with timing."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(incident: dict, *args: Any, **kwargs: Any) -> dict:
            incident_id = incident.get("id", "unknown")
            logger.info(
                "[%s] START incident=%s",
                step_name,
                incident_id,
            )

            start = time.monotonic()
            try:
                result = func(incident, *args, **kwargs)
                duration = time.monotonic() - start
                logger.info(
                    "[%s] DONE incident=%s duration=%.3fs",
                    step_name,
                    incident_id,
                    duration,
                )
                return result
            except Exception as e:
                duration = time.monotonic() - start
                logger.error(
                    "[%s] FAIL incident=%s duration=%.3fs error=%s",
                    step_name,
                    incident_id,
                    duration,
                    str(e),
                )
                raise

        return wrapper

    return decorator

"""
AI analysis pipeline step.

Runs after scoring and dedup. Calls the AI analyzer,
saves results to the incident, and logs the trace.
"""

import json
import logging

from src.opsmesh.core.sync_database import get_sync_db
from src.opsmesh.models.ai_trace import AITrace
from src.opsmesh.models.event import EventType
from src.opsmesh.models.incident import Incident
from src.opsmesh.services.ai.analyzer import analyze_incident
from src.opsmesh.services.ai.prompts import SYSTEM_PROMPT
from src.opsmesh.services.event_service import emit_event

logger = logging.getLogger("opsmesh.ai_step")


def run_ai_analysis(incident_id: str, incident_data: dict) -> dict:
    """
    Run AI analysis and save results.

    Returns the analysis result dict for inclusion
    in the job result.
    """
    db = get_sync_db()

    try:
        # Run analysis
        result = analyze_incident(incident_data)

        # Load the incident
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            return {"error": "Incident not found"}

        # Save AI results to the incident
        incident.ai_root_cause = json.dumps({
            "summary": result.root_cause_summary,
            "confidence": result.root_cause_confidence,
            "contributing_factors": result.contributing_factors,
            "category": result.root_cause_category,
            "severity_assessment": result.severity_assessment,
            "escalation_needed": result.escalation_needed,
            "related_systems": result.related_systems,
            "prevention_recommendations": result.prevention_recommendations,
        })

        incident.ai_suggested_actions = json.dumps(result.suggested_actions)
        incident.ai_reviewed = False

        # Log the trace
        trace = AITrace(
            incident_id=incident.id,
            model=result.model,
            system_prompt=SYSTEM_PROMPT,
            user_prompt=result.raw_prompt,
            response_content=result.raw_response,
            parsed_result={
                "root_cause": {
                    "summary": result.root_cause_summary,
                    "confidence": result.root_cause_confidence,
                },
                "actions_count": len(result.suggested_actions),
            },
            confidence=result.root_cause_confidence,
            latency_ms=result.latency_ms,
            tokens_input=result.tokens_used,
            tokens_total=result.tokens_used,
        )
        db.add(trace)

        # Emit AI analysis completed event
        emit_event(
            db=db,
            incident_id=incident_id,
            event_type=EventType.AI_ANALYSIS_COMPLETED,
            summary=f"AI analysis done ({result.root_cause_confidence:.0%})",
            actor="worker",
            metadata={
                "model": result.model,
                "confidence": result.root_cause_confidence,
                "actions_count": len(result.suggested_actions),
                "latency_ms": result.latency_ms,
            },
        )

        db.commit()

        logger.info(
            "AI analysis saved: incident=%s confidence=%.2f actions=%d",
            incident_id,
            result.root_cause_confidence,
            len(result.suggested_actions),
        )

        return {
            "root_cause": result.root_cause_summary,
            "confidence": result.root_cause_confidence,
            "actions_count": len(result.suggested_actions),
            "model": result.model,
            "latency_ms": result.latency_ms,
        }

    except Exception as e:
        db.rollback()
        logger.error("AI analysis failed for %s: %s", incident_id, e)
        return {"error": str(e)}
    finally:
        db.close()

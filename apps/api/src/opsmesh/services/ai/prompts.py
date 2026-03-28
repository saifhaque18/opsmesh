"""
Prompt templates for AI incident analysis.

Design principles:
- Structured JSON output for reliable parsing
- Context-rich prompts that include all relevant incident data
- Clear role definition and constraints
- Confidence scoring to flag uncertain analyses
"""

SYSTEM_PROMPT = """You are an expert Site Reliability Engineer \
and incident response specialist.
You analyze production incidents and provide:
1. Root cause analysis with confidence scoring
2. Actionable response steps prioritized by impact
3. Severity assessment based on business impact

Rules:
- Base your analysis ONLY on the incident data provided
- Express uncertainty when information is insufficient
- Prioritize actions that reduce blast radius first
- Consider downstream service dependencies
- Be specific and actionable — no vague suggestions
- Always respond in valid JSON matching the schema below

Response JSON schema:
{
  "root_cause": {
    "summary": "1-2 sentence root cause hypothesis",
    "confidence": 0.0-1.0,
    "contributing_factors": ["factor1", "factor2"],
    "category": "resource|error|performance|security|deployment|config|unknown"
  },
  "suggested_actions": [
    {
      "step": 1,
      "action": "Specific action to take",
      "priority": "immediate|high|medium|low",
      "estimated_time": "time estimate",
      "rationale": "Why this action helps"
    }
  ],
  "severity_assessment": "Brief assessment of business impact",
  "escalation_needed": true/false,
  "related_systems": ["system1", "system2"],
  "prevention_recommendations": ["recommendation1"]
}"""


def build_analysis_prompt(incident: dict) -> str:
    """
    Build the user message for incident analysis.

    Includes all available context:
    - Incident metadata
    - Severity scoring results
    - Cluster/dedup context
    - Historical patterns
    """
    parts = []

    parts.append("Analyze this production incident:\n")

    # Core incident data
    parts.append(f"Title: {incident.get('title', 'Unknown')}")
    if incident.get("description"):
        parts.append(f"Description: {incident['description']}")
    parts.append(f"Source: {incident.get('source', 'unknown')}")
    parts.append(f"Severity: {incident.get('severity', 'medium')}")
    parts.append(f"Service: {incident.get('service', 'unknown')}")
    parts.append(f"Environment: {incident.get('environment', 'unknown')}")

    if incident.get("region"):
        parts.append(f"Region: {incident['region']}")

    # Scoring context
    if incident.get("severity_score") is not None:
        parts.append(f"\nAutomated severity score: {incident['severity_score']:.3f}")
    if incident.get("_severity_label"):
        parts.append(f"Severity label: {incident['_severity_label']}")
    if incident.get("_score_explanation"):
        parts.append(f"Score rationale: {incident['_score_explanation']}")

    # Cluster/dedup context
    if incident.get("is_duplicate"):
        parts.append("\nThis incident is a DUPLICATE of a previous occurrence.")
    cluster_count = incident.get("_cluster_incident_count", 0)
    if cluster_count > 1:
        parts.append(
            f"This type of incident has occurred {cluster_count} times recently."
        )

    # Category from enrichment
    if incident.get("_category"):
        parts.append(f"Automated category: {incident['_category']}")

    # Detection time
    if incident.get("detected_at"):
        parts.append(f"\nDetected at: {incident['detected_at']}")

    return "\n".join(parts)


def build_response_steps_prompt(incident: dict, root_cause: dict) -> str:
    """
    Build a focused prompt for response step generation.

    Used when you want detailed, actionable steps
    after the initial analysis.
    """
    parts = []

    parts.append("Generate detailed response steps for this incident:\n")
    parts.append(f"Title: {incident.get('title', 'Unknown')}")
    parts.append(f"Service: {incident.get('service', 'unknown')}")
    parts.append(f"Environment: {incident.get('environment', 'unknown')}")

    if root_cause.get("summary"):
        parts.append(f"\nRoot cause: {root_cause['summary']}")
    if root_cause.get("contributing_factors"):
        parts.append(
            f"Contributing factors: {', '.join(root_cause['contributing_factors'])}"
        )

    parts.append(
        "\nProvide 3-6 specific, actionable steps. "
        "Prioritize by impact. Include estimated time for each step. "
        "Respond in the JSON format specified in your instructions."
    )

    return "\n".join(parts)

"""
Safety Agent — analyses safety concerns, near-miss patterns, hazard controls.
"""
from models.schemas import AgentFinding, Incident
from tools.safety_tools import (
    get_safety_incident_history,
    get_hazard_status,
    assess_safety_risk,
)
from tools.rag_tools import make_rag_tool
from agents.base import make_agent_executor, run_domain_agent

DOMAIN_PROMPT = """
ROLE: EHS (Environment, Health & Safety) Specialist

Your job is to determine whether there is a safety dimension to the incident —
either as a cause, a consequence, or a latent hazard that requires immediate action.

STEPS:
1. Assess the safety risk level of the described incident.
2. Get hazard controls and compliance status for the affected line.
3. Review safety incident history — look for recurring patterns (same hazard type ≥ 3 events).
4. Search the knowledge base for the relevant safety standards, protocols, and prior incidents.
5. Determine if any safety actions are required immediately (independent of root cause).

Return a detailed analysis covering:
  - Safety risk classification (Near-Miss / First Aid / Recordable / etc.)
  - Active safety hazards and compliance status
  - Incident history patterns and recurrence risk
  - Immediate safety actions required (if any)
  - Regulatory notification requirements (if any)
  - Preventive recommendations to reduce recurrence
"""

_TOOLS = [
    assess_safety_risk,
    get_hazard_status,
    get_safety_incident_history,
    make_rag_tool("safety"),
]


def run(incident: Incident) -> AgentFinding:
    executor = make_agent_executor(
        domain_system_prompt=DOMAIN_PROMPT,
        tools=_TOOLS,
        agent_name="SafetyAgent",
    )
    return run_domain_agent(
        executor=executor,
        incident=incident,
        agent_name="SafetyAgent",
        domain="safety",
        analysis_instruction=(
            f"Perform a safety analysis for incident {incident.id}. "
            f"Focus on line {incident.line_id}. "
            "Assess the safety risk level, check hazard controls, review the safety "
            "incident history for patterns, and determine what immediate safety actions "
            "are required. Cross-reference with safety standards and protocols."
        ),
    )

"""
Quality Agent — analyses defect rates, SPC status, and quality threshold violations.
"""
from models.schemas import AgentFinding, Incident
from tools.quality_tools import (
    get_current_defect_rate,
    get_defect_breakdown,
    check_quality_thresholds,
    get_recent_quality_events,
)
from tools.rag_tools import make_rag_tool
from agents.base import make_agent_executor, run_domain_agent

DOMAIN_PROMPT = """
ROLE: Quality Analysis Specialist

Your job is to determine whether a quality issue (defect spike, out-of-spec product,
SPC violation) is contributing to the reported incident.

STEPS:
1. Get current defect rate and SPC status for the affected line.
2. Get defect type breakdown to identify the dominant defect mode.
3. Check quality thresholds and document required responses.
4. Review recent quality events on the line.
5. Search the knowledge base for KBAs and prior incidents matching the defect type.
6. Identify likely causes from the data and documentation.

Return a detailed analysis covering:
  - Current defect rate vs. thresholds
  - Defect type breakdown
  - Prior incidents with the same defect pattern
  - Most likely quality-related contributing factors
  - Immediate quality response actions required
"""

_TOOLS = [
    get_current_defect_rate,
    get_defect_breakdown,
    check_quality_thresholds,
    get_recent_quality_events,
    make_rag_tool("quality"),
]


def run(incident: Incident) -> AgentFinding:
    executor = make_agent_executor(
        domain_system_prompt=DOMAIN_PROMPT,
        tools=_TOOLS,
        agent_name="QualityAgent",
    )
    return run_domain_agent(
        executor=executor,
        incident=incident,
        agent_name="QualityAgent",
        domain="quality",
        analysis_instruction=(
            f"Perform a full quality analysis for incident {incident.id}. "
            f"Focus on line {incident.line_id}. "
            "Determine if a defect spike or quality threshold violation is present, "
            "identify the defect type, and trace it to likely root causes using "
            "historical incidents and KBA documentation."
        ),
    )

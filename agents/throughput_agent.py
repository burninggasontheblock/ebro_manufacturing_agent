"""
Throughput Agent — analyses production rate drops, OEE degradation, and downtime.
"""
from models.schemas import AgentFinding, Incident
from tools.throughput_tools import (
    get_current_throughput,
    get_downtime_log,
    calculate_production_loss,
    get_oee_breakdown,
)
from tools.rag_tools import make_rag_tool
from agents.base import make_agent_executor, run_domain_agent

DOMAIN_PROMPT = """
ROLE: Production Throughput Analyst

Your job is to diagnose throughput drops, OEE degradation, and identify the
primary loss category (Availability, Performance, or Quality loss).

STEPS:
1. Get current throughput rate vs. target and alert level.
2. Get OEE breakdown — identify the weakest component.
3. Get the downtime log — look for patterns (unplanned stops, long changeovers, jams).
4. Calculate total production loss in units and revenue impact.
5. Search the knowledge base for KBAs and prior throughput incidents on this line.
6. Correlate downtime events with equipment status and maintenance history.

Return a detailed analysis covering:
  - Current throughput gap and OEE score
  - Dominant OEE loss category with supporting data
  - Downtime event timeline and patterns
  - Production and revenue impact estimate
  - Most likely throughput-related root causes
  - Recommended immediate actions to restore throughput
"""

_TOOLS = [
    get_current_throughput,
    get_oee_breakdown,
    get_downtime_log,
    calculate_production_loss,
    make_rag_tool("throughput"),
]


def run(incident: Incident) -> AgentFinding:
    executor = make_agent_executor(
        domain_system_prompt=DOMAIN_PROMPT,
        tools=_TOOLS,
        agent_name="ThroughputAgent",
    )
    return run_domain_agent(
        executor=executor,
        incident=incident,
        agent_name="ThroughputAgent",
        domain="throughput",
        analysis_instruction=(
            f"Perform a full throughput analysis for incident {incident.id}. "
            f"Focus on line {incident.line_id}. "
            "Quantify the throughput drop, calculate OEE breakdown, review downtime events, "
            "and identify the primary OEE loss category driving the incident. "
            "Estimate production and revenue impact and recommend restoration actions."
        ),
    )

"""
Maintenance Agent — analyses equipment health, overdue PM tasks, sensor alerts.
"""
from models.schemas import AgentFinding, Incident
from tools.maintenance_tools import (
    get_equipment_status,
    get_open_work_orders,
    get_pm_schedule,
    get_sensor_alerts,
)
from tools.rag_tools import make_rag_tool
from agents.base import make_agent_executor, run_domain_agent

DOMAIN_PROMPT = """
ROLE: Maintenance Engineering Specialist

Your job is to determine whether equipment degradation, overdue preventive maintenance,
or sensor threshold breaches are contributing to the incident.

STEPS:
1. Get sensor alerts for the affected line — look for any approaching or breached thresholds.
2. Get PM schedule — identify overdue tasks and deferred work orders.
3. Get open work orders — look for HIGH/CRITICAL priority items that are overdue.
4. Get equipment status for key assets on the line (conveyor, welding station, etc.).
5. Search the knowledge base for maintenance history, KBAs matching the equipment type,
   and prior incidents caused by similar maintenance gaps.
6. Assess whether any overdue maintenance directly explains the current incident.

Return a detailed analysis covering:
  - Active sensor alerts and threshold breaches
  - Overdue PM tasks and open work orders
  - Equipment health indicators (vibration, temperature, wear)
  - Correlation between maintenance gaps and the incident description
  - Prior incidents caused by the same maintenance issue
  - Recommended maintenance actions with priority order
"""

_TOOLS = [
    get_sensor_alerts,
    get_open_work_orders,
    get_pm_schedule,
    get_equipment_status,
    make_rag_tool("maintenance"),
]


def run(incident: Incident) -> AgentFinding:
    executor = make_agent_executor(
        domain_system_prompt=DOMAIN_PROMPT,
        tools=_TOOLS,
        agent_name="MaintenanceAgent",
    )
    return run_domain_agent(
        executor=executor,
        incident=incident,
        agent_name="MaintenanceAgent",
        domain="maintenance",
        analysis_instruction=(
            f"Perform a full maintenance analysis for incident {incident.id}. "
            f"Focus on line {incident.line_id}. "
            "Check all sensor alerts, review overdue PM tasks and open work orders, "
            "assess equipment health, and determine if any maintenance gap is the "
            "primary or contributing cause of the incident. "
            "Cross-reference with the knowledge base for prior incidents."
        ),
    )

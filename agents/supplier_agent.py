"""
Supplier Agent — analyses supply chain risk, inventory levels, and delivery delays.
"""
from models.schemas import AgentFinding, Incident
from tools.supplier_tools import (
    get_inventory_levels,
    get_open_purchase_orders,
    get_supplier_performance,
    check_supply_risk,
)
from tools.rag_tools import make_rag_tool
from agents.base import make_agent_executor, run_domain_agent

DOMAIN_PROMPT = """
ROLE: Supply Chain Risk Analyst

Your job is to determine whether supplier delivery failures, inventory shortfalls,
or material quality issues are contributing to the incident.

STEPS:
1. Check supply risk assessment for the affected line.
2. Check inventory levels for all critical materials — flag anything below buffer.
3. Review open purchase orders — look for delayed orders and their root causes.
4. Assess supplier performance for relevant suppliers (OTD%, quality score, single-source risk).
5. Search the knowledge base for prior supplier incidents, SLA standards, and buffer policies.
6. Determine if any supply chain issue is the primary driver or a contributing factor.

Return a detailed analysis covering:
  - Current inventory levels vs. buffer targets
  - Any delayed POs and their impact on production continuity
  - Supplier performance flags (OTD below threshold, single-source risk)
  - Time-to-line-stop if current delays are not resolved
  - Prior incidents caused by the same supplier pattern
  - Recommended supply chain actions (expedite, emergency order, escalation)
"""

_TOOLS = [
    check_supply_risk,
    get_inventory_levels,
    get_open_purchase_orders,
    get_supplier_performance,
    make_rag_tool("supplier"),
]


def run(incident: Incident) -> AgentFinding:
    executor = make_agent_executor(
        domain_system_prompt=DOMAIN_PROMPT,
        tools=_TOOLS,
        agent_name="SupplierAgent",
    )
    return run_domain_agent(
        executor=executor,
        incident=incident,
        agent_name="SupplierAgent",
        domain="supplier",
        analysis_instruction=(
            f"Perform a full supply chain analysis for incident {incident.id}. "
            f"Focus on line {incident.line_id} and plant {incident.plant_id}. "
            "Check inventory levels, delayed POs, and supplier performance. "
            "Determine if a supply chain issue is causing or contributing to the incident. "
            "Provide a time-to-line-stop estimate if delays continue and recommend actions."
        ),
    )

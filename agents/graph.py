"""
LangGraph multi-agent orchestration graph.

Flow:
  START → orchestrator_node
        → [parallel] quality, throughput, maintenance, supplier, safety
          (only those selected by the orchestrator)
        → rca_node
        → [parallel] doc_shift_handoff, doc_maintenance_request, doc_corrective_action, doc_supplier_questions
        → END

State uses Annotated[List, add] so parallel nodes safely append their findings
without a write-write conflict.
"""
from __future__ import annotations

import json
import re
from operator import add
from typing import Annotated, Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

import config
from models.schemas import (
    AgentFinding,
    Incident,
    IncidentReport,
    ShiftHandoffNote,
    MaintenanceRequest,
    CorrectiveActionPlan,
    SupplierQuestionnaire,
)

# ── Domain agents ─────────────────────────────────────────────────────────────
import agents.quality_agent            as quality_agent
import agents.throughput_agent         as throughput_agent
import agents.maintenance_agent        as maintenance_agent
import agents.supplier_agent           as supplier_agent
import agents.safety_agent             as safety_agent
import agents.rca_agent                as rca_agent

# ── Action / document agents ──────────────────────────────────────────────────
import agents.shift_handoff_agent      as shift_handoff_agent
import agents.maintenance_request_agent as maintenance_request_agent
import agents.corrective_action_agent  as corrective_action_agent
import agents.supplier_questions_agent as supplier_questions_agent


# ── Graph state ───────────────────────────────────────────────────────────────

class GraphState(TypedDict):
    # Input — never mutated after START
    incident: dict

    # Orchestrator output
    agents_to_run: List[str]

    # Domain agent outputs — Annotated[List, add] merges parallel writes safely
    findings: Annotated[List[dict], add]

    # RCA output
    report: Optional[dict]

    # Post-RCA document outputs
    shift_handoff:         Optional[dict]
    maintenance_request:   Optional[dict]
    corrective_action_plan: Optional[dict]
    supplier_questionnaire: Optional[dict]

    error: Optional[str]


# ── Orchestrator ──────────────────────────────────────────────────────────────

_ORCHESTRATOR_SYSTEM = """You are the manufacturing operations incident orchestrator.

Given an incident description, decide which specialist analysis agents to invoke.
Available agents: quality, throughput, maintenance, supplier, safety

Rules:
- ALWAYS include throughput for output drops, slow production, line stops
- ALWAYS include quality for defects, rejects, out-of-spec, defect spike
- ALWAYS include maintenance for equipment issues, breakdowns, downtime
- ALWAYS include supplier for delivery delays, material shortages, supplier failures
- ALWAYS include safety for injuries, near-misses, unsafe conditions
- When uncertain about a category, include it (false negatives are worse)
- Examples:
    "output dropped on Line B"      → throughput, maintenance, quality
    "defect spike"                  → quality, maintenance, supplier
    "missed supplier delivery"      → supplier, throughput

Return ONLY a JSON object: {"agents": ["quality", "throughput", ...]}
"""


def orchestrator_node(state: GraphState) -> Dict[str, Any]:
    incident_dict = state["incident"]
    description = incident_dict.get("description", "")
    line_id = incident_dict.get("line_id", "")

    llm = config.get_llm(temperature=0.0)
    response = llm.invoke([
        SystemMessage(content=_ORCHESTRATOR_SYSTEM),
        HumanMessage(content=f"Incident: {description}\nLine: {line_id}"),
    ])

    raw = response.content.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]+?)```", raw, flags=re.IGNORECASE)
    if m:
        raw = m.group(1)

    try:
        data = json.loads(raw)
        agents_to_run = data.get("agents", ["quality", "throughput", "maintenance"])
    except json.JSONDecodeError:
        agents_to_run = ["quality", "throughput", "maintenance"]

    return {"agents_to_run": agents_to_run}


# ── Domain agent nodes ────────────────────────────────────────────────────────

def _make_domain_node(agent_key: str, agent_module):
    def node(state: GraphState) -> Dict[str, Any]:
        if agent_key not in state.get("agents_to_run", []):
            return {}  # Skipped — return empty dict; parallel superstep merge is safe

        incident = Incident(**state["incident"])
        try:
            finding: AgentFinding = agent_module.run(incident)
        except Exception as exc:
            finding = AgentFinding(
                agent_name=f"{agent_key.capitalize()}Agent",
                domain=agent_key,
                analysis_summary=f"Agent error: {exc}",
            )
        return {"findings": [finding.model_dump()]}

    node.__name__ = f"{agent_key}_node"
    return node


quality_node     = _make_domain_node("quality",     quality_agent)
throughput_node  = _make_domain_node("throughput",  throughput_agent)
maintenance_node = _make_domain_node("maintenance", maintenance_agent)
supplier_node    = _make_domain_node("supplier",    supplier_agent)
safety_node      = _make_domain_node("safety",      safety_agent)


# ── RCA node ──────────────────────────────────────────────────────────────────

def rca_node(state: GraphState) -> Dict[str, Any]:
    incident = Incident(**state["incident"])
    findings = [AgentFinding(**f) for f in state.get("findings", [])]
    try:
        report: IncidentReport = rca_agent.run(incident, findings)
        return {"report": report.model_dump()}
    except Exception as exc:
        return {"error": str(exc)}


# ── Post-RCA document nodes (run in parallel after RCA) ───────────────────────

def shift_handoff_node(state: GraphState) -> Dict[str, Any]:
    if not state.get("report"):
        return {}
    try:
        incident = Incident(**state["incident"])
        report   = IncidentReport(**state["report"])
        note: ShiftHandoffNote = shift_handoff_agent.run(incident, report)
        return {"shift_handoff": note.model_dump()}
    except Exception as exc:
        return {"shift_handoff": {"error": str(exc), "incident_id": state["incident"].get("id", "")}}


def maintenance_request_node(state: GraphState) -> Dict[str, Any]:
    if not state.get("report"):
        return {}
    try:
        incident = Incident(**state["incident"])
        report   = IncidentReport(**state["report"])
        findings = [AgentFinding(**f) for f in state.get("findings", [])]
        wo: MaintenanceRequest = maintenance_request_agent.run(incident, report, findings)
        return {"maintenance_request": wo.model_dump()}
    except Exception as exc:
        return {"maintenance_request": {"error": str(exc)}}


def corrective_action_node(state: GraphState) -> Dict[str, Any]:
    if not state.get("report"):
        return {}
    try:
        incident = Incident(**state["incident"])
        report   = IncidentReport(**state["report"])
        cap: CorrectiveActionPlan = corrective_action_agent.run(incident, report)
        return {"corrective_action_plan": cap.model_dump()}
    except Exception as exc:
        return {"corrective_action_plan": {"error": str(exc)}}


def supplier_questions_node(state: GraphState) -> Dict[str, Any]:
    if not state.get("report"):
        return {}
    # Skip if supplier agent wasn't invoked
    if "supplier" not in state.get("agents_to_run", []):
        return {}
    try:
        incident = Incident(**state["incident"])
        report   = IncidentReport(**state["report"])
        findings = [AgentFinding(**f) for f in state.get("findings", [])]
        result: SupplierQuestionnaire | None = supplier_questions_agent.run(incident, report, findings)
        if result is None:
            return {}
        return {"supplier_questionnaire": result.model_dump()}
    except Exception as exc:
        return {"supplier_questionnaire": {"error": str(exc)}}


# ── Routing ───────────────────────────────────────────────────────────────────

def route_after_orchestrator(state: GraphState) -> List[str]:
    """Fan out to selected domain agents in parallel."""
    valid = {"quality", "throughput", "maintenance", "supplier", "safety"}
    selected = [a for a in state.get("agents_to_run", []) if a in valid]
    return selected or ["throughput"]


# ── Graph assembly ────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    g = StateGraph(GraphState)

    # ── Nodes ──────────────────────────────────────────────────────────────────
    g.add_node("orchestrator",        orchestrator_node)
    # Domain
    g.add_node("quality",             quality_node)
    g.add_node("throughput",          throughput_node)
    g.add_node("maintenance",         maintenance_node)
    g.add_node("supplier",            supplier_node)
    g.add_node("safety",              safety_node)
    # RCA
    g.add_node("rca",                 rca_node)
    # Post-RCA documents (node names must not match GraphState keys — LangGraph restriction)
    g.add_node("doc_shift_handoff",       shift_handoff_node)
    g.add_node("doc_maintenance_request", maintenance_request_node)
    g.add_node("doc_corrective_action",   corrective_action_node)
    g.add_node("doc_supplier_questions",  supplier_questions_node)

    # ── Edges ──────────────────────────────────────────────────────────────────
    g.add_edge(START, "orchestrator")

    # Parallel fan-out to domain agents
    g.add_conditional_edges(
        "orchestrator",
        route_after_orchestrator,
        {
            "quality":     "quality",
            "throughput":  "throughput",
            "maintenance": "maintenance",
            "supplier":    "supplier",
            "safety":      "safety",
        },
    )

    # All domain agents converge into RCA
    for agent in ["quality", "throughput", "maintenance", "supplier", "safety"]:
        g.add_edge(agent, "rca")

    # RCA fans out to 4 parallel document agents
    g.add_edge("rca", "doc_shift_handoff")
    g.add_edge("rca", "doc_maintenance_request")
    g.add_edge("rca", "doc_corrective_action")
    g.add_edge("rca", "doc_supplier_questions")

    # All document agents converge to END
    for node in [
        "doc_shift_handoff",
        "doc_maintenance_request",
        "doc_corrective_action",
        "doc_supplier_questions",
    ]:
        g.add_edge(node, END)

    return g.compile()


# ── Public result container ───────────────────────────────────────────────────

from dataclasses import dataclass, field


@dataclass
class FullAnalysisResult:
    report:                 IncidentReport
    shift_handoff:          ShiftHandoffNote          | None = None
    maintenance_request:    MaintenanceRequest         | None = None
    corrective_action_plan: CorrectiveActionPlan       | None = None
    supplier_questionnaire: SupplierQuestionnaire      | None = None


# ── Public entry point ────────────────────────────────────────────────────────

def run_incident(incident: Incident) -> FullAnalysisResult:
    """
    Run the full multi-agent graph for an incident.
    Returns a FullAnalysisResult containing the RCA report and all action documents.
    """
    graph = build_graph()

    initial_state: GraphState = {
        "incident":              incident.model_dump(),
        "agents_to_run":         [],
        "findings":              [],
        "report":                None,
        "shift_handoff":         None,
        "maintenance_request":   None,
        "corrective_action_plan": None,
        "supplier_questionnaire": None,
        "error":                 None,
    }

    final_state = graph.invoke(initial_state)

    if final_state.get("error"):
        raise RuntimeError(f"Graph error: {final_state['error']}")

    report_dict = final_state.get("report")
    if not report_dict:
        raise RuntimeError("RCA node produced no report.")

    def _safe(cls, key):
        d = final_state.get(key)
        if not d or "error" in d:
            return None
        try:
            return cls(**d)
        except Exception:
            return None

    return FullAnalysisResult(
        report=IncidentReport(**report_dict),
        shift_handoff=_safe(ShiftHandoffNote, "shift_handoff"),
        maintenance_request=_safe(MaintenanceRequest, "maintenance_request"),
        corrective_action_plan=_safe(CorrectiveActionPlan, "corrective_action_plan"),
        supplier_questionnaire=_safe(SupplierQuestionnaire, "supplier_questionnaire"),
    )

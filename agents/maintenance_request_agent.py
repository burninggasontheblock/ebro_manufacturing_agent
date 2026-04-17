"""
Maintenance Request Agent.

Generates a formal maintenance work order from the incident findings,
including equipment IDs, problem descriptions, required work, parts, and safety notes.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta

from langchain_core.messages import HumanMessage, SystemMessage

import config
from models.schemas import (
    AgentFinding,
    Incident,
    IncidentReport,
    MaintenanceRequest,
    MaintenanceRequestItem,
)
from rag.knowledge_base import retrieve_as_text


_SYSTEM = """You are a maintenance engineering coordinator for a manufacturing facility.

Given an incident report and maintenance findings, create a formal maintenance work order.

OUTPUT FORMAT (strict JSON):
{
  "priority": "CRITICAL | HIGH | MEDIUM | LOW",
  "required_completion_date": "<ISO date string>",
  "special_instructions": "<any LOTO, permit-to-work, or coordination notes>",
  "approvals_required": ["<role, e.g. 'EHS sign-off required before hot work'>", ...],
  "work_items": [
    {
      "item_number": 1,
      "equipment_id": "<e.g. CONV-LB-MAIN>",
      "problem_description": "<observed fault>",
      "work_requested": "<specific task to be performed>",
      "parts_required": ["<part number + description, e.g. 'BRG-6205-2RS x2 — deep-groove bearing'>"],
      "estimated_duration_hours": 2.5,
      "safety_precautions": ["<e.g. 'LOTO required — procedure SAFE-LOTO-001'>"]
    },
    ...
  ]
}

RULES:
- Priority CRITICAL = line stopped or imminent safety risk; HIGH = line degraded; MEDIUM = planned window
- Include a separate work_item for each distinct piece of equipment requiring attention
- parts_required must include part numbers where known from the maintenance history
- safety_precautions must reference procedure codes (LOTO, PPE, etc.) where applicable
- estimated_duration_hours must be realistic for the task described
- Return ONLY the JSON — no preamble
"""


def run(incident: Incident, report: IncidentReport, findings: list[AgentFinding]) -> MaintenanceRequest:
    llm = config.get_llm(temperature=0.0)

    # Pull maintenance-specific findings
    maint_findings = [f for f in findings if f.domain == "maintenance"]
    maint_text = "\n\n".join(f.analysis_summary for f in maint_findings) or "No maintenance findings."

    # RAG for parts / procedures
    rag_ctx = retrieve_as_text(
        f"maintenance work order equipment {incident.line_id} parts procedure",
        domain="maintenance",
        k=3,
    )

    primary = report.root_cause_hypotheses[0] if report.root_cause_hypotheses else None

    human = f"""
INCIDENT: {incident.id}
Description: {incident.description}
Plant: {incident.plant_id} | Line: {incident.line_id or 'N/A'}
Timestamp: {incident.timestamp or datetime.now().strftime('%Y-%m-%d %H:%M')}

PRIMARY ROOT CAUSE:
{primary.hypothesis if primary else 'Under investigation'}

MAINTENANCE AGENT FINDINGS:
{maint_text}

RECOMMENDED IMMEDIATE ACTIONS:
{chr(10).join(f'  • {a}' for a in report.recommended_immediate_actions) or '  None'}

RELEVANT KNOWLEDGE BASE (parts, procedures, history):
{rag_ctx}

Create the maintenance work order JSON now.
"""

    response = llm.invoke([
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=human),
    ])

    return _parse(response.content, incident, report)


def _parse(raw: str, incident: Incident, report: IncidentReport) -> MaintenanceRequest:
    m = re.search(r"```(?:json)?\s*([\s\S]+?)```", raw)
    text = m.group(1) if m else raw
    brace = text.find("{")
    text = text[brace:] if brace != -1 else text

    try:
        dec = json.JSONDecoder()
        data, _ = dec.raw_decode(text.strip())
    except json.JSONDecodeError:
        return MaintenanceRequest(
            wo_number=f"WO-AUTO-{incident.id}",
            incident_id=incident.id,
            priority="HIGH",
            line_id=incident.line_id or "",
            plant_id=incident.plant_id,
            raw_request=raw,
        )

    work_items = []
    for item in data.get("work_items", []):
        work_items.append(MaintenanceRequestItem(
            item_number=item.get("item_number", len(work_items) + 1),
            equipment_id=item.get("equipment_id", "UNKNOWN"),
            problem_description=item.get("problem_description", ""),
            work_requested=item.get("work_requested", ""),
            parts_required=item.get("parts_required", []),
            estimated_duration_hours=item.get("estimated_duration_hours"),
            safety_precautions=item.get("safety_precautions", []),
        ))

    today = datetime.now()
    priority = data.get("priority", "HIGH")
    # Auto-compute WO number
    wo_num = f"WO-{incident.plant_id}-{today.strftime('%Y%m%d')}-{incident.id.split('-')[-1]}"

    # Deadline: CRITICAL same day, HIGH +1d, MEDIUM +3d, LOW +7d
    deadline_delta = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 3, "LOW": 7}.get(priority, 1)
    required_by = (today + timedelta(days=deadline_delta)).strftime("%Y-%m-%d")

    return MaintenanceRequest(
        wo_number=wo_num,
        incident_id=incident.id,
        priority=priority,
        requested_by="Manufacturing AI System",
        requested_date=today.strftime("%Y-%m-%d %H:%M"),
        required_completion_date=data.get("required_completion_date", required_by),
        line_id=incident.line_id or "",
        plant_id=incident.plant_id,
        work_items=work_items,
        special_instructions=data.get("special_instructions", ""),
        approvals_required=data.get("approvals_required", []),
        raw_request=raw,
    )

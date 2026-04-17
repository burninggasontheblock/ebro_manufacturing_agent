"""
Shift Handoff Note Agent.

Drafts a structured shift handoff note from the incident and RCA report so the
outgoing supervisor can brief the incoming shift clearly and completely.
"""
from __future__ import annotations

import json
import re
from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage

import config
from models.schemas import Incident, IncidentReport, ShiftHandoffNote


_SYSTEM = """You are a manufacturing shift supervisor assistant.

Given an incident and its root-cause analysis, draft a professional shift handoff note
that the outgoing supervisor will hand to the incoming shift.

OUTPUT FORMAT (strict JSON):
{
  "situation_summary": "<2-3 sentences: what happened, when, what is the current state>",
  "actions_completed": [
    "<specific action already taken, e.g. 'Belt tension re-adjusted at 08:45'>",
    ...
  ],
  "pending_actions": [
    "<action still required by next shift, e.g. 'WO-LB-1201 bearing replacement — parts in cage'>",
    ...
  ],
  "watch_items": [
    "<metric or condition to monitor, e.g. 'Vibration C-14: check every 30 min, call maintenance >2.5mm/s'>",
    ...
  ],
  "do_not_restart_until": [
    "<condition that must be confirmed before resuming full production>",
    ...
  ],
  "escalation_contacts": [
    "<name / role / contact, e.g. 'Mike Torres — Maintenance Lead — ext. 4421'>",
    ...
  ]
}

RULES:
- Be specific: use equipment IDs, metric values, times, and names where known
- do_not_restart_until must be concrete and verifiable (not vague)
- watch_items must have clear thresholds and escalation triggers
- pending_actions must reference work order IDs where applicable
- Return ONLY the JSON — no preamble
"""


def run(incident: Incident, report: IncidentReport) -> ShiftHandoffNote:
    llm = config.get_llm(temperature=0.1)

    primary = report.root_cause_hypotheses[0] if report.root_cause_hypotheses else None

    human = f"""
INCIDENT: {incident.id}
Description: {incident.description}
Plant: {incident.plant_id} | Line: {incident.line_id or 'N/A'}
Timestamp: {incident.timestamp or datetime.now().strftime('%Y-%m-%d %H:%M')}

EXECUTIVE SUMMARY:
{report.executive_summary}

PRIMARY ROOT CAUSE:
{primary.hypothesis if primary else 'Under investigation'}
Confidence: {primary.confidence_label if primary else 'N/A'} ({primary.confidence:.0%} if primary else '')

IMMEDIATE ACTIONS REQUIRED:
{chr(10).join(f'  • {a}' for a in report.recommended_immediate_actions) or '  None documented'}

AGENTS INVOKED: {', '.join(report.agents_invoked)}

Draft the shift handoff note JSON now.
"""

    response = llm.invoke([
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=human),
    ])

    return _parse(response.content, incident)


def _parse(raw: str, incident: Incident) -> ShiftHandoffNote:
    m = re.search(r"```(?:json)?\s*([\s\S]+?)```", raw)
    text = m.group(1) if m else raw
    brace = text.find("{")
    text = text[brace:] if brace != -1 else text

    try:
        dec = json.JSONDecoder()
        data, _ = dec.raw_decode(text.strip())
    except json.JSONDecodeError:
        return ShiftHandoffNote(incident_id=incident.id, raw_note=raw)

    return ShiftHandoffNote(
        incident_id=incident.id,
        situation_summary=data.get("situation_summary", ""),
        actions_completed=data.get("actions_completed", []),
        pending_actions=data.get("pending_actions", []),
        watch_items=data.get("watch_items", []),
        do_not_restart_until=data.get("do_not_restart_until", []),
        escalation_contacts=data.get("escalation_contacts", []),
        raw_note=raw,
    )

"""
Corrective Action Plan Agent.

Produces a structured CAP (Corrective Action Plan) with IMMEDIATE, SHORT_TERM,
LONG_TERM and PREVENTIVE actions, each with an owner, due date, and success criteria.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta

from langchain_core.messages import HumanMessage, SystemMessage

import config
from models.schemas import (
    CorrectiveActionItem,
    CorrectiveActionPlan,
    Incident,
    IncidentReport,
)
from rag.knowledge_base import retrieve_as_text


_SYSTEM = """You are a continuous-improvement engineer at a manufacturing facility.

Given an incident report and root-cause analysis, produce a Corrective Action Plan (CAP).
The CAP must address the primary root cause AND prevent recurrence.

OUTPUT FORMAT (strict JSON):
{
  "problem_statement": "<one paragraph: what happened, root cause, impact>",
  "root_cause_addressed": "<single sentence primary root cause>",
  "review_date": "<ISO date — 30 days from today>",
  "approver": "<role, e.g. 'Plant Manager'>",
  "effectiveness_kpis": [
    "<measurable KPI, e.g. 'Line B throughput ≥ 380 uph for 5 consecutive days'>",
    ...
  ],
  "actions": [
    {
      "action_number": 1,
      "category": "IMMEDIATE",
      "action": "<specific action>",
      "owner": "<role or name>",
      "due_date": "<ISO date>",
      "success_criteria": "<how we know it is done>"
    },
    ...
  ]
}

CATEGORY DEFINITIONS:
  IMMEDIATE   — within 24 hours; stop the bleeding (contains, quarantines, restores)
  SHORT_TERM  — within 2 weeks; fixes the root cause
  LONG_TERM   — within 90 days; systemic / engineering solution
  PREVENTIVE  — ongoing or recurring; prevents recurrence across similar assets/lines

RULES:
- Minimum 2 actions per category
- Each action must have a specific, named owner (role is fine: 'Maintenance Lead', 'QA Manager')
- success_criteria must be measurable and verifiable — not 'done' or 'completed'
- effectiveness_kpis must be numeric with thresholds and time horizons
- Return ONLY the JSON — no preamble
"""


def run(incident: Incident, report: IncidentReport) -> CorrectiveActionPlan:
    llm = config.get_llm(temperature=0.1)

    # Retrieve prior CAP / corrective action patterns from knowledge base
    rag_ctx = retrieve_as_text(
        f"corrective action plan {incident.line_id} root cause recurrence prevention",
        domain="rca",
        k=3,
    )

    hypotheses_text = "\n".join(
        f"  #{h.rank} ({h.confidence_label} {h.confidence:.0%}): {h.hypothesis}"
        for h in report.root_cause_hypotheses[:3]
    )

    human = f"""
INCIDENT: {incident.id}
Description: {incident.description}
Plant: {incident.plant_id} | Line: {incident.line_id or 'N/A'}
Today's date: {datetime.now().strftime('%Y-%m-%d')}

ROOT-CAUSE HYPOTHESES:
{hypotheses_text or '  Under investigation'}

EXECUTIVE SUMMARY:
{report.executive_summary}

IMMEDIATE ACTIONS ALREADY IDENTIFIED:
{chr(10).join(f'  • {a}' for a in report.recommended_immediate_actions) or '  None'}

PREVENTIVE ACTIONS ALREADY IDENTIFIED:
{chr(10).join(f'  • {a}' for a in report.recommended_preventive_actions) or '  None'}

RELEVANT PRIOR INCIDENTS & STANDARDS:
{rag_ctx}

Produce the full Corrective Action Plan JSON now.
"""

    response = llm.invoke([
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=human),
    ])

    return _parse(response.content, incident, report)


def _parse(raw: str, incident: Incident, report: IncidentReport) -> CorrectiveActionPlan:
    m = re.search(r"```(?:json)?\s*([\s\S]+?)```", raw)
    text = m.group(1) if m else raw
    brace = text.find("{")
    text = text[brace:] if brace != -1 else text

    try:
        dec = json.JSONDecoder()
        data, _ = dec.raw_decode(text.strip())
    except json.JSONDecodeError:
        primary = report.root_cause_hypotheses[0].hypothesis if report.root_cause_hypotheses else "Unknown"
        return CorrectiveActionPlan(
            cap_id=f"CAP-{incident.id}",
            incident_id=incident.id,
            root_cause_addressed=primary,
            raw_plan=raw,
        )

    actions = []
    for a in data.get("actions", []):
        actions.append(CorrectiveActionItem(
            action_number=a.get("action_number", len(actions) + 1),
            category=a.get("category", "SHORT_TERM"),
            action=a.get("action", ""),
            owner=a.get("owner", "TBD"),
            due_date=a.get("due_date", ""),
            success_criteria=a.get("success_criteria", ""),
            status="OPEN",
        ))

    today = datetime.now()
    cap_id = f"CAP-{incident.plant_id}-{today.strftime('%Y%m%d')}-{incident.id.split('-')[-1]}"
    review_date = data.get("review_date", (today + timedelta(days=30)).strftime("%Y-%m-%d"))

    return CorrectiveActionPlan(
        cap_id=cap_id,
        incident_id=incident.id,
        root_cause_addressed=data.get("root_cause_addressed", ""),
        problem_statement=data.get("problem_statement", ""),
        actions=actions,
        effectiveness_kpis=data.get("effectiveness_kpis", []),
        review_date=review_date,
        approver=data.get("approver", "Plant Manager"),
        raw_plan=raw,
    )

"""
Supplier Questions Agent.

Generates a structured supplier inquiry questionnaire when a supplier delay,
quality non-conformance, or supply-chain issue is involved in the incident.
Covers root cause, timeline, prevention, and accountability questions.
"""
from __future__ import annotations

import json
import re
from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage

import config
from models.schemas import (
    AgentFinding,
    Incident,
    IncidentReport,
    SupplierQuestion,
    SupplierQuestionnaire,
)
from rag.knowledge_base import retrieve_as_text


_SYSTEM = """You are a supplier quality and procurement manager at a manufacturing facility.

Given an incident involving a supplier issue, generate a structured set of questions
to send to the supplier. The questions should drive accountability and corrective action.

OUTPUT FORMAT (strict JSON):
{
  "supplier_name": "<supplier name>",
  "po_references": ["<PO-XXXX>", ...],
  "urgency": "IMMEDIATE | STANDARD",
  "escalation_note": "<escalation statement if performance is chronic, else empty string>",
  "requested_deliverables": [
    "<document or data to be provided alongside answers, e.g. 'Corrective action plan (8D format)'>",
    ...
  ],
  "questions": [
    {
      "question_number": 1,
      "category": "ROOT_CAUSE | TIMELINE | PREVENTION | COMPENSATION | COMMUNICATION",
      "question": "<specific question>",
      "context": "<why this question is being asked — reference incident facts>",
      "expected_response_format": "<e.g. 'Written 5-Why analysis', 'Date and time table', 'Yes/No + explanation'>"
    },
    ...
  ]
}

CATEGORY DEFINITIONS:
  ROOT_CAUSE    — What caused the failure? What was the supplier's internal process failure?
  TIMELINE      — When did they know? What notifications were sent? What is the recovery schedule?
  PREVENTION    — What systemic changes will prevent recurrence?
  COMPENSATION  — What expediting, cost relief, or premium freight will the supplier provide?
  COMMUNICATION — Was early warning given? What is their escalation process?

RULES:
- Include at least 2 questions per category that is relevant to the incident
- Context must reference specific facts from the incident (PO numbers, dates, quantities, impacts)
- Questions must be direct and professional — not adversarial, but firm
- urgency = IMMEDIATE if there is an ongoing line stop or delivery still outstanding
- If the supplier has prior performance issues, include an escalation_note
- requested_deliverables should match the seriousness of the incident
- Return ONLY the JSON — no preamble
"""


def run(incident: Incident, report: IncidentReport, findings: list[AgentFinding]) -> SupplierQuestionnaire | None:
    """
    Returns None if no supplier issue was identified (so the graph can skip cleanly).
    """
    # Only run if supplier agent was invoked
    supplier_findings = [f for f in findings if f.domain == "supplier"]
    if not supplier_findings:
        return None

    llm = config.get_llm(temperature=0.1)

    # RAG: prior supplier incidents, SLA standards
    rag_ctx = retrieve_as_text(
        f"supplier delivery failure corrective action {incident.description}",
        domain="supplier",
        k=4,
    )

    supplier_text = "\n\n".join(f.analysis_summary for f in supplier_findings)

    human = f"""
INCIDENT: {incident.id}
Description: {incident.description}
Plant: {incident.plant_id} | Line: {incident.line_id or 'N/A'}
Timestamp: {incident.timestamp or datetime.now().strftime('%Y-%m-%d %H:%M')}

EXECUTIVE SUMMARY:
{report.executive_summary}

SUPPLIER AGENT FINDINGS:
{supplier_text}

RELEVANT SUPPLIER HISTORY & SLA STANDARDS:
{rag_ctx}

Generate the supplier questionnaire JSON now.
"""

    response = llm.invoke([
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=human),
    ])

    return _parse(response.content, incident)


def _parse(raw: str, incident: Incident) -> SupplierQuestionnaire:
    m = re.search(r"```(?:json)?\s*([\s\S]+?)```", raw)
    text = m.group(1) if m else raw
    brace = text.find("{")
    text = text[brace:] if brace != -1 else text

    try:
        dec = json.JSONDecoder()
        data, _ = dec.raw_decode(text.strip())
    except json.JSONDecodeError:
        return SupplierQuestionnaire(
            supplier_name="Unknown",
            incident_id=incident.id,
            urgency="STANDARD",
            raw_questionnaire=raw,
        )

    questions = []
    for q in data.get("questions", []):
        questions.append(SupplierQuestion(
            question_number=q.get("question_number", len(questions) + 1),
            category=q.get("category", "ROOT_CAUSE"),
            question=q.get("question", ""),
            context=q.get("context", ""),
            expected_response_format=q.get("expected_response_format", ""),
        ))

    return SupplierQuestionnaire(
        supplier_name=data.get("supplier_name", "Unknown"),
        incident_id=incident.id,
        po_references=data.get("po_references", []),
        urgency=data.get("urgency", "STANDARD"),
        questions=questions,
        requested_deliverables=data.get("requested_deliverables", []),
        escalation_note=data.get("escalation_note", ""),
        raw_questionnaire=raw,
    )

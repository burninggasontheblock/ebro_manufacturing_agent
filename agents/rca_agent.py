"""
Root Cause Analysis Synthesizer Agent.

Takes all domain agent findings and produces ranked root-cause hypotheses
with confidence scores, supporting evidence, and recommended actions.
"""
from __future__ import annotations

import json
import re
from typing import Any, List

from langchain_core.messages import HumanMessage, SystemMessage

import config
from models.schemas import AgentFinding, Incident, IncidentReport, RootCauseHypothesis
from tools.rag_tools import make_rag_tool
from rag.knowledge_base import retrieve_as_text


_RCA_SYSTEM = """You are the Root Cause Analysis Synthesizer for a manufacturing operations AI system.

You will receive:
1. An incident description (plant, line, problem statement)
2. Findings from multiple domain specialist agents (quality, throughput, maintenance,
   supplier, safety) — each with data-driven analysis

YOUR TASK: Synthesise these findings into a structured root-cause analysis report.

OUTPUT FORMAT (strict JSON):
{
  "executive_summary": "<2-3 sentence plain-English summary for the operations manager>",
  "hypotheses": [
    {
      "rank": 1,
      "hypothesis": "<concise root cause statement>",
      "confidence": 0.85,
      "confidence_label": "HIGH",
      "supporting_evidence": ["<evidence 1>", "<evidence 2>", ...],
      "contributing_agents": ["MaintenanceAgent", "ThroughputAgent"],
      "recommended_actions": ["<action 1>", "<action 2>", ...],
      "estimated_resolution_time": "<e.g. 2-4 hours>"
    },
    ...
  ],
  "recommended_immediate_actions": ["<action 1>", "<action 2>", ...],
  "recommended_preventive_actions": ["<action 1>", "<action 2>", ...],
  "estimated_production_impact": "<e.g. ~$34,000 revenue at risk per 8-hour shift>",
  "confidence_note": "<explanation of confidence methodology>"
}

CONFIDENCE SCORING GUIDE:
  HIGH   (0.75–1.00): Multiple independent data points corroborate, prior incident match,
                       sensor data or maintenance record directly supports hypothesis
  MEDIUM (0.45–0.74): Plausible, some supporting data but not definitive, no prior incident match
  LOW    (0.10–0.44): Possible but speculative, limited evidence, requires investigation to confirm

RULES:
- Rank hypotheses from most to least likely (rank 1 = primary root cause)
- Include 2-4 hypotheses minimum (shows completeness)
- Each hypothesis must cite specific evidence (metric values, document IDs, dates)
- Do NOT repeat the agent findings verbatim — synthesise and elevate insights
- Immediate actions must be prioritised by urgency
- Return ONLY the JSON object — no preamble or explanation
"""


def _llm_content_to_str(content: Any) -> str:
    """Normalize AIMessage.content (str or list of blocks) to a single string."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                t = block.get("text")
                if isinstance(t, str):
                    parts.append(t)
            else:
                tx = getattr(block, "text", None)
                if isinstance(tx, str):
                    parts.append(tx)
        return "".join(parts)
    return str(content)


def run(
    incident: Incident,
    findings: List[AgentFinding],
) -> IncidentReport:
    """Synthesise domain findings into a structured root-cause analysis report."""

    # Large structured JSON; Anthropic default max_tokens (1024) truncates mid-object → parse errors
    llm = config.get_llm(temperature=0.0, max_tokens=8192)

    # Build context from all agent findings
    findings_text = _format_findings(findings)

    # Augment with a final broad RAG search
    rag_context = retrieve_as_text(
        query=incident.description,
        domain="rca",
        k=3,
    )

    human_content = f"""
INCIDENT:
  ID:          {incident.id}
  Description: {incident.description}
  Plant:       {incident.plant_id}
  Line:        {incident.line_id or 'N/A'}
  Timestamp:   {incident.timestamp or 'N/A'}

DOMAIN AGENT FINDINGS:
{findings_text}

ADDITIONAL KNOWLEDGE BASE CONTEXT:
{rag_context}

Synthesise the above into a root-cause analysis report following the JSON format specified.
"""

    response = llm.invoke([
        SystemMessage(content=_RCA_SYSTEM),
        HumanMessage(content=human_content),
    ])

    return _parse_rca_response(_llm_content_to_str(response.content), incident, findings)


def _format_findings(findings: List[AgentFinding]) -> str:
    parts = []
    for f in findings:
        parts.append(
            f"── {f.agent_name} ({f.domain.upper()}) ──\n"
            f"{f.analysis_summary}\n"
            f"Tools used: {', '.join(f.raw_tool_outputs[:3]) if f.raw_tool_outputs else 'N/A'}"
        )
    return "\n\n".join(parts)


def _extract_json_object_string(text: str) -> str | None:
    """
    Recover JSON from LLM output — handles ```json fences, optional preamble,
    and missing closing fences (common with long replies).
    """
    s = (text or "").strip()
    if not s:
        return None

    # Cut from first markdown fence (if any) — do not require a closing ```
    open_fence = re.search(r"```(?:json)?\s*", s, flags=re.IGNORECASE)
    if open_fence:
        s = s[open_fence.end() :].strip()
    s = re.sub(r"\s*```\s*$", "", s).strip()

    brace = s.find("{")
    if brace == -1:
        return None
    return s[brace:]


def _parse_llm_json_dict(text: str) -> dict | None:
    """Parse a single JSON object from messy LLM text."""
    candidate = _extract_json_object_string(text)
    if not candidate:
        return None
    dec = json.JSONDecoder()
    cand = candidate.strip()
    try:
        obj, _ = dec.raw_decode(cand, 0)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        pass
    try:
        obj = json.loads(candidate.strip())
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        return None


def _parse_rca_response(
    raw: str,
    incident: Incident,
    findings: List[AgentFinding],
) -> IncidentReport:
    """Parse LLM JSON output into an IncidentReport, with graceful fallback."""
    data = _parse_llm_json_dict(raw)

    if data is None:
        try:
            data = json.loads(raw.strip())
        except json.JSONDecodeError:
            data = None

    if data is None:
        # Fallback: wrap raw text as single low-confidence hypothesis
        snippet = (raw or "")[:2000]
        return IncidentReport(
            incident=incident,
            agents_invoked=[f.agent_name for f in findings],
            findings=findings,
            root_cause_hypotheses=[
                RootCauseHypothesis(
                    rank=1,
                    hypothesis="Unable to parse structured hypotheses — see executive summary.",
                    confidence=0.3,
                    confidence_label="LOW",
                    supporting_evidence=[snippet],
                    contributing_agents=[f.agent_name for f in findings],
                    recommended_actions=["Manual investigation required"],
                )
            ],
            executive_summary=snippet,
            confidence_note="JSON parsing failed — raw LLM output shown.",
        )

    hypotheses = []
    for h in data.get("hypotheses", []):
        label = h.get("confidence_label", "")
        conf = float(h.get("confidence", 0.5))
        if not label:
            if conf >= 0.75:
                label = "HIGH"
            elif conf >= 0.45:
                label = "MEDIUM"
            else:
                label = "LOW"

        hypotheses.append(RootCauseHypothesis(
            rank=h.get("rank", 1),
            hypothesis=h.get("hypothesis", ""),
            confidence=conf,
            confidence_label=label,
            supporting_evidence=h.get("supporting_evidence", []),
            contributing_agents=h.get("contributing_agents", []),
            recommended_actions=h.get("recommended_actions", []),
            estimated_resolution_time=h.get("estimated_resolution_time"),
        ))

    hypotheses.sort(key=lambda x: x.rank)

    return IncidentReport(
        incident=incident,
        agents_invoked=[f.agent_name for f in findings],
        findings=findings,
        root_cause_hypotheses=hypotheses,
        executive_summary=data.get("executive_summary", ""),
        recommended_immediate_actions=data.get("recommended_immediate_actions", []),
        recommended_preventive_actions=data.get("recommended_preventive_actions", []),
        estimated_production_impact=data.get("estimated_production_impact", ""),
        confidence_note=data.get("confidence_note", ""),
    )

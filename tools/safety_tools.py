"""
Safety domain tools — safety incident history, hazard status, compliance checks.
"""
from langchain_core.tools import tool


_SAFETY_HISTORY = {
    "LINE-B": [
        {"date": "2024-10-11", "type": "Near-Miss",  "description": "Conveyor pinch-point — operator bypassed LOTO at transfer station C-14"},
        {"date": "2024-07-03", "type": "Near-Miss",  "description": "Pinch point near idler roller during belt tracking adjustment"},
        {"date": "2023-09-22", "type": "Near-Miss",  "description": "Conveyor jam clearance without LOTO — similar to 2024-10-11 event"},
        {"date": "2023-05-14", "type": "First Aid",  "description": "Minor laceration from sharp metal edge — inadequate PPE"},
    ],
    "LINE-A": [
        {"date": "2024-11-20", "type": "Near-Miss", "description": "Ergonomic — repetitive strain report, workstation height adjusted"},
    ],
    "WAREHOUSE": [
        {"date": "2025-01-08", "type": "Near-Miss", "description": "Forklift/pedestrian conflict in Bay 3 — near collision"},
    ],
}

_HAZARD_STATUS = {
    "LINE-B": {
        "pinch_point_guards": "INSTALLED (Oct 2024) — interlock functional",
        "loto_compliance_pct": 97,
        "ppe_compliance_pct": 99,
        "emergency_stop_tested": "2025-02-15 — PASS",
        "open_safety_actions": ["Engineering review of guard design — in progress (due Q2 2025)"],
    },
    "LINE-A": {
        "pinch_point_guards": "Installed and compliant",
        "loto_compliance_pct": 99,
        "ppe_compliance_pct": 100,
        "emergency_stop_tested": "2025-03-01 — PASS",
        "open_safety_actions": [],
    },
}


@tool
def get_safety_incident_history(area: str, months: int = 24) -> str:
    """
    Retrieve safety incident history for a plant area or production line.

    Args:
        area:   Area identifier (e.g. 'LINE-B', 'LINE-A', 'WAREHOUSE')
        months: Look-back window in months (default 24)

    Returns:
        Plain text list of safety incidents with dates, types, and descriptions.
    """
    history = _SAFETY_HISTORY.get(area.upper(), [])
    if not history:
        return f"No safety incidents recorded for {area} in the last {months} months."

    near_miss = [e for e in history if e["type"] == "Near-Miss"]
    first_aid  = [e for e in history if e["type"] == "First Aid"]
    recordable = [e for e in history if e["type"] == "Recordable"]

    lines = [f"Safety Incident History — {area.upper()} (last {months} months)\n"]
    lines.append(f"  Summary: {len(near_miss)} near-misses, {len(first_aid)} first-aid, {len(recordable)} recordable\n")

    for e in history:
        lines.append(f"  [{e['date']}] {e['type']}: {e['description']}")

    if len(near_miss) >= 3:
        lines.append(
            f"\n  ⚠ PATTERN: {len(near_miss)} near-miss events detected. "
            "Indicates systemic hazard — engineering controls or behaviour change required."
        )
    return "\n".join(lines)


@tool
def get_hazard_status(line_id: str) -> str:
    """
    Get the current safety hazard controls and compliance status for a line.

    Args:
        line_id: Production line identifier

    Returns:
        Plain text hazard and compliance status report.
    """
    data = _HAZARD_STATUS.get(line_id.upper())
    if not data:
        return f"No hazard status data for {line_id}."

    lines = [f"Hazard & Compliance Status — {line_id.upper()}\n"]
    lines.append(f"  Pinch-point guards:        {data['pinch_point_guards']}")
    lines.append(f"  LOTO compliance:           {data['loto_compliance_pct']}%")
    lines.append(f"  PPE compliance:            {data['ppe_compliance_pct']}%")
    lines.append(f"  Emergency stop last test:  {data['emergency_stop_tested']}")
    if data["open_safety_actions"]:
        lines.append(f"\n  Open safety actions:")
        for action in data["open_safety_actions"]:
            lines.append(f"    • {action}")
    else:
        lines.append("\n  Open safety actions: None")
    return "\n".join(lines)


@tool
def assess_safety_risk(incident_description: str, line_id: str) -> str:
    """
    Assess safety risk level for a described incident and recommend immediate actions.

    Args:
        incident_description: Free-text description of the safety concern
        line_id:              Production line where the concern arose

    Returns:
        Plain text risk level and required immediate actions.
    """
    description_lower = incident_description.lower()
    risk_level = "LOW"
    actions = []

    # Keyword-based risk escalation
    if any(w in description_lower for w in ["injury", "hurt", "blood", "fracture", "burn", "chemical"]):
        risk_level = "RECORDABLE"
        actions = [
            "1. Ensure injured person receives immediate first aid / medical attention",
            "2. Notify EHS within 2 hours",
            "3. Preserve scene — do not disturb until EHS clears",
            "4. Begin 24-hour incident investigation",
        ]
    elif any(w in description_lower for w in ["loto", "bypass", "guard removed", "pinch", "near miss", "near-miss"]):
        risk_level = "NEAR-MISS"
        actions = [
            "1. Stop the operation immediately if unsafe condition persists",
            "2. Log near-miss in safety system within 24 hours",
            "3. Supervisor review and corrective action within 48 hours",
            "4. Check LOTO compliance for all Line B operators",
        ]
    elif any(w in description_lower for w in ["fire", "explosion", "toxic", "fatality", "amputation"]):
        risk_level = "CATASTROPHIC"
        actions = [
            "1. CALL EMERGENCY SERVICES IMMEDIATELY",
            "2. Activate site emergency plan",
            "3. Notify Plant Manager and VP Operations NOW",
            "4. Regulatory notification required within 1 hour",
        ]
    else:
        actions = [
            "1. Document the concern",
            "2. Review with supervisor",
            "3. Monitor for escalation",
        ]

    return (
        f"Safety Risk Assessment — {line_id.upper()}\n"
        f"  Risk Level: {risk_level}\n\n"
        f"  Recommended Actions:\n" +
        "\n".join(f"  {a}" for a in actions)
    )

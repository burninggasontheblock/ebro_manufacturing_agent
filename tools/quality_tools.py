"""
Quality domain tools — defect metrics, SPC thresholds, quality alerts.
"""
import json
import random
from langchain_core.tools import tool


# ── Simulated live data store (replace with real DB/historian calls) ──────────

_QUALITY_DATA = {
    "LINE-A": {"defect_rate_pct": 0.9, "ucl": 1.4, "avg_12mo": 0.8, "last_spike": "2024-05-22"},
    "LINE-B": {"defect_rate_pct": 4.7, "ucl": 1.9, "avg_12mo": 1.1, "last_spike": "2023-11-08"},
    "LINE-C": {"defect_rate_pct": 0.8, "ucl": 1.1, "avg_12mo": 0.6, "last_spike": "2023-06-14"},
}

_DEFECT_BREAKDOWN = {
    "LINE-B": {
        "short_shots_pct": 0.4,
        "porosity_pct": 1.8,
        "dimensional_pct": 1.2,
        "surface_finish_pct": 1.3,
        "total_pct": 4.7,
    }
}


@tool
def get_current_defect_rate(line_id: str) -> str:
    """
    Retrieve the current defect rate and SPC status for a production line.

    Args:
        line_id: Production line identifier (e.g. 'LINE-A', 'LINE-B', 'LINE-C')

    Returns:
        JSON string with defect_rate_pct, ucl, avg_12mo, spc_status.
    """
    data = _QUALITY_DATA.get(line_id.upper())
    if not data:
        return json.dumps({"error": f"No quality data for {line_id}"})

    rate = data["defect_rate_pct"]
    ucl = data["ucl"]
    if rate > 3 * ucl:
        status = "RED_ALERT — rate exceeds 3×UCL, production hold required"
    elif rate > ucl:
        status = "YELLOW_ALERT — rate exceeds UCL, QA supervisor review required"
    else:
        status = "NORMAL"

    return json.dumps({
        "line_id": line_id.upper(),
        "defect_rate_pct": rate,
        "ucl": ucl,
        "avg_12mo": data["avg_12mo"],
        "spc_status": status,
        "last_spike_date": data["last_spike"],
    }, indent=2)


@tool
def get_defect_breakdown(line_id: str) -> str:
    """
    Get breakdown of defect types by category for a production line.

    Args:
        line_id: Production line identifier

    Returns:
        JSON string with defect type percentages.
    """
    data = _DEFECT_BREAKDOWN.get(line_id.upper())
    if not data:
        return json.dumps({"message": f"No defect breakdown available for {line_id}. Rate is within normal range."})
    return json.dumps(data, indent=2)


@tool
def check_quality_thresholds(line_id: str, defect_rate: float) -> str:
    """
    Check whether a given defect rate triggers any quality threshold alerts.

    Args:
        line_id:     Production line identifier
        defect_rate: Current defect rate as a percentage (e.g. 4.7 for 4.7%)

    Returns:
        Plain text describing threshold status and required response actions.
    """
    data = _QUALITY_DATA.get(line_id.upper())
    if not data:
        return f"No threshold data for {line_id}."

    ucl = data["ucl"]
    lines = [f"Line {line_id} | Current rate: {defect_rate}% | UCL: {ucl}%"]

    if defect_rate > 3 * ucl:
        lines.append("STATUS: RED ALERT (> 3×UCL)")
        lines.append("REQUIRED ACTIONS:")
        lines.append("  1. Immediate production hold on this line")
        lines.append("  2. Quarantine last 2 hours of production")
        lines.append("  3. Notify QA Manager and Plant Manager immediately")
        lines.append("  4. Root-cause investigation must begin within 30 minutes")
    elif defect_rate > ucl:
        lines.append("STATUS: YELLOW ALERT (> UCL)")
        lines.append("REQUIRED ACTIONS:")
        lines.append("  1. QA supervisor review within 30 minutes")
        lines.append("  2. Increase inspection frequency to 100% for next hour")
        lines.append("  3. Check recent material lot change and process parameters")
    else:
        lines.append("STATUS: NORMAL — monitor and log")

    return "\n".join(lines)


@tool
def get_recent_quality_events(line_id: str, days: int = 30) -> str:
    """
    Retrieve recent quality-related events (defect spikes, audits, NCRs) for a line.

    Args:
        line_id: Production line identifier
        days:    Look-back window in days (default 30)

    Returns:
        Plain text list of recent events.
    """
    events = {
        "LINE-B": [
            "2025-03-10: Defect rate 2.1% (above UCL 1.9%) — cause: contaminated weld wire spool, replaced",
            "2025-02-18: Quality audit passed — no findings",
            "2025-01-30: Defect rate 1.5% — borderline, additional QA check initiated",
            "2025-01-12: New resin batch PM-2025-0112 introduced — process settled after 30 min",
        ],
        "LINE-A": [
            "2025-03-20: Quality audit — 1 minor finding (labelling), corrected same day",
            "2025-02-28: Defect rate 1.2% (below UCL 1.4%) — normal variation",
        ],
        "LINE-C": [
            "2025-03-15: Customer complaint traced to Line C cosmetic defect — contained, 12 units affected",
        ],
    }
    line_events = events.get(line_id.upper(), [])
    if not line_events:
        return f"No recorded quality events for {line_id} in the last {days} days."
    return f"Recent quality events for {line_id}:\n" + "\n".join(f"  • {e}" for e in line_events)

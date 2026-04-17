"""
Throughput domain tools — production rate, OEE, downtime events.
"""
import json
from langchain_core.tools import tool


_THROUGHPUT_DATA = {
    "LINE-A": {"current_uph": 441, "target_uph": 450, "oee": 0.81},
    "LINE-B": {"current_uph": 218, "target_uph": 380, "oee": 0.47},
    "LINE-C": {"current_uph": 508, "target_uph": 520, "oee": 0.84},
}

_DOWNTIME_LOG = {
    "LINE-B": [
        {"timestamp": "2025-04-16 07:42", "duration_min": 12, "category": "Unplanned", "description": "Conveyor belt speed reduction — operators adjusting tension"},
        {"timestamp": "2025-04-16 06:10", "duration_min": 8,  "category": "Minor stop",  "description": "Product jam at conveyor transfer station C-14"},
        {"timestamp": "2025-04-15 22:55", "duration_min": 45, "category": "Unplanned", "description": "Motor thermal trip — cooling duct obstructed"},
        {"timestamp": "2025-04-15 14:30", "duration_min": 18, "category": "Changeover", "description": "Shift changeover (exceeded 15-min target)"},
    ],
    "LINE-A": [
        {"timestamp": "2025-04-16 08:00", "duration_min": 15, "category": "Planned PM", "description": "Weekly lubrication check"},
    ],
}


@tool
def get_current_throughput(line_id: str) -> str:
    """
    Get the current throughput rate and OEE for a production line.

    Args:
        line_id: Production line identifier (e.g. 'LINE-B')

    Returns:
        JSON with current_uph, target_uph, variance_pct, oee, alert_level.
    """
    data = _THROUGHPUT_DATA.get(line_id.upper())
    if not data:
        return json.dumps({"error": f"No throughput data for {line_id}"})

    variance_pct = round((data["current_uph"] - data["target_uph"]) / data["target_uph"] * 100, 1)

    if variance_pct <= -40:
        alert = "CRITICAL — throughput drop > 40%"
    elif variance_pct <= -25:
        alert = "RED_ALERT — throughput drop > 25%"
    elif variance_pct <= -10:
        alert = "YELLOW_ALERT — throughput drop > 10%"
    else:
        alert = "NORMAL"

    return json.dumps({
        "line_id": line_id.upper(),
        "current_uph": data["current_uph"],
        "target_uph":  data["target_uph"],
        "variance_pct": variance_pct,
        "oee": f"{data['oee']*100:.1f}%",
        "alert_level": alert,
    }, indent=2)


@tool
def get_downtime_log(line_id: str, hours: int = 24) -> str:
    """
    Retrieve recent downtime events for a production line.

    Args:
        line_id: Production line identifier
        hours:   Look-back window in hours (default 24)

    Returns:
        Formatted list of downtime events with timestamps and descriptions.
    """
    events = _DOWNTIME_LOG.get(line_id.upper(), [])
    if not events:
        return f"No downtime events recorded for {line_id} in the last {hours} hours."
    lines = [f"Downtime events for {line_id.upper()} (last {hours}h):"]
    for e in events:
        lines.append(
            f"  [{e['timestamp']}] {e['category']} — {e['duration_min']} min — {e['description']}"
        )
    total = sum(e["duration_min"] for e in events)
    lines.append(f"\n  Total downtime: {total} minutes")
    return "\n".join(lines)


@tool
def calculate_production_loss(line_id: str, duration_hours: float) -> str:
    """
    Calculate the estimated production units lost due to a throughput drop.

    Args:
        line_id:        Production line identifier
        duration_hours: How long the reduced throughput has been observed

    Returns:
        Plain text with lost units, financial estimate, and cumulative impact.
    """
    data = _THROUGHPUT_DATA.get(line_id.upper())
    if not data:
        return f"No data for {line_id}."

    lost_uph = data["target_uph"] - data["current_uph"]
    units_lost = int(lost_uph * duration_hours)
    # Rough financial estimate: $45 value per unit average
    revenue_risk = units_lost * 45

    return (
        f"Production Loss Estimate — {line_id.upper()}\n"
        f"  Target rate:    {data['target_uph']} units/hr\n"
        f"  Current rate:   {data['current_uph']} units/hr\n"
        f"  Shortfall:      {lost_uph} units/hr\n"
        f"  Duration:       {duration_hours} hours\n"
        f"  Units lost:     ~{units_lost:,} units\n"
        f"  Revenue at risk: ~${revenue_risk:,.0f} (at $45/unit avg)\n"
    )


@tool
def get_oee_breakdown(line_id: str) -> str:
    """
    Get the OEE component breakdown (Availability, Performance, Quality) for a line.

    Args:
        line_id: Production line identifier

    Returns:
        Plain text OEE breakdown with component scores.
    """
    breakdown = {
        "LINE-A": {"availability": 0.92, "performance": 0.94, "quality": 0.987},
        "LINE-B": {"availability": 0.61, "performance": 0.78, "quality": 0.988},
        "LINE-C": {"availability": 0.93, "performance": 0.96, "quality": 0.994},
    }
    d = breakdown.get(line_id.upper())
    if not d:
        return f"No OEE breakdown for {line_id}."

    oee = d["availability"] * d["performance"] * d["quality"]
    return (
        f"OEE Breakdown — {line_id.upper()}\n"
        f"  Availability: {d['availability']*100:.1f}%  (target ≥ 90%)\n"
        f"  Performance:  {d['performance']*100:.1f}%  (target ≥ 90%)\n"
        f"  Quality:      {d['quality']*100:.1f}%  (target ≥ 98%)\n"
        f"  ─────────────────────────────────\n"
        f"  OEE:          {oee*100:.1f}%  (target ≥ 80%)\n"
        f"\n"
        f"  {'⚠ AVAILABILITY is the primary OEE loss driver.' if d['availability'] < 0.85 else ''}"
    )

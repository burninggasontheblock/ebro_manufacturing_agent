"""
Maintenance domain tools — equipment status, PM schedule, work orders, sensor data.
"""
import json
from langchain_core.tools import tool


_EQUIPMENT_STATUS = {
    "CONV-LB-MAIN": {
        "name": "Main Assembly Conveyor — Line B",
        "status": "DEGRADED",
        "belt_thickness_mm": 18,
        "belt_replace_threshold_mm": 16,
        "belt_elongation_pct": 0.4,
        "vibration_C7_mm_s": 1.2,
        "vibration_C11_mm_s": 1.1,
        "vibration_C14_mm_s": 2.2,
        "vibration_threshold_mm_s": 2.5,
        "motor_temp_C": 47,
        "motor_temp_limit_C": 60,
        "belt_tension_N": 398,
        "belt_tension_spec_N": "350-420",
        "hours_since_last_pm": 360,
        "pm_interval_hours": 2000,
    },
    "WS-LB-03": {
        "name": "Welding Station 03 — Line B",
        "status": "MAINTENANCE_OVERDUE",
        "drive_rolls_hours": 580,
        "drive_rolls_interval_hours": 500,
        "contact_tip_hours": 580,
        "contact_tip_interval_hours": 500,
        "liner_hours": 980,
        "liner_interval_hours": 1000,
        "gas_flow_l_per_min": 17.5,
        "gas_flow_spec": "15-20",
        "wire_feed_speed_m_per_min": 5.8,
        "wire_feed_spec": "5.5-6.5",
    },
}

_OPEN_WORK_ORDERS = [
    {
        "wo_id": "WO-LB-1201",
        "description": "Replace bearing BRG-6205-2RS at conveyor position C-14 — vibration elevated 2.2mm/s",
        "equipment": "CONV-LB-MAIN",
        "priority": "HIGH",
        "raised": "2025-03-15",
        "scheduled": "2025-03-22",
        "status": "OPEN — OVERDUE",
    },
    {
        "wo_id": "WO-WS-2025-044",
        "description": "Replace drive rolls and contact tips — welding station WS-LB-03 (overdue 80h)",
        "equipment": "WS-LB-03",
        "priority": "MEDIUM",
        "raised": "2025-03-28",
        "scheduled": "2025-04-05",
        "status": "OPEN — OVERDUE",
    },
]


@tool
def get_equipment_status(equipment_id: str) -> str:
    """
    Get the current health status and sensor readings for a piece of equipment.

    Args:
        equipment_id: Equipment identifier (e.g. 'CONV-LB-MAIN', 'WS-LB-03')

    Returns:
        JSON with status, sensor readings, and threshold comparisons.
    """
    data = _EQUIPMENT_STATUS.get(equipment_id.upper())
    if not data:
        # Try fuzzy match
        for k, v in _EQUIPMENT_STATUS.items():
            if equipment_id.lower() in k.lower() or equipment_id.lower() in v["name"].lower():
                data = v
                equipment_id = k
                break
    if not data:
        return json.dumps({"error": f"No equipment data for {equipment_id}. Known IDs: {list(_EQUIPMENT_STATUS.keys())}"})
    return json.dumps(data, indent=2)


@tool
def get_open_work_orders(line_id: str = None) -> str:
    """
    Retrieve open maintenance work orders, optionally filtered to a line.

    Args:
        line_id: Optional production line filter (e.g. 'LINE-B')

    Returns:
        Formatted text listing open work orders with priority and status.
    """
    wos = _OPEN_WORK_ORDERS
    if line_id:
        # Simple filter: LB in equipment ID matches LINE-B etc.
        tag = line_id.replace("LINE-", "LB-").replace("LINE_", "LB-")
        wos = [w for w in wos if tag.lower() in w["equipment"].lower() or "lb" in w["equipment"].lower()]

    if not wos:
        return f"No open work orders for {line_id}."

    lines = [f"Open Work Orders ({len(wos)} found):\n"]
    for w in wos:
        lines.append(
            f"  [{w['priority']}] {w['wo_id']}\n"
            f"    Equipment: {w['equipment']}\n"
            f"    Description: {w['description']}\n"
            f"    Raised: {w['raised']} | Scheduled: {w['scheduled']}\n"
            f"    Status: {w['status']}\n"
        )
    return "\n".join(lines)


@tool
def get_pm_schedule(line_id: str) -> str:
    """
    Get the upcoming preventive maintenance schedule for a production line.

    Args:
        line_id: Production line identifier

    Returns:
        Plain text PM schedule with due dates and current hours.
    """
    schedules = {
        "LINE-B": (
            "Preventive Maintenance Schedule — LINE-B\n\n"
            "  CONV-LB-MAIN (Main Conveyor):\n"
            "    Last full PM:     2025-01-12  (bearing replacement C-7, C-11)\n"
            "    Hours since PM:   ~1,360 hours\n"
            "    Next PM due:      2025-06-20 (projected, at 2,000h)\n"
            "    C-14 bearing:     WO-LB-1201 OVERDUE — vibration 2.2mm/s (threshold 2.5)\n\n"
            "  WS-LB-03 (Welding Station):\n"
            "    Drive rolls:      580h since last change (OVERDUE — threshold 500h)\n"
            "    Contact tips:     580h since last change (OVERDUE — threshold 500h)\n"
            "    Liner:            980h since last change (due at 1,000h)\n"
            "    WO-WS-2025-044:   OPEN and OVERDUE\n\n"
            "  Belt inspection:\n"
            "    Belt thickness:   18mm (replace at 16mm — ~3-4 months remaining)\n"
            "    Belt elongation:  0.4% (limit 0.5%)"
        ),
        "LINE-A": (
            "Preventive Maintenance Schedule — LINE-A\n\n"
            "  All PM tasks current — no overdue items.\n"
            "  Next scheduled PM: 2025-05-03"
        ),
    }
    s = schedules.get(line_id.upper())
    if not s:
        return f"No PM schedule data for {line_id}."
    return s


@tool
def get_sensor_alerts(line_id: str) -> str:
    """
    Get any active sensor alerts or threshold breaches for a line's equipment.

    Args:
        line_id: Production line identifier

    Returns:
        Plain text list of active sensor alerts.
    """
    alerts = {
        "LINE-B": [
            "WARN  | CONV-LB-MAIN | Vibration C-14: 2.2mm/s (threshold 2.5mm/s) — trending up, WO-LB-1201 overdue",
            "INFO  | CONV-LB-MAIN | Belt elongation 0.4% (limit 0.5%) — 80% of limit, monitor",
            "WARN  | WS-LB-03     | Drive rolls 580h (threshold 500h) — overdue by 80h",
            "WARN  | WS-LB-03     | Contact tips 580h (threshold 500h) — overdue by 80h",
            "INFO  | WS-LB-03     | Wire feeder liner 980h (threshold 1000h) — replace soon",
        ],
        "LINE-A": [
            "INFO  | All sensors normal",
        ],
        "LINE-C": [
            "INFO  | All sensors normal",
        ],
    }
    line_alerts = alerts.get(line_id.upper(), [])
    if not line_alerts:
        return f"No sensor alerts for {line_id}."
    return f"Active sensor alerts — {line_id.upper()}:\n" + "\n".join(f"  {a}" for a in line_alerts)

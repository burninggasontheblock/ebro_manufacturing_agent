"""
Supplier domain tools — inventory levels, delivery status, supplier performance.
"""
import json
from langchain_core.tools import tool


_INVENTORY = {
    "ABS-RESIN":  {"supplier": "PolyMerge Corp",      "days_on_hand": 6.2, "buffer_days": 7,  "reorder_point_days": 5},
    "PCB-X440":   {"supplier": "TechComponents Ltd",  "days_on_hand": 8.0, "buffer_days": 10, "reorder_point_days": 5},
    "PCB-X442":   {"supplier": "TechComponents Ltd",  "days_on_hand": 7.5, "buffer_days": 10, "reorder_point_days": 5},
    "BRG-6205-2RS": {"supplier": "PrecisionParts GmbH", "days_on_hand": 21, "buffer_days": 14, "reorder_point_days": 7},
    "PA66-RESIN": {"supplier": "PolyMerge Corp",      "days_on_hand": 4.1, "buffer_days": 7,  "reorder_point_days": 5},
}

_OPEN_PURCHASE_ORDERS = [
    {
        "po_id": "PO-2025-0344",
        "supplier": "TechComponents Ltd",
        "item": "PCB-X440",
        "qty": 500,
        "original_due": "2025-04-01",
        "revised_due": "2025-04-07",
        "delay_days": 6,
        "status": "DELAYED",
        "reason": "Component shortage — MOSFET Q47B at TechComponents sub-supplier",
    },
    {
        "po_id": "PO-2025-0351",
        "supplier": "PolyMerge Corp",
        "item": "ABS-RESIN",
        "qty": 2000,
        "original_due": "2025-04-18",
        "revised_due": "2025-04-18",
        "delay_days": 0,
        "status": "ON_TIME",
        "reason": "",
    },
    {
        "po_id": "PO-2025-0359",
        "supplier": "PolyMerge Corp",
        "item": "PA66-RESIN",
        "qty": 1500,
        "original_due": "2025-04-12",
        "revised_due": "2025-04-16",
        "delay_days": 4,
        "status": "DELAYED",
        "reason": "Logistics delay — customs clearance",
    },
]

_SUPPLIER_PERFORMANCE = {
    "PolyMerge Corp":      {"otd_ytd_pct": 90.0, "quality_score": 88, "tier": 1, "single_source": True},
    "TechComponents Ltd":  {"otd_ytd_pct": 86.3, "quality_score": 91, "tier": 1, "single_source": True},
    "PrecisionParts GmbH": {"otd_ytd_pct": 98.2, "quality_score": 99, "tier": 2, "single_source": False},
}


@tool
def get_inventory_levels(material: str = None) -> str:
    """
    Get current inventory levels and buffer-stock status for materials.

    Args:
        material: Specific material SKU (e.g. 'PCB-X440'). Pass 'ALL' or leave empty for all items.

    Returns:
        Formatted inventory report with days-on-hand and buffer status.
    """
    if material and material.upper() != "ALL":
        item = _INVENTORY.get(material.upper())
        if not item:
            return f"No inventory data for material '{material}'."
        items = {material.upper(): item}
    else:
        items = _INVENTORY

    lines = ["Inventory Status:\n"]
    for sku, data in items.items():
        doh = data["days_on_hand"]
        buf = data["buffer_days"]
        rop = data["reorder_point_days"]

        if doh <= rop:
            status = "CRITICAL — BELOW REORDER POINT"
        elif doh < buf:
            status = "LOW — below buffer target"
        else:
            status = "OK"

        lines.append(
            f"  {sku:<15} | Supplier: {data['supplier']:<22} | "
            f"On hand: {doh:.1f}d | Buffer target: {buf}d | Status: {status}"
        )
    return "\n".join(lines)


@tool
def get_open_purchase_orders(supplier: str = None) -> str:
    """
    Get open purchase orders, optionally filtered by supplier.

    Args:
        supplier: Supplier name filter (partial match). Pass 'ALL' for all POs.

    Returns:
        Formatted list of open POs with due dates and delay status.
    """
    pos = _OPEN_PURCHASE_ORDERS
    if supplier and supplier.upper() != "ALL":
        pos = [p for p in pos if supplier.lower() in p["supplier"].lower()]

    if not pos:
        return f"No open POs found for supplier '{supplier}'."

    lines = [f"Open Purchase Orders ({len(pos)}):\n"]
    for p in pos:
        delay_text = f"⚠ {p['delay_days']} days LATE — {p['reason']}" if p["delay_days"] > 0 else "On time"
        lines.append(
            f"  [{p['status']}] {p['po_id']}\n"
            f"    Supplier: {p['supplier']} | Item: {p['item']} | Qty: {p['qty']}\n"
            f"    Original due: {p['original_due']} | Revised: {p['revised_due']}\n"
            f"    {delay_text}\n"
        )
    return "\n".join(lines)


@tool
def get_supplier_performance(supplier_name: str) -> str:
    """
    Get performance metrics for a specific supplier.

    Args:
        supplier_name: Full or partial supplier name

    Returns:
        JSON with OTD%, quality score, tier, and risk flags.
    """
    for name, data in _SUPPLIER_PERFORMANCE.items():
        if supplier_name.lower() in name.lower():
            flags = []
            if data["otd_ytd_pct"] < 90:
                flags.append("OTD below Tier 1 threshold (90%)")
            if data["quality_score"] < 85:
                flags.append("Quality score below threshold — 100% incoming inspection required")
            if data["single_source"]:
                flags.append("SINGLE SOURCE — no qualified alternate supplier")
            return json.dumps({
                "supplier": name,
                "otd_ytd_pct": data["otd_ytd_pct"],
                "quality_score": data["quality_score"],
                "tier": data["tier"],
                "single_source": data["single_source"],
                "risk_flags": flags,
            }, indent=2)
    return f"No performance data found for supplier '{supplier_name}'."


@tool
def check_supply_risk(line_id: str) -> str:
    """
    Assess supply-chain risk for a production line based on inventory and open POs.

    Args:
        line_id: Production line to assess

    Returns:
        Plain text risk assessment with time-to-stop-production estimates.
    """
    line_materials = {
        "LINE-B": ["ABS-RESIN", "PCB-X440", "BRG-6205-2RS"],
        "LINE-A": ["ABS-RESIN", "PA66-RESIN"],
        "LINE-C": ["PCB-X440", "PCB-X442"],
    }

    materials = line_materials.get(line_id.upper(), [])
    if not materials:
        return f"No supply chain data mapped for {line_id}."

    lines = [f"Supply Chain Risk Assessment — {line_id.upper()}\n"]
    for mat in materials:
        inv = _INVENTORY.get(mat)
        if not inv:
            continue
        doh = inv["days_on_hand"]
        buf = inv["buffer_days"]

        # Check if there's a delayed PO for this material
        delayed = [p for p in _OPEN_PURCHASE_ORDERS if p["item"] == mat and p["delay_days"] > 0]
        delay_note = ""
        if delayed:
            d = delayed[0]
            delay_note = f" | ⚠ PO {d['po_id']} delayed {d['delay_days']}d — {d['reason']}"

        if doh < buf and delayed:
            risk = "HIGH RISK — buffer below target AND incoming order delayed"
        elif doh < inv["reorder_point_days"]:
            risk = "CRITICAL — below reorder point, expedite required"
        elif doh < buf:
            risk = "MEDIUM RISK — buffer below target"
        else:
            risk = "LOW RISK"

        lines.append(f"  {mat}: {doh:.1f}d on hand (buffer: {buf}d) — {risk}{delay_note}")

    return "\n".join(lines)

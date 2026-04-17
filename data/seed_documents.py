"""
Synthetic manufacturing knowledge base.
Documents are split into four categories:
  kba          – Knowledge-base articles (troubleshooting guides)
  standard     – Process & quality standards
  incident     – Prior incident post-mortems
  maintenance  – Equipment maintenance history logs
  supplier     – Supplier performance & SLA records
"""

from typing import List, Dict, Any

DOCUMENTS: List[Dict[str, Any]] = [

    # ── KBA: Equipment ───────────────────────────────────────────────────────

    {
        "id": "KBA-EQ-001",
        "title": "Conveyor Belt Failure Modes and Diagnostics",
        "category": "kba",
        "tags": ["conveyor", "equipment", "throughput", "line-b", "mechanical"],
        "content": (
            "Conveyor Belt Failure Modes and Diagnostics\n\n"
            "Conveyor belts are one of the most common causes of throughput drops on assembly lines. "
            "Key failure modes include:\n\n"
            "1. BELT SLIPPAGE: Occurs when the drive roller loses traction. Symptoms: belt speed drops "
            "20-40% below set-point, motor amperage spikes. Common cause: worn lagging on drive roller, "
            "belt tension too low. Diagnosis: check tension gauge reading vs. spec (spec: 350-420 N for "
            "standard 600mm belt). Resolution: re-tension or replace lagging.\n\n"
            "2. ROLLER BEARING FAILURE: Progressive degradation. Symptoms: squealing noise, conveyor "
            "vibration, gradual speed reduction, elevated motor temperature. Mean time to failure after "
            "first symptom: 48-72 hours. Resolution: bearing replacement (PM part: BRG-6205-2RS).\n\n"
            "3. BELT TRACKING DRIFT: Belt migrates to one side. Symptoms: product misalignment, "
            "edge wear on belt, occasional jams. Cause: misaligned idler rollers or uneven load "
            "distribution. Resolution: adjust tracking idlers or realign load chute.\n\n"
            "4. MOTOR OVERHEATING: Causes thermal protection cutout. Symptoms: sudden stop, "
            "motor thermal indicator lit. Check: ambient temperature (limit 45°C), load vs. rated "
            "capacity, cooling fan operation. Resolution: allow 30-min cool-down, inspect load, "
            "check cooling.\n\n"
            "Line B historically experiences roller bearing issues in Q4 due to increased production "
            "volume. Last PM was scheduled for bearing inspection every 2,000 operating hours."
        ),
    },

    {
        "id": "KBA-EQ-002",
        "title": "CNC Machining Center — Spindle and Coolant System Diagnostics",
        "category": "kba",
        "tags": ["cnc", "spindle", "coolant", "equipment", "quality", "defect"],
        "content": (
            "CNC Machining Center — Spindle and Coolant System Diagnostics\n\n"
            "Spindle Issues:\n"
            "- Spindle vibration above 2.5 mm/s RMS indicates bearing wear or imbalance.\n"
            "- Tool run-out > 0.01mm causes surface finish defects and dimensional out-of-spec parts.\n"
            "- Check spindle warm-up cycles: cold spindle operation leads to thermal expansion "
            "errors averaging +0.015mm/°C on aluminium workpieces.\n\n"
            "Coolant System:\n"
            "- Low coolant concentration (below 6% emulsion) accelerates tool wear and increases "
            "surface roughness by up to 35%. Check concentration with refractometer daily.\n"
            "- Coolant contamination with tramp oil (>2%) degrades chip evacuation and raises "
            "bacterial count, causing foul odour and skin issues.\n"
            "- Clogged nozzles reduce cooling effectiveness; inspect and clean weekly.\n\n"
            "Defect correlation: In 78% of defect spike events in 2023, root cause traced to "
            "coolant concentration below threshold OR spindle warm-up skipped during shift change."
        ),
    },

    {
        "id": "KBA-EQ-003",
        "title": "Injection Moulding Press — Defect Troubleshooting Guide",
        "category": "kba",
        "tags": ["injection-moulding", "defect", "quality", "warp", "flash", "short-shot"],
        "content": (
            "Injection Moulding Press — Defect Troubleshooting Guide\n\n"
            "SHORT SHOTS (incomplete fill):\n"
            "Cause: insufficient injection pressure, blocked gates, degraded resin, cold mould.\n"
            "Resolution: increase injection pressure 10% increments, check gate dimensions, "
            "verify mould temperature (spec: 60-80°C for ABS), check resin moisture (< 0.1%).\n\n"
            "FLASH (material overflow at parting line):\n"
            "Cause: clamping force too low, worn parting surfaces, injection speed too high.\n"
            "Check: clamp force dial (spec: 120 tons for current mould), parting line wear.\n\n"
            "WARPAGE:\n"
            "Cause: uneven cooling, excessive residual stress. Check cooling channel temperatures "
            "(delta should be < 5°C between inlet and outlet). Cooling time spec: 18-22 seconds.\n\n"
            "SINK MARKS:\n"
            "Cause: insufficient packing pressure or time. Increase packing pressure; "
            "packing time spec is 4-6 seconds.\n\n"
            "DEFECT SPIKE PATTERN: Defect rates above 2% typically follow material lot changes "
            "or shift changeovers without proper mould purging."
        ),
    },

    {
        "id": "KBA-EQ-004",
        "title": "Automated Welding Station — Weld Quality Issues",
        "category": "kba",
        "tags": ["welding", "defect", "quality", "porosity", "wire-feed"],
        "content": (
            "Automated Welding Station — Weld Quality Issues\n\n"
            "POROSITY:\n"
            "Cause: gas contamination, moisture in base material, wire oxidation.\n"
            "Check: shielding gas flow (spec: 15-20 L/min), gas purity (> 99.95%), "
            "wire storage humidity (< 60% RH), base metal surface cleanliness.\n\n"
            "WIRE FEED INCONSISTENCY:\n"
            "Cause: worn drive rolls, kinked liner, incorrect contact tip size.\n"
            "Symptoms: arc instability, spatter increase > 15%, irregular bead width.\n"
            "Resolution: replace drive rolls every 500 hours, replace liner every 1,000 hours.\n\n"
            "BURN-THROUGH:\n"
            "Cause: excessive heat input, worn tip, incorrect travel speed.\n"
            "Check: travel speed (spec: 400-450 mm/min for 3mm steel), heat input formula.\n\n"
            "INTERMITTENT ARC FAILURE:\n"
            "Cause: contact tip wear, loose cable connections, incorrect wire stickout (spec: 12-15mm).\n\n"
            "Correlation: Wire feed inconsistency accounts for 65% of all weld defect spikes "
            "recorded in the past 24 months."
        ),
    },

    # ── KBA: Quality ─────────────────────────────────────────────────────────

    {
        "id": "KBA-QC-001",
        "title": "Statistical Process Control — Out-of-Control Patterns",
        "category": "kba",
        "tags": ["spc", "quality", "control-chart", "defect-spike"],
        "content": (
            "Statistical Process Control — Out-of-Control Patterns\n\n"
            "Eight standard Western Electric rules for detecting out-of-control conditions:\n\n"
            "RULE 1 (Spike): One point > 3σ from centreline → immediate investigation required.\n"
            "RULE 2 (Trend): 9 consecutive points on same side of centreline → process shift.\n"
            "RULE 3 (Trend): 6 consecutive points trending up or down → tool wear or drift.\n"
            "RULE 4 (Alternating): 14 alternating up/down points → over-adjustment or two "
            "alternating causes.\n\n"
            "Common assignable causes by pattern:\n"
            "- Sudden spike: material lot change, operator error, equipment failure, measurement error.\n"
            "- Gradual drift: tool wear, thermal expansion, raw material gradual change.\n"
            "- Step change: new operator, new setup, equipment repair, process parameter change.\n\n"
            "Response protocol: Stop production when defect rate exceeds 2.0% (UCL for our process). "
            "Quarantine last 2 hours of production. Root-cause investigation must be documented "
            "within 4 hours. Return to production only after written sign-off from QA manager."
        ),
    },

    {
        "id": "KBA-QC-002",
        "title": "Incoming Inspection and Supplier Material Certification",
        "category": "kba",
        "tags": ["quality", "incoming-inspection", "supplier", "material", "certification"],
        "content": (
            "Incoming Inspection and Supplier Material Certification\n\n"
            "All raw materials must be accompanied by a Certificate of Conformance (CoC) from the "
            "supplier. Inspection sampling plan follows ANSI/ASQ Z1.4 Level II.\n\n"
            "Critical checks:\n"
            "- Dimensional verification per drawing revision\n"
            "- Material composition (spectro test for metals, rheology test for polymers)\n"
            "- Surface condition (no oxidation, contamination, or damage)\n\n"
            "HIGH-RISK SUPPLIERS (require 100% incoming inspection, not sampling):\n"
            "- Suppliers on Approved Supplier List (ASL) with quality score < 85\n"
            "- Suppliers with a delivery delay > 3 events in trailing 6 months\n"
            "- New suppliers within first 6 months of qualification\n\n"
            "Correlation with defect spikes: 40% of defect spikes in 2023 were traced to "
            "non-conforming incoming material that passed sampling inspection. Recommend "
            "tightening AQL from 1.0 to 0.65 for polymer resins."
        ),
    },

    # ── Standards ─────────────────────────────────────────────────────────────

    {
        "id": "STD-PROD-001",
        "title": "Production Line Throughput Standards and KPIs",
        "category": "standard",
        "tags": ["throughput", "kpi", "oee", "line-b", "line-a", "production"],
        "content": (
            "Production Line Throughput Standards and KPIs\n\n"
            "TARGET THROUGHPUT RATES:\n"
            "  Line A: 450 units/hour (target OEE: 82%)\n"
            "  Line B: 380 units/hour (target OEE: 80%)\n"
            "  Line C: 520 units/hour (target OEE: 85%)\n\n"
            "ALERT THRESHOLDS:\n"
            "  Yellow alert: throughput drops > 10% below target for > 15 minutes\n"
            "  Red alert:    throughput drops > 25% below target for > 5 minutes\n"
            "  Critical:     throughput drops > 40% or full stop\n\n"
            "OEE COMPONENTS:\n"
            "  Availability = Run Time / Planned Production Time (target: ≥ 90%)\n"
            "  Performance  = (Ideal Cycle Time × Total Count) / Run Time (target: ≥ 90%)\n"
            "  Quality       = Good Count / Total Count (target: ≥ 98%)\n\n"
            "SHIFT CHANGEOVER: Max allowed downtime 15 minutes per shift change. "
            "Any overrun triggers a downtime report. Line B has historically averaged "
            "22 minutes due to tooling complexity — this is a known improvement opportunity.\n\n"
            "PLANNED MAINTENANCE WINDOWS:\n"
            "  Saturday 06:00-10:00: All lines available for PM\n"
            "  First Monday of month 22:00-02:00: Deep maintenance window"
        ),
    },

    {
        "id": "STD-QA-001",
        "title": "Quality Threshold Standards — Defect Classification",
        "category": "standard",
        "tags": ["quality", "defect", "threshold", "classification", "alert"],
        "content": (
            "Quality Threshold Standards — Defect Classification\n\n"
            "DEFECT CATEGORIES:\n"
            "  Critical (Class A): Defects that affect safety, function, or regulatory compliance. "
            "ZERO tolerance. Production stop required immediately.\n"
            "  Major (Class B):    Defects visible to customer or affecting assembly. "
            "Threshold: > 0.5% triggers hold and investigation.\n"
            "  Minor (Class C):    Cosmetic defects not affecting function. "
            "Threshold: > 2.0% triggers process review.\n\n"
            "DEFECT RATE BASELINES (12-month rolling):\n"
            "  Line A: 0.8% average, UCL 1.4%\n"
            "  Line B: 1.1% average, UCL 1.9%\n"
            "  Line C: 0.6% average, UCL 1.1%\n\n"
            "A 'defect spike' is defined as a defect rate exceeding UCL in any 1-hour window.\n\n"
            "RESPONSE MATRIX:\n"
            "  < UCL:         Monitor, log in SPC system\n"
            "  UCL to 3×UCL:  Yellow alert, QA supervisor review within 30 min\n"
            "  > 3×UCL:       Red alert, production hold, QA manager + plant manager notification\n\n"
            "REWORK policy: Parts may be reworked for Class B/C defects only. Class A: scrap only."
        ),
    },

    {
        "id": "STD-SAFE-001",
        "title": "Safety Incident Classification and Response Protocol",
        "category": "standard",
        "tags": ["safety", "incident", "protocol", "near-miss", "injury"],
        "content": (
            "Safety Incident Classification and Response Protocol\n\n"
            "INCIDENT TYPES:\n"
            "  Near Miss:      Potential harm event, no injury. Log within 24h. "
            "Supervisor review within 48h.\n"
            "  First Aid:      Minor injury treated on-site. Report to EHS within 2h. "
            "Investigation within 24h.\n"
            "  Recordable:     OSHA recordable injury. Immediate EHS notification. "
            "24h investigation, 72h corrective action plan.\n"
            "  Lost Time:      Injury causing missed workdays. Immediate plant manager + "
            "VP Operations notification. External review team.\n"
            "  Catastrophic:   Fatality or permanent disability. Emergency services + "
            "regulatory notification within 1h.\n\n"
            "ROOT CAUSE METHODOLOGY: Use 5-Why analysis for all recordable+. "
            "Fishbone diagram required for lost-time and catastrophic.\n\n"
            "COMMON SAFETY RISK AREAS IN THIS FACILITY:\n"
            "  - Line B pinch points at conveyor transfer stations (3 near-misses in 2023)\n"
            "  - Chemical exposure at welding station (PPE compliance issue Q2 2023)\n"
            "  - Forklift/pedestrian conflict in Warehouse Bay 3\n\n"
            "LOCKOUT/TAGOUT: All maintenance activities require LOTO per procedure SAFE-LOTO-001. "
            "Violations result in immediate stop-work order."
        ),
    },

    {
        "id": "STD-SUPPLY-001",
        "title": "Supplier SLA and Delivery Performance Standards",
        "category": "standard",
        "tags": ["supplier", "sla", "delivery", "on-time", "performance"],
        "content": (
            "Supplier SLA and Delivery Performance Standards\n\n"
            "DELIVERY PERFORMANCE TARGETS:\n"
            "  On-Time Delivery (OTD): ≥ 95% of orders delivered within agreed lead time\n"
            "  Lead Time Adherence: Orders not > 2 business days late\n"
            "  Fill Rate: ≥ 98% of ordered quantity delivered per shipment\n\n"
            "SUPPLIER TIER CLASSIFICATION:\n"
            "  Tier 1 (Strategic):   OTD < 90% triggers quarterly business review\n"
            "  Tier 2 (Preferred):   OTD < 92% triggers corrective action request\n"
            "  Tier 3 (Approved):    OTD < 95% triggers probationary status\n\n"
            "CRITICAL SUPPLIERS (single-source, no alternate):\n"
            "  - Resin supplier: PolyMerge Corp (lead time: 14 days, buffer stock: 7 days)\n"
            "  - PCB assemblies: TechComponents Ltd (lead time: 21 days, buffer: 5 days)\n"
            "  - Precision bearings: PrecisionParts GmbH (lead time: 10 days, buffer: 14 days)\n\n"
            "ESCALATION TRIGGERS:\n"
            "  - Delay > 3 business days: Supplier account manager contact required\n"
            "  - Delay > 5 business days: VP Supply Chain notification\n"
            "  - Delay causing line stop: Emergency procurement protocol activated\n\n"
            "BUFFER STOCK POLICY: Critical components maintain 7-day minimum buffer. "
            "Buffer below 3 days triggers automatic emergency order."
        ),
    },

    # ── Prior Incidents ───────────────────────────────────────────────────────

    {
        "id": "INC-2024-007",
        "title": "Post-Mortem: Line B Throughput Drop 42% — March 2024",
        "category": "incident",
        "tags": ["throughput", "line-b", "conveyor", "bearing", "maintenance"],
        "content": (
            "INCIDENT POST-MORTEM: INC-2024-007\n"
            "Date: 2024-03-14  |  Line: B  |  Duration: 6.5 hours\n"
            "Severity: HIGH  |  Production lost: ~2,470 units\n\n"
            "DESCRIPTION:\n"
            "Line B throughput dropped from 380 units/hour to 220 units/hour at 09:15. "
            "Operators noticed conveyor belt speed reduction and intermittent stops.\n\n"
            "ROOT CAUSE:\n"
            "Failed roller bearing (BRG-6205-2RS) at position C-7 on the main assembly conveyor. "
            "Bearing had accumulated 2,340 operating hours, 340 hours past the PM interval. "
            "PM was deferred twice due to production schedule pressure.\n\n"
            "CONTRIBUTING FACTORS:\n"
            "1. PM schedule deferred — maintenance team understaffed due to sick leave\n"
            "2. Vibration sensor at C-7 was offline for 3 weeks (work order WO-2024-0089 pending)\n"
            "3. No backup conveyor available for Line B\n\n"
            "CORRECTIVE ACTIONS:\n"
            "1. Replaced bearing BRG-6205-2RS at positions C-7, C-11 (preventive)\n"
            "2. Reinstated vibration sensor (completed 2024-03-16)\n"
            "3. PM deferral limit set to maximum 200 hours without VP Manufacturing approval\n\n"
            "RECURRENCE RISK: HIGH if PM schedule adherence not maintained."
        ),
    },

    {
        "id": "INC-2024-015",
        "title": "Post-Mortem: Defect Spike — Injection Moulding Line — May 2024",
        "category": "incident",
        "tags": ["defect", "quality", "injection-moulding", "supplier", "resin", "line-a"],
        "content": (
            "INCIDENT POST-MORTEM: INC-2024-015\n"
            "Date: 2024-05-22  |  Line: A  |  Duration: 4 hours\n"
            "Severity: HIGH  |  Defect rate peak: 8.3% (UCL: 1.4%)\n\n"
            "DESCRIPTION:\n"
            "Defect rate on Line A spiked to 8.3% during 14:00-18:00 shift. "
            "Defect type: short shots and sink marks on housing components.\n\n"
            "ROOT CAUSE:\n"
            "Non-conforming resin batch from PolyMerge Corp (Batch PM-2024-0441). "
            "Moisture content was 0.18% vs. specified maximum of 0.10%. "
            "Incoming inspection used sampling (AQL 1.0) and the affected pallet passed.\n\n"
            "CONTRIBUTING FACTORS:\n"
            "1. Resin moisture not measured at press (only at incoming inspection)\n"
            "2. Dryer pre-heat time was 2 hours; spec requires 4 hours for marginal batches\n"
            "3. Supplier CoC moisture value was correct but measured with different protocol\n\n"
            "CORRECTIVE ACTIONS:\n"
            "1. Moisture measurement added to press-side acceptance checklist\n"
            "2. PolyMerge Corp placed on enhanced inspection (100% incoming, 6 months)\n"
            "3. Dryer protocol updated: minimum 4-hour pre-heat regardless of CoC value\n\n"
            "FINANCIAL IMPACT: $34,000 scrap + $12,000 rework + $8,000 line downtime."
        ),
    },

    {
        "id": "INC-2024-031",
        "title": "Post-Mortem: Supplier Delivery Failure — TechComponents PCB — Aug 2024",
        "category": "incident",
        "tags": ["supplier", "delay", "pcb", "techcomponents", "line-stop", "line-c"],
        "content": (
            "INCIDENT POST-MORTEM: INC-2024-031\n"
            "Date: 2024-08-05  |  Supplier: TechComponents Ltd  |  Duration: 2.5 days line stop\n"
            "Severity: CRITICAL  |  Revenue impact: ~$180,000\n\n"
            "DESCRIPTION:\n"
            "TechComponents Ltd failed to deliver PCB assemblies (PO-2024-0771) on the confirmed "
            "date of 2024-08-03. Line C went to planned stop on 2024-08-05 when buffer inventory "
            "of 5 days was exhausted.\n\n"
            "ROOT CAUSE:\n"
            "TechComponents experienced a component shortage for MOSFET Q47B from their "
            "sub-supplier. This was not communicated to our procurement team until 2024-08-02 "
            "despite being known internally by TechComponents since 2024-07-28.\n\n"
            "CONTRIBUTING FACTORS:\n"
            "1. No supplier early-warning system in place\n"
            "2. Buffer stock policy at minimum (5 days) with no flex inventory\n"
            "3. No qualified alternate supplier for PCB assemblies\n\n"
            "CORRECTIVE ACTIONS:\n"
            "1. TechComponents required to provide bi-weekly supply risk updates\n"
            "2. Buffer stock target increased to 10 days for PCB assemblies\n"
            "3. Alternate supplier qualification initiated (target: Q1 2025)\n\n"
            "Note: TechComponents has had 4 late deliveries in trailing 12 months."
        ),
    },

    {
        "id": "INC-2023-044",
        "title": "Post-Mortem: Weld Quality Defect Spike — Line B — Nov 2023",
        "category": "incident",
        "tags": ["defect", "quality", "welding", "wire-feed", "line-b"],
        "content": (
            "INCIDENT POST-MORTEM: INC-2023-044\n"
            "Date: 2023-11-08  |  Line: B  |  Duration: 3 hours\n"
            "Severity: HIGH  |  Defect rate peak: 11.2%\n\n"
            "DESCRIPTION:\n"
            "Weld quality defect spike on Line B. Defect type: porosity and incomplete fusion "
            "on seam welds. Operator reported arc instability.\n\n"
            "ROOT CAUSE:\n"
            "Wire feed drive rolls worn beyond specification. Drive roll profile measured "
            "at 0.85mm vs. spec 1.2mm. Contact tip also worn (last replaced 680 hours ago "
            "vs. 500-hour interval).\n\n"
            "CONTRIBUTING FACTORS:\n"
            "1. Consumable replacement schedule not tracked in CMMS\n"
            "2. Operator reported instability on previous shift; not escalated\n"
            "3. Shielding gas flow meter found to be reading 2 L/min low (calibration drift)\n\n"
            "CORRECTIVE ACTIONS:\n"
            "1. Drive rolls and contact tips replaced; schedule added to CMMS\n"
            "2. Gas flow meters calibrated; calibration interval reduced 12→6 months\n"
            "3. Shift handover checklist updated to include arc stability observation\n\n"
            "ROOT CAUSE PATTERN: This is the third weld defect event in 18 months. "
            "All three traced to consumable neglect."
        ),
    },

    {
        "id": "INC-2024-052",
        "title": "Post-Mortem: Safety Near-Miss — Conveyor Pinch Point — Line B — Oct 2024",
        "category": "incident",
        "tags": ["safety", "near-miss", "conveyor", "line-b", "pinch-point"],
        "content": (
            "INCIDENT POST-MORTEM: INC-2024-052\n"
            "Date: 2024-10-11  |  Line: B  |  Classification: Near-Miss\n\n"
            "DESCRIPTION:\n"
            "Operator reached into conveyor transfer station to clear jam without engaging "
            "LOTO. Hand came within 50mm of pinch point between belt and roller.\n\n"
            "ROOT CAUSE:\n"
            "Operator bypassed LOTO because previous jam clearing had been done informally "
            "without incident. Cultural normalization of unsafe shortcut.\n\n"
            "CONTRIBUTING FACTORS:\n"
            "1. No physical interlock preventing access during conveyor operation\n"
            "2. LOTO training refresher overdue by 4 months for this operator\n"
            "3. Production pressure — operator felt clearing the jam quickly was expected\n\n"
            "CORRECTIVE ACTIONS:\n"
            "1. Physical guard with interlock installed at transfer station (completed Oct 17)\n"
            "2. LOTO refresher training for all Line B operators (completed Oct 20)\n"
            "3. Toolbox talk on stop-work authority: operators empowered to stop without pressure\n\n"
            "PATTERN: Line B has had 3 near-miss events at conveyor pinch points since 2022. "
            "Engineering review of guard design in progress."
        ),
    },

    # ── Maintenance History ───────────────────────────────────────────────────

    {
        "id": "MAINT-LB-2024-Q4",
        "title": "Line B Maintenance History — Q4 2024",
        "category": "maintenance",
        "tags": ["maintenance", "line-b", "conveyor", "bearing", "pm", "history"],
        "content": (
            "LINE B MAINTENANCE LOG — Q4 2024\n\n"
            "2024-10-05: PM-LB-240  Conveyor roller inspection. All bearings checked. "
            "Position C-7 measured at 1,980 hours — flagged for next PM (due at 2,000h). "
            "Belt tension verified: 395 N (in spec). Tracking aligned.\n\n"
            "2024-10-19: WO-LB-1144  Drive motor cooling fan replaced. Fan had seized "
            "causing motor temp to reach 62°C (limit 60°C). Motor now operating at 45°C.\n\n"
            "2024-11-02: PM-LB-241  Bearing position C-7 reached 2,000h. PM deferred "
            "by shift supervisor — reason: 'no downtime slot available this week.' "
            "Work order WO-LB-1149 raised, priority MEDIUM.\n\n"
            "2024-11-15: PM-LB-242  Scheduled full conveyor PM completed. "
            "Bearings C-7, C-11, C-14 replaced (BRG-6205-2RS). Belt inspected, no cracks. "
            "Tension reset to 400 N. Vibration sensors tested: all functional.\n\n"
            "2024-12-01: WO-LB-1162  Vibration sensor C-7 alarm — reading 3.1mm/s RMS "
            "(threshold 2.5). Investigated: sensor mount loose, not a bearing fault. "
            "Mount tightened; reading now 1.2mm/s.\n\n"
            "UPCOMING SCHEDULED MAINTENANCE:\n"
            "2025-01-04: Full PM due (interval 2,000h). Current hours since last PM: 1,640.\n"
            "Next bearing inspection due: 2025-01-18 (projected 2,000h milestone)."
        ),
    },

    {
        "id": "MAINT-LB-2025-Q1",
        "title": "Line B Maintenance History — Q1 2025",
        "category": "maintenance",
        "tags": ["maintenance", "line-b", "conveyor", "bearing", "overdue", "vibration"],
        "content": (
            "LINE B MAINTENANCE LOG — Q1 2025\n\n"
            "2025-01-04: PM-LB-243  Scheduled PM partially completed. "
            "Bearings inspected — C-7 and C-11 showing grease discolouration (early wear indicator). "
            "Replacement deferred pending parts arrival (ETA: 2025-01-10). "
            "Vibration at C-7: 1.8mm/s RMS. Flagged for monitoring.\n\n"
            "2025-01-12: WO-LB-1178  Parts BRG-6205-2RS received. Bearing replacement at C-7 "
            "and C-11 completed. Post-replacement vibration: C-7 0.9mm/s, C-11 1.1mm/s.\n\n"
            "2025-02-08: WO-LB-1192  Motor thermal trip on Line B at 14:35. "
            "Cause: cooling duct partially blocked by debris. Duct cleared; production resumed "
            "after 45-minute stop. Temperature normal.\n\n"
            "2025-03-01: PM-LB-244  Belt inspection. Belt thickness at 18mm (new: 22mm, "
            "replace threshold: 16mm). Belt elongation measured: 0.4% (limit 0.5%). "
            "Belt life estimated 3-4 months remaining.\n\n"
            "2025-03-15: Vibration sensor C-14 reporting 2.2mm/s RMS (approaching 2.5 threshold). "
            "WO-LB-1201 raised, priority HIGH. Bearing replacement scheduled 2025-03-22.\n\n"
            "NOTE: As of end Q1 2025, WO-LB-1201 is OPEN and bearing at C-14 not yet replaced."
        ),
    },

    {
        "id": "MAINT-WS-2024",
        "title": "Welding Station Maintenance History — 2024",
        "category": "maintenance",
        "tags": ["maintenance", "welding", "wire-feed", "consumables", "line-b"],
        "content": (
            "WELDING STATION MAINTENANCE LOG — 2024\n\n"
            "Station: WS-LB-03 (Line B, Bay 3)\n\n"
            "2024-01-15: Consumable replacement — drive rolls, contact tips, liner. "
            "Hours at replacement: 510h (due: 500h). ✓\n\n"
            "2024-04-20: Drive rolls replaced — 490h. Contact tip replaced — 490h. ✓\n\n"
            "2024-07-10: Shielding gas flow calibration check. Meter reading 17.2 L/min "
            "vs. reference 18.0 L/min. Within tolerance (±10%). No action.\n\n"
            "2024-09-05: Drive rolls — 520h since last replacement (OVERDUE by 20h). "
            "Replaced during unplanned stop. Contact tip also replaced.\n\n"
            "2024-10-22: Wire feed motor brushes replaced (routine, 2,000h interval).\n\n"
            "2024-12-01: Contact tip — 480h since last replacement. Proactive replacement "
            "during scheduled window. Drive rolls at 480h — replaced at same time.\n\n"
            "CURRENT STATUS (as of 2025-03-31):\n"
            "  Drive rolls: 580 hours since last replacement (OVERDUE — threshold 500h)\n"
            "  Contact tips: 580 hours since last replacement (OVERDUE — threshold 500h)\n"
            "  Liner: 980 hours since last replacement (due at 1,000h — replace soon)\n"
            "  WO-WS-2025-044 raised 2025-03-28, status: OPEN, priority: MEDIUM"
        ),
    },

    # ── Supplier Records ──────────────────────────────────────────────────────

    {
        "id": "SUP-POLY-2024",
        "title": "PolyMerge Corp — Supplier Performance Record 2024",
        "category": "supplier",
        "tags": ["supplier", "polymerge", "resin", "quality", "delivery", "performance"],
        "content": (
            "SUPPLIER PERFORMANCE RECORD: PolyMerge Corp\n"
            "Material: ABS and PA66 Resins  |  Tier: 1 (Strategic, Single-Source)\n"
            "Lead Time: 14 days  |  Buffer Stock Policy: 7 days\n\n"
            "2024 DELIVERY PERFORMANCE:\n"
            "  Q1 2024: OTD 91% (3 late deliveries, avg 1.5 days late)\n"
            "  Q2 2024: OTD 88% — flagged (INC-2024-015: bad resin batch)\n"
            "  Q3 2024: OTD 97% — enhanced inspection period, improved quality\n"
            "  Q4 2024: OTD 94% — 1 late delivery (customs delay, 2 days)\n"
            "  Full year OTD: 92.5% (below 95% target)\n\n"
            "QUALITY INCIDENTS:\n"
            "  May 2024: Batch PM-2024-0441 — moisture out of spec (INC-2024-015)\n"
            "  Aug 2024: Batch PM-2024-0603 — minor pigment variation, accepted with deviation\n\n"
            "CORRECTIVE ACTIONS OPEN:\n"
            "  CAR-2024-031: Moisture testing protocol alignment (closed Oct 2024)\n"
            "  CAR-2024-042: SPC implementation at PolyMerge extrusion line (due Q1 2025, OPEN)\n\n"
            "RISK ASSESSMENT: MEDIUM-HIGH. Single-source; quality improving but not stable. "
            "Alternate supplier qualification (AltResin AG) in progress, ETA Q2 2025.\n\n"
            "CURRENT BUFFER STOCK: 6.2 days (above 7-day target? No — marginally below)."
        ),
    },

    {
        "id": "SUP-TECH-2024",
        "title": "TechComponents Ltd — Supplier Performance Record 2024",
        "category": "supplier",
        "tags": ["supplier", "techcomponents", "pcb", "delivery", "delay", "line-c"],
        "content": (
            "SUPPLIER PERFORMANCE RECORD: TechComponents Ltd\n"
            "Material: PCB Assemblies (Model PCB-X440, PCB-X442)  |  Tier: 1 (Single-Source)\n"
            "Lead Time: 21 days  |  Buffer Stock Policy: 10 days (increased after INC-2024-031)\n\n"
            "2024 DELIVERY PERFORMANCE:\n"
            "  Q1 2024: OTD 90% (2 late deliveries)\n"
            "  Q2 2024: OTD 85% (3 late deliveries — BELOW TIER 1 THRESHOLD)\n"
            "  Q3 2024: OTD 82% — INC-2024-031 line stop event (Aug 2024)\n"
            "  Q4 2024: OTD 88% — improving, still below target\n"
            "  Full year OTD: 86.3% (significantly below 95% target)\n\n"
            "CURRENT STATUS (Q1 2025):\n"
            "  Jan 2025: OTD 91% (1 late delivery, 3 days)\n"
            "  Feb 2025: OTD 100% — no delays\n"
            "  Mar 2025: Order PO-2025-0344 (PCB-X440, 500 units) — due 2025-04-01. "
            "TechComponents flagged potential delay on 2025-03-25 due to component availability. "
            "Revised delivery: 2025-04-07 (6 days late). Buffer stock: 8 days (sufficient).\n\n"
            "ALTERNATE SUPPLIER STATUS:\n"
            "  CircuitPro Ltd: Qualification 60% complete. Target Q3 2025.\n\n"
            "RISK ASSESSMENT: HIGH. Chronic delivery performance below target. "
            "Current buffer provides 8-day protection against further delays."
        ),
    },

    {
        "id": "SUP-PREC-2024",
        "title": "PrecisionParts GmbH — Supplier Performance Record 2024",
        "category": "supplier",
        "tags": ["supplier", "precisionparts", "bearings", "delivery", "performance"],
        "content": (
            "SUPPLIER PERFORMANCE RECORD: PrecisionParts GmbH\n"
            "Material: Precision Bearings (BRG-6205-2RS and variants)  |  Tier: 2 (Preferred)\n"
            "Lead Time: 10 days  |  Buffer Stock Policy: 14 days\n\n"
            "2024 DELIVERY PERFORMANCE:\n"
            "  Full year OTD: 98.2% — exceeds target\n"
            "  Quality score: 99.1% — excellent\n"
            "  Only 1 late delivery in 2024 (1 day, weather-related logistics)\n\n"
            "CURRENT STOCK LEVELS:\n"
            "  BRG-6205-2RS: 42 units in stock (covers ~21 days at current consumption)\n"
            "  BRG-6306-2RS: 18 units in stock\n"
            "  BRG-6008-2RS: 7 units in stock (below 14-day buffer — reorder triggered)\n\n"
            "RISK ASSESSMENT: LOW. Reliable supplier with strong performance history. "
            "No open corrective actions."
        ),
    },
]


def get_documents_by_category(category: str) -> List[Dict[str, Any]]:
    return [d for d in DOCUMENTS if d["category"] == category]


def get_document_by_id(doc_id: str) -> Dict[str, Any] | None:
    for d in DOCUMENTS:
        if d["id"] == doc_id:
            return d
    return None


def get_documents_by_tag(tag: str) -> List[Dict[str, Any]]:
    return [d for d in DOCUMENTS if tag in d.get("tags", [])]

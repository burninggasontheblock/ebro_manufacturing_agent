"""
Manufacturing Operations AI — Multi-Agent Root Cause Analysis System

Demo scenarios:
  1. "Output dropped on Line B"     → throughput + maintenance + quality agents
  2. "Defect spike on Line B"       → quality + maintenance + supplier agents
  3. "Missed supplier delivery"     → supplier + throughput agents

After the RCA four document agents run in parallel:
  • Shift Handoff Note
  • Maintenance Work Order
  • Corrective Action Plan
  • Supplier Questionnaire (when supplier involved)

Usage:
  python main.py                  # run all three demo scenarios
  python main.py --scenario 1     # run a specific scenario (1, 2, or 3)
  python main.py --rebuild-rag    # rebuild FAISS vector store

  Embeddings use OpenAI — set OPENAI_API_KEY in .env.

Python API:
  from main import analyze_incident
  from models.schemas import Incident
  result = analyze_incident(Incident(id="INC-001", description="...",
                                     plant_id="PLANT-A", line_id="LINE-B"))
  print(result.report.executive_summary)
  print(result.shift_handoff.situation_summary)
"""
from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from models.schemas import (
    CorrectiveActionPlan,
    Incident,
    IncidentReport,
    MaintenanceRequest,
    RootCauseHypothesis,
    ShiftHandoffNote,
    SupplierQuestionnaire,
)

console = Console()


# ── Demo scenarios ────────────────────────────────────────────────────────────

DEMO_SCENARIOS: list[Incident] = [
    Incident(
        id="INC-2025-041",
        description=(
            "Output dropped on Line B. Throughput fell from 380 to ~220 units/hour "
            "at approximately 07:30 this morning. Operators are reporting belt speed "
            "reduction and intermittent stops at the main assembly conveyor. "
            "No scheduled maintenance was planned for today."
        ),
        plant_id="PLANT-A",
        line_id="LINE-B",
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
        raw_metrics={"current_uph": 218, "target_uph": 380, "downtime_today_min": 63},
    ),
    Incident(
        id="INC-2025-042",
        description=(
            "Defect spike on Line B weld quality. Defect rate has spiked to 4.7% "
            "(UCL is 1.9%). Predominant defect types are porosity and arc instability. "
            "The issue started roughly two hours into the current shift."
        ),
        plant_id="PLANT-A",
        line_id="LINE-B",
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
        raw_metrics={"defect_rate_pct": 4.7, "ucl": 1.9},
    ),
    Incident(
        id="INC-2025-043",
        description=(
            "Missed supplier delivery. TechComponents Ltd has confirmed that "
            "PO-2025-0344 for PCB-X440 assemblies will be 6 days late, arriving "
            "2025-04-07 instead of the confirmed date of 2025-04-01. "
            "Current buffer inventory is approximately 8 days."
        ),
        plant_id="PLANT-A",
        line_id="LINE-C",
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
        raw_metrics={"buffer_days_on_hand": 8, "po_delay_days": 6},
    ),
]


# ── Public API ────────────────────────────────────────────────────────────────

def analyze_incident(incident: Incident):
    """
    Run the full multi-agent pipeline.
    Returns a FullAnalysisResult with .report, .shift_handoff,
    .maintenance_request, .corrective_action_plan, .supplier_questionnaire
    """
    from agents.graph import run_incident
    return run_incident(incident)


# ── Display helpers ───────────────────────────────────────────────────────────

def _conf_colour(label: str) -> str:
    return {"HIGH": "green", "MEDIUM": "yellow", "LOW": "red"}.get(label, "white")


def print_incident_header(incident: Incident) -> None:
    console.print(Panel(
        f"[bold cyan]INCIDENT[/bold cyan]  {incident.id}\n"
        f"[dim]Plant:[/dim] {incident.plant_id}  "
        f"[dim]Line:[/dim] {incident.line_id or 'N/A'}  "
        f"[dim]Time:[/dim] {incident.timestamp or 'N/A'}\n\n"
        f"[white]{incident.description}[/white]",
        title="[bold yellow]Manufacturing Operations AI[/bold yellow]",
        border_style="yellow",
        expand=False,
    ))


# ── Section: RCA report ───────────────────────────────────────────────────────

def print_rca_report(report: IncidentReport) -> None:
    console.print(Panel(
        f"[white]{report.executive_summary}[/white]",
        title="[bold green]1. Executive Summary[/bold green]",
        border_style="green",
    ))

    console.print(
        f"[dim]Agents invoked:[/dim] [cyan]{', '.join(report.agents_invoked)}[/cyan]\n"
    )

    # Hypothesis summary table
    tbl = Table(title="Root-Cause Hypotheses", box=box.ROUNDED, show_lines=True, expand=True)
    tbl.add_column("#",           style="dim",   width=3)
    tbl.add_column("Hypothesis",  style="white", ratio=3)
    tbl.add_column("Confidence",  style="bold",  width=13)
    tbl.add_column("Resolution",  style="cyan",  width=14)
    tbl.add_column("Top Evidence",style="dim",   ratio=2)

    for h in report.root_cause_hypotheses:
        col = _conf_colour(h.confidence_label)
        ev  = "; ".join(h.supporting_evidence[:2])
        if len(h.supporting_evidence) > 2:
            ev += f" (+{len(h.supporting_evidence)-2})"
        tbl.add_row(
            str(h.rank), h.hypothesis,
            f"[{col}]{h.confidence_label} ({h.confidence:.0%})[/{col}]",
            h.estimated_resolution_time or "TBD", ev,
        )
    console.print(tbl)
    console.print()

    # Detailed hypotheses
    for h in report.root_cause_hypotheses:
        col = _conf_colour(h.confidence_label)
        lines = [f"[bold]{h.hypothesis}[/bold]"]
        if h.supporting_evidence:
            lines.append("\n[underline]Evidence:[/underline]")
            lines += [f"  • {e}" for e in h.supporting_evidence]
        if h.contributing_agents:
            lines.append(f"\n[dim]Agents: {', '.join(h.contributing_agents)}[/dim]")
        if h.recommended_actions:
            lines.append("\n[underline]Actions:[/underline]")
            lines += [f"  {i}. {a}" for i, a in enumerate(h.recommended_actions, 1)]
        console.print(Panel(
            "\n".join(lines),
            title=f"[{col}]Hypothesis #{h.rank} — {h.confidence_label} ({h.confidence:.0%})[/{col}]",
            border_style=col,
        ))

    if report.recommended_immediate_actions:
        console.print("[bold red]IMMEDIATE ACTIONS:[/bold red]")
        for i, a in enumerate(report.recommended_immediate_actions, 1):
            console.print(f"  {i}. {a}")
        console.print()

    if report.recommended_preventive_actions:
        console.print("[bold yellow]Preventive Actions:[/bold yellow]")
        for i, a in enumerate(report.recommended_preventive_actions, 1):
            console.print(f"  {i}. {a}")
        console.print()

    if report.estimated_production_impact:
        console.print(f"[bold]Production Impact:[/bold] {report.estimated_production_impact}")
    if report.confidence_note:
        console.print(f"[dim]{report.confidence_note}[/dim]")
    console.print()


# ── Section: Shift Handoff ────────────────────────────────────────────────────

def print_shift_handoff(note: ShiftHandoffNote | None) -> None:
    if not note:
        return
    lines = []
    lines.append(f"[bold]Situation:[/bold]\n{note.situation_summary}\n")

    if note.do_not_restart_until:
        lines.append("[bold red]DO NOT RESTART UNTIL:[/bold red]")
        lines += [f"  ✗ {c}" for c in note.do_not_restart_until]
        lines.append("")

    if note.actions_completed:
        lines.append("[bold green]Actions Completed:[/bold green]")
        lines += [f"  ✓ {a}" for a in note.actions_completed]
        lines.append("")

    if note.pending_actions:
        lines.append("[bold yellow]Pending Actions for Next Shift:[/bold yellow]")
        lines += [f"  → {a}" for a in note.pending_actions]
        lines.append("")

    if note.watch_items:
        lines.append("[bold cyan]Watch Items:[/bold cyan]")
        lines += [f"  👁 {w}" for w in note.watch_items]
        lines.append("")

    if note.escalation_contacts:
        lines.append("[dim]Escalation Contacts:[/dim]")
        lines += [f"  • {c}" for c in note.escalation_contacts]

    console.print(Panel(
        "\n".join(lines),
        title="[bold blue]2. Shift Handoff Note[/bold blue]",
        border_style="blue",
    ))
    console.print()


# ── Section: Maintenance Work Order ──────────────────────────────────────────

def print_maintenance_request(wo: MaintenanceRequest | None) -> None:
    if not wo:
        return

    priority_colour = {"CRITICAL": "red", "HIGH": "yellow", "MEDIUM": "cyan", "LOW": "dim"}.get(
        wo.priority, "white"
    )

    header = (
        f"[bold]WO:[/bold] {wo.wo_number}  "
        f"[bold]Priority:[/bold] [{priority_colour}]{wo.priority}[/{priority_colour}]  "
        f"[bold]Required by:[/bold] {wo.required_completion_date or 'ASAP'}\n"
        f"[bold]Line:[/bold] {wo.line_id}  [bold]Plant:[/bold] {wo.plant_id}\n"
        f"[bold]Requested:[/bold] {wo.requested_date or 'Now'}\n"
    )

    if wo.special_instructions:
        header += f"\n[yellow]Special Instructions:[/yellow] {wo.special_instructions}\n"
    if wo.approvals_required:
        header += f"[red]Approvals Required:[/red] {', '.join(wo.approvals_required)}\n"

    work_lines = [header]
    for item in wo.work_items:
        work_lines.append(f"\n[bold]Item {item.item_number} — {item.equipment_id}[/bold]")
        work_lines.append(f"  [dim]Problem:[/dim]  {item.problem_description}")
        work_lines.append(f"  [dim]Work:[/dim]     {item.work_requested}")
        if item.parts_required:
            work_lines.append(f"  [dim]Parts:[/dim]    " + ", ".join(item.parts_required))
        if item.estimated_duration_hours:
            work_lines.append(f"  [dim]Duration:[/dim] {item.estimated_duration_hours}h")
        if item.safety_precautions:
            work_lines.append("  [red]Safety:[/red]   " + " | ".join(item.safety_precautions))

    console.print(Panel(
        "\n".join(work_lines),
        title="[bold magenta]3. Maintenance Work Order[/bold magenta]",
        border_style="magenta",
    ))
    console.print()


# ── Section: Corrective Action Plan ──────────────────────────────────────────

def print_corrective_action_plan(cap: CorrectiveActionPlan | None) -> None:
    if not cap:
        return

    header_lines = [
        f"[bold]CAP ID:[/bold] {cap.cap_id}  [bold]Review Date:[/bold] {cap.review_date}  "
        f"[bold]Approver:[/bold] {cap.approver}",
        f"\n[bold]Problem Statement:[/bold]\n{cap.problem_statement}",
        f"\n[bold]Root Cause Addressed:[/bold] {cap.root_cause_addressed}",
    ]
    if cap.effectiveness_kpis:
        header_lines.append("\n[bold]Effectiveness KPIs:[/bold]")
        header_lines += [f"  • {k}" for k in cap.effectiveness_kpis]

    # Action table
    tbl = Table(box=box.SIMPLE_HEAVY, expand=True, show_lines=True)
    tbl.add_column("#",          width=3,  style="dim")
    tbl.add_column("Category",   width=14, style="bold")
    tbl.add_column("Action",     ratio=3)
    tbl.add_column("Owner",      width=20, style="cyan")
    tbl.add_column("Due",        width=12, style="yellow")
    tbl.add_column("Success Criteria", ratio=2, style="dim")

    cat_colour = {
        "IMMEDIATE":  "red",
        "SHORT_TERM": "yellow",
        "LONG_TERM":  "cyan",
        "PREVENTIVE": "green",
    }
    for a in cap.actions:
        col = cat_colour.get(a.category, "white")
        tbl.add_row(
            str(a.action_number),
            f"[{col}]{a.category}[/{col}]",
            a.action, a.owner, a.due_date, a.success_criteria,
        )

    console.print(Panel(
        "\n".join(header_lines) + "\n",
        title="[bold green]4. Corrective Action Plan[/bold green]",
        border_style="green",
        expand=True,
    ))
    console.print(tbl)
    console.print()


# ── Section: Supplier Questionnaire ──────────────────────────────────────────

def print_supplier_questionnaire(sq: SupplierQuestionnaire | None) -> None:
    if not sq:
        return

    urgency_col = "red" if sq.urgency == "IMMEDIATE" else "yellow"
    header = (
        f"[bold]Supplier:[/bold] {sq.supplier_name}  "
        f"[bold]Urgency:[/bold] [{urgency_col}]{sq.urgency}[/{urgency_col}]\n"
    )
    if sq.po_references:
        header += f"[bold]PO References:[/bold] {', '.join(sq.po_references)}\n"
    if sq.escalation_note:
        header += f"\n[bold red]Escalation Note:[/bold red] {sq.escalation_note}\n"
    if sq.requested_deliverables:
        header += "\n[bold]Requested Deliverables:[/bold]\n"
        header += "\n".join(f"  • {d}" for d in sq.requested_deliverables)

    q_lines = [header, ""]

    cat_col = {
        "ROOT_CAUSE":    "red",
        "TIMELINE":      "yellow",
        "PREVENTION":    "green",
        "COMPENSATION":  "magenta",
        "COMMUNICATION": "cyan",
    }
    for q in sq.questions:
        col = cat_col.get(q.category, "white")
        q_lines.append(
            f"[{col}][bold]Q{q.question_number} [{q.category}][/bold][/{col}]  "
            f"{q.question}"
        )
        if q.context:
            q_lines.append(f"  [dim]Context: {q.context}[/dim]")
        if q.expected_response_format:
            q_lines.append(f"  [dim]Expected: {q.expected_response_format}[/dim]")
        q_lines.append("")

    console.print(Panel(
        "\n".join(q_lines),
        title="[bold cyan]5. Supplier Questionnaire[/bold cyan]",
        border_style="cyan",
    ))
    console.print()


# ── Full print ────────────────────────────────────────────────────────────────

def print_full_result(result) -> None:
    print_rca_report(result.report)
    print_shift_handoff(result.shift_handoff)
    print_maintenance_request(result.maintenance_request)
    print_corrective_action_plan(result.corrective_action_plan)
    print_supplier_questionnaire(result.supplier_questionnaire)


# ── CLI runner ────────────────────────────────────────────────────────────────

def run_scenario(incident: Incident) -> None:
    print_incident_header(incident)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(
            "[cyan]Running multi-agent pipeline "
            "(orchestrator → domain agents → RCA → handoff/WO/CAP/supplier questions)...[/cyan]",
            total=None,
        )
        start = time.time()
        result = analyze_incident(incident)
        elapsed = time.time() - start

    console.print(f"\n[dim]Analysis completed in {elapsed:.1f}s[/dim]\n")
    print_full_result(result)
    console.rule()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Manufacturing Operations AI — Multi-Agent RCA + Action Documents"
    )
    parser.add_argument(
        "--scenario", type=int, choices=[1, 2, 3],
        help="Run a specific demo scenario",
    )
    parser.add_argument(
        "--rebuild-rag", action="store_true",
        help="Force rebuild the FAISS vector store",
    )
    args = parser.parse_args()

    if args.rebuild_rag:
        console.print("[yellow]Rebuilding vector store...[/yellow]")
        from rag.knowledge_base import rebuild_store
        rebuild_store()
        console.print("[green]Done.[/green]")
        if not args.scenario:
            sys.exit(0)

    with Progress(SpinnerColumn(), TextColumn("[dim]Initialising knowledge base...[/dim]"),
                  transient=True) as p:
        p.add_task("", total=None)
        from rag.knowledge_base import _get_store
        _get_store()

    if args.scenario:
        run_scenario(DEMO_SCENARIOS[args.scenario - 1])
    else:
        for i, scenario in enumerate(DEMO_SCENARIOS, 1):
            console.print(f"\n[bold magenta]═══ SCENARIO {i}/3 ═══[/bold magenta]\n")
            run_scenario(scenario)


if __name__ == "__main__":
    main()

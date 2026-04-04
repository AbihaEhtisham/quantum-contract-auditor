"""
dashboard.py  —  Rich terminal dashboard for the Quantum Smart Contract Auditor.
"""
import time
from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

console = Console()

def _bar(prob, width=28, char="█"):
    filled = int(prob * width)
    return char * filled + "░" * (width - filled)

def _vstyle(v):
    return "bold bright_green" if v == "SAFE" else "bold bright_red"

def print_banner():
    console.print()
    t = Text()
    t.append("  ⚛  QUANTUM-ENHANCED SMART CONTRACT AUDITOR  ⚛  ", style="bold white")
    console.print(Panel(Align.center(t),
        subtitle="[dim]Formal Grammar  ·  Quantum Walk  ·  Qiskit AerSimulator[/dim]",
        border_style="bright_cyan", padding=(1, 4)))
    console.print("[dim]  NUST BSCS-14D  ·  Eman Fatima & Abiha Ehtisham  ·  Supervised by Dr. Iqbal[/dim]\n")

def run_phase(label, detail, duration=0.8):
    with Progress(SpinnerColumn(spinner_name="dots2", style="bright_cyan"),
                  TextColumn("[bold cyan]{task.description}"),
                  TimeElapsedColumn(), console=console, transient=True) as p:
        p.add_task(f"{label}  [dim]{detail}[/dim]", total=None)
        time.sleep(duration)

def show_grammar_panel(report):
    from core.grammar import GrammarEngine
    engine = GrammarEngine()
    tokens  = engine.tokenize(report.command)
    classes = [engine._classify_token(t) for t in tokens]
    cls_colors = {"AUTH":"bright_green","CHECK":"cyan","UPDATE":"yellow",
                  "CALL":"bright_magenta","BAD":"bright_red","UNKNOWN":"dim"}
    tbl = Table(box=box.SIMPLE, show_header=True, header_style="dim cyan",
                padding=(0, 1), expand=False)
    tbl.add_column("Token", style="bold white")
    tbl.add_column("Class", style="cyan")
    tbl.add_column("CFG Transition")
    for i, (t, c) in enumerate(zip(tokens, classes)):
        path_step = report.cfg_path[i] if i < len(report.cfg_path) else ""
        tbl.add_row(t, Text(c, style=cls_colors.get(c, "white")), Text(path_step, style="dim"))
    color = "bright_green" if report.grammar_verdict == "SAFE" else "bright_red"
    icon  = "✓" if report.grammar_verdict == "SAFE" else "✗"
    console.print(Panel(tbl,
        title=f"[bold]Phase 1[/bold]  Grammar Engine  [{color}]{icon} {report.grammar_verdict}[/{color}]",
        border_style=color, subtitle=f"[dim]Parse: {report.parse_time_ms:.2f} ms[/dim]", padding=(0,1)))
    if report.violated_rule:
        console.print(f"  [bright_red]⚠  Rule {report.violated_rule} violated — {report.attack_type}[/bright_red]")

def show_walk_panel(report):
    color = "bright_green" if report.walk_verdict == "SAFE" else "bright_red"
    grid = Table.grid(padding=(0,2))
    grid.add_column(min_width=20, style="dim")
    grid.add_column()
    grid.add_row("Safe  P(q_accept)",   Text(f"{_bar(report.walk_safe_prob)}  {report.walk_safe_prob:.1%}", style="bright_green"))
    grid.add_row("Vuln  P(q_reject)",   Text(f"{_bar(report.walk_vuln_prob)}  {report.walk_vuln_prob:.1%}", style="bright_red"))
    grid.add_row("Paths (superpos.)",   Text(f"{report.paths_explored:,}  simultaneous paths explored", style="bright_cyan"))
    grid.add_row("Classical sample",    Text(" → ".join(report.classical_path), style="dim"))
    grid.add_row("Walk time",           Text(f"{report.walk_time_ms:.2f} ms", style="dim"))
    console.print(Panel(grid,
        title=f"[bold]Phase 2[/bold]  Quantum Walk  [{color}]{report.walk_verdict}[/{color}]",
        border_style="bright_cyan", padding=(0,1)))

def show_circuit_panel(report):
    color = "bright_green" if report.circuit_verdict == "SAFE" else "bright_red"
    stats = Table.grid(padding=(0,3))
    stats.add_column(style="dim", min_width=18)
    stats.add_column()
    stats.add_row("Qubits",        Text(str(report.n_qubits), style="bright_cyan bold"))
    stats.add_row("Circuit depth", Text(str(report.circuit_depth), style="cyan"))
    stats.add_row("Gate count",    Text(str(report.gate_count), style="cyan"))
    stats.add_row("Shots",         Text("1024", style="dim"))
    stats.add_row("Sim time",      Text(f"{report.sim_time_ms:.2f} ms", style="dim"))

    hist_rows = ["", "[dim]Measurement histogram:[/dim]"]
    sorted_counts = sorted(report.measurement_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    for bs, cnt in sorted_counts:
        prob = cnt / 1024
        lc   = "bright_green" if bs[0] == "0" else "bright_red"
        hist_rows.append(f"  [{lc}]|{bs}⟩[/{lc}]  {_bar(prob, 20)}  [dim]{cnt:4d}  {prob:.1%}[/dim]")
    hist_rows += [
        "",
        f"  [bright_green]P(SAFE)      {_bar(report.prob_safe, 24)}  {report.prob_safe:.1%}[/bright_green]",
        f"  [bright_red]P(VULN)      {_bar(report.prob_vulnerable, 24)}  {report.prob_vulnerable:.1%}[/bright_red]",
    ]
    body = Group(stats, Text("\n".join(hist_rows)))
    console.print(Panel(body,
        title=f"[bold]Phase 3[/bold]  Qiskit AerSimulator  [{color}]{report.circuit_verdict}[/{color}]",
        border_style="bright_blue", padding=(0,1)))

def show_verdict_banner(report):
    is_safe = report.is_safe
    fc   = "bright_green" if is_safe else "bright_red"
    icon = "✓  SAFE" if is_safe else "✗  VULNERABLE"
    t = Text(justify="center")
    t.append(f"\n  {icon}  \n", style=f"bold {fc}")
    t.append(f"  Confidence: {report.final_confidence:.1%}   ", style="bold white")
    t.append(f"Risk: {report.risk_level}   ", style=f"bold {fc}")
    t.append(f"Total pipeline: {report.total_time_ms:.1f} ms  \n", style="dim white")
    if not is_safe and report.attack_type:
        t.append(f"\n  Attack Detected: {report.attack_type}\n", style=f"bold {fc}")
    if not is_safe and report.real_world_incident:
        t.append(f"  Real-world: {report.real_world_incident}\n", style="dim")
    console.print(Panel(Align.center(t), border_style=fc, padding=(0,2)))

def show_explanation(report):
    if report.explanation:
        console.print(Panel(Text(report.explanation, style="dim white"),
            title="[dim]Explanation[/dim]", border_style="dim", padding=(0,1)))
    if report.solidity_analog:
        console.print(Panel(
            Syntax(report.solidity_analog, "solidity", theme="monokai",
                   line_numbers=False, word_wrap=True),
            title="[dim]Solidity Analog[/dim]", border_style="dim yellow", padding=(0,1)))

def show_summary_table(reports):
    console.print()
    console.print(Rule("[bold cyan]  AUDIT SESSION SUMMARY  [/bold cyan]", style="cyan"))
    tbl = Table(box=box.ROUNDED, header_style="bold cyan", border_style="dim cyan",
                padding=(0,1), expand=True)
    tbl.add_column("ID",      style="dim",       width=4)
    tbl.add_column("Command", style="bold white", min_width=24)
    tbl.add_column("Grammar", justify="center",  width=12)
    tbl.add_column("Walk",    justify="center",  width=10)
    tbl.add_column("Circuit", justify="center",  width=10)
    tbl.add_column("VERDICT", justify="center",  width=14)
    tbl.add_column("Conf",    justify="right",   width=7)
    tbl.add_column("Attack Type",                min_width=22)
    for r in reports:
        gi = "[bright_green]✓ SAFE[/]" if r.grammar_verdict == "SAFE" else "[bright_red]✗ VULN[/]"
        wi = "[bright_green]✓ SAFE[/]" if r.walk_verdict    == "SAFE" else "[bright_red]✗ VULN[/]"
        ci = "[bright_green]✓ SAFE[/]" if r.circuit_verdict == "SAFE" else "[bright_red]✗ VULN[/]"
        vt = "[bold bright_green]  ✓ SAFE  [/]" if r.is_safe else "[bold bright_red]  ✗ VULN  [/]"
        tbl.add_row(r.scenario_id, r.command, gi, wi, ci, vt,
                    f"{r.final_confidence:.0%}", r.attack_type or "[dim]—[/dim]")
    console.print(tbl)
    safe_n = sum(1 for r in reports if r.is_safe)
    console.print(f"\n  [bold]{len(reports)}[/bold] scenarios audited   "
                  f"[bright_green]{safe_n} SAFE[/bright_green]   "
                  f"[bright_red]{len(reports)-safe_n} VULNERABLE[/bright_red]\n")


class AuditDashboard:
    def __init__(self, pause_phases=0.6, pause_scenarios=1.2):
        self.pause_phases    = pause_phases
        self.pause_scenarios = pause_scenarios
        self._reports = []

    def start(self): print_banner()

    def audit_scenario(self, scenario, report):
        console.print()
        console.print(Rule(
            f"[bold]Scenario {scenario['id']}[/bold]  [dim]{scenario['description']}[/dim]",
            style="bright_cyan"))
        console.print(f"  [dim]Command:[/dim] [bold white]{scenario['command']}[/bold white]\n")
        run_phase("Phase 1", "Grammar parsing + CFG validation...", 0.7)
        show_grammar_panel(report)
        time.sleep(self.pause_phases)
        run_phase("Phase 2", "Quantum walk simulation...", 0.6)
        show_walk_panel(report)
        time.sleep(self.pause_phases)
        run_phase("Phase 3", "Qiskit AerSimulator (1024 shots)...", 0.9)
        show_circuit_panel(report)
        time.sleep(self.pause_phases)
        show_verdict_banner(report)
        show_explanation(report)
        time.sleep(self.pause_scenarios)
        self._reports.append(report)

    def show_summary(self):
        if self._reports:
            show_summary_table(self._reports)
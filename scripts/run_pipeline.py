"""
Main Pipeline Runner
Orchestrates all PhD defence preparation agents.

Usage:
  .venv/Scripts/python scripts/run_pipeline.py --all              (full pipeline, sequential)
  .venv/Scripts/python scripts/run_pipeline.py --all --parallel   (run independent agents concurrently)
  .venv/Scripts/python scripts/run_pipeline.py --resume           (skip agents already done — safe after partial run)
  .venv/Scripts/python scripts/run_pipeline.py --status           (show what's done vs missing, no API calls)
  .venv/Scripts/python scripts/run_pipeline.py --agent thesis_analyst   (single agent)
  .venv/Scripts/python scripts/run_pipeline.py --quick            (questions + answers + flashcards only)
  .venv/Scripts/python scripts/run_pipeline.py --force            (regenerate all outputs)
  .venv/Scripts/python scripts/run_pipeline.py --research nox_mitigation
"""

import sys
import time
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Add parent dir for imports
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "agents"))

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
import importlib
import importlib.util

console = Console()

AGENT_MAP = {
    "thesis_analyst":       ("01_thesis_analyst",      "Thesis Analyst",          "Analyzes thesis PDF chapter by chapter"),
    "automl_analyst":       ("02_automl_analyst",       "AutoML Analyst",          "Analyzes AutoML presentation (171 slides)"),
    "question_generator":   ("03_question_generator",   "Question Generator",      "Generates professor questions by archetype"),
    "answer_drafter":       ("04_answer_drafter",       "Answer Drafter",          "Drafts 3-tier answers for hard questions"),
    "weakness_analyst":     ("05_weakness_analyst",     "Weakness Analyst",        "Identifies weak points + counter-arguments"),
    "flashcard_maker":      ("06_flashcard_maker",      "Flashcard Maker",         "Creates 100+ Q&A flashcards"),
    "study_planner":        ("07_study_planner",        "Study Planner",           "Generates 7-day daily schedule"),
    "deep_researcher":      ("08_deep_researcher",      "Deep Researcher",         "Deep-dives into specific weak topic areas"),
    "professor_griller":    ("09_professor_griller",    "Professor Griller",       "Simulates real examiners from input/notes/examiners.md"),
    "thesis_summary":       ("10_thesis_summary",       "Thesis Summary",          "Tiered spoken summaries: 1/3/5-sentence + 1/3/5-min"),
    "committee_qa":         ("11_committee_qa",         "Committee Q&A",           "Polished answers to known committee questions from candidate notes"),
    "deep_technical_qa":    ("12_deep_technical_qa",    "Deep Technical Q&A",      "Research-backed answers: MPC design, engine, DNN modelling, AutoML"),
}

FULL_PIPELINE_ORDER = [
    "thesis_analyst",
    "automl_analyst",
    "weakness_analyst",
    "question_generator",
    "professor_griller",
    "answer_drafter",
    "thesis_summary",       # needs weakness_report; runs after weakness_analyst
    "committee_qa",         # uses embedded candidate notes; independent
    "deep_technical_qa",    # uses embedded questions + prior outputs as context
    "flashcard_maker",
    "deep_researcher",
    "study_planner",
]

QUICK_PIPELINE = [
    "question_generator",
    "answer_drafter",
    "flashcard_maker",
]

# Agents that can safely run in parallel (no inter-agent dependencies).
# study_planner runs last so it can reference all prior outputs.
PARALLEL_GROUPS = [
    # Group 1: heavy file I/O — thesis PDF + PPTX parsing
    ["thesis_analyst", "automl_analyst"],
    # Group 2: all pure-Claude calls, independent of each other
    ["weakness_analyst", "question_generator", "professor_griller",
     "flashcard_maker", "answer_drafter", "thesis_summary", "committee_qa",
     "deep_technical_qa", "deep_researcher"],
    # Group 3: synthesizes everything — must be last
    ["study_planner"],
]

# Maps each agent to its primary output file(s) for --status and --resume checks.
# Format: (subfolder, filename)
AGENT_OUTPUTS = {
    "thesis_analyst":     [("summaries",         "thesis_analysis.md")],
    "automl_analyst":     [("summaries",         "automl_analysis.md")],
    "question_generator": [("questions_answers", "all_questions.md")],
    "answer_drafter":     [("questions_answers", "answers_thesis.md"),
                           ("questions_answers", "answers_automl.md")],
    "weakness_analyst":   [("weak_points",       "weakness_report.md"),
                           ("weak_points",       "automl_weakness_report.md"),
                           ("literature_gaps",   "literature_gaps.md")],
    "flashcard_maker":    [("summaries",         "flashcards.md")],
    "study_planner":      [("study_plan",        "7day_plan.md")],
    "deep_researcher":    [("literature_gaps",   "gp_mpc_research.md")],  # proxy: any one topic file
    "professor_griller":  [("questions_answers", "professor_griller.md")],
    "thesis_summary":     [("summaries",         "thesis_summary.md")],
    "committee_qa":       [("questions_answers", "committee_qa.md")],
    "deep_technical_qa":  [("questions_answers", "deep_technical_qa.md")],
}

OUTPUT_DIR = ROOT / "output"


def agent_is_done(agent_key: str) -> bool:
    """Return True only if ALL primary outputs for this agent already exist on disk."""
    outputs = AGENT_OUTPUTS.get(agent_key, [])
    if not outputs:
        return False
    return all((OUTPUT_DIR / sub / fname).exists() for sub, fname in outputs)


def run_agent(agent_key: str, force: bool = False, topic: str = None, angle: str = "balanced") -> bool:
    module_name, display_name, description = AGENT_MAP[agent_key]

    console.print(f"\n[bold cyan]>> {display_name}[/bold cyan]  [dim]{description}[/dim]")
    t0 = time.time()

    try:
        spec = importlib.util.spec_from_file_location(
            module_name,
            ROOT / "agents" / f"{module_name}.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if agent_key == "deep_researcher":
            module.run(topic=topic, force=force)
        elif agent_key == "thesis_summary":
            module.run(force=force, angle=angle)
        else:
            module.run(force=force)

        elapsed = time.time() - t0
        console.print(f"  [green]OK Done[/green] in {elapsed:.1f}s")
        return True

    except Exception as e:
        console.print(f"  [red]FAIL Failed: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False


def run_agents_parallel(agent_keys: list[str], force: bool = False) -> dict[str, bool]:
    """Run a group of agents concurrently. Returns {agent_key: success}."""
    results = {}
    with ThreadPoolExecutor(max_workers=len(agent_keys)) as executor:
        futures = {
            executor.submit(run_agent, key, force): key
            for key in agent_keys
        }
        for future in as_completed(futures):
            key = futures[future]
            try:
                results[key] = future.result()
            except Exception as e:
                console.print(f"  [red]FAIL {key} raised: {e}[/red]")
                results[key] = False
    return results


def print_output_summary():
    output_dir = ROOT / "output"
    files = [f for f in sorted(output_dir.rglob("*.md")) if ".obsidian" not in str(f)]

    console.print("\n[bold]Output Summary:[/bold]")
    table = Table(show_header=True, header_style="bold")
    table.add_column("File", style="cyan")
    table.add_column("Size")
    table.add_column("Status")
    for f in files:
        size = f.stat().st_size
        rel = str(f.relative_to(output_dir))
        table.add_row(rel, f"{size:,} bytes", "[green]OK[/green]")
    console.print(table)

    # Check if all primary outputs exist -- print Obsidian callout
    all_done = all(agent_is_done(k) for k in FULL_PIPELINE_ORDER)
    if all_done:
        console.print(Panel.fit(
            "[bold green]All outputs generated![/bold green]\n\n"
            "Next step — open your Obsidian study vault:\n"
            "  1. Launch Obsidian\n"
            "  2. Open folder as vault: [cyan]output/[/cyan] (inside this repo)\n"
            "  3. Click 'Trust author and enable plugins'\n"
            "  4. Open [cyan]summaries/flashcards.md[/cyan] -> card icon -> Review Flashcards\n\n"
            "Flashcards ready. Start with [cyan]questions_answers/professor_griller.md[/cyan].",
            title="Study Time",
            style="green"
        ))


def main():
    parser = argparse.ArgumentParser(description="PhD Defence Preparation Pipeline")
    parser.add_argument("--all", action="store_true", help="Run full pipeline")
    parser.add_argument("--parallel", action="store_true", help="Run independent agents concurrently (use with --all)")
    parser.add_argument("--quick", action="store_true", help="Run quick pipeline (Q&A + flashcards)")
    parser.add_argument("--resume", action="store_true", help="Skip agents whose outputs already exist (safe re-run, no duplicate calls)")
    parser.add_argument("--agent", help="Run a single agent by name")
    parser.add_argument("--research", help="Run deep researcher on a specific topic")
    parser.add_argument("--angle", default="balanced",
                        choices=["balanced", "control", "ml", "practical"],
                        help="Framing angle for thesis_summary agent (default: balanced)")
    parser.add_argument("--force", action="store_true", help="Regenerate all outputs (overwrites existing)")
    parser.add_argument("--status", action="store_true", help="Show which outputs exist vs missing, then exit")
    parser.add_argument("--list", action="store_true", help="List available agents")
    args = parser.parse_args()

    console.print(Panel.fit(
        "[bold]PhD Defence Preparation System[/bold]\n"
        "Powered by Claude | see CLAUDE.md for thesis details",
        style="blue"
    ))

    if args.list:
        table = Table(show_header=True, header_style="bold")
        table.add_column("Agent Key")
        table.add_column("Name")
        table.add_column("Description")
        for key, (_, name, desc) in AGENT_MAP.items():
            table.add_row(key, name, desc)
        console.print(table)
        return

    if args.status:
        console.print("\n[bold]Pipeline Status — existing outputs:[/bold]")
        table = Table(show_header=True, header_style="bold")
        table.add_column("Agent")
        table.add_column("Output File(s)")
        table.add_column("Status")
        for key in FULL_PIPELINE_ORDER:
            outputs = AGENT_OUTPUTS.get(key, [])
            for sub, fname in outputs:
                path = OUTPUT_DIR / sub / fname
                exists = path.exists()
                size = f"{path.stat().st_size:,} bytes" if exists else "—"
                status_str = f"[green]DONE {size}[/green]" if exists else "[red]MISSING[/red]"
                table.add_row(AGENT_MAP[key][1], f"{sub}/{fname}", status_str)
        console.print(table)
        # Show quick commands for missing ones
        missing = [k for k in FULL_PIPELINE_ORDER if not agent_is_done(k)]
        if missing:
            console.print("\n[yellow]Run missing agents (one at a time — safe, no duplicate calls):[/yellow]")
            for k in missing:
                console.print(f"  .venv/Scripts/python scripts/run_pipeline.py --agent {k}")
        else:
            console.print("\n[green]All outputs present. Run --force to regenerate.[/green]")
        return

    if args.research:
        run_agent("deep_researcher", force=args.force, topic=args.research)
        print_output_summary()
        return

    if args.agent:
        if args.agent not in AGENT_MAP:
            console.print(f"[red]Unknown agent: {args.agent}[/red]")
            console.print(f"Available: {', '.join(AGENT_MAP.keys())}")
            sys.exit(1)
        run_agent(args.agent, force=args.force, angle=args.angle)
        print_output_summary()
        return

    if args.resume:
        missing = [k for k in FULL_PIPELINE_ORDER if not agent_is_done(k)]
        if not missing:
            console.print("[green]All outputs already exist. Nothing to do. Use --force to regenerate.[/green]")
            print_output_summary()
            return
        console.print(f"[yellow]Resume mode: {len(missing)} agent(s) missing — running sequentially[/yellow]")
        for k in missing:
            console.print(f"  [dim]skipping already-done agents...[/dim]" if k != missing[0] else "")
        results = {}
        for agent_key in missing:
            console.print(f"\n[cyan]>> Running: {AGENT_MAP[agent_key][1]}[/cyan]")
            results[agent_key] = run_agent(agent_key, angle=args.angle)
        console.print("\n[bold]Resume Complete[/bold]")
        for key, success in results.items():
            status = "[green]OK[/green]" if success else "[red]FAIL[/red]"
            console.print(f"  {status} {AGENT_MAP[key][1]}")
        print_output_summary()
        return

    if args.quick:
        pipeline = QUICK_PIPELINE
        console.print("[yellow]Quick pipeline: Q&A + flashcards only[/yellow]")
        results = {}
        for agent_key in pipeline:
            results[agent_key] = run_agent(agent_key, force=args.force)
    elif args.all and args.parallel:
        console.print(f"[yellow]Full pipeline — parallel mode ({len(PARALLEL_GROUPS)} groups)[/yellow]")
        results = {}
        for i, group in enumerate(PARALLEL_GROUPS, 1):
            if len(group) == 1:
                console.print(f"\n[bold]Group {i}:[/bold] {group[0]}")
                results[group[0]] = run_agent(group[0], force=args.force)
            else:
                console.print(f"\n[bold]Group {i} (parallel):[/bold] {', '.join(group)}")
                results.update(run_agents_parallel(group, force=args.force))
    elif args.all:
        pipeline = FULL_PIPELINE_ORDER
        console.print(f"[yellow]Full pipeline: {len(pipeline)} agents (sequential)[/yellow]")
        results = {}
        for agent_key in pipeline:
            results[agent_key] = run_agent(agent_key, force=args.force, angle=args.angle)
    else:
        parser.print_help()
        return

    console.print("\n[bold]Pipeline Complete[/bold]")
    for key, success in results.items():
        status = "[green]OK[/green]" if success else "[red]FAIL[/red]"
        console.print(f"  {status} {AGENT_MAP[key][1]}")

    print_output_summary()


if __name__ == "__main__":
    main()

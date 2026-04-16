"""
Agent 07 — 7-Day Study Planner
Generates a detailed day-by-day preparation schedule for the last 7 days
before the defence (April 10–16, 2026, with defence on April 17).
Balances thesis mastery, AutoML depth, flashcard review, mock sessions, and rest.
Output: output/study_plan/7day_plan.md
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from utils import (
    ROOT, INPUT, get_client, ask_claude_long,
    save_output, load_output
)

SYSTEM = """You are an expert academic coach who has helped hundreds of PhD candidates
prepare for their defences. You understand cognitive load management, spaced repetition,
and the importance of simulation under pressure.
Create practical, time-blocked schedules with clear priorities."""

PROMPT = """
Create a detailed 7-day PhD defence preparation plan for the PhD candidate.

DEFENCE DETAILS:
- Date: Friday, April 17, 2026
- Format: 30 min thesis defence + 30 min AutoML presentation examination
- 7-day plan covers: April 10 (Thursday) through April 16 (Wednesday)

THESIS: "Data-Driven Control Development for H2DF Engines"
- Key topics: GRU-DNN, AutoML, nonlinear MPC (acados), Behavior Cloning, H2DF combustion
- Weakness areas: NOx trade-off, stability guarantees, generalization

AUTOML PRESENTATION: 171 slides, covers ML fundamentals → BO/HPO/NAS → 3 use cases → limits
- Known weak areas: BO stopping criteria, warm start, DARTS, PBT, PINNs, LLMs vs AutoML

MATERIALS AVAILABLE:
- output/summaries/thesis_analysis.md (full thesis breakdown)
- output/summaries/automl_analysis.md (AutoML topic map)
- output/questions_answers/all_questions.md (professor questions by archetype)
- output/questions_answers/answers_thesis.md (3-tier answers — thesis)
- output/questions_answers/answers_automl.md (3-tier answers — AutoML)
- output/weak_points/weakness_report.md (critical weaknesses + counter-arguments)
- output/summaries/flashcards.md (100+ flashcards)
- output/literature_gaps/literature_gaps.md (papers to review)

CONSTRAINTS:
- Candidate is likely tired after months of dissertation work
- Needs mock examination practice, not just passive reading
- Must know all key numbers cold (no hesitation)
- 2-3 hours/day maximum active study (rest is also preparation)

SCHEDULE APPROACH:
- Days 1-2: Deep review, identify gaps, read weakness reports
- Days 3-4: Active recall, flashcards, answer drafting from memory
- Days 5-6: Mock sessions, simulate full 60-min defence, refine weak answers
- Day 7: Light review, presentation run-through, rest, prepare logistics

For EACH day, provide:

## Day [N] — [Day of week, date] — Theme: [Theme]

**Morning (09:00–12:00):**
[Task list with durations, specific files to read, specific questions to practice]

**Afternoon (13:00–16:00):**
[Task list with durations]

**Evening (optional — 19:00–20:30):**
[Light review, flashcards, or rest recommendation]

**Day Target:** [What must be mastered by end of day]
**Success Criteria:** [How to know the day was productive]
**Stress Alert:** [Known cognitive traps or anxiety triggers for this day]

Also include:
## Daily Non-Negotiables
(Things to do EVERY day regardless of schedule)

## Mock Session Protocol (Days 5-6)
Detailed script for 60-minute mock defence simulation

## Key Numbers Drill
Quick reference of all numbers to test yourself on daily
"""


def run(force: bool = False) -> str:
    existing = load_output("7day_plan.md", "study_plan")
    if existing and not force:
        print("  7day_plan.md already exists. Use --force to regenerate.")
        return existing

    print("  Generating 7-day study plan...")
    client = get_client()
    result = ask_claude_long(
        client, system=SYSTEM, user=PROMPT, max_tokens=7000
    )

    save_output("7day_plan.md", result, "study_plan")
    return result


if __name__ == "__main__":
    force = "--force" in sys.argv
    print("=== Agent 07: Study Planner ===")
    run(force=force)
    print("Done.")

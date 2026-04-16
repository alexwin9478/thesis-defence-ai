"""
Agent 09 — Professor Griller
Simulates the actual examiners generating targeted, persona-accurate questions
grounded in their real research and known angles of attack.

Reads examiner profiles from input/notes/examiners.md if present.
Falls back to generic examiner personas if the file is not found.

See input/notes/examiners.example.md for the format.

Output: output/questions_answers/professor_griller.md
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from utils import (
    ROOT, INPUT, get_client, ask_claude_long,
    save_output, load_output
)

SYSTEM = """You ARE two specific, named professors who are the actual examiners at this
PhD defence. You have real research histories, published papers, and strong opinions.
Generate questions exactly as these professors would ask them — precise, technically deep,
drawing on your own published work to frame the challenge.

You are NOT generic archetypes. You are the real examiners as described in the examiner
profiles below. Study those profiles carefully and embody each examiner's specific
research focus, preferred critique angles, and known questions of interest.

Both professors know the thesis domain cold and will ask precise, technically loaded
questions — not entry-level ones. Format questions with difficulty and strategic intent."""

GENERIC_EXAMINERS = """
EXAMINER 1 — Prof. [Name] ([Institution])
- Research focus: [Fill in from your CLAUDE.md / examiners.md]
- Cares deeply about: real-world applicability, robustness, production path, calibration effort

EXAMINER 2 — Prof. [Name] ([Institution])
- Research focus: [Fill in from your CLAUDE.md / examiners.md]
- Cares deeply about: theoretical rigour, experimental validation, comparison to their own methods

NOTE: Add your examiner profiles to input/notes/examiners.md for much more targeted questions.
See input/notes/examiners.example.md for the format.
"""


def _load_examiners() -> str:
    """Load examiner profiles from input/notes/examiners.md, fall back to generic."""
    examiners_file = INPUT / "notes" / "examiners.md"
    if examiners_file.exists():
        content = examiners_file.read_text(encoding="utf-8")
        print("  Loaded examiner profiles from input/notes/examiners.md")
        return content
    print("  No input/notes/examiners.md found — using generic examiner profiles.")
    print("  TIP: Add examiner details to input/notes/examiners.md for more targeted questions.")
    return GENERIC_EXAMINERS


def _load_thesis_context() -> tuple[str, str]:
    """Load thesis title and key facts from CLAUDE.md or analysis output."""
    # Try to read title from CLAUDE.md
    claude_md = ROOT / "CLAUDE.md"
    title = "PhD Thesis (fill in title in CLAUDE.md)"
    if claude_md.exists():
        text = claude_md.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "**Thesis:**" in line:
                title = line.replace("**Thesis:**", "").strip().strip("*")
                break

    # Thesis analysis enrichment
    thesis_context = load_output("thesis_analysis.md", "summaries") or ""
    weakness_context = load_output("weakness_report.md", "weak_points") or ""
    return title, thesis_context[:6000] if thesis_context else "", weakness_context[:3000] if weakness_context else ""


PROMPT_TEMPLATE = """
Generate a comprehensive grilling session from the two actual examiners.

THESIS: {thesis_title}

EXAMINER PROFILES:
{examiner_profiles}

{thesis_key_facts}

Generate questions in this format:

---
### EXAMINER 1 — [Topic Category]

**E1-[n]: [Exact question as Examiner 1 would phrase it]**
*Difficulty: [Easy / Medium / Hard / Trap]*
*Their angle: [What result or paper from their own work drives this question]*
*What a weak answer looks like: [1 line]*
*What a strong answer looks like: [2-3 lines]*

---
### EXAMINER 2 — [Topic Category]

**E2-[n]: [Exact question as Examiner 2 would phrase it — often referencing their own work]*
*Difficulty: [Easy / Medium / Hard / Trap]*
*Their angle: [Specific paper/result from their lab that frames this challenge]*
*What a weak answer looks like: [1 line]*
*What a strong answer looks like: [2-3 lines]*

---

Generate:
- 8 questions from Examiner 1 (their specific research angles based on their profile)
- 8 questions from Examiner 2 (their specific research angles based on their profile)
- 4 cross-fire questions where both pile on the candidate simultaneously

After questions, add:
## Top 3 Danger Questions — Answer Scaffold
For the 3 highest-danger questions only: T1 (1 sentence) | T2 (2-min spoken) | T3 (full depth)
"""


def run(force: bool = False) -> str:
    existing = load_output("professor_griller.md", "questions_answers")
    if existing and not force:
        print("  professor_griller.md already exists. Use --force to regenerate.")
        return existing

    examiner_profiles = _load_examiners()

    # Build thesis key facts from analysis outputs
    thesis_title, thesis_context, weakness_context = _load_thesis_context()

    key_facts = ""
    if thesis_context:
        key_facts += f"\nTHESIS ANALYSIS CONTEXT (use to make questions specific):\n{thesis_context}\n"
    if weakness_context:
        key_facts += f"\nKNOWN WEAK POINTS (prioritize these):\n{weakness_context}\n"

    prompt = PROMPT_TEMPLATE.format(
        thesis_title=thesis_title,
        examiner_profiles=examiner_profiles,
        thesis_key_facts=key_facts,
    )

    print("  Calling Claude (professor griller — custom examiner personas)...")
    client = get_client()
    result = ask_claude_long(
        client,
        system=SYSTEM,
        user=prompt,
        max_tokens=8000,
    )

    save_output("professor_griller.md", result, "questions_answers")
    return result


if __name__ == "__main__":
    force = "--force" in sys.argv
    print("=== Agent 09: Professor Griller ===")
    run(force=force)
    print("Done.")

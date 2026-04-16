"""
Agent 11 — Committee Q&A Polisher
Takes raw candidate notes for known committee questions and produces
polished, defence-ready answers with 3-tier structure where appropriate.

These are questions the candidate has already thought through — this agent
turns rough notes into clean, spoken answers.

SETUP: Place your notes in input/notes/committee_questions.md before running.
See input/notes/committee_questions.example.md for the required format.

Output: output/questions_answers/committee_qa.md
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from utils import INPUT, get_client, ask_claude_long, save_output, load_output

SYSTEM = """You are a PhD candidate preparing for your thesis defence.
You write defence answers in first person, confidently and precisely.
For each question, produce a POLISHED spoken answer — not bullet points, but fluent sentences
the candidate can actually say aloud. Where the candidate's notes contain specific facts,
real-world examples, or numbers, preserve them exactly. Do not invent new claims.
Use the candidate's own framing — just elevate the language and structure."""


def _load_candidate_notes() -> str:
    """Load candidate notes from input/notes/committee_questions.md."""
    notes_file = INPUT / "notes" / "committee_questions.md"
    if notes_file.exists():
        content = notes_file.read_text(encoding="utf-8")
        # Strip comment lines (lines starting with #)
        lines = [l for l in content.splitlines() if not l.strip().startswith("#")]
        return "\n".join(lines).strip()

    raise FileNotFoundError(
        "\n"
        "  committee_questions.md not found in input/notes/\n"
        "\n"
        "  To use this agent:\n"
        "  1. Copy input/notes/committee_questions.example.md to input/notes/committee_questions.md\n"
        "  2. Fill in your own questions and rough notes\n"
        "  3. Re-run this agent\n"
        "\n"
        "  The file format is:\n"
        "    Q: [question text]\n"
        "    Notes: [your rough notes]\n"
        "    ---\n"
        "    Q: [next question]\n"
        "    Notes: [notes]\n"
    )


PROMPT_TEMPLATE = """
Below are raw candidate notes for known committee questions at a PhD defence.
For EACH question, produce a polished, defence-ready answer in fluent English.

Structure each answer as:
### Q: [question as asked]
**One-liner:** [15-word max spoken version for when asked "briefly"]

**Full answer (spoken):**
[2-4 sentences or short paragraphs. Fluent, first-person, confident. Preserve all specific
facts, examples, and numbers from the notes. Do not invent. If the notes reference a figure
to check, note that explicitly as "(verify figure reference)" so the candidate knows.]

**If probed further:**
[1-2 bullet points of depth the candidate can add if the examiner pushes]

---

CANDIDATE NOTES:
{candidate_notes}
"""


def run(force: bool = False) -> str:
    existing = load_output("committee_qa.md", "questions_answers")
    if existing and not force:
        print("  committee_qa.md already exists. Use --force to regenerate.")
        return existing

    candidate_notes = _load_candidate_notes()

    print("  Polishing committee Q&A from candidate notes...")
    client = get_client()
    prompt = PROMPT_TEMPLATE.format(candidate_notes=candidate_notes)
    result = ask_claude_long(client, system=SYSTEM, user=prompt, max_tokens=8000)

    header = (
        "# Committee Q&A — Polished Answers\n\n"
        "> Generated from candidate's own notes. Verify figure references marked "
        "`(verify figure reference)` before the defence.\n\n"
        "---\n\n"
    )
    save_output("committee_qa.md", header + result, "questions_answers")
    return result


if __name__ == "__main__":
    force = "--force" in sys.argv
    print("=== Agent 11: Committee Q&A Polisher ===")
    run(force=force)
    print("Done.")

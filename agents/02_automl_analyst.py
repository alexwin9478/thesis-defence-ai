"""
Agent 02 — AutoML Presentation Analyst
Extracts structure, key arguments, and knowledge requirements from the
AutoML defence presentation (171 slides). Identifies what the candidate
must deeply know for the 30-minute AutoML examination.
Output: output/summaries/automl_analysis.md
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from utils import (
    ROOT, INPUT, get_client, extract_pptx_structured, slides_to_text,
    ask_claude_long, save_output, load_output
)

def _find_pptx(folder: Path, label: str) -> Path:
    """Find the first PPTX in the given input subfolder."""
    pptxs = sorted(folder.glob("*.pptx"))
    if pptxs:
        return pptxs[0]
    raise FileNotFoundError(
        f"No PPTX found in {folder} for '{label}'. "
        "Copy your presentation into the appropriate input/ subfolder."
    )


PPTX_PATH = None   # resolved at runtime: input/presentation/*.pptx
NOTES_PATH = None  # resolved at runtime: input/notes/*.pptx

SYSTEM = """You are an expert in AutoML, hyperparameter optimization, neural architecture
search, and machine learning systems. You are helping a PhD candidate prepare for
a 30-minute expert examination on AutoML. Be technical, precise, and strategic."""

PROMPT_TEMPLATE = """
The candidate must defend a 30-minute presentation on Automated Machine Learning (AutoML).
The presentation covers the following topic areas (extracted from 171 slides):

PRESENTATION CONTENT:
{pptx_text}

KNOWN PROFESSOR QUESTIONS (from candidate's notes):
{known_questions}

Based on this content, provide:

## 1. Topic Map
List all major AutoML topics covered, with depth indicator (basic/intermediate/deep).

## 2. Core Concepts to Master
For each key concept, provide:
- One-line definition
- Why it matters in the thesis context
- Common examiner trap question

## 3. Key Comparisons the Candidate Must Know
(e.g., Grid vs Random vs BO, HPO vs NAS vs joint, BO variants)

## 4. Mathematical Foundations
List the equations/theory the candidate must be able to derive or explain at the board.

## 5. Anticipated Hard Questions
Generate 20 hard examiner questions with brief answer guidance.

## 6. Known Weak Points in the Presentation
Identify slides or claims that may invite challenge.

## 7. Bridge Answers
For each topic where candidate may be unsure, provide a "bridge" to their own H2DF work.
"""


def run(force: bool = False) -> str:
    existing = load_output("automl_analysis.md", "summaries")
    if existing and not force:
        print("  automl_analysis.md already exists. Use --force to regenerate.")
        return existing

    try:
        pptx_path = _find_pptx(INPUT / "presentation", "AutoML presentation")
        notes_path = _find_pptx(INPUT / "notes", "professor questions")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print(f"  Extracting AutoML presentation: {pptx_path.name}")
    slides = extract_pptx_structured(pptx_path)
    # Focus on main content slides (skip backup/bibliography)
    main_slides = [s for s in slides if s["slide_num"] <= 65]
    pptx_text = slides_to_text(main_slides, include_notes=True)

    print(f"  Extracting professor questions: {notes_path.name}")
    notes_slides = extract_pptx_structured(notes_path)
    known_q_slides = [s for s in notes_slides if s["slide_num"] in [10, 11, 12, 15, 20]]
    known_questions = slides_to_text(known_q_slides, include_notes=False)

    print("  Calling Claude (AutoML analysis)...")
    client = get_client()
    result = ask_claude_long(
        client,
        system=SYSTEM,
        user=PROMPT_TEMPLATE.format(
            pptx_text=pptx_text[:120_000],
            known_questions=known_questions[:8000],
        ),
        max_tokens=16000,
    )

    save_output("automl_analysis.md", result, "summaries")
    return result


if __name__ == "__main__":
    force = "--force" in sys.argv
    print("=== Agent 02: AutoML Analyst ===")
    run(force=force)
    print("Done.")

"""
Agent 03 — Professor Question Generator
Generates a comprehensive set of exam questions from multiple professor archetypes.
Covers both the thesis (30 min) and the AutoML presentation (30 min).
Output: output/questions_answers/all_questions.md
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from utils import (
    ROOT, INPUT, get_client, ask_claude_long,
    save_output, load_output,
    load_claude_md, extract_thesis_title, CLAUDE_MD_FALLBACK,
)

SYSTEM = """You are simulating a panel of four PhD examination professors with
different expertise and examination styles. Generate rigorous, realistic questions
that real professors would ask during a defence.

The professors are:
1. Prof. CONTROL — Expert in nonlinear control, MPC, stability theory (likely to challenge
   theoretical guarantees, lack of Lyapunov stability, no convexity proof)
2. Prof. ML — Expert in deep learning, generalization, data-driven methods (will attack
   data distribution shifts, GRU choice justification, overfitting, evaluation methodology)
3. Prof. ENGINE — Expert in combustion engines, IC engines, emissions regulations
   (will probe physical understanding, NOx trade-off, fuel injection strategies)
4. Prof. AUTOML — Expert in hyperparameter optimization, NAS, Bayesian optimization
   (will stress-test the AutoML knowledge from the presentation)

Be highly specific. Use exact numbers from the thesis where relevant."""

PROMPT_TEMPLATE = """
Generate exam questions for a PhD defence. TWO parts, 30 min each.

{thesis_context}

Format per professor:
### Prof. [NAME]
**Q[n]: [question]** | Difficulty: Hard/Trap | Tests: [1 line] | Hint: [1-2 lines]

Generate 7 questions per professor (28 total) + 6 cross-topic synthesis questions.
"""


def _build_prompt() -> str:
    """Build the question generation prompt using CLAUDE.md and prior analysis outputs."""
    claude_text = load_claude_md()
    thesis_title = extract_thesis_title(claude_text)

    thesis_analysis = load_output("thesis_analysis.md", "summaries")
    automl_analysis = load_output("automl_analysis.md", "summaries")

    context_parts = [f'Thesis: "{thesis_title}"']
    if thesis_analysis:
        context_parts.append(f"THESIS ANALYSIS (use for specific facts and numbers):\n{thesis_analysis[:2500]}")
    elif claude_text:
        context_parts.append(f"THESIS CONTEXT (from CLAUDE.md):\n{claude_text[:2500]}")
    else:
        context_parts.append(f"THESIS CONTEXT: {CLAUDE_MD_FALLBACK}")

    if automl_analysis:
        context_parts.append(f"AUTOML PRESENTATION CONTEXT:\n{automl_analysis[:1500]}")

    return PROMPT_TEMPLATE.format(thesis_context="\n\n".join(context_parts))


def run(force: bool = False) -> str:
    existing = load_output("all_questions.md", "questions_answers")
    if existing and not force:
        print("  all_questions.md already exists. Use --force to regenerate.")
        return existing

    print("  Calling Claude (question generation)...")
    client = get_client()
    result = ask_claude_long(
        client,
        system=SYSTEM,
        user=_build_prompt(),
        max_tokens=6000,
    )

    save_output("all_questions.md", result, "questions_answers")
    return result


if __name__ == "__main__":
    force = "--force" in sys.argv
    print("=== Agent 03: Question Generator ===")
    run(force=force)
    print("Done.")

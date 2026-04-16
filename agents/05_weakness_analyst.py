"""
Agent 05 — Weakness Analyst & Deep Researcher
Identifies technical/methodological weak points in both the thesis and the
AutoML presentation. For each weakness, provides a prepared counter-argument
and identifies relevant literature the candidate should know.
Output: output/weak_points/weakness_report.md
         output/literature_gaps/literature_gaps.md
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from utils import (
    ROOT, INPUT, get_client, ask_claude_long,
    save_output, load_output,
    load_claude_md, extract_thesis_title, CLAUDE_MD_FALLBACK,
)

SYSTEM = """You are a rigorous academic reviewer who specializes in identifying
methodological weaknesses in PhD theses. Your role is to:
1. Find every legitimate technical weakness
2. Identify missing baselines or comparisons
3. Find unsupported claims
4. Identify gaps relative to state-of-the-art
5. Suggest literature the candidate MUST know to defend against attacks
Be honest and thorough — the candidate needs to know the real weaknesses."""

WEAKNESS_PROMPT_TEMPLATE = """
Perform a deep critical analysis of this PhD thesis:
"{thesis_title}"

THESIS CONTRIBUTIONS:
{thesis_contributions}

PROVIDE:

## Critical Weaknesses (Thesis)

For each weakness:
### W[n]: [Title]
**Category:** [Theoretical / Experimental / Methodological / Presentation]
**Description:** [Detailed explanation of the weakness]
**Severity:** [Low / Medium / High / Fatal]
**Prepared Counter-Argument:**
> [How candidate should respond]
**Supporting Literature:** [Key papers/methods the candidate should cite]

Focus areas (adapt to the specific thesis domain):
- Absence of stability/safety guarantees (Lyapunov, ISS, etc.)
- Performance trade-offs with regulatory or safety implications
- Missing baseline comparisons to state-of-the-art alternatives
- Generalization beyond the training or experimental envelope
- Data representativeness and distribution shift
- Deployed controller safety when it diverges from the reference controller
- Computational cost justification for training/optimization runs
- Choice of model architecture vs modern alternatives
- Absence of uncertainty quantification
- Limited operating range tested
- Constraint handling: what happens when soft constraints are violated?

## Literature Gaps

List papers the candidate MUST read before the defence:
### [Paper reference]
**Why relevant:** [How it relates to a weakness or attack]
**Key argument to know:** [The one thing to know from this paper]

## Comparison to State of Art

How does this thesis compare to established alternative approaches in its domain?
"""

AUTOML_WEAKNESS_PROMPT = """
Perform a critical analysis of the AutoML presentation for PhD defence.

The presentation covers:
- ML fundamentals and AutoML motivation
- Grid/Random/Bayesian optimization search strategies
- 3 use cases: Battery CNN, RL tuning, Hardware-aware NAS for combustion
- MLOps integration
- Limitations and future (Agentic AI, LLMs)

Identify:

## AutoML Presentation Weaknesses

### Conceptual Gaps
- What AutoML theory is likely missing or underexplained?
- Are there important algorithms not covered (SMAC, BOHB, Hyperband, ASHA)?
- Is the BO/TPE explanation mathematically rigorous enough?

### Known Controversial Claims
- "Do Mechanical Engineers still need Data Scientists?" — how to defend this?
- Claims about AutoML vs Agentic AI — what's the state of the art really?

### Missing Comparisons
- What evaluation baselines are missing?
- Are the use case results contextualized against SOTA?

## AutoML Literature to Know
List 10 essential AutoML papers/books the candidate must be familiar with:
- AutoML: Methods, Systems, Challenges (Hutter, Kotthoff, Vanschoren)
- Optuna, Hyperopt, Ray Tune, SMAC
- BOHB: Robust and Efficient Hyperparameter Optimization
- DARTS: Differentiable Architecture Search
- Population Based Training (Jaderberg et al.)
For each: one-line summary and why it may come up.
"""


def _build_weakness_prompt() -> str:
    """Build the weakness analysis prompt using CLAUDE.md and prior outputs."""
    claude_text = load_claude_md()
    thesis_title = extract_thesis_title(claude_text)

    thesis_analysis = load_output("thesis_analysis.md", "summaries")
    if thesis_analysis:
        contributions = (
            "Derived from the thesis analysis below. Use specific numbers and claims as found:\n\n"
            + thesis_analysis[:3000]
        )
    elif claude_text:
        contributions = (
            "Derived from the candidate's CLAUDE.md context below:\n\n"
            + claude_text[:3000]
        )
    else:
        contributions = CLAUDE_MD_FALLBACK
    return WEAKNESS_PROMPT_TEMPLATE.format(
        thesis_title=thesis_title,
        thesis_contributions=contributions,
    )


def run(force: bool = False) -> None:
    client = get_client()
    weakness_prompt = _build_weakness_prompt()

    existing_weakness = load_output("weakness_report.md", "weak_points")
    if existing_weakness and not force:
        print("  weakness_report.md already exists. Use --force to regenerate.")
    else:
        print("  Analyzing thesis weaknesses...")
        weakness = ask_claude_long(
            client, system=SYSTEM, user=weakness_prompt, max_tokens=16000
        )
        save_output("weakness_report.md", weakness, "weak_points")

    existing_automl_weakness = load_output("automl_weakness_report.md", "weak_points")
    if existing_automl_weakness and not force:
        print("  automl_weakness_report.md already exists. Use --force to regenerate.")
    else:
        print("  Analyzing AutoML presentation weaknesses...")
        automl_weakness = ask_claude_long(
            client, system=SYSTEM, user=AUTOML_WEAKNESS_PROMPT, max_tokens=12000
        )
        save_output("automl_weakness_report.md", automl_weakness, "weak_points")

    existing_lit = load_output("literature_gaps.md", "literature_gaps")
    if existing_lit and not force:
        print("  literature_gaps.md already exists. Use --force to regenerate.")
    else:
        print("  Generating literature gap analysis...")
        lit_prompt = (
            weakness_prompt
            + "\n\nFocus ONLY on the Literature Gaps and Comparison to State of Art sections."
        )
        lit = ask_claude_long(client, system=SYSTEM, user=lit_prompt, max_tokens=8000)
        save_output("literature_gaps.md", lit, "literature_gaps")


if __name__ == "__main__":
    force = "--force" in sys.argv
    print("=== Agent 05: Weakness Analyst ===")
    run(force=force)
    print("Done.")

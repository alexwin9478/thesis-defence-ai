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
    save_output, load_output
)

SYSTEM = """You are a rigorous academic reviewer who specializes in identifying
methodological weaknesses in PhD theses. Your role is to:
1. Find every legitimate technical weakness
2. Identify missing baselines or comparisons
3. Find unsupported claims
4. Identify gaps relative to state-of-the-art
5. Suggest literature the candidate MUST know to defend against attacks
Be honest and thorough — the candidate needs to know the real weaknesses."""

WEAKNESS_PROMPT = """
Perform a deep critical analysis of this PhD thesis:
"A Data-Driven Control Development Workflow for Hydrogen-Diesel Dual-Fuel Engines"

THESIS CONTRIBUTIONS:
1. GRU-DNN trained on >99,000 H2DF engine cycles (predicts IMEP, NOx, PM, MPRR)
2. AutoML with 27,000 parallelized BO-TPE trials on HPC for architecture optimization
3. Nonlinear MPC using acados with DNN as learned dynamics:
   - IMEP: +27.8% vs baseline diesel controller
   - Soot: -61.1%
   - CO2 potential: -39.7%
   - NOx: +105.1% (significant increase)
4. Behavior Cloning (BC): replicates MPC, <2ms inference, deployed on ESP32/Raspberry Pi
5. End-to-end toolchain (data acquisition to test bench) in under 1 day

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

Focus areas:
- Absence of stability/safety guarantees (Lyapunov, ISS, etc.)
- NOx increase — regulatory implications
- No comparison to GP-MPC, koopman operator MPC, other DNN-MPC approaches
- Generalization beyond training envelope
- Data representativeness and distribution shift
- BC safety: no formal guarantees when MPC and BC diverge
- AutoML 27k trials — computational cost justification
- GRU vs modern alternatives (Transformer, S4, Mamba)
- No uncertainty quantification in DNN predictions
- Limited operating range tested
- Soft constraints — what happens when violated?

## Literature Gaps

List papers the candidate MUST read before the defence:
### [Paper reference]
**Why relevant:** [How it relates to a weakness or attack]
**Key argument to know:** [The one thing to know from this paper]

## Comparison to State of Art

How does this thesis compare to:
1. GP-MPC approaches (Hewing et al., Berkenkamp et al.)
2. Koopman operator MPC
3. PINN-MPC
4. Other DNN-MPC approaches
5. Standard behavior cloning for control systems
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


def run(force: bool = False) -> None:
    client = get_client()

    existing_weakness = load_output("weakness_report.md", "weak_points")
    if existing_weakness and not force:
        print("  weakness_report.md already exists. Use --force to regenerate.")
    else:
        print("  Analyzing thesis weaknesses...")
        weakness = ask_claude_long(
            client, system=SYSTEM, user=WEAKNESS_PROMPT, max_tokens=16000
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
            WEAKNESS_PROMPT
            + "\n\nFocus ONLY on the Literature Gaps and Comparison to State of Art sections."
        )
        lit = ask_claude_long(client, system=SYSTEM, user=lit_prompt, max_tokens=8000)
        save_output("literature_gaps.md", lit, "literature_gaps")


if __name__ == "__main__":
    force = "--force" in sys.argv
    print("=== Agent 05: Weakness Analyst ===")
    run(force=force)
    print("Done.")

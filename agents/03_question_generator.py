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
    save_output, load_output
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
Thesis: "Data-Driven Control for H2DF Engines" | Presentation: AutoML (171 slides)

THESIS FACTS: GRU-DNN, >99k cycles, IMEP/NOx/PM/MPRR outputs; AutoML 27k HPC trials (TPE);
NMPC via acados: +27.8% IMEP, -61.1% soot, -39.7% CO2, +105.1% NOx;
BC: <2ms inference, ESP32/Raspberry Pi. Weak points: NOx trade-off, no Lyapunov proof,
no convexity proof, BC safety, TRL prototype, GRU vs LSTM, generalization.

AUTOML TOPICS: Grid/Random/BO-TPE; HPO/NAS/joint; 3 use-cases; MLOps; abstraction trap;
Agentic AI vs AutoML.

Format per professor:
### Prof. [NAME]
**Q[n]: [question]** | Difficulty: Hard/Trap | Tests: [1 line] | Hint: [1-2 lines]

Generate 7 questions per professor (28 total) + 6 cross-topic synthesis questions.
"""


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
        user=PROMPT_TEMPLATE,
        max_tokens=6000,
    )

    save_output("all_questions.md", result, "questions_answers")
    return result


if __name__ == "__main__":
    force = "--force" in sys.argv
    print("=== Agent 03: Question Generator ===")
    run(force=force)
    print("Done.")

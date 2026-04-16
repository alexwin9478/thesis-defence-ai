"""
Agent 04 — Answer Drafter
For each identified professor question, drafts a 3-tier answer:
  Tier 1: One-sentence summary (for when asked "briefly")
  Tier 2: 2-minute spoken answer
  Tier 3: Full technical depth with numbers and references
Output: output/questions_answers/answers_thesis.md
         output/questions_answers/answers_automl.md
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from utils import (
    ROOT, INPUT, get_client, ask_claude_long,
    save_output, load_output
)

SYSTEM = """You are the PhD candidate preparing defence answers. Write in first person.
Be confident, precise, use exact numbers. Acknowledge weaknesses then redirect to contributions.
Numbers: >99k cycles, 27k AutoML trials, +27.8% IMEP, -61.1% soot, -39.7% CO2,
+105.1% NOx, <2ms BC inference, <1 day toolchain, GRU, acados, RPi+ESP32."""

THESIS_QA_PROMPT = """
Draft 3-tier defence answers for the 8 hardest thesis questions.

QUESTIONS:
1. "Your NOx increases 105%. How do you defend this?"
2. "Where are the Lyapunov stability guarantees for your MPC?"
3. "Does your DNN generalize beyond the training envelope?"
4. "What safety guarantees does behavior cloning provide vs MPC?"
5. "Why GRU and not LSTM, Transformer, or a physics-based model?"
6. "How does your approach compare to GP-MPC or LSTM-MPC?"
7. "What is the TRL and what's needed for production deployment?"
8. "How would an OEM trust a controller developed in one day?"

Format per question:
### Q: [question]
**T1:** [1 sentence] | **T2:** [2-min spoken paragraph] | **T3:** [full technical depth + future work]
**Bridge:** [fallback phrase if memory fails]
"""

AUTOML_QA_PROMPT = """
Draft 3-tier defence answers for the 8 hardest AutoML presentation questions.

QUESTIONS:
1. "Why BO-TPE over evolutionary/genetic algorithms?"
2. "What is the stopping criterion for BO? How do you know when to stop?"
3. "What is DARTS and how is it more efficient than standard NAS?"
4. "What is the warm-start problem in AutoML?"
5. "What are PINNs and could they replace your GRU?"
6. "What is the abstraction trap in AutoML?"
7. "How do LLMs/foundation models challenge the future of AutoML?"
8. "How did you choose the HPO search space boundaries?"

Same 3-tier format: T1 (1 sentence) | T2 (2-min spoken) | T3 (full depth) | Bridge (fallback)
"""


def run(force: bool = False) -> None:
    client = get_client()

    # Thesis answers
    existing_thesis = load_output("answers_thesis.md", "questions_answers")
    if existing_thesis and not force:
        print("  answers_thesis.md already exists. Use --force to regenerate.")
    else:
        print("  Drafting thesis answers (this may take ~2 min)...")
        thesis_answers = ask_claude_long(
            client, system=SYSTEM, user=THESIS_QA_PROMPT, max_tokens=7000
        )
        save_output("answers_thesis.md", thesis_answers, "questions_answers")

    # AutoML answers
    existing_automl = load_output("answers_automl.md", "questions_answers")
    if existing_automl and not force:
        print("  answers_automl.md already exists. Use --force to regenerate.")
    else:
        print("  Drafting AutoML answers (this may take ~2 min)...")
        automl_answers = ask_claude_long(
            client, system=SYSTEM, user=AUTOML_QA_PROMPT, max_tokens=7000
        )
        save_output("answers_automl.md", automl_answers, "questions_answers")


if __name__ == "__main__":
    force = "--force" in sys.argv
    print("=== Agent 04: Answer Drafter ===")
    run(force=force)
    print("Done.")

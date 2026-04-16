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
    save_output, load_output,
    load_claude_md, extract_thesis_title, CLAUDE_MD_FALLBACK,
)

SYSTEM_TEMPLATE = """You are the PhD candidate preparing defence answers. Write in first person.
Be confident, precise, use exact numbers from your thesis. Acknowledge weaknesses then redirect to contributions.

YOUR THESIS CONTEXT (use specific details from here in every answer):
{thesis_facts}"""

THESIS_QA_PROMPT = """
Draft 3-tier defence answers for the key hard thesis questions derived from the thesis context above.

Cover these fundamental challenge areas every examiner will probe:
1. The most significant performance trade-off in your thesis results — how do you defend it?
2. Where are the formal stability/safety guarantees for your controller?
3. Does your model generalize beyond the training data envelope?
4. What safety guarantees does your embedded/deployed controller provide vs the full controller?
5. Why did you choose your specific neural network architecture over alternatives?
6. How does your approach compare to established state-of-the-art methods in your domain?
7. What is the Technology Readiness Level and what is needed for production deployment?
8. How would an end user or industry partner trust a controller developed with your workflow?

Format per question:
### Q: [question tailored to this specific thesis]
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
5. "What are PINNs and could they replace your model?"
6. "What is the abstraction trap in AutoML?"
7. "How do LLMs/foundation models challenge the future of AutoML?"
8. "How did you choose the HPO search space boundaries?"

Same 3-tier format: T1 (1 sentence) | T2 (2-min spoken) | T3 (full depth) | Bridge (fallback)
"""


def _build_system() -> str:
    """Build the answer-drafter system prompt using CLAUDE.md and prior outputs."""
    claude_text = load_claude_md()
    thesis_analysis = load_output("thesis_analysis.md", "summaries")

    if thesis_analysis:
        facts = thesis_analysis[:2000]
    elif claude_text:
        facts = claude_text[:2000]
    else:
        facts = CLAUDE_MD_FALLBACK
    return SYSTEM_TEMPLATE.format(thesis_facts=facts)


def run(force: bool = False) -> None:
    client = get_client()
    system = _build_system()

    # Thesis answers
    existing_thesis = load_output("answers_thesis.md", "questions_answers")
    if existing_thesis and not force:
        print("  answers_thesis.md already exists. Use --force to regenerate.")
    else:
        print("  Drafting thesis answers (this may take ~2 min)...")
        thesis_answers = ask_claude_long(
            client, system=system, user=THESIS_QA_PROMPT, max_tokens=7000
        )
        save_output("answers_thesis.md", thesis_answers, "questions_answers")

    # AutoML answers
    existing_automl = load_output("answers_automl.md", "questions_answers")
    if existing_automl and not force:
        print("  answers_automl.md already exists. Use --force to regenerate.")
    else:
        print("  Drafting AutoML answers (this may take ~2 min)...")
        automl_answers = ask_claude_long(
            client, system=system, user=AUTOML_QA_PROMPT, max_tokens=7000
        )
        save_output("answers_automl.md", automl_answers, "questions_answers")


if __name__ == "__main__":
    force = "--force" in sys.argv
    print("=== Agent 04: Answer Drafter ===")
    run(force=force)
    print("Done.")

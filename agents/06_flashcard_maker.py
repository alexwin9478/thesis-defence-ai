"""
Agent 06 — Flashcard Maker
Creates Q&A flashcards in two batches (50 cards each) to stay within
CLI token limits. Merges into a single output file.
Output: output/summaries/flashcards.md
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from utils import (
    ROOT, INPUT, get_client, ask_claude_long,
    save_output, load_output
)

SYSTEM = """Create PhD defence flashcards for Obsidian Spaced Repetition plugin.

FORMAT RULES — follow exactly:
- Single-line answer: Question::Answer
- Multi-line answer:
  Question
  ?
  Answer line 1
  Answer line 2

No **Q:** / **A:** markup. No --- separators. Plain text only.
Use exact numbers. Keep answers tight."""

BATCH_1_PROMPT = """
Flashcard Batch 1 of 2 — 50 cards.

Single-line: What does IMEP stand for?::Indicated Mean Effective Pressure — average pressure over piston cycle, proxy for engine work output
Multi-line example:
What are the 3 gates in a GRU?
?
1. Update gate (z) — how much past state to keep
2. Reset gate (r) — how much past state to forget
3. New gate — candidate hidden state


## Cat 1: Key Numbers (15 cards)
All quantitative results: IMEP %, soot %, CO2 %, NOx %, training samples,
AutoML trials, inference time, development time, HPC trials, platforms.

## Cat 2: Acronyms & Definitions (15 cards)
H2DF, IMEP, MPRR, MPC, BC, GRU, RCP, HES, AutoML, HPO, NAS, TPE, BO, HPC,
PRBS, acados, RCCI, EGR, SCR, TRL.

## Cat 3: GRU / DNN Technical (10 cards)
GRU gates vs LSTM gates; why GRU chosen; training pipeline; input/output features;
data collection method (PRBS); overfitting countermeasures; validation approach.

## Cat 4: MPC Formulation (10 cards)
Receding horizon principle; acados role; soft constraints via slack; cost function
components; prediction horizon; why DNN as dynamics model; MPC vs BC trade-off.
"""

BATCH_2_PROMPT = """
Flashcard Batch 2 of 2 — 50 cards. Same format as batch 1 (:: for single-line, ? for multi-line).


## Cat 5: AutoML Core Concepts (15 cards)
HPO vs NAS vs joint; BO-TPE vs BO-GP; acquisition functions (EI/UCB/PI);
Hyperband / BOHB / ASHA; PBT; DARTS; surrogate model; warm-start problem;
search space design; stopping criterion.

## Cat 6: Combustion Fundamentals (10 cards)
Otto cycle / IMEP calculation; Zeldovich NOx mechanism; PM/soot formation;
NOx-PM trade-off; MPRR safety limit; hydrogen substitution ratio; HES definition.

## Cat 7: Control Theory (10 cards)
Lyapunov stability; ISS; terminal constraint; behavior cloning guarantees (and lack of);
DNN-MPC vs GP-MPC; what BC cannot guarantee; why BC for deployment.

## Cat 8: Key Comparisons (15 cards)
GRU vs LSTM vs Transformer; DNN-MPC vs GP-MPC; AutoML vs manual tuning;
Grid vs Random vs BO; MPC vs BC (cost, safety, deployment); TPE vs GP-BO;
H2 vs diesel combustion characteristics; Examiner 1 vs Examiner 2 critique angles (from your examiners.md).
"""


def run(force: bool = False) -> str:
    existing = load_output("flashcards.md", "summaries")
    if existing and not force:
        print("  flashcards.md already exists. Use --force to regenerate.")
        return existing

    client = get_client()

    # Batch 1
    print("  Generating flashcards batch 1/2 (50 cards)...")
    batch1 = ask_claude_long(client, system=SYSTEM, user=BATCH_1_PROMPT, max_tokens=7000)

    # Batch 2
    print("  Generating flashcards batch 2/2 (50 cards)...")
    batch2 = ask_claude_long(client, system=SYSTEM, user=BATCH_2_PROMPT, max_tokens=7000)

    # YAML frontmatter with flashcards tag — required by Obsidian Spaced Repetition plugin
    # Tag must be "flashcards" (plural) matching flashcardTags in data.json
    result = "---\ntags: [flashcards]\n---\n# PhD Defence Flashcards\n\n#flashcards\n\n## Batch 1: Numbers, Acronyms, DNN, MPC\n\n" \
             + batch1 + "\n\n## Batch 2: AutoML, Combustion, Control, Comparisons\n\n" \
             + batch2

    save_output("flashcards.md", result, "summaries")
    return result


if __name__ == "__main__":
    force = "--force" in sys.argv
    print("=== Agent 06: Flashcard Maker ===")
    run(force=force)
    print("Done.")

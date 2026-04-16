"""
Agent 10 — Thesis Summary Generator
Generates cascading spoken summaries of the thesis for the examination opening question:
"Please summarise your thesis in X minutes."

Each tier extends the previous one verbatim — the candidate practises the shortest
version first and learns longer versions as additive blocks.

Tiers:
  - 1 sentence  (~15 words, pure essence — the anchor for all longer versions)
  - 3 sentences (~45 words, extends 1-sentence)
  - 5 sentences (~75 words, extends 3-sentence)
  - 1 minute    (~150 words, extends 5-sentence into spoken prose)
  - 3 minutes   (~400 words, extends 1-minute with workflow stages + key results)
  - 5 minutes   (~700 words, extends 3-minute with boundary conditions + outlook)

Optional --angle flag steers the framing:
  control    -> emphasise MPC + real-time deployment angle
  ml         -> emphasise DNN + AutoML + architecture search angle
  practical  -> emphasise toolchain speed, TRL, production path
  (default)  -> balanced, strongest contribution first

EXAMINATION CONTEXT: These summaries are for Part 2 of the private examination.
The examiners will spontaneously ask "summarise your thesis" at a length they choose.
You will NOT be presenting slides — this is a pure spoken answer.

Output: output/summaries/thesis_summary.md
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from utils import ROOT, INPUT, get_client, ask_claude_long, save_output, load_output

SYSTEM = """You are a PhD candidate preparing for a thesis examination.
You speak confidently, precisely, and never sound defensive.
You answer the question that was asked — no more, no less.
All summaries must be in first person. Use exact numbers from the thesis.
Never use filler phrases like "In this thesis I..." — start directly with the contribution.

EXAMINATION CONTEXT: These summaries are for Part 2 of the private examination.
The examiners will spontaneously ask "summarise your thesis" at a length they choose.
You will NOT be presenting slides — this is a pure spoken answer.
Deliver it directly, confidently, and without any visual aids."""

PROMPT_TEMPLATE = """
These summaries prepare you for when the examiners spontaneously say:
"Please summarise your thesis in X minutes."
You will NOT be presenting slides. Deliver these as spoken answers — directly and confidently.

CRITICAL REQUIREMENT FOR CASCADING STRUCTURE:
Each tier MUST open with the complete text of the previous tier, copied verbatim.
Do NOT paraphrase or rephrase. This allows the candidate to practise the shortest
version first and learn each longer version purely as an extension.

Angle: {angle_instruction}

THESIS CONTEXT:
{thesis_contributions}

---

Generate EXACTLY this structure:

## 1 sentence (~15 words)
[One sentence. The single most important thing. No numbers needed.
This is your anchor — EVERY longer version must begin with this exact sentence.]

---

## 3 sentences (~45 words)
COPY your 1-sentence answer here VERBATIM, then add EXACTLY 2 more sentences:
[Sentence 1: VERBATIM copy of your 1-sentence answer above — word for word]
[Sentence 2: The gap — what was missing before this thesis AND what you built]
[Sentence 3: The headline result — one quantitative outcome and what it enables]

---

## 5 sentences (~75 words)
COPY your 3-sentence block VERBATIM, then add EXACTLY 2 more sentences:
[Sentences 1-3: VERBATIM copy of your 3-sentence answer above — word for word]
[Sentence 4: The key enabling technical choice and precisely why it mattered]
[Sentence 5: The "so what" — what this means for the next engineer or researcher,
and why the methodology generalises beyond this specific system]

---

## 1 minute (~150 words)
OPEN with your 5-sentence block expanded into fluent spoken prose (lightly — do not
rephrase, only smooth the transitions). Then continue the story:
[After the 5-sentence core: add the high-level framing. No acronyms without brief
definition. No limitations at this tier — confident, forward. End with the single
most impressive number.]

---

## 3 minutes (~400 words)
OPEN with your 1-minute version VERBATIM. Then add:
[Walk through the workflow stages (data -> surrogate -> controller -> deployment).
State the key results as a group. Introduce ONE core limitation honestly.
Mention toolchain speed as the "so what" for industry.]

---

## 5 minutes (~700 words)
OPEN with your 3-minute version VERBATIM. Then add:
[Boundary conditions paragraph: where this works, where it does not, what the TRL means.
Close with the forward-looking statement — what the next researcher must do to take
this to production, and how your automated toolchain makes that iteration faster.]

---

## Steering notes (for the candidate)
[3-5 bullet points: what to expand if the examiner probes, what to cut if time runs
short, which number to land on if interrupted, and how to bridge to the next
examination section when the examiner signals the transition.]
"""

ANGLE_INSTRUCTIONS = {
    "control":   "Emphasise the MPC contribution and real-time embedded deployment. Lead with the controller performance numbers. Frame the DNN and AutoML as enabling infrastructure for the control goal.",
    "ml":        "Emphasise the DNN architecture and AutoML contribution. Lead with the parallelised search and what it automated. Frame the MPC as the downstream application proving the model quality.",
    "practical": "Emphasise the end-to-end toolchain and time-to-deployment story. Lead with 'under 1 day vs months'. Frame everything through the lens of: what does this mean for an engineer at an OEM or research lab?",
    "balanced":  "Start with the strongest single contribution, then show how the prior steps enabled it, then close with the deployment story. Balanced across all contributions.",
}


def _load_thesis_contributions() -> str:
    """Load thesis context from CLAUDE.md and prior analysis outputs."""
    contributions = ""

    # Try CLAUDE.md first
    claude_md = ROOT / "CLAUDE.md"
    if claude_md.exists():
        text = claude_md.read_text(encoding="utf-8")
        # Extract contributions and key numbers sections
        in_section = False
        lines = []
        for line in text.splitlines():
            if "Core thesis contributions" in line or "Must-Know Numbers" in line:
                in_section = True
            elif line.startswith("## ") and in_section:
                in_section = False
            if in_section:
                lines.append(line)
        if lines:
            contributions += "\n".join(lines[:60]) + "\n"

    # Enrich with analysis outputs if available
    thesis_context = load_output("thesis_analysis.md", "summaries")
    weakness_context = load_output("weakness_report.md", "weak_points")

    if thesis_context:
        contributions += f"\n\nFROM THESIS ANALYSIS:\n{thesis_context[:4000]}"
    if weakness_context:
        contributions += f"\n\nKEY WEAKNESSES TO REFERENCE AT THE RIGHT TIER:\n{weakness_context[:2000]}"

    if not contributions.strip():
        contributions = (
            "Fill in CLAUDE.md with your thesis contributions and key numbers.\n"
            "Run thesis_analyst first to generate thesis_analysis.md for richer summaries."
        )

    return contributions


def run(force: bool = False, angle: str = "balanced") -> str:
    output_file = f"thesis_summary_{angle}.md" if angle != "balanced" else "thesis_summary.md"

    existing = load_output(output_file, "summaries")
    if existing and not force:
        print(f"  {output_file} already exists. Use --force to regenerate.")
        return existing

    angle_instruction = ANGLE_INSTRUCTIONS.get(angle, ANGLE_INSTRUCTIONS["balanced"])
    thesis_contributions = _load_thesis_contributions()

    prompt = PROMPT_TEMPLATE.format(
        angle_instruction=angle_instruction,
        thesis_contributions=thesis_contributions,
    )

    print(f"  Generating cascading thesis summary (angle: {angle})...")
    client = get_client()
    result = ask_claude_long(client, system=SYSTEM, user=prompt, max_tokens=6000)

    save_output(output_file, result, "summaries")
    return result


if __name__ == "__main__":
    force = "--force" in sys.argv
    angle = "balanced"
    for arg in sys.argv[1:]:
        if arg.startswith("--angle="):
            angle = arg.split("=", 1)[1]
        elif arg in ("control", "ml", "practical", "balanced"):
            angle = arg
    print("=== Agent 10: Thesis Summary Generator ===")
    print(f"  Angle: {angle}")
    run(force=force, angle=angle)
    print("Done.")

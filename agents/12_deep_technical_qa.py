"""
Agent 12 — Deep Technical Q&A
Generates research-backed answers to hard technical questions on:
  - Your specific methodology (controller design, model choices, deployment)
  - Data-driven / surrogate modelling
  - AutoML methodology (BO vs alternatives, NAS, stopping criteria)
  - General ML+control questions relevant to your domain

Reads domain-specific context from CLAUDE.md and prior agent outputs.
Optional override: add input/notes/deep_questions.md for fully custom questions.

Two batches to stay within token budget.
Output: output/questions_answers/deep_technical_qa.md
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from utils import ROOT, INPUT, get_client, ask_claude_long, save_output, load_output

SYSTEM = """You are an expert in data-driven control, machine learning, and the domain
of the candidate's thesis. You are helping a PhD candidate prepare precise, technically
rigorous answers to hard examiner questions. Each answer must:
- Be factually correct and cite relevant literature where it strengthens the answer
- Acknowledge genuine limitations honestly before pivoting to what was done and why
- Be speakable — clear sentences the candidate can say aloud under pressure
- Include a one-liner "if interrupted" fallback at the end of each answer"""

# Generic thesis/methodology questions — adapted from thesis context loaded at runtime
THESIS_QUESTIONS_TEMPLATE = """
For each question below, provide:
**Q: [question]**
*One-liner:* [15 words max -- the answer if cut off mid-sentence]
*Full answer:* [3-6 sentences, technically precise, speakable]
*If probed:* [1-2 deeper points the candidate can add]

---

THESIS CONTEXT (use to make all answers specific to this candidate's work):
{thesis_context}

---

QUESTIONS -- METHODOLOGY & SYSTEM-SPECIFIC:

Q1: Why did you choose a data-driven / surrogate model approach rather than a first-principles model?
(Frame answer using the candidate's specific system and the limitations of physics-based modelling for it)

Q2: Why were transients / dynamic operation excluded from the scope?
(Frame around time constants, model complexity, and what would be needed to extend it)

Q3: How did you define the prediction horizon for the MPC, and what drove that choice?
(Include: computational tractability vs optimality trade-off, real-time requirements, horizon length justification)

Q4: What does "optimality" actually mean in your MPC formulation?
(Frame: local, model-based optimality vs global; comparison to the baseline controller)

Q5: What sensors does the controller need at runtime? Could cheaper alternatives replace them?
(Frame around what the model requires as inputs vs what's production-available)

Q6: Why this specific set of control inputs? What about other actuators?
(Frame: which actuators were controlled, which were held fixed as disturbances and why)

Q7: How does your data collection approach scale as the system complexity grows?
(Frame: combinatorial growth, what would change if one more variable were added, safer alternatives)

Q8: What safety mechanisms governed data collection? Are there safer alternatives?
(Frame: how unsafe operating points were detected and prevented during excitation)

Q9: How would you transfer this approach from your specific test setup to a production system?
(Frame: what changes for multi-unit / multi-variant deployment, TRL gap, transfer learning)

Q10: How did you handle model uncertainty and cycle-to-cycle or measurement variation?
(Frame: point prediction vs uncertainty quantification; what Bayesian extensions would add)

Q11: Why was [key input variable] not included in the model?
(Frame: data availability, variance during training, what would be needed to add it)

Q12: What is the boundary of your system's operating envelope and what happens outside it?
(Frame: training coverage, extrapolation risk, out-of-distribution detection options)

Q13: What is the key environmental / condition variable you have NOT validated against?
(Frame: the most important unvalidated operating condition and what testing would be needed)
"""

# AutoML questions — generic, domain-independent
AUTOML_QUESTIONS = """
For each question below, provide:
**Q: [question]**
*One-liner:* [15 words max]
*Full answer:* [3-6 sentences, technically precise, citable]
*If probed:* [1-2 deeper points]

---

CONTEXT: Use the candidate's specific AutoML setup (search strategy, trial count, compute
infrastructure) as context where relevant. Generic AutoML knowledge should be grounded in
the candidate's actual choices.

THESIS AUTOML CONTEXT:
{automl_context}

---

QUESTIONS -- AUTOML:

Q1: Why Bayesian Optimisation / TPE over Evolutionary or Genetic Algorithms?
(BO sample efficiency for expensive objectives; EA advantages for very high dimensions)

Q2: Why not use RL instead of AutoML for architecture search?
(RL-NAS: Zoph & Le 2017; computational cost; DARTS and BOHB as alternatives)

Q3: How can prior knowledge be incorporated? Interactive/Informed BO (IBO)?
(Warm-starting from prior runs, meta-learning, Bayesian priors, SMAC instance features)

Q4: Population-Based Training (PBT) -- what is it and how does it compare to your approach?
(Dynamic hyperparameter schedules vs static; exploit-explore in PBT; when PBT is better)

Q5: Treating architecture as hyperparameters -- is this too naive and inefficient?
(Black-box vs DARTS gradient-based; ENAS; when black-box BO-TPE is competitive)

Q6: DARTS and DAG-based efficient NAS -- how do they work and when are they better?
(Differentiable architecture search, bi-level optimisation, collapse problems, RNN NAS)

Q7: How do you avoid overfitting in AutoML? Pruning and dataset size considerations?
(MedianPruner, early stopping, temporal leakage in time-series, held-out test set)

Q8: Physics-Informed Neural Networks (PINNs) -- could they improve your model's safety?
(PDE residual in loss; extrapolation; data efficiency; deriving physics for your domain)

Q9: BO stopping criteria -- how do you decide when to stop?
(Fixed budget; EI below threshold; surrogate convergence; statistical tests; future work)

Q10: Why are some hyperparameters discrete and others continuous? How were boundaries set?
(Architecture vs training HPs; TPE's handling; boundaries from compute budget and literature)

Q11: LLMs and foundation models -- how do they challenge the future of AutoML?
(LLM as optimizer; OPRO; warm start from task description; limitations for domain-constrained search)

Q12: The initial value problem in BO -- how do you handle cold start?
(LHS / Sobol sequences; meta-learning from prior runs; human-in-the-loop warm start)
"""


def _load_thesis_context() -> tuple[str, str]:
    """Load thesis and AutoML context from CLAUDE.md and prior outputs."""
    thesis_ctx_parts = []
    automl_ctx_parts = []

    # Read from CLAUDE.md
    claude_md = ROOT / "CLAUDE.md"
    if claude_md.exists():
        text = claude_md.read_text(encoding="utf-8")
        thesis_ctx_parts.append(text[:3000])

    # Prior analysis outputs
    thesis_analysis = load_output("thesis_analysis.md", "summaries")
    automl_analysis = load_output("automl_analysis.md", "summaries")
    weakness = load_output("weakness_report.md", "weak_points")

    if thesis_analysis:
        thesis_ctx_parts.append(f"THESIS ANALYSIS:\n{thesis_analysis[:2500]}")
    if weakness:
        thesis_ctx_parts.append(f"KEY WEAKNESSES:\n{weakness[:1500]}")
    if automl_analysis:
        automl_ctx_parts.append(f"AUTOML ANALYSIS:\n{automl_analysis[:3000]}")

    thesis_context = "\n\n".join(thesis_ctx_parts) if thesis_ctx_parts else (
        "Fill in CLAUDE.md with your thesis details and run thesis_analyst first."
    )
    automl_context = "\n\n".join(automl_ctx_parts) if automl_ctx_parts else (
        "Fill in CLAUDE.md with your AutoML details and run automl_analyst first."
    )

    return thesis_context, automl_context


def _load_custom_questions() -> tuple[str, str] | None:
    """Load custom question batches from input/notes/deep_questions.md if present."""
    q_file = INPUT / "notes" / "deep_questions.md"
    if not q_file.exists():
        return None
    print("  Loaded custom questions from input/notes/deep_questions.md")
    content = q_file.read_text(encoding="utf-8")
    # Split into two batches at "## Part 2" or "--- AUTOML ---" markers
    if "## Part 2" in content:
        parts = content.split("## Part 2", 1)
        return parts[0].strip(), "## Part 2" + parts[1].strip()
    return content, None


def run(force: bool = False) -> str:
    existing = load_output("deep_technical_qa.md", "questions_answers")
    if existing and not force:
        print("  deep_technical_qa.md already exists. Use --force to regenerate.")
        return existing

    thesis_context, automl_context = _load_thesis_context()
    custom = _load_custom_questions()

    if custom:
        batch1_prompt, batch2_prompt_raw = custom
        batch2_prompt = batch2_prompt_raw or AUTOML_QUESTIONS.format(automl_context=automl_context)
    else:
        batch1_prompt = THESIS_QUESTIONS_TEMPLATE.format(thesis_context=thesis_context)
        batch2_prompt = AUTOML_QUESTIONS.format(automl_context=automl_context)

    client = get_client()

    print("  Generating methodology/domain answers (batch 1/2)...")
    batch1 = ask_claude_long(client, system=SYSTEM, user=batch1_prompt, max_tokens=7000)

    print("  Generating AutoML answers (batch 2/2)...")
    batch2 = ask_claude_long(client, system=SYSTEM, user=batch2_prompt, max_tokens=7000)

    header = (
        "# Deep Technical Q&A -- Research-Backed Answers\n\n"
        "> Hard technical questions on your methodology, system-specific design choices, and AutoML.\n"
        "> Each answer includes a one-liner fallback and depth points for follow-up probes.\n\n"
        "---\n\n"
        "## Part 1 -- Methodology & Domain Questions\n\n"
    )
    separator = "\n\n---\n\n## Part 2 -- AutoML Questions\n\n"

    result = header + batch1 + separator + batch2
    save_output("deep_technical_qa.md", result, "questions_answers")
    return result


if __name__ == "__main__":
    force = "--force" in sys.argv
    print("=== Agent 12: Deep Technical Q&A ===")
    run(force=force)
    print("Done.")

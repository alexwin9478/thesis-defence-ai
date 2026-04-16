"""
Agent 08 — Deep Researcher
Performs deep research on specific topics the candidate is weak on.
Can be called on demand for any topic. Uses web search metaphor via Claude's
knowledge base to provide current state-of-the-art understanding.
Output: output/literature_gaps/<topic>_research.md
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from utils import (
    ROOT, INPUT, get_client, ask_claude_long,
    save_output, load_output
)

SYSTEM = """You are a research expert with deep knowledge of:
- Model Predictive Control (MPC) theory and applications
- Data-driven/learning-based control methods
- AutoML, Bayesian Optimization, Neural Architecture Search
- Combustion engines, emissions, hydrogen fuel
- Deep learning: RNNs, GRUs, LSTMs, Transformers

Provide thorough, accurate, and citable responses. Always contextualize
relative to the thesis work on H2DF engine control."""

TOPIC_PROMPTS = {
    "gp_mpc": """
Research: Gaussian Process Model Predictive Control (GP-MPC)
Context: How does this compare to the DNN-MPC approach in the thesis?

Provide:
1. What is GP-MPC? How does it work fundamentally?
2. Key papers (Hewing et al. 2020, Berkenkamp et al., etc.)
3. GP-MPC vs DNN-MPC: pros, cons, computational complexity
4. When does GP-MPC outperform DNN-MPC?
5. Safety guarantees in GP-MPC (confidence bounds, constraint satisfaction)
6. How to answer: "Why didn't you use GP-MPC?"
""",

    "lyapunov_mpc": """
Research: Lyapunov Stability in MPC and Learning-Based Control
Context: The thesis MPC lacks Lyapunov stability guarantees — prepare defence.

Provide:
1. What is Lyapunov stability in the context of MPC?
2. How is stability proven in nominal MPC (terminal cost, terminal set)?
3. Why is stability hard to prove for DNN-MPC?
4. Current approaches: Lyapunov neural networks, stability-constrained learning
5. Key references (Berkenkamp, Wabersich, etc.)
6. Honest answer: "We acknowledge this gap. Here's the risk and mitigation..."
""",

    "behavior_cloning_safety": """
Research: Safety and Guarantees in Behavior Cloning for Control Systems
Context: BC is used to replace MPC on embedded hardware in the thesis.

Provide:
1. What is behavior cloning? Imitation learning taxonomy
2. Distribution shift problem in BC (DAgger, etc.)
3. Safety guarantees: what can and cannot be guaranteed?
4. When does BC fail? Edge cases and OOD behavior
5. How to answer: "What happens when BC and MPC would diverge?"
6. Recent work on safe imitation learning
""",

    "nox_mitigation": """
Research: NOx Mitigation Strategies for H2DF Engines
Context: The thesis shows 105.1% NOx increase — must defend this trade-off.

Provide:
1. Why does H2 increase NOx? (lean/premixed flame temperature)
2. Current NOx mitigation strategies for H2 combustion:
   - EGR (Exhaust Gas Recirculation)
   - Water injection
   - Lean burn / stratified charge
   - SCR (Selective Catalytic Reduction)
   - Injection timing retard
3. Euro VII implications for H2DF NOx
4. How to frame: "105% increase is acknowledged, here's the mitigation roadmap"
5. Regulatory context: why short-term NOx increase can still be justified
""",

    "automl_algorithms": """
Research: Key AutoML Algorithms — Deep Technical Summary
Context: Candidate must answer expert-level questions on AutoML methods.

Provide:
1. Bayesian Optimization fundamentals:
   - Surrogate model (GP vs TPE vs SMAC)
   - Acquisition functions: EI, UCB, PI — formulas and when to use
   - TPE (Tree-structured Parzen Estimator): how it differs from GP-BO

2. Multi-fidelity methods:
   - Hyperband algorithm (SHA + resource halving)
   - BOHB (BO + Hyperband): how they combine
   - ASHA: asynchronous version
   - Successive Halving algorithm

3. Neural Architecture Search:
   - DARTS: Differentiable Architecture Search (how DAG + softmax works)
   - ENAS: Efficient NAS with parameter sharing
   - ProxylessNAS, Once-for-All

4. Population-Based Training (PBT):
   - How it differs from HPO (schedules vs fixed configs)
   - Exploit-and-explore mechanism

5. Key differences: when to use what?
""",

    "dnn_mpc_comparison": """
Research: Comparison of Data-Driven MPC Approaches
Context: Prepare answer for "How does your DNN-MPC compare to state of art?"

Provide a structured comparison table and discussion of:
1. GP-MPC (Hewing, Berkenkamp, Koller)
2. Koopman Operator MPC (linear MPC with Koopman lifted states)
3. DNN/RNN-MPC (this thesis approach)
4. PINN-MPC (physics-informed)
5. Gaussian Mixture Model MPC
6. Tube-based robust MPC with learned uncertainty

For each: computational complexity, data requirements, safety guarantees,
scalability, and suitability for H2DF engine control.
""",
}


def run(topic: str = None, force: bool = False) -> None:
    client = get_client()

    if topic:
        topics_to_run = {topic: TOPIC_PROMPTS.get(topic)}
        if not topics_to_run[topic]:
            print(f"Unknown topic: {topic}. Available: {list(TOPIC_PROMPTS.keys())}")
            sys.exit(1)
    else:
        topics_to_run = TOPIC_PROMPTS

    for topic_name, prompt in topics_to_run.items():
        filename = f"{topic_name}_research.md"
        existing = load_output(filename, "literature_gaps")
        if existing and not force:
            print(f"  {filename} already exists. Use --force to regenerate.")
            continue

        print(f"  Researching: {topic_name}...")
        result = ask_claude_long(
            client,
            system=SYSTEM,
            user=prompt,
            max_tokens=8000,
        )
        save_output(filename, result, "literature_gaps")


if __name__ == "__main__":
    force = "--force" in sys.argv
    topic_arg = None
    for arg in sys.argv[1:]:
        if not arg.startswith("--"):
            topic_arg = arg

    print("=== Agent 08: Deep Researcher ===")
    if topic_arg:
        print(f"  Topic: {topic_arg}")
    else:
        print(f"  Running all topics: {list(TOPIC_PROMPTS.keys())}")
    run(topic=topic_arg, force=force)
    print("Done.")

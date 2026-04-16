"""
Agent 01 — Thesis Analyst
Extracts chapter-by-chapter structure, key claims, methods, results, and
limitations from the thesis PDF.
Output: output/summaries/thesis_analysis.md
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from utils import (
    ROOT, INPUT, get_client, extract_pdf_text,
    ask_claude_long, save_output, load_output
)

def _find_thesis_pdf() -> Path:
    """Find the thesis PDF: prefers input/thesis/*.pdf, falls back to any .pdf there."""
    thesis_dir = INPUT / "thesis"
    pdfs = sorted(thesis_dir.glob("*.pdf"))
    if pdfs:
        return pdfs[0]
    raise FileNotFoundError(
        f"No thesis PDF found in {thesis_dir}. "
        "Copy your thesis PDF into input/thesis/ and re-run."
    )


THESIS_PDF = None  # resolved at runtime via _find_thesis_pdf()

SYSTEM = """You are an expert academic reviewer specializing in control engineering,
machine learning for dynamical systems, and automotive powertrain technology.
You are helping a PhD candidate prepare for their thesis defence.
Be precise, technical, and structured. Use Markdown with clear headings."""

PROMPT_TEMPLATE = """
Analyze this PhD thesis excerpt. The thesis is titled:
"A Data-Driven Control Development Workflow for Hydrogen-Diesel Dual-Fuel Engines"

For EACH chapter, provide:
1. **Core Claim / Contribution**: What does this chapter contribute?
2. **Methods**: Key techniques, algorithms, or frameworks used
3. **Key Results**: Quantitative results with exact numbers
4. **Assumptions**: What assumptions underlie the methods?
5. **Limitations**: What does NOT work, what is NOT shown?
6. **Potential Attack Vectors**: What would a critical examiner challenge here?

Chapter structure from the thesis:
- Introduction (11)
- Fundamentals (12)
- Experimental Setup (13)
- Deep Neural Network (14): GRU-based DNN, >99k H2DF cycles, AutoML with 27k trials
- Model Predictive Control (15): acados, nonlinear MPC with DNN dynamics, 27.8% IMEP improvement
- Behavior Cloning (16): mimics MPC, <2ms inference, ESP32/Raspberry Pi deployment
- Conclusion (17)

THESIS TEXT:
{text}

Provide a comprehensive chapter-by-chapter analysis followed by a synthesis section.
"""


def run(force: bool = False) -> str:
    existing = load_output("thesis_analysis.md", "summaries")
    if existing and not force:
        print("  thesis_analysis.md already exists. Use --force to regenerate.")
        return existing

    try:
        pdf_path = _find_thesis_pdf()
        print(f"  Using thesis: {pdf_path.name}")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print("  Extracting PDF text...")
    # 150k chars ≈ 37k tokens — covers the full thesis structure without
    # overwhelming the CLI subprocess. The key chapters (DNN/MPC/BC) are
    # in the first ~150 pages which fall within this window.
    text = extract_pdf_text(pdf_path, max_chars=150_000)

    print("  Calling Claude (thesis analysis — allow 10+ min via CLI)...")
    client = get_client()
    result = ask_claude_long(
        client,
        system=SYSTEM,
        user=PROMPT_TEMPLATE.format(text=text[:150_000]),
        max_tokens=16000,
    )

    save_output("thesis_analysis.md", result, "summaries")
    return result


if __name__ == "__main__":
    force = "--force" in sys.argv
    print("=== Agent 01: Thesis Analyst ===")
    run(force=force)
    print("Done.")

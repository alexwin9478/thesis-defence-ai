"""
Regression test — verifies that all dynamic context-loading helpers and
_build_* functions work correctly without calling the Claude API.

Tests three scenarios for each agent:
  A) Filled CLAUDE.md  + prior analysis outputs available
  B) Filled CLAUDE.md  + NO prior analysis outputs
  C) Empty/missing CLAUDE.md + NO prior outputs (fallback path)

Also checks that no hardcoded personal data (old exam names, specific numbers
from the H2DF thesis, personal paths) appears in the generated prompts.
"""

import sys
import shutil
import textwrap
from pathlib import Path

# ── point Python at the scripts/ folder ─────────────────────────────────────
REPO = Path("/home/runner/work/thesis-defence-ai/thesis-defence-ai")
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "agents"))

# ── dummy data ───────────────────────────────────────────────────────────────

DUMMY_CLAUDE_MD = textwrap.dedent("""\
    # PhD Defence Preparation

    **Defence Date:** Wednesday, June 18, 2025

    **Thesis:** *"Robust Control of Autonomous Underwater Vehicles Using Reinforcement Learning"*

    **Core thesis contributions:**
    1. Deep RL policy trained on 50,000 simulation episodes
    2. Sim-to-real transfer with domain randomisation (8 physical parameters)
    3. MPC safety layer with 15 ms inference on Jetson Nano
    4. +18.3% trajectory tracking improvement vs PID baseline

    **Key acronyms:** AUV, RL, MPC, DR, SIL, HIL
""")

DUMMY_THESIS_ANALYSIS = textwrap.dedent("""\
    ## Chapter 3 — Deep RL Policy
    **Contribution:** Trained deep RL policy on 50k simulation episodes.
    **Key Results:** +18.3% tracking improvement vs PID.
    **Limitations:** No uncertainty quantification; tested in calm water only.
""")

DUMMY_AUTOML_ANALYSIS = textwrap.dedent("""\
    ## AutoML Section
    Used Optuna TPE with 1,200 trials to tune RL hyperparameters.
""")

DUMMY_WEAKNESS_REPORT = textwrap.dedent("""\
    ## W1: No sim-to-real gap quantification
    **Severity:** High
    **Counter-Argument:** Domain randomisation over 8 physical parameters mitigates this.
""")

# Strings that MUST NOT appear in any generated prompt (old hardcoded personal data)
FORBIDDEN_STRINGS = [
    "Willems",
    "Andert",
    "H2DF engine control",
    "C:\\Git\\phd-defence-prep",
    "27.8% IMEP",
    "+105.1% NOx",
    "-61.1% soot",
    "99,000 H2DF",
    ">99k cycles",
    "27,000 parallelized",
    "April 17, 2026",
    "April 10 (Thursday) through April 16",
]


# ── test helpers ─────────────────────────────────────────────────────────────

PASS = 0
FAIL = 0


def check(label: str, condition: bool, detail: str = ""):
    global PASS, FAIL
    if condition:
        print(f"  PASS  {label}")
        PASS += 1
    else:
        print(f"  FAIL  {label}" + (f"\n        {detail}" if detail else ""))
        FAIL += 1


def assert_contains(label: str, text: str, needle: str):
    check(label, needle in text, f"Expected to find: {repr(needle[:80])}")


def assert_not_contains(label: str, text: str, needle: str):
    check(label, needle not in text, f"Found forbidden string: {repr(needle)}")


def setup_dummy_files(with_claude: bool, with_prior_outputs: bool):
    """Write dummy CLAUDE.md and/or output files into the live repo paths."""
    if with_claude:
        (REPO / "CLAUDE.md").write_text(DUMMY_CLAUDE_MD, encoding="utf-8")
    else:
        if (REPO / "CLAUDE.md").exists():
            (REPO / "CLAUDE.md").unlink()

    summaries = REPO / "output" / "summaries"
    weak_points = REPO / "output" / "weak_points"

    for d in [summaries, weak_points]:
        d.mkdir(parents=True, exist_ok=True)

    if with_prior_outputs:
        (summaries / "thesis_analysis.md").write_text(DUMMY_THESIS_ANALYSIS, encoding="utf-8")
        (summaries / "automl_analysis.md").write_text(DUMMY_AUTOML_ANALYSIS, encoding="utf-8")
        (weak_points / "weakness_report.md").write_text(DUMMY_WEAKNESS_REPORT, encoding="utf-8")
    else:
        for f in ["thesis_analysis.md", "automl_analysis.md"]:
            p = summaries / f
            if p.exists():
                p.unlink()
        p = weak_points / "weakness_report.md"
        if p.exists():
            p.unlink()


def teardown():
    """Remove dummy files to leave the repo in its original state."""
    if (REPO / "CLAUDE.md").exists():
        (REPO / "CLAUDE.md").unlink()
    for sub, name in [
        ("summaries", "thesis_analysis.md"),
        ("summaries", "automl_analysis.md"),
        ("weak_points", "weakness_report.md"),
    ]:
        p = REPO / "output" / sub / name
        if p.exists():
            p.unlink()


# ── import helpers (after repo is on sys.path) ────────────────────────────────

def reload_utils():
    """Re-import utils so cached module state (ROOT/OUTPUT globals) is fresh."""
    import importlib
    import utils as u
    importlib.reload(u)
    return u


# ── individual test suites ───────────────────────────────────────────────────

def test_utils_helpers():
    print("\n=== utils.py helpers ===")
    import utils as u

    # extract_thesis_title — filled value
    text_filled = DUMMY_CLAUDE_MD
    title = u.extract_thesis_title(text_filled)
    check("extract_thesis_title (filled)", "AUV" in title or "Reinforcement" in title,
          f"Got: {title!r}")

    # extract_thesis_title — placeholder
    text_placeholder = '**Thesis:** *"[YOUR THESIS TITLE]"*'
    title_fb = u.extract_thesis_title(text_placeholder)
    check("extract_thesis_title (placeholder → fallback)", "[" in title_fb,
          f"Expected fallback, got: {title_fb!r}")

    # extract_defence_date — filled
    date = u.extract_defence_date(text_filled)
    check("extract_defence_date (filled)", "June" in date or "2025" in date,
          f"Got: {date!r}")

    # extract_defence_date — placeholder
    text_date_ph = "**Defence Date:** [DATE, e.g. Friday, April 17, 2026]"
    date_fb = u.extract_defence_date(text_date_ph)
    check("extract_defence_date (placeholder → fallback)", "[" in date_fb,
          f"Expected fallback, got: {date_fb!r}")

    # extract_defence_date — missing
    date_missing = u.extract_defence_date("no date here")
    check("extract_defence_date (missing → fallback)", "[" in date_missing)

    # load_claude_md — exists
    (REPO / "CLAUDE.md").write_text(DUMMY_CLAUDE_MD, encoding="utf-8")
    loaded = u.load_claude_md()
    check("load_claude_md (file exists)", "Reinforcement" in loaded)

    # load_claude_md — missing
    (REPO / "CLAUDE.md").unlink()
    loaded_empty = u.load_claude_md()
    check("load_claude_md (missing → empty string)", loaded_empty == "")

    # CLAUDE_MD_FALLBACK is a non-empty string
    check("CLAUDE_MD_FALLBACK defined", bool(u.CLAUDE_MD_FALLBACK))


def test_agent03_scenarios():
    print("\n=== Agent 03 — Question Generator (_build_prompt) ===")

    import importlib.util

    def load_agent(num):
        name = {3: "03_question_generator", 4: "04_answer_drafter",
                5: "05_weakness_analyst",   7: "07_study_planner"}[num]
        path = REPO / "agents" / f"{name}.py"
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    a03 = load_agent(3)

    # ── Scenario A: CLAUDE.md + prior outputs ─────────────────────────────
    setup_dummy_files(with_claude=True, with_prior_outputs=True)
    a03 = load_agent(3)
    prompt_A = a03._build_prompt()
    assert_contains("A: thesis title in prompt", prompt_A, "Underwater")
    assert_contains("A: prior analysis in prompt", prompt_A, "THESIS ANALYSIS")
    assert_contains("A: AUV analysis content", prompt_A, "50k simulation")
    assert_contains("A: automl context present", prompt_A, "AUTOML PRESENTATION CONTEXT")
    for bad in FORBIDDEN_STRINGS:
        assert_not_contains(f"A: no forbidden '{bad[:20]}'", prompt_A, bad)

    # ── Scenario B: CLAUDE.md only, no prior outputs ───────────────────────
    setup_dummy_files(with_claude=True, with_prior_outputs=False)
    a03b = load_agent(3)
    prompt_B = a03b._build_prompt()
    assert_contains("B: thesis title in prompt", prompt_B, "Underwater")
    assert_contains("B: CLAUDE.md context used", prompt_B, "CANDIDATE CONTEXT" if "CANDIDATE" in prompt_B else "CLAUDE.md")
    for bad in FORBIDDEN_STRINGS:
        assert_not_contains(f"B: no forbidden '{bad[:20]}'", prompt_B, bad)

    # ── Scenario C: no CLAUDE.md, no prior outputs ─────────────────────────
    setup_dummy_files(with_claude=False, with_prior_outputs=False)
    a03c = load_agent(3)
    prompt_C = a03c._build_prompt()
    assert_contains("C: fallback string present", prompt_C, "CLAUDE.md")
    for bad in FORBIDDEN_STRINGS:
        assert_not_contains(f"C: no forbidden '{bad[:20]}'", prompt_C, bad)


def test_agent04_scenarios(load_agent):
    print("\n=== Agent 04 — Answer Drafter (_build_system) ===")

    # Scenario A: prior outputs available
    setup_dummy_files(with_claude=True, with_prior_outputs=True)
    a04 = load_agent(4)
    sys_A = a04._build_system()
    assert_contains("A: thesis content in system", sys_A, "50k simulation")
    for bad in FORBIDDEN_STRINGS:
        assert_not_contains(f"A: no forbidden '{bad[:20]}'", sys_A, bad)

    # Scenario B: CLAUDE.md only
    setup_dummy_files(with_claude=True, with_prior_outputs=False)
    a04b = load_agent(4)
    sys_B = a04b._build_system()
    assert_contains("B: CLAUDE.md used in system", sys_B, "Reinforcement")
    for bad in FORBIDDEN_STRINGS:
        assert_not_contains(f"B: no forbidden '{bad[:20]}'", sys_B, bad)

    # Scenario C: nothing
    setup_dummy_files(with_claude=False, with_prior_outputs=False)
    a04c = load_agent(4)
    sys_C = a04c._build_system()
    assert_contains("C: fallback in system", sys_C, "CLAUDE.md")
    for bad in FORBIDDEN_STRINGS:
        assert_not_contains(f"C: no forbidden '{bad[:20]}'", sys_C, bad)


def test_agent05_scenarios(load_agent):
    print("\n=== Agent 05 — Weakness Analyst (_build_weakness_prompt) ===")

    # Scenario A
    setup_dummy_files(with_claude=True, with_prior_outputs=True)
    a05 = load_agent(5)
    wp_A = a05._build_weakness_prompt()
    assert_contains("A: thesis title in prompt", wp_A, "Underwater")
    assert_contains("A: prior analysis used", wp_A, "50k simulation")
    for bad in FORBIDDEN_STRINGS:
        assert_not_contains(f"A: no forbidden '{bad[:20]}'", wp_A, bad)

    # Scenario B
    setup_dummy_files(with_claude=True, with_prior_outputs=False)
    a05b = load_agent(5)
    wp_B = a05b._build_weakness_prompt()
    assert_contains("B: thesis title still present", wp_B, "Underwater")
    assert_contains("B: CLAUDE.md content used", wp_B, "Reinforcement")
    for bad in FORBIDDEN_STRINGS:
        assert_not_contains(f"B: no forbidden '{bad[:20]}'", wp_B, bad)

    # Scenario C
    setup_dummy_files(with_claude=False, with_prior_outputs=False)
    a05c = load_agent(5)
    wp_C = a05c._build_weakness_prompt()
    assert_contains("C: fallback contributions", wp_C, "CLAUDE.md")
    for bad in FORBIDDEN_STRINGS:
        assert_not_contains(f"C: no forbidden '{bad[:20]}'", wp_C, bad)


def test_agent07_scenarios(load_agent):
    print("\n=== Agent 07 — Study Planner (_build_prompt) ===")

    # Scenario A
    setup_dummy_files(with_claude=True, with_prior_outputs=True)
    a07 = load_agent(7)
    sp_A = a07._build_prompt()
    assert_contains("A: defence date present", sp_A, "June")
    assert_contains("A: thesis title present", sp_A, "Underwater")
    assert_contains("A: CLAUDE.md context included", sp_A, "CANDIDATE CONTEXT")
    assert_contains("A: thesis analysis included", sp_A, "THESIS ANALYSIS")
    assert_contains("A: weaknesses included", sp_A, "KNOWN WEAKNESSES")
    for bad in FORBIDDEN_STRINGS:
        assert_not_contains(f"A: no forbidden '{bad[:20]}'", sp_A, bad)

    # Scenario B
    setup_dummy_files(with_claude=True, with_prior_outputs=False)
    a07b = load_agent(7)
    sp_B = a07b._build_prompt()
    assert_contains("B: defence date present", sp_B, "June")
    assert_contains("B: thesis title present", sp_B, "Underwater")
    for bad in FORBIDDEN_STRINGS:
        assert_not_contains(f"B: no forbidden '{bad[:20]}'", sp_B, bad)

    # Scenario C — no CLAUDE.md
    setup_dummy_files(with_claude=False, with_prior_outputs=False)
    a07c = load_agent(7)
    sp_C = a07c._build_prompt()
    assert_contains("C: date fallback present", sp_C, "[Defence date")
    assert_contains("C: title fallback present", sp_C, "[Thesis title")
    for bad in FORBIDDEN_STRINGS:
        assert_not_contains(f"C: no forbidden '{bad[:20]}'", sp_C, bad)


def test_agent01_prompt_template():
    """Agent 01 uses PROMPT_TEMPLATE.format(thesis_title=..., text=...) directly."""
    print("\n=== Agent 01 — Thesis Analyst (PROMPT_TEMPLATE) ===")
    import importlib.util
    path = REPO / "agents" / "01_thesis_analyst.py"
    spec = importlib.util.spec_from_file_location("01_thesis_analyst", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    setup_dummy_files(with_claude=True, with_prior_outputs=False)
    import utils as u
    importlib.util.spec_from_file_location  # just ensure import is ok
    claude_text = u.load_claude_md()
    title = u.extract_thesis_title(claude_text)

    rendered = mod.PROMPT_TEMPLATE.format(thesis_title=title, text="[DUMMY THESIS TEXT]")
    assert_contains("thesis title rendered into prompt", rendered, "Underwater")
    assert_contains("thesis text placeholder rendered", rendered, "[DUMMY THESIS TEXT]")
    for bad in FORBIDDEN_STRINGS:
        assert_not_contains(f"no forbidden '{bad[:20]}'", rendered, bad)


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Regression Test — dynamic context loading (no API calls)")
    print("=" * 60)

    import importlib.util

    def load_agent(num):
        name = {3: "03_question_generator", 4: "04_answer_drafter",
                5: "05_weakness_analyst",   7: "07_study_planner"}[num]
        path = REPO / "agents" / f"{name}.py"
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    try:
        test_utils_helpers()
        test_agent01_prompt_template()
        test_agent03_scenarios()
        test_agent04_scenarios(load_agent)
        test_agent05_scenarios(load_agent)
        test_agent07_scenarios(load_agent)

    finally:
        teardown()
        print()

    print("=" * 60)
    print(f"  Results:  {PASS} passed,  {FAIL} failed")
    print("=" * 60)

    if FAIL > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()

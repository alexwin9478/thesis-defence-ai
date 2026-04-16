# PhD Defence Preparation — CLAUDE.example.md
# Copy this to CLAUDE.md and fill in your own details before running the pipeline.

## Project Overview

This repository is the preparation system for the PhD defence of [YOUR NAME].

**Defence Date:** [DATE, e.g. Friday, April 17, 2026]

## Examination Format

<!-- Fill in your defence structure. Common formats:
  - German/Dutch:  public lecture (30 min) → private Part 1: presentation Q&A (30 min) → private Part 2: thesis Q&A (30 min)
  - UK viva:       private exam only, 1–3 examiners, 1–3 hours, no public component
  - US defence:    public presentation (~45 min) → closed committee Q&A (30–60 min)
-->

**Structure:**
1. **Public lecture** (~[DURATION] min, before private session): [DESCRIBE WHAT IS PRESENTED PUBLICLY — e.g. presentation on [TOPIC]]
2. **Part 1 — [NAME THIS PART]** ([DURATION] min, private): [DESCRIBE — e.g. "Examination on the public lecture content; no further presentation needed"]
3. **Part 2 — Thesis examination** ([DURATION] min, private): Opens with examiners requesting a spoken thesis summary (length chosen spontaneously — prepare 1/3/5-minute versions). Followed by deep examination questions.

**Examiners:**
- [EXAMINER 1 NAME] ([INSTITUTION]) — [RESEARCH FOCUS]. Known critique style: [DESCRIBE]. Relevant papers: [LIST 1–2]
- [EXAMINER 2 NAME] ([INSTITUTION]) — [RESEARCH FOCUS]. Known critique style: [DESCRIBE]. Relevant papers: [LIST 1–2]

<!-- TIP: The more detail you add about examiners, the more targeted the professor_griller questions will be.
  Include: institution, research focus, any papers they co-authored with you, their known critique style. -->

**Format:**
- Part 1: [DURATION] minutes — [EXAMINATION PART 1 DESCRIPTION]
- Part 2: [DURATION] minutes — [EXAMINATION PART 2 DESCRIPTION]

**Thesis:** *"[YOUR THESIS TITLE]"*
**Presentation:** (place in `input/presentation/`)
**Notes/Questions:** (place in `input/notes/`)

**Core thesis contributions:**
1. [Contribution 1 — with key numbers]
2. [Contribution 2]
3. [Contribution 3]
4. [Contribution 4]

**Key acronyms:** [LIST KEY ACRONYMS USED IN YOUR THESIS]

## Repository Structure

```
input/
  thesis/          → Place your thesis PDF here (any filename)
  presentation/    → Place your defence presentation PPTX here
  notes/           → Place professor question notes PPTX here
output/
  summaries/       → Per-chapter summaries and synthesis
  questions_answers/ → Q&A sets organized by topic
  study_plan/      → 7-day day-by-day plan
  weak_points/     → Identified vulnerabilities and prepared defences
  literature_gaps/ → Gaps, limitations, future work
agents/            → Agent definitions and prompts
scripts/           → Python scripts to run the agent pipeline
```

## Python Environment

Always use the venv: `.venv/Scripts/python` (Windows) or `.venv/bin/python` (Unix).
Never install packages globally. Add new deps via `.venv/Scripts/pip install <pkg>`.

## Key Technical Areas to Master

### Must-Know Numbers (fill in from your thesis)
- [Metric 1]: [value]
- [Metric 2]: [value]
- [Key weakness metric — must have strong answer]: [value]

### Likely Hard Questions from Committee
1. [Anticipated hard question 1]
2. [Anticipated hard question 2]
3. [Anticipated hard question 3]

## Defence Preparation Principles

- Always prepare 3-tier answers: (1) one-line summary, (2) 2-minute explanation, (3) full technical depth
- For every weakness, prepare: acknowledgment → context → mitigation → future work
- Know the key results by heart — never look uncertain about your own numbers
- Prepare "bridging" answers: when unsure, bridge to what you do know confidently
- Study the committee members' own work to anticipate their angle of attack

## Optional: input/notes/ Enhancement Files

The pipeline reads these optional files from `input/notes/` to produce better-targeted output.
Place them there before running the relevant agent.

| File | Used by agent | What to put in it |
|------|--------------|-------------------|
| `examiners.md` | `professor_griller` | Background on each examiner: institution, research focus, critique style, 2–3 key papers |
| `committee_questions.md` | `committee_qa` | Your own rough notes for known committee questions (free format) |
| `deep_questions.md` | `deep_technical_qa` | Domain-specific questions you want researched in depth |
| `weak_points.md` | `weakness_analyst` | Your own list of thesis weak points you want specifically addressed |

See `input/notes/` for `.example.md` templates for each file.

## Environment Variable

Set `ANTHROPIC_API_KEY` in your shell or create a `.env` file (already in .gitignore).
Alternatively, authenticate via Claude.ai subscription: `claude --version`

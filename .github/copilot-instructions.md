# GitHub Copilot Instructions — PhD Defence Preparation

## Project Intent

This is a multi-agent AI pipeline for PhD thesis defence preparation.
It generates study materials (Q&A, flashcards, summaries, weak-point analyses) from a thesis PDF
and defence presentation by orchestrating 12 specialised Claude agents.

## Scope and Boundaries

- **Python only.** All agent logic lives in `agents/`. Orchestration lives in `scripts/run_pipeline.py`.
- **Output is Markdown.** All generated study materials are `.md` files written to `output/`.
- **No global installs.** Always use `.venv/Scripts/python` (Windows) or `.venv/bin/python` (Unix).
- **No hardcoded personal paths.** Agents must find input files via `_find_thesis_pdf()` / `_find_pptx()` helpers in each agent, not hardcoded paths.
- **No hardcoded personal names in agent prompts.** Refer to "the PhD candidate", not a specific person.

## Environment Rules

- Virtual environment: `.venv/` (already exists — do not recreate)
- Install packages: `.venv/Scripts/pip install <pkg>`
- API key: `ANTHROPIC_API_KEY` in `.env` (already gitignored)
- Auth fallback: `claude -p` CLI (Claude.ai subscription) — no API key required for basic use

## Key Files

| File | Role |
|------|------|
| `scripts/run_pipeline.py` | Main orchestrator — `--all`, `--agent`, `--resume`, `--status`, `--force` |
| `scripts/utils.py` | Shared utilities: `get_client()`, `ask_claude_long()`, `save_output()`, `load_output()` |
| `agents/01_thesis_analyst.py` | First agent — reads thesis PDF with PyMuPDF |
| `agents/09_professor_griller.py` | Generates examiner-persona questions |
| `agents/10_thesis_summary.py` | Cascading spoken summaries with `--angle` flag |
| `agents/11_committee_qa.py` | Reads candidate notes from `input/notes/committee_questions.md` |
| `CLAUDE.md` / `AGENTS.md` | Project context and thesis details — read this first |

## Response Contract

- When modifying agents: preserve the `run(force=False)` entry point signature
- When modifying the orchestrator: update `AGENT_MAP`, `FULL_PIPELINE_ORDER`, `AGENT_OUTPUTS`, and `PARALLEL_GROUPS` together
- When adding a new agent: follow the existing numbered naming (`NN_agent_name.py`)
- All output files go through `save_output(filename, content, subfolder)` — never write directly

## Do NOT

- Do not import packages not in `requirements.txt` without adding them
- Do not use `sys.exit()` inside agent `run()` functions — raise exceptions instead
- Do not use Unicode symbols (arrows, checkmarks, etc.) in console output — use ASCII only (cp1252 safe)
- Do not commit `.env`, `output/` content, or `input/` PDFs

```
  ____  _     ____     ____       __                          ____
 |  _ \| |__ |  _ \   |  _ \  ___/ _| ___ _ __   ___ ___   |  _ \ _ __ ___ _ __
 | |_) | '_ \| | | |  | | | |/ _ \ |_ / _ \ '_ \ / __/ _ \  | |_) | '__/ _ \ '_ \
 |  __/| | | | |_| |  | |_| |  __/  _|  __/ | | | (_|  __/  |  __/| | |  __/ |_) |
 |_|   |_| |_|____/   |____/ \___|_|  \___|_| |_|\___\___|  |_|   |_|  \___| .__/
                                                                              |_|
```

# PhD / Thesis Defence Preparation — AI-Powered Pipeline

An open-source multi-agent AI pipeline that reads your thesis PDF and defence
presentation, then generates the full stack of study materials you need to ace
your defence: Q&A banks, examiner simulations, cascading spoken summaries,
flashcards, weak-point analysis, and a day-by-day study plan.

Powered by [Claude](https://claude.ai) (Anthropic). Works with a Claude.ai subscription
(no API key needed) or an Anthropic API key for faster SDK mode.

> **Disclaimer:** This tool assists with preparation — it does not replace independent
> study, knowledge of your own work, or genuine understanding of the research.
> Use it to identify gaps, practise answers, and stress-test your arguments.
> **The final defence is yours.**

---

## What it generates

| Output | Description |
|--------|-------------|
| `summaries/thesis_analysis.md` | Chapter-by-chapter breakdown, key claims, attack vectors |
| `summaries/automl_analysis.md` | Topic map + hard questions from your presentation |
| `summaries/flashcards.md` | 100+ Obsidian spaced-repetition flashcards |
| `summaries/thesis_summary.md` | Cascading spoken summaries (1-sentence → 5-minute) |
| `questions_answers/all_questions.md` | 40+ questions from 4 examiner archetypes |
| `questions_answers/answers_thesis.md` | 3-tier answers for thesis questions |
| `questions_answers/professor_griller.md` | Simulated examination from your real examiners |
| `questions_answers/committee_qa.md` | Polished answers from your own committee question notes |
| `questions_answers/deep_technical_qa.md` | Research-backed answers to 25 hard technical questions |
| `weak_points/weakness_report.md` | Critical weaknesses + prepared counter-arguments |
| `study_plan/7day_plan.md` | Day-by-day study plan with mock session protocol |

---

## 10-Step Setup

**Prerequisites:**
- Python 3.10+
- [Claude Code CLI](https://claude.ai/code) installed and logged in (free with Claude.ai subscription)
- OR an Anthropic API key (`sk-ant-...`) — faster, optional
- [Obsidian](https://obsidian.md) desktop app (free — for flashcard review)

---

**Step 1 — Clone the repo**
```bash
git clone https://github.com/alexwin9478/thesis-defence-ai
cd thesis-defence-ai
```

**Step 2 — Create and activate the Python virtual environment**
```bash
# Windows
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

# macOS / Linux
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

**Step 3 — Configure your thesis details**
```bash
cp CLAUDE.example.md CLAUDE.md
# Open CLAUDE.md and fill in:
#   - Your thesis title + core contributions + key numbers
#   - Your examiners (name, institution, research focus)
#   - Your examination format (duration, structure, public lecture vs private)
#   - Key acronyms from your thesis
```

**Step 4 — Add your input files**
```
input/thesis/        <- copy your thesis PDF here (any filename)
input/presentation/  <- copy your defence presentation PPTX here
```

**Step 5 — (Optional) Add examiner and question notes**
```bash
# Copy the templates and fill them in for more targeted output:
cp input/notes/examiners.example.md input/notes/examiners.md
cp input/notes/committee_questions.example.md input/notes/committee_questions.md
```
See `input/notes/*.example.md` for the format. The more detail you add, the better.

**Step 6 — Authenticate with Claude**
```bash
# Option A: Claude.ai subscription (no API key needed)
claude --version   # should print version + account

# Option B: Anthropic API key (faster, ~$5-$20 per full run)
cp .env.example .env
# edit .env  ->  ANTHROPIC_API_KEY=sk-ant-...
```

**Step 7 — Verify setup**
```bash
# Windows
.venv\Scripts\python scripts\run_pipeline.py --status

# macOS / Linux
.venv/bin/python scripts/run_pipeline.py --status
# Should show all agents as MISSING -- correct for a first run
```

**Step 8 — Run the full pipeline**
```bash
# Windows (sequential, ~30-45 min via CLI subscription)
.venv\Scripts\python scripts\run_pipeline.py --all

# macOS / Linux
.venv/bin/python scripts/run_pipeline.py --all

# Faster: parallel mode (runs independent agents concurrently)
.venv\Scripts\python scripts\run_pipeline.py --all --parallel
```

**Step 9 — Study with Obsidian**
1. Install Obsidian (free): https://obsidian.md
2. Open Obsidian -> **"Open folder as vault"** -> select the `output/` directory
3. Click **"Trust author and enable plugins"** when prompted
4. Open `summaries/flashcards.md` -> click the **card-stack icon** -> **"Review Flashcards"**

**Step 10 — Mock grilling in Claude Code**
```
Open this repo in Claude Code and type:
  Grill me as Examiner 1
  Ask me a hard question about [topic] and critique my answer
```

---

## Pipeline commands

```bash
# Full pipeline
python scripts/run_pipeline.py --all

# Parallel mode (faster)
python scripts/run_pipeline.py --all --parallel

# Resume after failure -- skips already-generated outputs (safe)
python scripts/run_pipeline.py --resume

# Check status (no API calls)
python scripts/run_pipeline.py --status

# Single agent
python scripts/run_pipeline.py --agent professor_griller

# Thesis summary with framing angle
python scripts/run_pipeline.py --agent thesis_summary --angle control
# Angles: balanced | control | ml | practical

# Deep research on a specific weak topic
python scripts/run_pipeline.py --research behavior_cloning_safety
# Topics: gp_mpc | lyapunov_mpc | behavior_cloning_safety | nox_mitigation | automl_algorithms | dnn_mpc_comparison

# Quick mode: Q&A + flashcards only (skips thesis/presentation analysis)
python scripts/run_pipeline.py --quick

# Force regenerate all outputs
python scripts/run_pipeline.py --all --force
```

> **Credit-saving tips:** Use `--resume` not `--all` after any failure. Use `--status` to
> inspect before running. Use `--force` only when you need to regenerate specific outputs.

---

## Important Warnings

> **Token Budget:** Running the full pipeline costs ~500k-2M tokens depending on
> thesis length and number of agents.
>
> - **Claude.ai subscription (CLI mode):** 1-3 hours of compute time per full run.
>   Individual agents are cheap to re-run separately.
> - **Anthropic API key (SDK mode):** ~$5-$20 USD per full run (claude-opus-4-6 pricing).
>   Significantly faster than CLI mode.
>
> The heaviest agents are `thesis_analyst` and `automl_analyst` (large file inputs).

---

> **Context Window & PDF Truncation:**
> The pipeline uses `claude-opus-4-6` (200,000 token context window).
> Rule of thumb: **1 page of thesis text = ~470 tokens** (350 words x 1.33 tokens/word).
>
> | Thesis length | Approx. tokens | Notes |
> |--------------|---------------|-------|
> | 150 pages | ~70k tokens | Safe |
> | 200 pages | ~94k tokens | Safe |
> | 300 pages | ~141k tokens | Safe |
> | 400+ pages | ~188k+ tokens | Risk of truncation -- set MAX_THESIS_PAGES |
>
> If chapters are missing from `output/summaries/thesis_analysis.md`, set
> `MAX_THESIS_PAGES=300` in your `.env` file (see `.env.example` for details).
>
> This applies to both SDK mode and CLI mode -- the model context window is the same.
> CLI mode is simply slower at processing large inputs.

---

> **Examiner Research Quality:**
> The `professor_griller` agent generates questions in the voice of your actual examiners.
> **The more detail you add, the better the simulation.**
>
> Add examiner notes to `input/notes/examiners.md` (see template). At minimum include:
> name, institution, and research focus. For best results, add:
> - 2-3 of their papers most relevant to your thesis
> - Their known critique style (strict on theory? application-focused? comparative?)
> - Any papers they co-authored with you or your group

---

## Customising for Your Thesis

The pipeline is designed to be thesis-agnostic. All customisation goes into two places:

**1. `CLAUDE.md`** (copy from `CLAUDE.example.md`) — the agent's source of truth:
- Thesis title and core contributions (with numbers)
- Examination format (duration, structure, public vs private, examiners)
- Must-know numbers from your results
- Known hard questions from your committee

**2. `input/notes/` files** (optional, for better-targeted output):

| File | Extends agent | What to add |
|------|--------------|-------------|
| `examiners.md` | `professor_griller` | Examiner backgrounds, publications, critique style |
| `committee_questions.md` | `committee_qa` | Your rough notes on known committee questions |
| `deep_questions.md` | `deep_technical_qa` | Domain-specific questions for your field |
| `weak_points.md` | `weakness_analyst` | Your own list of weak points to target |

Use `*.example.md` templates as starting points.

---

## Agent Pipeline

| # | Agent | Output | Purpose |
|---|-------|--------|---------|
| 01 | `thesis_analyst` | `summaries/thesis_analysis.md` | Chapter-by-chapter breakdown + attack vectors |
| 02 | `automl_analyst` | `summaries/automl_analysis.md` | Presentation topic map + hard questions |
| 03 | `question_generator` | `questions_answers/all_questions.md` | 40+ questions from 4 professor archetypes |
| 04 | `answer_drafter` | `questions_answers/answers_thesis.md` | 3-tier answers (1-sentence / 2-min / full) |
| 05 | `weakness_analyst` | `weak_points/weakness_report.md` | Weaknesses + counter-arguments |
| 06 | `flashcard_maker` | `summaries/flashcards.md` | 100+ Obsidian spaced-repetition flashcards |
| 07 | `study_planner` | `study_plan/7day_plan.md` | Day-by-day schedule |
| 08 | `deep_researcher` | `literature_gaps/<topic>.md` | On-demand deep research |
| 09 | `professor_griller` | `questions_answers/professor_griller.md` | Real examiner personas + simulated grilling |
| 10 | `thesis_summary` | `summaries/thesis_summary.md` | Cascading summaries (1-sentence to 5-minute) |
| 11 | `committee_qa` | `questions_answers/committee_qa.md` | Polished answers from your own notes |
| 12 | `deep_technical_qa` | `questions_answers/deep_technical_qa.md` | Research-backed technical Q&A |

---

## Obsidian — Study with Flashcards

All outputs are Markdown files. [Obsidian](https://obsidian.md) (free desktop app) gives you:
- Rendered Markdown with linking and graph view
- **Spaced Repetition flashcard review** (SM-2 scheduling, pre-configured)

### Setup
1. Install Obsidian: https://obsidian.md (free, Windows / Mac / Linux)
   - Windows: `winget install Obsidian.Obsidian`
2. Open Obsidian -> **"Open folder as vault"** -> select the `output/` directory
3. Click **"Trust author and enable plugins"** when prompted
4. Open `summaries/flashcards.md` -> click the **card-stack icon** in the left ribbon -> **"Review Flashcards"**

Review daily: mark Hard / Good / Easy and Obsidian spaces cards automatically (SM-2 algorithm).

**Troubleshooting:** If flashcards don't appear, go to Settings -> Community Plugins -> disable then re-enable **"Spaced Repetition"**.

---

## Cascading Thesis Summaries

Agent 10 generates summaries that build on each other for incremental memorisation:
- **1 sentence**: The anchor — every longer version starts with this exact sentence
- **3 sentences**: Extends the 1-sentence with the gap + result
- **5 sentences**: Extends with the key enabling choice + generalisation
- **1 minute**: Extends the 5-sentence into flowing prose
- **3 minutes**: Extends with workflow stages + key results
- **5 minutes**: Extends with boundary conditions + forward-looking close

Practise the 1-sentence first. Learn each longer version as "what I add after the previous one."

---

## Authentication Details

The pipeline has two authentication modes, auto-selected at runtime:

| Mode | How | Speed | Cost |
|------|-----|-------|------|
| **SDK** (preferred) | Set `ANTHROPIC_API_KEY` in `.env` | Fast | ~$5-$20 per full run |
| **CLI fallback** | Claude.ai subscription (`claude --version`) | Slow | Included in subscription |

Priority: SDK (API key) -> CLI (subscription fallback)

If `ANTHROPIC_API_KEY` is set and valid, SDK mode is used automatically.
If not, the pipeline falls back to `claude -p` (requires the Claude Code CLI to be installed and logged in).

---

## Contributing

Improvements welcome — especially:
- New agents for additional study materials
- Support for non-English examinations
- Integration with other AI providers

Please open an issue or PR.

---

*Built for a PhD defence at RWTH Aachen. Generalised for anyone defending a thesis.*
*Powered by [Claude](https://claude.ai) (Anthropic).*

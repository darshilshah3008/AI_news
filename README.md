# AI Signal OS

**Stop tracking AI news. Start knowing what to build next.**

AI Signal OS is a local-first decision engine for builders, technical founders, and product engineers.
It ingests AI news reports, scores each signal against your project constraints, and recommends whether you should:

- **BUILD** now
- **TEST** soon
- **LEARN** and evaluate
- **WATCH** for changes
- **IGNORE** as low-value noise

---

## Table of Contents

1. [What problem this solves](#what-problem-this-solves)
2. [How AI Signal OS works](#how-ai-signal-os-works)
3. [System architecture](#system-architecture)
4. [Data model](#data-model)
5. [Scoring and recommendation logic](#scoring-and-recommendation-logic)
6. [Web product walkthrough](#web-product-walkthrough)
7. [CLI command reference](#cli-command-reference)
8. [Export workflows](#export-workflows)
9. [Local setup and run](#local-setup-and-run)
10. [Demo workflow (Orin Nano use case)](#demo-workflow-orin-nano-use-case)
11. [Testing](#testing)
12. [Codebase map](#codebase-map)
13. [Troubleshooting](#troubleshooting)
14. [Limitations and next steps](#limitations-and-next-steps)

---

## What problem this solves

AI builders are overloaded with updates from model releases, benchmarks, tooling launches, funding news, and ecosystem chatter.
Most feeds answer **"what happened"** but not:

- Why does this matter to my product?
- Does this fit my hardware/deployment constraints?
- What should my team do this week?

AI Signal OS focuses on decision support, not headline volume.

---

## How AI Signal OS works

### End-to-end flow

1. **Ingest reports** from markdown files in `reports/`.
2. **Parse articles** into structured records (title, source, summary, URL, date, etc.).
3. **Infer metadata** (edge/deployment fit, modality, entities).
4. **Store records** in SQLite (`data/ai_signal_os.db`).
5. **Load project profile** with constraints (hardware, latency, frameworks, exclusions, goals).
6. **Score each article** for importance + project relevance.
7. **Assign action label** (BUILD/TEST/LEARN/WATCH/IGNORE).
8. **Render outputs** in web dashboard and export markdown briefs/timelines.

---

## System architecture

AI Signal OS is split into focused modules:

- **Parsing Layer**: `aisignal/parser.py`
- **Persistence Layer**: `aisignal/db.py`
- **Recommendation Engine**: `aisignal/scoring.py`
- **Application Services**: `aisignal/services.py`
- **Web App (WSGI)**: `aisignal/web.py`
- **CLI Entry Point**: `__main__.py`

The web app is implemented with Python standard library WSGI for local reliability in constrained environments.
No cloud services are required.

---

## Data model

### Article record fields

Stored in `articles` table:

- `report_date`
- `category`
- `source`
- `title`
- `published_date`
- `summary`
- `tags` (JSON)
- `url` (unique)
- `modality`
- `deployment_fit`
- `entities` (JSON)
- `dedupe_key`

### Project profile fields

Stored in `projects` table:

- `name`, `description`
- `hardware_target`
- `deployment_style`
- `offline_requirement`
- `latency_sensitivity`
- `power_sensitivity`
- `memory_constraints`
- `preferred_frameworks` (JSON)
- `excluded_technologies` (JSON)
- `categories_of_interest` (JSON)
- `goals`
- `evaluation_priorities`

### Included sample profiles

- **Orin Nano Edge Assistant**
- **Document AI Startup**
- **AI SaaS Copilot**

---

## Scoring and recommendation logic

The MVP uses deterministic heuristics (no external LLM required).

### Signals considered

- **Edge/local deployment terms**: `edge`, `on-device`, `Jetson`, `Orin`, `TensorRT`, `ONNX`, `CUDA`, `quantization`, `real-time`
- **Document AI terms**: `document`, `OCR`, `RAG`, `retrieval`, `PDF`
- **SaaS assistant terms**: `assistant`, `copilot`, `agent`, `API`, `integration`
- **Lower-value business noise** (score penalties): `funding`, `raises`, `acquires`, `lawsuit`, `conference`

### Score outputs

For every article + project pair:

- `importance_score` (0–100)
- `relevance_score` (0–100)
- `confidence_score` (0–1)
- `reasoning` summary
- `action` label:
  - `BUILD` (highest combined score)
  - `TEST`
  - `LEARN`
  - `WATCH`
  - `IGNORE` (lowest)

### Why this design

- Transparent and inspectable behavior
- Fast local execution
- Easy to extend with model-based reranking later

---

## Web product walkthrough

Start server and open `http://127.0.0.1:8000`.

### 1) Landing (`/`)

- Positioning message
- CTA to create project profile
- Quick links to demo project dashboards

### 2) Project Onboarding (`/projects/new`)

- Form for all core project constraints
- Saves/updates profile in SQLite

### 3) Dashboard (`/dashboard?project_id=<id>`)

- Top scored signals
- Recommended actions this week
- Noise/watch list
- Links to Feed, Weekly Brief, Timeline

### 4) Signal Feed (`/signals?project_id=<id>`)

- Full recommendation list
- Filter by action (`BUILD`, `TEST`, `IGNORE`)

### 5) Weekly Brief (`/weekly-brief?project_id=<id>`)

- Executive summary
- Top relevant developments
- Models/tools to test
- Suggested architecture direction
- Prototype next steps
- What to ignore
- Risks/open questions

### 6) Timeline (`/timeline?project_id=<id>`)

- Date-bucketed relevant developments
- Action + relevance context per item

---

## CLI command reference

Run from the parent directory with module path available (`PYTHONPATH=/workspace` in this environment):

```bash
PYTHONPATH=/workspace python -m AI_news <command>
```

### Commands

- `init-db`
  - Initialize SQLite schema and seed demo project profiles.
- `ingest-file <path>`
  - Parse and ingest a single markdown report.
- `ingest-dir [path]`
  - Parse and ingest all markdown reports from a directory.
- `list-articles`
  - List ingested article records.
- `recommend <project_id> [--limit N]`
  - Print scored recommendations for a project.
- `export-project <project_id>`
  - Generate project weekly brief markdown in `data/exports/`.
- `export-timeline <project_id>`
  - Generate project timeline markdown in `data/exports/`.
- `runserver [--host HOST] [--port PORT]`
  - Start local web app.

---

## Export workflows

Exports are written to:

- `data/exports/project_<id>_brief.md`
- `data/exports/project_<id>_timeline.md`

These are designed for:

- team sharing in markdown
- decision memos
- NotebookLM ingestion
- async planning docs

---

## Local setup and run

```bash
cd AI_news
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Initialize and ingest

```bash
PYTHONPATH=/workspace python -m AI_news init-db
PYTHONPATH=/workspace python -m AI_news ingest-dir /workspace/AI_news/reports
```

### Run web app

```bash
PYTHONPATH=/workspace python -m AI_news runserver --host 127.0.0.1 --port 8000
```

---

## Demo workflow (Orin Nano use case)

Use this to validate product value quickly:

1. Open landing page.
2. Select **Orin Nano Edge Assistant** profile.
3. On dashboard, inspect top `BUILD` and `TEST` items.
4. Open Signal Feed, filter to `BUILD` and `TEST`.
5. Open Weekly Brief to get team-ready action plan.
6. Export brief + timeline markdown and drop into your planning docs.

Expected outcome: clear shortlist of signals that matter for edge constraints and explicit deprioritization of low-value noise.

---

## Testing

Run:

```bash
pytest -q
```

Current tests cover:

- markdown parsing (`tests/test_parser.py`)
- scoring behavior (`tests/test_scoring.py`)
- web route response (`tests/test_web.py`)

---

## Codebase map

```text
AI_news/
├── __main__.py                 # CLI commands + runserver
├── README.md
├── requirements.txt
├── reports/                    # input markdown reports
├── data/
│   └── exports/                # generated markdown exports
├── aisignal/
│   ├── __init__.py
│   ├── models.py               # dataclasses
│   ├── db.py                   # SQLite schema + persistence
│   ├── parser.py               # markdown parser + metadata inference
│   ├── scoring.py              # recommendation scoring engine
│   ├── services.py             # ingest/recommend/brief/timeline/export services
│   ├── web.py                  # WSGI web app + server
│   ├── static/
│   │   └── style.css           # product styling
│   └── templates/              # initial html templates
└── tests/
    ├── test_parser.py
    ├── test_scoring.py
    └── test_web.py
```

---

## Troubleshooting

### `No module named AI_news`

Run commands with project parent on `PYTHONPATH`, for example:

```bash
PYTHONPATH=/workspace python -m AI_news init-db
```

### `ingest-dir` ingested 0 items

Ensure you pass the correct reports directory path (for this repo: `/workspace/AI_news/reports`).

### Server not reachable

Check host/port and use:

```bash
PYTHONPATH=/workspace python -m AI_news runserver --host 127.0.0.1 --port 8000
```

---

## Limitations and next steps

### Current limitations

- Heuristic scoring only (no semantic dedupe or model reranking yet)
- No auth/multi-tenant user system yet
- No persisted feedback loop from user decisions back into ranking weights

### Recommended next steps

1. Add user feedback capture (`useful/not useful`, `ship/test/skip`).
2. Add semantic clustering for duplicate stories.
3. Add optional LLM explanation layer on top of deterministic core.
4. Add email/Slack weekly digest distribution.
5. Add project-level evaluation dashboards (latency/quality/cost trend view).

---

If you want, next I can add:

- a **"How scoring works" visual explanation panel** in the UI,
- a **seed script** that creates synthetic report data for fresh demos,
- and a **roadmap.md** with Phase 1/2/3 product milestones.

# Implementation Plan: Job Finder Automation

**Branch**: `001-job-finder` | **Date**: 2026-05-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-job-finder/spec.md`

## Summary

macOS Python 3.11+ CLI tool that parses a PDF résumé with pdfplumber, scrapes LATAM/Brazil remote jobs from three independent sources (Serper.dev/Google Jobs, Indeed via Playwright, Himalayas REST API), scores each posting against the résumé profile using a configurable LLM (Ollama locally or claude-sonnet-4-6 via GitHub Models), and persists qualifying jobs as Markdown notes in an Obsidian vault with slug-based deduplication and a regenerated Index.md after every run.

---

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**:
- `pdfplumber==0.11.4` — multi-page PDF text extraction
- `playwright==1.44.0` + `playwright-stealth==1.0.6` — humanised browser scraping
- `openai==1.30.1` — unified SDK for Ollama (OpenAI-compatible endpoint) and GitHub Models
- `requests==2.32.3` — Himalayas REST API + Serper.dev
- `python-dotenv==1.0.1` — env-var configuration from `.env`
- `python-slugify==8.0.4` — deterministic slug-based deduplication

**Storage**: Local filesystem — Obsidian vault at
`/Users/douglashennrich/Library/Mobile Documents/iCloud~md~obsidian/Documents/DHennrich/DHennrich/Job Finder`

**Testing**: `pytest` (unit) + manual smoke tests per task; no CI/CD required

**Target Platform**: macOS (local CLI + launchd scheduling)

**Project Type**: CLI automation tool (single-user, personal)

**Performance Goals**: Full pipeline run (3 sources × 2 queries × 20 jobs) completes within 10 minutes

**Constraints**:
- Zero hard-coded secrets — all config via `.env`
- `COPILOT_TOKEN` auto-detected via `subprocess.run(["gh", "auth", "token"])` if env var unset
- Playwright stealth; graceful per-source failure (continues remaining sources)
- No Obsidian plugins — plain Markdown with YAML frontmatter only
- Minimum score threshold configurable via `MIN_SCORE` env var (default 60)

**Scale/Scope**: Single user; ~20 jobs/source/query; ~60–120 raw jobs per run before dedup

---

## Constitution Check

*Gates evaluated against `.specify/memory/constitution.md` v1.0.1*

| Gate | Principle | Status | Note |
|------|-----------|--------|------|
| No hard-coded secrets | I. Configuration-First | ✅ Pass | All config via `.env`; `COPILOT_TOKEN` auto-detected via `gh auth token` |
| Fail-fast on bad config | I. Configuration-First | ✅ Pass | `Config.load()` raises `ValueError`/`RuntimeError` before pipeline starts |
| Per-source failure isolation | II. Graceful Degradation | ✅ Pass | Each `scraper.fetch()` wrapped in `try/except`; pipeline continues |
| LLM parse fallback chain | III. AI Output Safety | ✅ Pass | 3-stage: `json.loads` → regex → sentinel; score clamped `[0,100]` |
| Tier derived by app code | III. AI Output Safety | ✅ Pass | `_derive_tier(score)` is authoritative; LLM tier field ignored |
| Plain Markdown + YAML only | IV. Obsidian-Native Storage | ✅ Pass | No plugins; frontmatter only; `Index.md` fully regenerated each run |
| Slug-based deduplication | IV. Obsidian-Native Storage | ✅ Pass | `slugify(title + company)` in-memory + vault check |
| Rejected-score cache | IV. Obsidian-Native Storage | ✅ Pass | `_discarded.txt` persists rejected slugs; plain text, append-only |
| No server/DB/API | V. CLI Simplicity | ✅ Pass | Single `python main.py`; launchd scheduling only |
| Pipeline ≤ 10 min | V. CLI Simplicity | ✅ Pass | Validated: ~4 min with `qwen2.5:14b` × 20 jobs (down from 2h27 with 27B model) |

---

## Project Structure

### Documentation (this feature)

```text
specs/001-job-finder/
├── plan.md          ← this file
├── research.md      ← Phase 0 output
├── data-model.md    ← Phase 1 output
├── quickstart.md    ← Phase 1 output
├── contracts/
│   └── cli.md       ← Phase 1 output
└── tasks.md         ← Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

```text
job-finder/
├── .env                                    # secrets (git-ignored)
├── .env.example                            # documented template
├── requirements.txt                        # pinned Python deps
├── main.py                                 # entry point — orchestrates full pipeline
├── config.py                               # Config dataclass; loads .env; auto-detects token
├── resume/
│   ├── __init__.py
│   ├── profile.py                          # Profile dataclass
│   └── parser.py                           # parse_pdf(path) → Profile
├── scrapers/
│   ├── __init__.py
│   ├── base.py                             # Job dataclass + BaseScraper ABC
│   ├── google_jobs.py                      # Serper.dev primary + Playwright fallback
│   ├── indeed.py                           # Playwright humanised scraper
│   └── himalayas.py                        # REST API scraper
├── llm/
│   ├── __init__.py                         # build_llm(config) factory
│   ├── base.py                             # BaseLLM ABC
│   ├── ollama.py                           # OllamaLLM provider
│   └── copilot.py                          # CopilotLLM provider (GitHub Models)
├── analyzer.py                             # analyze(job, profile, llm) → JobAnalysis
├── obsidian/
│   ├── __init__.py
│   ├── templates.py                        # render_job_note() + render_index()
│   └── writer.py                           # note_exists(), save_note(), update_index()
├── tests/
│   └── unit/                               # pytest unit tests
├── logs/                                   # stdout/stderr captured by launchd
├── com.douglashennrich.jobfinder.plist     # launchd job definition
└── install_launchd.sh                      # installs plist with live token (run after validation)
```

**Structure Decision**: Single-project flat layout (Option 1). No web framework, no database, no separate frontend. All I/O is filesystem reads/writes + external HTTP.

---

## Complexity Tracking

> No constitution violations. Straightforward single-project CLI with no forbidden patterns.

---

## Phase 0 — Research Findings

*See [research.md](./research.md) for full details with alternatives considered.*

| Decision | Choice | Rationale |
|----------|--------|-----------|
| PDF extraction | `pdfplumber` | Handles multi-page, text-layer PDFs; pure Python; no Java/JVM required |
| LLM abstraction | `openai` SDK (both providers) | Ollama exposes OpenAI-compatible endpoint; one SDK, zero provider-switch cost |
| Google Jobs source | Serper.dev primary, Playwright fallback | 2,500 free queries/month sufficient; fallback ensures resilience without wasted quota |
| Indeed scraping | Playwright + playwright-stealth | Indeed blocks headless bots; stealth + random delays + mouse simulation required |
| Himalayas | Public REST API (`/jobs/api`) | Cleanest data, no scraping needed, JSON response with `remote` field |
| Deduplication | Slug-based file existence check | `slugify(title + company)` → filename; O(1), no database, survives restarts |
| Cloud LLM auth | `gh auth token` subprocess | gh CLI installed and connected; no manual token rotation |
| Scheduling | launchd (after manual validation) | macOS-native; set up only once pipeline is confirmed working |
| Vault index | Plain Markdown table (no Dataview) | Works in all Obsidian versions without plugins |

---

## Phase 1 — Design & Contracts

*See [data-model.md](./data-model.md) and [contracts/cli.md](./contracts/cli.md) for full details.*

### Data Model Summary

| Entity | Key Fields | Lifecycle |
|--------|-----------|-----------|
| `Config` | All env vars as typed fields + `obsidian_job_folder` derived path | Created once at startup via `Config.load()` |
| `Profile` | `raw_text: str`, `pdf_path: str` | Created once at startup from PDF |
| `Job` | `title`, `company`, `location`, `description`, `url`, `source`, `salary?`, `posted_date?` | One per discovered listing |
| `JobAnalysis` | `score: int`, `tier: str`, `justification: str`, `matching_skills: list[str]`, `missing_skills: list[str]` | One per scored job |
| `VaultNote` | `{slug}.md` file in vault folder | Written if `score >= MIN_SCORE`; existence used for dedup |
| `IndexNote` | `Index.md` in vault folder | Fully regenerated each run from all existing notes |

### Interface Contract Summary

See [contracts/cli.md](./contracts/cli.md).

- **Invocation**: `python main.py` (no required args; all config from `.env`)
- **Exit codes**: 0 = success, 1 = fatal error (missing PDF, vault not found, LLM misconfigured)
- **Stdout**: human-readable progress log (`[SAVED]`, `[SKIP]`, `[ERROR source]`, `Done.` summary)
- **Side effects**: Creates/updates `.md` files in Obsidian vault; never modifies source files

# Implementation Plan: Source Restructure & Capgemini Scraper

**Branch**: `feature/003-src-restructure-capgemini-scraper` | **Date**: 2026-05-25 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/003-src-restructure-capgemini-scraper/spec.md`

## Summary

Two parallel changes: (1) relocate all Python source files from the project root into `src/` — the entrypoint becomes `python src/main.py`, the launchd plist is updated, and `pytest.ini` with `pythonpath = src` ensures existing tests pass unchanged; (2) add `CapgeminiScraper` using `requests` + `BeautifulSoup` against Capgemini's SSR job board, implementing `BaseScraper.fetch(query, max_results)` and mapping `query` to the `keyword` URL parameter.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**:
- `requests==2.32.3` — already installed; reused for `CapgeminiScraper`
- `beautifulsoup4>=4.12` — **new dependency**; HTML parsing for Capgemini page
- `html.parser` — stdlib backend; no additional parser package needed
- `pytest>=7.0` — already installed; `pythonpath = src` ini option requires pytest ≥ 7.0

**Storage**: N/A — scrapers are stateless; change is file relocation only

**Testing**: `pytest` with `pythonpath = src` in new `pytest.ini` at project root

**Target Platform**: macOS (local CLI, launchd-scheduled)

**Project Type**: CLI automation tool — file restructuring + new scraper module

**Performance Goals**: `CapgeminiScraper` completes in ≤ 5s (single HTTP GET + HTML parse); total pipeline budget unchanged (≤ 10 min per constitution §V)

**Constraints**:
- `CapgeminiScraper` MUST never raise — `try/except` wraps all logic; returns `[]` on failure (§II)
- No new environment variables — credential-free scraper
- `WorkingDirectory` in plist stays at project root — `.env` and `logs/` paths unaffected
- No import changes in any existing file (Python sys.path injection via script dir)
- No test file changes (pytest `pythonpath` setting resolves imports)

**Scale/Scope**: ~11 jobs per query from Capgemini (`size=11`); same pipeline scale as existing sources

## Constitution Check

*Gates evaluated against `.specify/memory/constitution.md` v1.0.1*

| Gate | Principle | Status | Note |
|------|-----------|--------|------|
| No hard-coded secrets or file paths | I. Configuration-First | ✅ Pass | No new secrets; plist path is machine-local and always was |
| Fail-fast on missing config | I. Configuration-First | ✅ Pass | No new required config; `Config.load()` unchanged |
| Per-source failure isolation | II. Graceful Degradation | ✅ Pass | `CapgeminiScraper` wraps all logic in `try/except`; returns `[]` on any failure |
| AI output safety | III. AI Output Safety | ✅ N/A | No LLM changes |
| Obsidian-native storage | IV. Obsidian-Native Storage | ✅ N/A | No storage changes |
| No new infrastructure | V. CLI Simplicity | ✅ Pass | File move + one scraper; no server, DB, or daemon |
| Pipeline ≤ 10 min | V. CLI Simplicity | ✅ Pass | Capgemini adds ≤ 5s; total budget unchanged |
| Smoke test per new module | Quality Gate | ✅ Required | `tests/unit/test_capgemini_scraper.py` must be created |

**Post-Phase 1 re-check**: All gates pass. `beautifulsoup4` addition is a leaf dependency with no security or architectural implications. `pytest.ini` is pure tooling configuration.

## Project Structure

### Documentation (this feature)

```text
specs/003-src-restructure-capgemini-scraper/
├── plan.md              # This file
├── spec.md
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── cli.md           # Phase 1 output
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

```text
job-finder/
├── src/                              # NEW — all Python source
│   ├── analyzer.py                   # MOVED from root
│   ├── config.py                     # MOVED from root
│   ├── main.py                       # MOVED from root; updated: register CapgeminiScraper
│   ├── llm/                          # MOVED from root
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── copilot.py
│   │   └── ollama.py
│   ├── obsidian/                     # MOVED from root
│   │   ├── __init__.py
│   │   ├── templates.py
│   │   └── writer.py
│   ├── resume/                       # MOVED from root
│   │   ├── __init__.py
│   │   ├── parser.py
│   │   └── profile.py
│   └── scrapers/                     # MOVED from root
│       ├── __init__.py
│       ├── base.py                   # Updated: source comment += "capgemini"
│       ├── capgemini.py              # NEW: CapgeminiScraper
│       ├── google_jobs.py
│       ├── himalayas.py
│       ├── indeed.py
│       ├── linkedin.py
│       └── solides.py
├── tests/                            # UNCHANGED — stays at root
│   └── unit/
│       ├── test_capgemini_scraper.py # NEW
│       ├── test_linkedin_scraper.py
│       └── test_solides_scraper.py
├── pytest.ini                        # NEW: pythonpath = src
├── requirements.txt                  # Updated: +beautifulsoup4>=4.12
└── com.douglashennrich.jobfinder.plist  # Updated: ProgramArguments path → src/main.py
```

**Structure Decision**: Standard Python `src` layout. All application source under `src/`; tests at root with `pytest.ini` configuring path resolution. No packaging infrastructure (`pyproject.toml`, `setup.py`) introduced — YAGNI per constitution §V.

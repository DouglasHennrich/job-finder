# Implementation Plan: LinkedIn & Solides Job Scrapers

**Branch**: `002-linkedin-solides-scrapers` | **Date**: 2026-05-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-linkedin-solides-scrapers/spec.md`

## Summary

Add two new job sources to the existing Job Finder pipeline: a `LinkedInScraper` (Playwright + playwright-stealth against LinkedIn's public job search pages, no credentials) and a `SolidesScraper` (plain `requests` against vagas.solides.com.br's public REST API, no credentials). Both implement the existing `BaseScraper` interface and are registered in `main.py` alongside the three existing scrapers. No new environment variables or dependencies are required.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**:
- `playwright==1.44.0` + `playwright-stealth==1.0.6` — already installed (used by `IndeedScraper`); reused for `LinkedInScraper`
- `requests==2.32.3` — already installed; reused for `SolidesScraper`
- `re` / `html.parser` — stdlib; used to strip HTML tags from Solides `description`

**Storage**: N/A — scrapers are stateless; output passed directly to scoring pipeline

**Testing**: `pytest` unit tests (smoke tests per constitution quality gate)

**Target Platform**: macOS (local CLI, same as existing pipeline)

**Project Type**: CLI automation tool extension (two new scraper modules)

**Performance Goals**: Both scrapers complete within 60 seconds per run (LinkedIn: Playwright warmup + stealth delays ~30s for 20 jobs; Solides: REST API ~1–2s for 20 jobs)

**Constraints**:
- `LinkedInScraper` MUST apply playwright-stealth + humanisation delays `uniform(1.5, 3.5)s` (constitution §Quality Gates)
- Both scrapers MUST never raise — `try/except` wraps all logic; returns `[]` on failure
- `SolidesScraper` filters remote/home-office jobs post-response in Python (on `homeOffice=True` or `jobType="home-office"`)
- No new env vars — both scrapers are credential-free
- Solides `description` HTML tags stripped before storage

**Scale/Scope**: ~20 jobs per scraper per query; same scale as existing scrapers

## Constitution Check

*Gates evaluated against `.specify/memory/constitution.md` v1.0.1*

| Gate | Principle | Status | Note |
|------|-----------|--------|------|
| No hard-coded secrets | I. Configuration-First | ✅ Pass | Both scrapers are credential-free; no API keys or tokens |
| Fail-fast on bad config | I. Configuration-First | ✅ Pass | No new config; existing `Config.load()` unchanged |
| Per-source failure isolation | II. Graceful Degradation | ✅ Pass | Both scrapers wrap all logic in `try/except`; return `[]` on any failure |
| Playwright stealth + humanisation | Quality Gate | ✅ Pass | `LinkedInScraper` applies `Stealth()` + `uniform(1.5, 3.5)s` delays (same as `IndeedScraper`) |
| Smoke test per module | Quality Gate | ✅ Pass | `tests/unit/test_linkedin_scraper.py` and `tests/unit/test_solides_scraper.py` required |
| No server/DB/API | V. CLI Simplicity | ✅ Pass | No new infrastructure; both scrapers are pure Python modules |
| Pipeline ≤ 10 min | V. CLI Simplicity | ✅ Pass | Solides adds ~2s; LinkedIn adds ~30s; total within budget |

## Project Structure

### Documentation (this feature)

```text
specs/002-linkedin-solides-scrapers/
├── plan.md          ← this file
├── spec.md
├── research.md      ← Phase 0 output
├── data-model.md    ← Phase 1 output
├── quickstart.md    ← Phase 1 output
├── contracts/
│   └── cli.md           ← Phase 1 output
├── checklists/
│   └── requirements.md
└── tasks.md         ← Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

```text
job-finder/
├── scrapers/
│   ├── base.py                              # Updated: source comment
│   ├── linkedin.py                          # NEW: LinkedInScraper
│   └── solides.py                           # NEW: SolidesScraper
├── main.py                                  # Updated: register new scrapers
└── tests/
    └── unit/
        ├── test_linkedin_scraper.py             # NEW: smoke test
        └── test_solides_scraper.py              # NEW: smoke test
```

**Structure Decision**: Flat single-project layout (same as existing codebase). New scrapers are plain Python modules in `scrapers/`. No new packages, services, or directories introduced.

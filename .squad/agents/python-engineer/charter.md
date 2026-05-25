# python-engineer — Python Pipeline Engineer

Core Python automation specialist responsible for project scaffolding, configuration management, resume PDF parsing, and pipeline orchestration.

## Project Context

**Project:** job-finder
**Stack:** Python 3.11+, pdfplumber, python-dotenv, python-slugify

## Responsibilities

- Implement and maintain `src/config.py` — Config dataclass, .env loading, `gh auth token` auto-detection
- Implement `src/resume/parser.py` — PDF text extraction with pdfplumber
- Implement `src/main.py` — full pipeline orchestration (scrape → deduplicate → analyze → save → index); register new scrapers (`LinkedInScraper`, `SolidesScraper`, `CapgeminiScraper`)
- Manage `requirements.txt` and dependency compatibility
- Handle cross-cutting concerns: logging, error handling, deduplication logic
- Write smoke tests for each module — including `tests/unit/test_linkedin_scraper.py` and `tests/unit/test_solides_scraper.py`
- **[spec-003]** Migrate all Python source files to `src/` (T003–T007): move `analyzer.py`, `config.py`, `main.py` and packages `llm/`, `obsidian/`, `resume/`, `scrapers/` under `src/`
- **[spec-003]** Create `pytest.ini` at project root with `pythonpath = src` so tests resolve imports without modification (T002)
- **[spec-003]** Update `com.douglashennrich.jobfinder.plist` to reference `src/main.py` as entrypoint; keep `WorkingDirectory` at project root (T008)
- **[spec-003]** Register `CapgeminiScraper` import and instantiation in `src/main.py` (T013)

## Capabilities

- Python 3.11+ (expert)
- pdfplumber / PDF text extraction (expert)
- python-dotenv / environment config (expert)
- Async Python / asyncio (proficient)
- Shell subprocess integration (proficient)
- launchd / macOS scheduling (basic)
- pytest / pytest.ini configuration (basic)

## Work Style

- Read `specs/001-job-finder/spec.md`, `specs/002-linkedin-solides-scrapers/spec.md`, and `specs/003-src-restructure-capgemini-scraper/spec.md` before starting work
- Follow the file structure defined in the plan exactly
- Validate each module with the smoke tests defined in the plan before moving on
- Never commit secrets — .env stays out of git
- After src/ migration, verify with `python src/main.py 2>&1 | head -5` and `pytest tests/ -v` from project root

## Status

active

# Feature Specification: Source Restructure & Capgemini Scraper

**Feature Branch**: `feature/003-src-restructure-capgemini-scraper`

**Created**: 2026-05-25

**Status**: Draft

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Migrate Source Files to `src/` (Priority: P1)

As a developer, I want all Python source files organised under a `src/` directory so that the project root is clean and separates source code from configuration, tooling, and metadata files.

**Why this priority**: The root directory currently mixes Python source files (`analyzer.py`, `config.py`, `main.py`) with packages (`llm/`, `obsidian/`, `resume/`, `scrapers/`), infrastructure scripts (`.plist`, `.sh`), and tooling configs. Moving source to `src/` is foundational — it must be done before adding new scrapers so new code lands in the right place from the start.

**Independent Test**: Can be fully tested by verifying that `python src/main.py` runs successfully end-to-end — finding jobs, scoring them, and saving Obsidian notes — with no import errors, and that `pytest tests/` still passes without modifications to any test file.

**Acceptance Scenarios**:

1. **Given** the project is in its current state, **When** all Python source files are moved to `src/`, **Then** `python src/main.py` runs without import errors or runtime failures
2. **Given** all source files are inside `src/`, **When** `pytest tests/` is run, **Then** all existing tests pass without modifying any test file
3. **Given** `src/main.py` is the new entrypoint, **When** the launchd plist is updated and `install_launchd.sh` is re-run, **Then** the scheduled job runs correctly as before
4. **Given** the migration is complete, **When** the project root is inspected, **Then** it contains only `src/`, `tests/`, `specs/`, `docs/`, config/tooling files (`.env`, `requirements.txt`, etc.) and infrastructure scripts — no Python source files at the root level
5. **Given** the migration is complete, **When** `.env` is loaded by the application, **Then** it is still found correctly because `WorkingDirectory` in the plist remains the project root

---

### User Story 2 — Capgemini Job Search Scraper (Priority: P2)

As a job seeker, I want the tool to search Capgemini's public job board so that I receive relevant fullstack/Node.js opportunities directly from one of the largest tech employers globally.

**Why this priority**: Capgemini is a major tech employer with frequent Node.js/fullstack openings. Adding this source directly (rather than relying on LinkedIn/Google to surface Capgemini jobs) gives fresher and more complete coverage of Capgemini's open roles.

**Independent Test**: Can be fully tested by running only the Capgemini scraper with a query and verifying it returns a list of `Job` objects with `source="capgemini"` — independently of any other scraper, scoring, or pipeline step.

**Acceptance Scenarios**:

1. **Given** a search query is provided, **When** the Capgemini scraper runs, **Then** it returns job listings from `https://www.capgemini.com/careers/join-capgemini/job-search/` matching the keyword, each containing at minimum: title, URL, and `source="capgemini"`
2. **Given** the Capgemini site returns no results for the query, **When** the scraper runs, **Then** it returns an empty list without raising an error
3. **Given** the Capgemini site is unreachable (network error, non-2xx response), **When** the scraper runs, **Then** it logs a warning and returns an empty list — the pipeline continues with other sources
4. **Given** a job is collected from Capgemini, **When** the `Job` object is created, **Then** `source` is set to `"capgemini"` and `url` points to `https://www.capgemini.com/jobs/{id}`
5. **Given** the scraper runs, **When** multiple pages of results are available, **Then** it respects `max_results` and stops fetching once the limit is reached

---

### User Story 3 — Pipeline Integration (Priority: P3)

As a job seeker, I want the Capgemini scraper to be fully integrated into the existing job-finding pipeline so that its results are automatically scored against my resume and saved to Obsidian alongside results from other sources.

**Why this priority**: The scraper has no value unless it feeds into the full pipeline. Integration must happen after both the migration (P1) and scraper (P2) are working.

**Independent Test**: Can be fully tested by running the full pipeline (`python src/main.py`) and verifying that Obsidian notes appear with `source: capgemini` in their frontmatter.

**Acceptance Scenarios**:

1. **Given** the full pipeline runs, **When** the Capgemini scraper is enabled, **Then** its results are merged with results from other sources before scoring
2. **Given** the Capgemini scraper returns results, **When** scoring runs, **Then** jobs above `MIN_SCORE` are saved as Obsidian notes with `source: capgemini` in their frontmatter
3. **Given** the Capgemini scraper returns no results, **When** the pipeline runs, **Then** the pipeline continues normally with no error or crash

---

### Edge Cases

- What happens if a job card on Capgemini is missing a title or URL? → The job is silently skipped (consistent with existing scrapers)
- What happens if `src/main.py` is run from inside the `src/` directory instead of the project root? → `.env` loading depends on `WorkingDirectory` from the plist (project root); running from inside `src/` directly may fail to find `.env` — documented as a known constraint
- What happens if both `keyword` values in the URL resolve to zero Capgemini results? → Empty list returned gracefully
- What happens if the Capgemini page structure changes (DOM update)? → The scraper fails gracefully with a warning, returning an empty list; pipeline is unaffected

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: All Python source files (`analyzer.py`, `config.py`, `main.py` and packages `llm/`, `obsidian/`, `resume/`, `scrapers/`) MUST be relocated to `src/`
- **FR-002**: The `tests/` directory MUST remain at the project root; pytest MUST be configured with `pythonpath = src` so test imports resolve without modification
- **FR-003**: The launchd plist (`com.douglashennrich.jobfinder.plist`) MUST be updated to reference `src/main.py` as the program entrypoint; `WorkingDirectory` MUST remain the project root
- **FR-004**: The project root MUST contain no Python source files after migration (only `src/`, `tests/`, `specs/`, `docs/`, infrastructure and configuration files)
- **FR-005**: A `CapgeminiScraper` class MUST implement the `BaseScraper` interface (`fetch(query: str, max_results: int) -> list[Job]`)
- **FR-006**: `CapgeminiScraper` MUST map the `query` argument to the `keyword` URL query parameter of `https://www.capgemini.com/careers/join-capgemini/job-search/`
- **FR-007**: `CapgeminiScraper` MUST include the `page` and `size` parameters in requests: `page=1`, `size=11` (as specified by the user)
- **FR-008**: `CapgeminiScraper` MUST set `source="capgemini"` on all returned `Job` objects
- **FR-009**: `CapgeminiScraper` MUST never raise — it MUST return an empty list and log a warning on any error
- **FR-010**: `CapgeminiScraper` MUST be registered in `main.py` alongside existing scrapers
- **FR-011**: `CapgeminiScraper` MUST use an HTTP request approach (not a headless browser) since the Capgemini job board renders listings in server-side HTML
- **FR-012**: The `source` comment in `scrapers/base.py` MUST be updated to include `"capgemini"` in the list of known sources

### Key Entities

- **`src/` directory**: New top-level container for all Python application source files; mirrors the current root structure inside `src/`
- **`CapgeminiScraper`**: A new scraper module at `src/scrapers/capgemini.py` implementing `BaseScraper`; fetches HTML from the Capgemini public job board and parses job listings

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `python src/main.py` completes a full run end-to-end with no errors after migration
- **SC-002**: `pytest tests/` passes with 100% of previously-passing tests still passing, without modifying any test file
- **SC-003**: The project root contains no `.py` files after migration
- **SC-004**: The Capgemini scraper returns at least 1 job result when the Capgemini job board is reachable and has listings matching the query
- **SC-005**: A full pipeline run produces at least 1 Obsidian note with `source: capgemini` when the Capgemini board has qualifying openings
- **SC-006**: When the Capgemini site is unreachable, the pipeline completes normally with results from other sources — no crash, no exception propagated

---

## Assumptions

- Python automatically adds the script's directory (`src/`) to `sys.path` when invoked as `python src/main.py`, so no import path changes are required in any source file
- The Capgemini job board at `https://www.capgemini.com/careers/join-capgemini/job-search/` renders job listings in server-side HTML; the `keyword` query param filters results server-side
- `WorkingDirectory` in the launchd plist stays as the project root, ensuring `.env`, `logs/`, and other root-relative paths continue to resolve correctly
- `tests/` stays at the project root (standard Python convention); a `pytest.ini` (or `pyproject.toml`) `pythonpath = src` setting is the sole change needed for tests to keep passing
- The Capgemini scraper keyword `fullstack+node` is passed as the query from `_build_queries()` in `main.py`; the scraper itself URL-encodes whatever query it receives
- Non-Python files at the root (`requirements.txt`, `.env`, `.env.example`, `com.douglashennrich.jobfinder.plist`, `install_launchd.sh`, `squad.config.ts`, `skills-lock.json`) remain at the project root and are not moved
- `logs/` directory remains at the project root; log file paths in the application remain unchanged

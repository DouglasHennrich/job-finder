# Tasks: Source Restructure & Capgemini Scraper

**Input**: Design documents from `specs/003-src-restructure-capgemini-scraper/`

**Prerequisites**: [plan.md](./plan.md) · [spec.md](./spec.md) · [research.md](./research.md) · [data-model.md](./data-model.md) · [contracts/cli.md](./contracts/cli.md) · [quickstart.md](./quickstart.md)

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no shared state)
- **[Story]**: User story this task belongs to (US1, US2, US3)
- All paths relative to project root

---

## Phase 1: Setup

**Purpose**: Dependency and tooling prerequisites needed before any story work begins

- [ ] T001 Add `beautifulsoup4>=4.12` to `requirements.txt` (required by US2 CapgeminiScraper)
- [ ] T002 Create `pytest.ini` at project root with content: `[pytest]\npythonpath = src` (required to keep tests passing after US1 migration)

---

## Phase 2: Foundational

**Purpose**: Create the `src/` directory that all migration tasks depend on

**⚠️ CRITICAL**: T003 must complete before T004–T007 can begin

- [ ] T003 Create `src/` directory; move `analyzer.py`, `config.py`, `main.py` from project root into `src/`

**Checkpoint**: `src/` exists with the three flat Python files — package moves can now proceed in parallel

---

## Phase 3: User Story 1 — Migrate Source Files to `src/` (Priority: P1) 🎯 MVP

**Goal**: All Python source files live under `src/`; `python src/main.py` runs end-to-end; `pytest tests/` passes unchanged

**Independent Test**: Run `python src/main.py` from project root with no import errors; run `pytest tests/ -v` to confirm all pre-existing tests still pass

### Implementation for User Story 1

- [ ] T004 [P] [US1] Move `llm/` package directory to `src/llm/` (rename/mv the directory)
- [ ] T005 [P] [US1] Move `obsidian/` package directory to `src/obsidian/`
- [ ] T006 [P] [US1] Move `resume/` package directory to `src/resume/`
- [ ] T007 [P] [US1] Move `scrapers/` package directory to `src/scrapers/`
- [ ] T008 [US1] Update `com.douglashennrich.jobfinder.plist`: change `ProgramArguments` second entry from `.../main.py` to `.../src/main.py` (WorkingDirectory stays unchanged)
- [ ] T009 [US1] Verify migration: from project root run `python src/main.py 2>&1 | head -5` to confirm no `ModuleNotFoundError`; run `pytest tests/ -v` to confirm all existing tests pass

**Checkpoint**: US1 complete — project root has no `.py` files; `python src/main.py` and `pytest tests/` both work

---

## Phase 4: User Story 2 — Capgemini Scraper (Priority: P2)

**Goal**: `CapgeminiScraper` in `src/scrapers/capgemini.py` fetches jobs from Capgemini's public job board using `requests` + BeautifulSoup

**Independent Test**: Run `python -c "from scrapers.capgemini import CapgeminiScraper; jobs = CapgeminiScraper().fetch('fullstack node', 11); print(type(jobs), len(jobs))"` from `src/` — returns a list; run `pytest tests/unit/test_capgemini_scraper.py -v`

### Implementation for User Story 2

- [ ] T010 [P] [US2] Create `src/scrapers/capgemini.py` implementing `BaseScraper.fetch(query, max_results) -> list[Job]` using `requests.get` + `BeautifulSoup(html.parser)` against `https://www.capgemini.com/careers/join-capgemini/job-search/?page=1&size=11&keyword={query}`; parse `<a href>` elements whose href contains `/jobs/`; set `source="capgemini"`, `company="Capgemini"`; wrap all logic in `try/except`; log warning and return `[]` on any error
- [ ] T011 [P] [US2] Update `source` comment in `src/scrapers/base.py` to add `"capgemini"` to the valid sources list: `# "google_jobs" | "indeed" | "himalayas" | "linkedin" | "solides" | "capgemini"`
- [ ] T012 [P] [US2] Create `tests/unit/test_capgemini_scraper.py` with three smoke tests: (1) `fetch()` returns a `list`; (2) graceful failure when `requests.get` raises (mock with `side_effect=RuntimeError`); (3) any returned jobs have `source == "capgemini"`

**Checkpoint**: US2 complete — `CapgeminiScraper` fetches and parses Capgemini jobs independently; smoke tests pass

---

## Phase 5: User Story 3 — Pipeline Integration (Priority: P3)

**Goal**: Capgemini results flow through the full pipeline and produce Obsidian notes with `source: capgemini`

**Independent Test**: Run `python src/main.py` from project root; check Obsidian output folder for notes containing `source: capgemini` in YAML frontmatter

### Implementation for User Story 3

- [ ] T013 [US3] Register `CapgeminiScraper` in `src/main.py`: add import `from scrapers.capgemini import CapgeminiScraper`; instantiate and add to the scrapers list alongside existing scrapers; use query from `_build_queries()` (e.g. `"senior fullstack developer nodejs react remote"`)

**Checkpoint**: US3 complete — full pipeline run produces Capgemini-sourced Obsidian notes

---

## Final Phase: Polish & Verification

**Purpose**: End-to-end verification, dependency install confirmation

- [ ] T014 Run `pip install -r requirements.txt` to install `beautifulsoup4`; verify no dependency conflicts
- [ ] T015 Run full test suite `pytest tests/ -v` from project root; confirm 100% of tests pass including new `test_capgemini_scraper.py`

---

## Dependencies

```
T001 ──────────────────────────────────────────► T014 (beautifulsoup4 install)
T002 ──────────────────────────────────────────► T009 (pytest verification)
T003 ──► T004 [P] ┐
         T005 [P] ├──► T008 ──► T009 (US1 verification)
         T006 [P] │
         T007 [P] ┘
T007 ──► T010 [P] ┐
         T011 [P] ├──► T013 ──► T015 (full pipeline verification)
         T012 [P] ┘
```

**US1 and US2 are independent**: US2 tasks (T010–T012) can start in parallel with US1 (T003–T009) since `CapgeminiScraper` is a new file that doesn't conflict with the migration.

---

## Parallel Execution Examples

### Parallel batch 1 (after T003): 
```
T004 (move llm/)  +  T005 (move obsidian/)  +  T006 (move resume/)  +  T007 (move scrapers/)
```

### Parallel batch 2 (after T007, T003):
```
T008 (update plist)  +  T010 (CapgeminiScraper)  +  T011 (base.py comment)  +  T012 (tests)
```

### Sequential gate:
```
T009 (US1 verify)  →  T013 (register in main.py)  →  T015 (full suite)
```

---

## Implementation Strategy

**MVP scope**: US1 only (T001–T009) delivers a clean `src/` layout with zero functional change — safest first increment, fully reversible.

**Full delivery order**: US1 → US2 → US3 → Polish

**Risk**: The file migration (T004–T007) is mechanical but must be done carefully — use `git mv` to preserve history. After T003–T007, verify immediately with `python src/main.py` before proceeding.

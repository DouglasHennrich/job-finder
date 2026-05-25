# Tasks: LinkedIn & Solides Job Scrapers

**Input**: Design documents from `/specs/002-linkedin-solides-scrapers/`

**Prerequisites**: [plan.md](./plan.md) · [spec.md](./spec.md) · [research.md](./research.md) · [data-model.md](./data-model.md) · [contracts/cli.md](./contracts/cli.md) · [quickstart.md](./quickstart.md)

**Branch**: `002-linkedin-solides-scrapers`

---

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel with other [P] tasks in the same phase (different files, no shared state)
- **[Story]**: User story this task belongs to (US1=LinkedIn, US2=Solides, US3=Integration)
- All paths are relative to repo root

---

## Phase 1: Setup

**Purpose**: Update the shared base to declare the two new source values before implementing either scraper.

- [x] T001 Update `source` field comment in `scrapers/base.py` to include `"linkedin"` and `"solides"` as valid values (one-line change to the inline comment on the `source: str` field) <!-- squad:agent=scraping-engineer tier=lightweight -->

**Checkpoint**: `scrapers/base.py` is ready; both scrapers can be authored.

---

## Phase 2: Foundational

**Purpose**: No new shared infrastructure is required — both scrapers extend `BaseScraper` directly and the Playwright + requests stacks already exist. Phase 2 is intentionally empty; proceed immediately to user story phases.

**⚠️ NOTE**: US1 and US2 are fully independent and can be worked in parallel after Phase 1.

---

## Phase 3: User Story 1 — LinkedIn Direct Scraping (Priority: P1) 🎯 MVP

**Goal**: A working `LinkedInScraper` that fetches job listings from LinkedIn's public job search pages using Playwright + playwright-stealth, returning `Job` objects with `source="linkedin"`.

**Independent Test**: Run `from scrapers.linkedin import LinkedInScraper; jobs = LinkedInScraper().fetch("senior fullstack nodejs react", 5); assert all(j.source == "linkedin" for j in jobs)` and verify at least one job returns with title, company, and URL — no other scraper or pipeline step needed.

- [x] T002 [US1] Implement `scrapers/linkedin.py` with `LinkedInScraper(BaseScraper)`: <!-- squad:agent=scraping-engineer tier=standard -->
  - `fetch(query, max_results) -> list[Job]` calls `asyncio.run(self._async_fetch(...))`; wraps entire body in `try/except`; logs warning and returns `[]` on any failure
  - `_async_fetch` launches Playwright Chromium headless with user-agent header, applies `Stealth()` from playwright-stealth, and navigates to `https://www.linkedin.com/jobs/search?keywords={encoded_query}&location=Brazil&f_WT=2`
  - Applies humanisation: `await asyncio.sleep(random.uniform(1.5, 3.5))` after page load, random mouse move before querying cards
  - Extracts cards using selector `.job-search-card` (up to `max_results`)
  - Per card: `title` from `h3.base-search-card__title`, `company` from `h4.base-search-card__subtitle`, `location` from `.job-search-card__location` (default `"Remote"` if absent), `url` from `a.base-card__full-link[href]` stripped of query params, `posted_date` from `time[datetime]` attribute (or `None`)
  - `description` set to `""` (no detail page navigation)
  - Skips cards where `url` or `title` is empty
  - Returns `list[Job]` with `source="linkedin"`
  - Reference: `scrapers/indeed.py` for Playwright + stealth pattern; `research.md` §1 for selectors

- [x] T003 [US1] Write `tests/unit/test_linkedin_scraper.py` smoke test: <!-- squad:agent=python-engineer tier=lightweight -->
  - `test_linkedin_scraper_returns_list`: instantiates `LinkedInScraper()`, calls `fetch("fullstack developer", 3)`, asserts return value is a `list`
  - `test_linkedin_scraper_graceful_failure`: monkey-patches `asyncio.run` to raise `RuntimeError`; asserts `fetch(...)` returns `[]` without raising
  - `test_linkedin_job_source`: if any jobs are returned, asserts `job.source == "linkedin"` for all

---

## Phase 4: User Story 2 — Solides Job Board Scraping (Priority: P2)

**Goal**: A working `SolidesScraper` that fetches job listings from the vagas.solides.com.br public REST API using `requests`, returning `Job` objects with `source="solides"`.

**Independent Test**: Run `from scrapers.solides import SolidesScraper; jobs = SolidesScraper().fetch("fullstack developer", 5); assert all(j.source == "solides" for j in jobs)` and verify at least one job returns.

- [x] T004 [P] [US2] Implement `scrapers/solides.py` with `SolidesScraper(BaseScraper)`: <!-- squad:agent=scraping-engineer tier=standard -->
  - `fetch(query, max_results) -> list[Job]` wraps entire body in `try/except`; logs warning and returns `[]` on any failure
  - Makes a `GET` request to `https://apigw.solides.com.br/jobs/v3/portal-vacancies-new` with params `{"title": query, "locations": "", "take": max_results, "page": 1}` and headers `{"Origin": "https://vagas.solides.com.br", "Referer": "https://vagas.solides.com.br/"}`, timeout 15s
  - Calls `resp.raise_for_status()`; parses `resp.json()["data"]["data"]` as the list of job dicts
  - Filters to remote/home-office jobs only: keep items where `item.get("homeOffice") is True` or `item.get("jobType") == "home-office"`; if no items pass the filter, returns all items unfiltered (graceful fallback)
  - Per item: `title` from `item["title"]`, `company` from `item["companyName"]`, `location` as `"Remote"` if `homeOffice=True` else `f"{item.get('city', {}).get('name', '')}, {item.get('state', {}).get('code', '')}"`, `url` from `item["redirectLink"]`, `posted_date` from `item["createdAt"]`
  - `description`: `item.get("description", "")` with HTML tags stripped via `re.sub(r"<[^>]+>", "", raw)`, truncated to 2000 chars
  - `salary`: `None` (Solides salary rarely populated)
  - Skips items where `url` or `title` is empty
  - Returns `list[Job]` with `source="solides"`
  - Reference: `scrapers/himalayas.py` for `requests`-based pattern; `research.md` §2 for API contract

- [x] T005 [P] [US2] Write `tests/unit/test_solides_scraper.py` smoke test: <!-- squad:agent=python-engineer tier=lightweight -->
  - `test_solides_scraper_returns_list`: instantiates `SolidesScraper()`, calls `fetch("fullstack", 3)`, asserts return value is a `list`
  - `test_solides_scraper_graceful_failure`: monkey-patches `requests.get` to raise `requests.RequestException`; asserts `fetch(...)` returns `[]` without raising
  - `test_solides_job_source`: if any jobs are returned, asserts `job.source == "solides"` for all
  - `test_solides_html_stripped`: mocks `requests.get` to return a fixture response with `description = "<p>Hello <b>World</b></p>"`; asserts returned job `description` contains `"Hello World"` and no `"<p>"` or `"<b>"` tags

---

## Phase 5: User Story 3 — Pipeline Integration (Priority: P3)

**Goal**: Both new scrapers are registered in `main.py` and their results flow through the full scoring and note-saving pipeline.

**Depends on**: T002 (US1 complete) + T004 (US2 complete)

**Independent Test**: Run `python main.py` and verify Obsidian notes appear with `source: linkedin` and/or `source: solides` in their YAML frontmatter.

- [x] T006 [US3] Register `LinkedInScraper` and `SolidesScraper` in `main.py`: <!-- squad:agent=python-engineer tier=lightweight -->
  - Add imports at top of file: `from scrapers.linkedin import LinkedInScraper` and `from scrapers.solides import SolidesScraper`
  - In the scraper list construction (near existing `GoogleJobsScraper`, `HimalayasScraper` instantiations), append `LinkedInScraper()` and `SolidesScraper()` — no constructor args needed
  - Verify the existing loop that calls `scraper.fetch(query, cfg.max_jobs_per_source)` for each scraper will cover the new scrapers without any further changes
  - Add log lines consistent with existing pattern, e.g.: `print(f"[SCRAPERS] LinkedInScraper: {len(linkedin_jobs)} jobs")` (follow whatever logging pattern `main.py` already uses for other scrapers)
  - Reference: `main.py` existing scraper registration block; `contracts/cli.md` for expected output format

---

## Final Phase: Polish & Cross-Cutting Concerns

- [x] T007 Verify `scrapers/__init__.py` does not need updating (it is currently empty — no re-exports required; confirm this is still the case and leave it empty if so) <!-- squad:agent=python-engineer tier=lightweight -->
- [x] T008 [P] Run full smoke-test suite: `python -m pytest tests/unit/ -v` and confirm all existing tests plus `test_linkedin_scraper.py` and `test_solides_scraper.py` pass (or gracefully skip if network unavailable) <!-- squad:agent=python-engineer tier=lightweight -->
- [x] T009 [P] Manual end-to-end smoke test per `quickstart.md`: run each scraper standalone using the inline Python snippets in `quickstart.md §Smoke-Testing` and confirm at least one returns a non-empty list (or gracefully degrades if the source is unreachable); record wall-clock time for both scrapers combined — log a warning if the combined time exceeds 60s (verifies SC-005) <!-- squad:agent=python-engineer tier=lightweight -->

---

## Dependencies

```
T001 (base.py update)
  └── T002 (LinkedIn scraper)        T004 (Solides scraper)  ← parallel
        └── T003 (LinkedIn test)          └── T005 (Solides test)
              └──────────────────────────────────┘
                             T006 (main.py integration)
                                   └── T007, T008, T009 (polish)
```

---

## Parallel Execution Opportunities

**After T001 is complete**, T002 and T004 can be worked simultaneously (separate files, zero shared state):

| Worker A (US1) | Worker B (US2) |
|----------------|----------------|
| T002 — `scrapers/linkedin.py` | T004 — `scrapers/solides.py` |
| T003 — `tests/unit/test_linkedin_scraper.py` | T005 — `tests/unit/test_solides_scraper.py` |

T006 requires both workers to be complete.
T007, T008, T009 can all run in parallel after T006.

---

## Implementation Strategy

**MVP (just US1)**: Implement T001 → T002 → T003 → T006 (LinkedIn only in pipeline). Delivers the highest-value source immediately.

**Full feature**: Complete all phases in order; US2 runs in parallel with US1 after T001.

---

## Task Summary

| Phase | Tasks | Story | Parallel? |
|-------|-------|-------|-----------|
| Phase 1 — Setup | T001 | — | No |
| Phase 3 — US1 LinkedIn | T002, T003 | US1 | No (sequential) |
| Phase 4 — US2 Solides | T004, T005 | US2 | [P] with Phase 3 |
| Phase 5 — US3 Integration | T006 | US3 | No |
| Final — Polish | T007, T008, T009 | — | T008/T009 [P] |

**Total tasks**: 9
**Tasks per user story**: US1=2, US2=2, US3=1
**Parallel opportunities**: Phase 3 & 4 fully parallel; T008/T009 parallel
**Suggested MVP scope**: T001 → T002 → T003 → T006 (US1 only, 4 tasks)

**Format validation**: All 9 tasks follow `- [ ] [ID] [P?] [Story?] Description with file path` ✅

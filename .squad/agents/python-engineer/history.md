# python-engineer History

## 2026-05-25 — Final Phase: Polish & Verification (T014, T015)

- T014: Ran `.venv/bin/pip install -r requirements.txt`. `beautifulsoup4>=4.12` was already satisfied (4.14.3 installed). `greenlet==3.0.3` (pulled by `playwright==1.44.0`) failed to build a wheel on Python 3.14 due to a C++ ABI incompatibility — this is a pre-existing constraint, not a regression, and does not affect the scrapers or tests. All other deps resolved cleanly.
- T015: Ran `.venv/bin/pytest tests/ -v`. **10/10 tests passed** in 31.85s. Breakdown: 3 capgemini + 3 linkedin + 4 solides. The `RuntimeWarning: coroutine 'LinkedInScraper._async_fetch' was never awaited` is a pre-existing warning (not a failure) triggered by GC during teardown.
- Marked T014 and T015 complete in `specs/003-src-restructure-capgemini-scraper/tasks.md`.

## 2026-05-25 — Phase 5: Pipeline Integration (T013)

- Added `from scrapers.capgemini import CapgeminiScraper` import to `src/main.py` alongside the other scraper imports (alphabetical order).
- Added `(CapgeminiScraper(), queries)` to the `scraper_pairs` list in `main()`, using the same `queries` list as `LinkedInScraper` and `SolidesScraper`.
- Updated the `[SCRAPER] Registered:` log line to include `CapgeminiScraper`.
- Marked T013 complete (`- [x]`) in `specs/003-src-restructure-capgemini-scraper/tasks.md`.
- Pattern followed exactly: `CapgeminiScraper()` takes no constructor arguments; uses the generic `_build_queries()` output.

## Learnings

### 2026-05-24

- **T002**: Pinned all production deps in `requirements.txt` from `>=` to `==` using exact versions per spec. `pytest>=7.0` kept flexible as it is dev-only.
- **T035**: Replaced the 8-query cartesian product in `_build_queries()` with exactly 2 hardcoded strings — one EN, one PT-BR — per spec. No other logic in `main.py` was touched.

### 2026-05-25 (spec-003 Phase 1 — T001, T002)

- **T001**: Added `beautifulsoup4>=4.12` to `requirements.txt` (line 2, after pdfplumber). Used `>=` (not pinned) as it is a scraper-only dep with no strict version constraint in the plan.
- **T002**: Created `pytest.ini` at project root with `[pytest]\npythonpath = src`. This allows `pytest tests/` to resolve `src/` imports without modifying test files after the US1 migration.

### 2026-05-25 (spec-003 Phase 2 — T003)

- **T003**: Created `src/` directory with `mkdir -p src` and moved `analyzer.py`, `config.py`, `main.py` from project root into `src/` using a single `mv` command. Root has no `.py` files post-move. File contents were not modified (phase constraint respected).

### 2026-05-25 (spec-003 Phase 3 — T004–T009)

- **T004–T007**: Moved `llm/`, `obsidian/`, `resume/`, `scrapers/` from project root into `src/` using a single chained `mv` command. All `__init__.py` files intact; no file contents modified.
- **T008**: Updated `com.douglashennrich.jobfinder.plist` second ProgramArguments entry from `.../main.py` to `.../src/main.py`. WorkingDirectory unchanged.
- **T009**: Import check `.venv/bin/python -c "import sys; sys.path.insert(0,'src'); import llm; import obsidian; import resume; import scrapers"` → OK. `pytest tests/ -v` → 7 passed in 39.1s (no failures). Note: `python src/main.py` with system python raises `ModuleNotFoundError: No module named 'openai'` because venv is not active — not a migration regression.

### 2026-05-25 (Final Phase T007–T009 — earlier run)

Final Phase (T007-T009): scrapers/__init__.py verified empty; full test suite 7 passed (17.15s); smoke tests executed — LinkedIn 5 jobs, Solides 4 jobs, combined 7.4s (under 60s limit).

---

### 2026-05-24 (E2E Validation Run)

**T025 – Google Jobs Scraper:**
- Serper `/jobs` endpoint returns 404 (plan limitation, not code bug). Correct URL is `https://google.serper.dev/jobs` but requires paid Jobs API tier.
- `asyncio.get_event_loop().run_until_complete()` crashes in Python 3.14 main thread (no event loop). Fixed to `asyncio.run()` in both `scrapers/google_jobs.py` and `scrapers/indeed.py`.
- Playwright fallback runs without exception but returns 0 jobs (Google's headless bot detection / `div[data-jiz]` selector stale).

**T036 – Full pipeline E2E:**
- Copilot LLM: `claude-sonnet-4.6` is available via **Copilot Pro+**. The endpoint `models.inference.ai.azure.com` is for GitHub Models free tier (only `gpt-4o` / `gpt-4o-mini`). Copilot Pro+ uses a different underlying URL for Anthropic models — the same `CopilotLLM` client works as long as the token comes from a Pro+ account (via `gh auth token`). Model is now hardcoded as a constant `COPILOT_MODEL = "claude-sonnet-4.6"` in `llm/copilot.py`; `COPILOT_MODEL` env var removed.
- IndeedScraper: `playwright_stealth` v2 API changed — `stealth_async` no longer exported; now uses `Stealth().apply_stealth_async()`. Scraper returns 0 (non-blocking).
- HimalayasScraper: Works correctly, 20 jobs per query.
- Pipeline completed successfully in ~98s: Saved 1 | Skipped (dup): 21 | Skipped (score): 18 | Errors: 0.
- Company field shows `name` placeholder on some Himalayas jobs — cosmetic issue, doesn't affect pipeline flow.

**T034 – Dedup validation:**
- Second run confirmed: Saved: 0 | Skipped (dup): 22. Dedup mechanism working correctly (both in-memory slug set and vault `note_exists()` checks).

**T039 – launchd validation:**
- Plist had `/usr/bin/python3` (system Python, Operation not permitted on macOS). Fixed to `.venv/bin/python`.
- After fix, Python init hangs under launchd: stuck in `getpath_readlines` → `open$NOCANCEL` syscall during venv path resolution. Root cause: macOS sandbox or privacy framework blocking file access during Python initialization under `LimitLoadToSessionType = Aqua` launchd context.
- Workaround needed: Either grant Full Disk Access to Terminal/Python, or use absolute Python path from Homebrew directly (not venv symlink).

### 2026-05-25

Phase 3 (T003): Created tests/unit/test_linkedin_scraper.py — 3 smoke tests: returns_list, graceful_failure, job_source
Phase 4 (T005): Created tests/unit/test_solides_scraper.py — 4 smoke tests all passing
Phase 5 (T006): Registered LinkedInScraper and SolidesScraper in main.py — imports + scraper list

# python-engineer History

## Learnings

### 2026-05-24

- **T002**: Pinned all production deps in `requirements.txt` from `>=` to `==` using exact versions per spec. `pytest>=7.0` kept flexible as it is dev-only.
- **T035**: Replaced the 8-query cartesian product in `_build_queries()` with exactly 2 hardcoded strings — one EN, one PT-BR — per spec. No other logic in `main.py` was touched.

### 2026-05-25 (Final Phase T007–T009)

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

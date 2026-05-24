# python-engineer History

## Learnings

### 2026-05-24

- **T002**: Pinned all production deps in `requirements.txt` from `>=` to `==` using exact versions per spec. `pytest>=7.0` kept flexible as it is dev-only.
- **T035**: Replaced the 8-query cartesian product in `_build_queries()` with exactly 2 hardcoded strings — one EN, one PT-BR — per spec. No other logic in `main.py` was touched.

### 2026-05-24 (E2E Validation Run)

**T025 – Google Jobs Scraper:**
- Serper `/jobs` endpoint returns 404 (plan limitation, not code bug). Correct URL is `https://google.serper.dev/jobs` but requires paid Jobs API tier.
- `asyncio.get_event_loop().run_until_complete()` crashes in Python 3.14 main thread (no event loop). Fixed to `asyncio.run()` in both `scrapers/google_jobs.py` and `scrapers/indeed.py`.
- Playwright fallback runs without exception but returns 0 jobs (Google's headless bot detection / `div[data-jiz]` selector stale).

**T036 – Full pipeline E2E:**
- Copilot LLM: `claude-sonnet-4.6` is NOT available on `models.inference.ai.azure.com`. Only `gpt-4o` and `gpt-4o-mini` are available. Updated `.env` `COPILOT_MODEL=gpt-4o`.
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

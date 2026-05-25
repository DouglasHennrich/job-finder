# scraping-engineer History

## Learnings

### 2026-05-24 — Scraper Fixes (T021/T022/T023)

- **Himalayas API has no `remote` boolean field** — the platform is remote-only by design. The `locationRestrictions` array holds geographic candidate restrictions (country names), not a remote indicator. Guarded with `if item.get("remote") is False: continue` as a future-proof no-op that would activate if the API ever returns non-remote entries.
- **GoogleJobsScraper fallback was dead code** — `_fetch_playwright()` existed but was never called. Fixed `fetch()` to use `asyncio.get_event_loop().run_until_complete(self._fetch_playwright(...))` as the fallback. `_fetch_remotive()` remains in the file but is no longer called from `fetch()`.
- **IndeedScraper RSS is blocked** — Indeed's RSS feed returns 403/empty for remote job searches. Replaced with Playwright+stealth (`stealth_async`) using incremental scroll, random mouse moves, and per-job detail page navigation. Each detail page also gets stealth applied before navigation.
- **playwright_stealth import**: the package is `playwright-stealth`, import as `from playwright_stealth import stealth_async` (async variant). The older `Stealth().apply_stealth_async(page)` pattern (used in google_jobs.py) is the class-based API; `stealth_async(page)` is the function-based API — both are valid depending on the installed version.

### 2026-05-24 — playwright_stealth v2 API break fix

- **v2 removed `stealth_async`** — `playwright-stealth` v2.x dropped the top-level `stealth_async` function entirely. The only export for async page stealth is now `Stealth` (class) with `await Stealth().apply_stealth_async(page)`.
- **Fix applied to `scrapers/indeed.py`**: changed `from playwright_stealth import stealth_async` → `from playwright_stealth import Stealth`, and changed call site `await stealth_async(page)` → `await Stealth().apply_stealth_async(page)`.
- **Smoke test confirmed**: after the fix, `IndeedScraper.fetch("senior nodejs developer remote", 2)` returned 2 jobs without errors.

### 2026-05-24 — T021 field mapping confirmed / T023 detail-page stealth fix

- **Himalayas API uses flat `companyName` field** (not nested `company.name`) — confirmed by passing T024 smoke test returning 5 real jobs with correct company names.
- **playwright-stealth: use `Stealth().apply_stealth_async(page)` pattern** — NOT standalone `stealth_async(page)`. The v2 class-based API is the only valid approach; the function-based `stealth_async` was removed. This applies to ALL page handles, including detail pages opened mid-scrape.

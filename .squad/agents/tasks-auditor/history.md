# tasks-auditor — History

## Learnings

### 2026-05-24 — First Audit Run
- **Summary:** 27 ✅ Done | 4 ⚠️ Partial | 0 ❌ Missing | 1 🔴 Broken | 7 ⏳ Pending (manual/external)
- **Patterns noticed:**
  - Orphaned `# TODO` scaffold comments left in `config.py`, `resume/parser.py`, `main.py` — code IS implemented below them, but comments create confusion
  - `T016 CopilotLLM` deviates from spec base_url (`api.githubcopilot.com` vs spec's `models.inference.ai.azure.com`) — functional but spec-non-conformant
  - `T022 GoogleJobsScraper` uses `/search` endpoint + organic parsing instead of spec's `/jobs` endpoint; Playwright fallback completely missing
  - `T023 IndeedScraper` has runtime `NameError`: `stealth_async(detail_page)` at line 100 is undefined (only `Stealth().apply_stealth_async()` was imported) — will break on any job with a detail URL
  - `T035 main.py` omits `IndeedScraper` from `scraper_pairs`; uses cache-first approach for resume loading (undocumented improvement but spec deviation)
  - All 3 manual/external smoke tests (T018, T025, T026) deferred — T026 would fail at runtime due to T023 bug even with external deps present

## Key Files

- `specs/001-job-finder/tasks.md` — source of truth for all tasks
- `specs/001-job-finder/spec.md` — acceptance criteria and user stories
- `specs/001-job-finder/plan.md` — implementation plan
- `specs/001-job-finder/contracts/cli.md` — CLI contracts and smoke test commands
- `.squad/routing.md` — agent routing table for escalation decisions
2026-05-25: Audited 002-linkedin-solides-scrapers — 9/9 tasks verified ✅

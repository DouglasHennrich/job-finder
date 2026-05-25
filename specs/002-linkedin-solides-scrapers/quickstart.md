# Quickstart: LinkedIn & Solides Scrapers

**Phase 1 output** | **Branch**: `002-linkedin-solides-scrapers` | **Date**: 2026-05-24

---

## What This Feature Adds

Two new job sources are added to the pipeline:

| Scraper | File | Approach | Credentials |
|---------|------|----------|-------------|
| `LinkedInScraper` | `scrapers/linkedin.py` | Playwright + stealth | None (public pages) |
| `SolidesScraper` | `scrapers/solides.py` | REST API via `requests` | None |

---

## Prerequisites

No new environment variables are required. Both scrapers work without credentials.

Verify `playwright` and `playwright-stealth` are installed (they are, for `IndeedScraper`):
```bash
python -m playwright install chromium
```

---

## Smoke-Testing Each Scraper Independently

### LinkedIn Scraper
```bash
python - <<'EOF'
from scrapers.linkedin import LinkedInScraper
scraper = LinkedInScraper()
jobs = scraper.fetch("senior fullstack developer nodejs react", max_results=5)
print(f"LinkedIn: {len(jobs)} jobs")
for j in jobs:
    print(f"  [{j.source}] {j.title} @ {j.company} — {j.url}")
EOF
```

Expected output (example):
```
LinkedIn: 5 jobs
  [linkedin] Senior Full Stack Developer @ Company XYZ — https://br.linkedin.com/jobs/view/...
  [linkedin] Full Stack Engineer (Node/React) @ StartupABC — https://br.linkedin.com/jobs/view/...
  ...
```

If LinkedIn blocks the request:
```
WARNING:scrapers.linkedin:LinkedInScraper failed: [reason]
LinkedIn: 0 jobs
```
This is graceful degradation — not a bug.

---

### Solides Scraper
```bash
python - <<'EOF'
from scrapers.solides import SolidesScraper
scraper = SolidesScraper()
jobs = scraper.fetch("fullstack developer", max_results=5)
print(f"Solides: {len(jobs)} jobs")
for j in jobs:
    print(f"  [{j.source}] {j.title} @ {j.company} — {j.url}")
EOF
```

Expected output:
```
Solides: 5 jobs
  [solides] Desenvolvedor Full Stack Pleno @ Empresa XPTO — https://xpto.solides.jobs/vacancies/...
  ...
```

---

## Full Pipeline Run

No changes to how you run the full pipeline:
```bash
python main.py
```

The two new scrapers are automatically included. Check logs for their contribution:
```
[SCRAPERS] GoogleJobsScraper: 12 jobs
[SCRAPERS] HimalayasScraper: 18 jobs
[SCRAPERS] IndeedScraper: 8 jobs
[SCRAPERS] LinkedInScraper: 15 jobs
[SCRAPERS] SolidesScraper: 20 jobs
[TOTAL] 73 raw jobs before dedup
```

---

## Files Changed

| File | Change |
|------|--------|
| `scrapers/linkedin.py` | **New** — LinkedInScraper implementation |
| `scrapers/solides.py` | **New** — SolidesScraper implementation |
| `scrapers/base.py` | **Updated** — `source` field comment |
| `main.py` | **Updated** — register both new scrapers |
| `tests/unit/test_linkedin_scraper.py` | **New** — smoke test |
| `tests/unit/test_solides_scraper.py` | **New** — smoke test |

---

## Known Limitations

| Issue | Impact | Mitigation |
|-------|--------|------------|
| LinkedIn bot detection | Scraper may return 0 jobs intermittently | Graceful degradation; pipeline continues |
| LinkedIn CSS selectors may change | Scraper breaks silently | Logged warning; update selectors as needed |
| Solides `homeOffice` filter | API may not support direct `homeOffice=true` param | Filter client-side in Python |
| Solides HTML in `description` field | Raw HTML tags in job notes | Strip tags before storing |

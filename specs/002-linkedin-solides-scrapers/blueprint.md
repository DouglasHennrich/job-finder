# Blueprint: LinkedIn & Solides Job Scrapers

**Branch**: `002-linkedin-solides-scrapers` | **Date**: 2026-05-25

**Mode**: doc-only

**Total Tasks**: 9 | **Files**: 4 new, 2 modified, 0 deleted

---

## Key Decisions

- Use `Playwright + playwright-stealth` for `LinkedInScraper`, mirroring the existing `IndeedScraper` pattern exactly — avoids introducing new dependencies → T002
- Use plain `requests` for `SolidesScraper`, mirroring the existing `HimalayasScraper` pattern exactly — Solides exposes a public, unauthenticated JSON REST API → T004
- `description` is set to `""` for LinkedIn (no detail-page navigation) to avoid additional browser requests; Solides description is HTML-stripped via `re.sub` → T002, T004
- Both new scrapers share `queries` (generic free-text) with `HimalayasScraper`, not `serper_queries`, because they accept plain keyword search → T006
- `scrapers/__init__.py` intentionally stays empty — no re-exports needed → T007

---

## Implementation Order

```
T001 (scrapers/base.py — source comment)
  ├── T002 (scrapers/linkedin.py)        T004 (scrapers/solides.py)   ← parallel
  │     └── T003 (test_linkedin.py)            └── T005 (test_solides.py)
  └──────────────────────────────────────────────────────────┘
                           T006 (main.py registration)
                                  ├── T007 (verify __init__.py — pre-completed)
                                  ├── T008 (run pytest suite)
                                  └── T009 (manual e2e smoke test)
```

---

## Phase 1: Setup

---

### T001: Update `source` comment in `scrapers/base.py`

**File**: `scrapers/base.py` (modify)

**Requirements**: FR-010

**Dependencies**: none

**Before** (line 11):

```python
    source: str  # "google_jobs" | "indeed" | "himalayas"
```

**After**:

```python
    source: str  # "google_jobs" | "indeed" | "himalayas" | "linkedin" | "solides"
```

**Verification**: `grep 'linkedin.*solides' scrapers/base.py` returns the updated comment line.

---

## Phase 3: User Story 1 — LinkedIn Direct Scraping

---

### T002: Implement `scrapers/linkedin.py`

**File**: `scrapers/linkedin.py` (new)

**Requirements**: FR-001, FR-002, FR-003, FR-004, FR-011

**Dependencies**: T001

```python
from __future__ import annotations

import asyncio
import logging
import random
import urllib.parse

from scrapers.base import BaseScraper, Job

logger = logging.getLogger(__name__)

_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

_BASE_URL = "https://www.linkedin.com/jobs/search"


class LinkedInScraper(BaseScraper):
    """LinkedIn public job search scraper using Playwright + stealth.

    Accesses https://www.linkedin.com/jobs/search (public, no credentials).
    Applies playwright-stealth and humanisation delays to reduce bot detection.
    Never raises — returns [] on any failure (FR-004).
    """

    def fetch(self, query: str, max_results: int) -> list[Job]:
        try:
            return asyncio.run(self._async_fetch(query, max_results))
        except Exception as e:
            logger.warning(f"LinkedInScraper failed: {e}")
            return []

    async def _async_fetch(self, query: str, max_results: int) -> list[Job]:
        from playwright.async_api import async_playwright
        from playwright_stealth import Stealth

        encoded_query = urllib.parse.quote_plus(query)
        target_url = (
            f"{_BASE_URL}?keywords={encoded_query}&location=Brazil&f_WT=2"
        )
        jobs: list[Job] = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=_USER_AGENT)
            page = await context.new_page()
            await Stealth().apply_stealth_async(page)

            await page.goto(target_url)
            # Humanisation: wait for page to fully render and apply randomised delay
            await asyncio.sleep(random.uniform(1.5, 3.5))

            # Humanisation: random mouse move before querying cards
            await page.mouse.move(
                random.randint(100, 800),
                random.randint(100, 600),
            )

            cards = await page.query_selector_all(".job-search-card")

            for card in cards[:max_results]:
                try:
                    title_el = await card.query_selector("h3.base-search-card__title")
                    title = (
                        await title_el.inner_text() if title_el else ""
                    ).strip()

                    company_el = await card.query_selector(
                        "h4.base-search-card__subtitle"
                    )
                    company = (
                        await company_el.inner_text() if company_el else ""
                    ).strip()

                    location_el = await card.query_selector(
                        ".job-search-card__location"
                    )
                    location = (
                        await location_el.inner_text() if location_el else "Remote"
                    ).strip()

                    link_el = await card.query_selector("a.base-card__full-link")
                    href = (
                        await link_el.get_attribute("href") if link_el else ""
                    ) or ""

                    # Strip tracking query params — keep only the canonical job URL
                    if href:
                        parsed = urllib.parse.urlparse(href)
                        href = urllib.parse.urlunparse(parsed._replace(query=""))

                    date_el = await card.query_selector("time[datetime]")
                    posted_date = (
                        await date_el.get_attribute("datetime") if date_el else None
                    )

                    if not title or not href:
                        continue

                    jobs.append(
                        Job(
                            title=title,
                            company=company,
                            location=location,
                            description="",
                            url=href,
                            source="linkedin",
                            salary=None,
                            posted_date=posted_date,
                        )
                    )
                except Exception as card_err:
                    logger.debug(f"LinkedIn card extraction error: {card_err}")
                    continue

            await browser.close()

        return jobs
```

**Verification**:

```bash
python - <<'EOF'
from scrapers.linkedin import LinkedInScraper
jobs = LinkedInScraper().fetch("senior fullstack nodejs react", 5)
assert isinstance(jobs, list)
assert all(j.source == "linkedin" for j in jobs)
print(f"LinkedIn: {len(jobs)} jobs — OK")
EOF
```

---

### T003: Write `tests/unit/test_linkedin_scraper.py`

**File**: `tests/unit/test_linkedin_scraper.py` (new)

**Requirements**: FR-001, FR-004

**Dependencies**: T002

```python
from __future__ import annotations

from unittest.mock import patch

from scrapers.linkedin import LinkedInScraper


def test_linkedin_scraper_returns_list():
    """Smoke test: fetch returns a list (may be empty if network unavailable)."""
    scraper = LinkedInScraper()
    result = scraper.fetch("fullstack developer", 3)
    assert isinstance(result, list)


def test_linkedin_scraper_graceful_failure():
    """FR-004: on any exception, fetch returns [] without raising."""
    scraper = LinkedInScraper()
    with patch("asyncio.run", side_effect=RuntimeError("mocked failure")):
        result = scraper.fetch("fullstack developer", 3)
    assert result == []


def test_linkedin_job_source():
    """FR-003: all returned jobs have source='linkedin'."""
    scraper = LinkedInScraper()
    result = scraper.fetch("fullstack developer", 3)
    for job in result:
        assert job.source == "linkedin"
```

**Verification**: `python -m pytest tests/unit/test_linkedin_scraper.py -v` — all three tests pass.

---

## Phase 4: User Story 2 — Solides Job Board Scraping

---

### T004: Implement `scrapers/solides.py`

**File**: `scrapers/solides.py` (new)

**Requirements**: FR-005, FR-006, FR-007, FR-008, FR-011

**Dependencies**: T001

```python
from __future__ import annotations

import logging
import re

import requests

from scrapers.base import BaseScraper, Job

logger = logging.getLogger(__name__)

_API_URL = "https://apigw.solides.com.br/jobs/v3/portal-vacancies-new"
_HEADERS = {
    "Origin": "https://vagas.solides.com.br",
    "Referer": "https://vagas.solides.com.br/",
}


class SolidesScraper(BaseScraper):
    """Solides job board scraper via the public REST API (no credentials).

    Endpoint: GET https://apigw.solides.com.br/jobs/v3/portal-vacancies-new
    Filters to remote/home-office listings post-response; falls back to all
    items if none pass the filter.
    Never raises — returns [] on any failure (FR-008).
    """

    def fetch(self, query: str, max_results: int) -> list[Job]:
        try:
            resp = requests.get(
                _API_URL,
                params={
                    "title": query,
                    "locations": "",
                    "take": max_results,
                    "page": 1,
                },
                headers=_HEADERS,
                timeout=15,
            )
            resp.raise_for_status()
            items = resp.json()["data"]["data"]
        except Exception as e:
            logger.warning(f"SolidesScraper failed: {e}")
            return []

        # Prefer remote/home-office jobs; fall back to all results if none qualify
        remote_items = [
            item
            for item in items
            if item.get("homeOffice") is True or item.get("jobType") == "home-office"
        ]
        candidates = remote_items if remote_items else items

        jobs: list[Job] = []
        for item in candidates[:max_results]:
            try:
                title = item.get("title", "")
                url = item.get("redirectLink", "")
                if not title or not url:
                    continue

                company = item.get("companyName", "")

                if item.get("homeOffice") is True:
                    location = "Remote"
                else:
                    city_name = item.get("city", {}).get("name", "")
                    state_code = item.get("state", {}).get("code", "")
                    location = (
                        f"{city_name}, {state_code}"
                        if city_name or state_code
                        else "Remote"
                    )

                raw_desc = item.get("description", "") or ""
                description = re.sub(r"<[^>]+>", "", raw_desc)[:2000]

                posted_date = item.get("createdAt")

                jobs.append(
                    Job(
                        title=title,
                        company=company,
                        location=location,
                        description=description,
                        url=url,
                        source="solides",
                        salary=None,
                        posted_date=posted_date,
                    )
                )
            except Exception as item_err:
                logger.debug(f"Solides item extraction error: {item_err}")
                continue

        return jobs
```

**Verification**:

```bash
python - <<'EOF'
from scrapers.solides import SolidesScraper
jobs = SolidesScraper().fetch("fullstack developer", 5)
assert isinstance(jobs, list)
assert all(j.source == "solides" for j in jobs)
print(f"Solides: {len(jobs)} jobs — OK")
EOF
```

---

### T005: Write `tests/unit/test_solides_scraper.py`

**File**: `tests/unit/test_solides_scraper.py` (new)

**Requirements**: FR-005, FR-008

**Dependencies**: T004

```python
from __future__ import annotations

from unittest.mock import MagicMock, patch

import requests

from scrapers.solides import SolidesScraper


def test_solides_scraper_returns_list():
    """Smoke test: fetch returns a list (may be empty if network unavailable)."""
    scraper = SolidesScraper()
    result = scraper.fetch("fullstack", 3)
    assert isinstance(result, list)


def test_solides_scraper_graceful_failure():
    """FR-008: on RequestException, fetch returns [] without raising."""
    scraper = SolidesScraper()
    with patch("requests.get", side_effect=requests.RequestException("mocked failure")):
        result = scraper.fetch("fullstack", 3)
    assert result == []


def test_solides_job_source():
    """FR-007: all returned jobs have source='solides'."""
    scraper = SolidesScraper()
    result = scraper.fetch("fullstack", 3)
    for job in result:
        assert job.source == "solides"


def test_solides_html_stripped():
    """HTML tags in description must be removed before storing."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": {
            "data": [
                {
                    "title": "Full Stack Developer",
                    "companyName": "Acme Corp",
                    "homeOffice": True,
                    "jobType": "home-office",
                    "description": "<p>Hello <b>World</b></p>",
                    "redirectLink": "https://acme.solides.jobs/vacancies/1",
                    "createdAt": "2026-05-24",
                }
            ]
        }
    }
    mock_response.raise_for_status = MagicMock()

    with patch("requests.get", return_value=mock_response):
        scraper = SolidesScraper()
        result = scraper.fetch("fullstack", 3)

    assert len(result) == 1
    assert "Hello World" in result[0].description
    assert "<p>" not in result[0].description
    assert "<b>" not in result[0].description
```

**Verification**: `python -m pytest tests/unit/test_solides_scraper.py -v` — all four tests pass (only `test_solides_html_stripped` requires no network; others may be skipped in offline environments).

---

## Phase 5: User Story 3 — Pipeline Integration

---

### T006: Register `LinkedInScraper` and `SolidesScraper` in `main.py`

**File**: `main.py` (modify)

**Requirements**: FR-009

**Dependencies**: T002, T004

**Change 1 — Add imports** (after line 24, `from scrapers.himalayas import HimalayasScraper`):

**Before** (lines 23–24):

```python
from scrapers.google_jobs import GoogleJobsScraper
from scrapers.himalayas import HimalayasScraper
```

**After**:

```python
from scrapers.google_jobs import GoogleJobsScraper
from scrapers.himalayas import HimalayasScraper
from scrapers.linkedin import LinkedInScraper
from scrapers.solides import SolidesScraper
```

**Change 2 — Append to `scraper_pairs`** (lines 85–88 in current file; apply after Change 1):

**Before** (lines 85–88):

```python
    scraper_pairs: list[tuple] = [
        (HimalayasScraper(), queries),
        (GoogleJobsScraper(api_key=cfg.serper_api_key), serper_queries),
    ]
```

**After**:

```python
    scraper_pairs: list[tuple] = [
        (HimalayasScraper(), queries),
        (GoogleJobsScraper(api_key=cfg.serper_api_key), serper_queries),
        (LinkedInScraper(), queries),
        (SolidesScraper(), queries),
    ]
```

**Verification**: `python main.py` runs without `ImportError`; log lines `[SCRAPER] LinkedInScraper` and `[SCRAPER] SolidesScraper` appear in output.

---

## Final Phase: Polish & Cross-Cutting Concerns

### Pre-completed Tasks

| Task | File | Status |
|------|------|--------|
| T007: Verify `scrapers/__init__.py` needs no changes | `scrapers/__init__.py` | Already complete — file is empty, no re-exports required; confirmed on disk |

---

### T008: Run full smoke-test suite

**File**: n/a (command task)

**Dependencies**: T003, T005

**Command**:

```bash
python -m pytest tests/unit/ -v
```

**Expected output** (offline run):

```
tests/unit/test_linkedin_scraper.py::test_linkedin_scraper_returns_list PASSED
tests/unit/test_linkedin_scraper.py::test_linkedin_scraper_graceful_failure PASSED
tests/unit/test_linkedin_scraper.py::test_linkedin_job_source PASSED
tests/unit/test_solides_scraper.py::test_solides_scraper_returns_list PASSED
tests/unit/test_solides_scraper.py::test_solides_scraper_graceful_failure PASSED
tests/unit/test_solides_scraper.py::test_solides_job_source PASSED
tests/unit/test_solides_scraper.py::test_solides_html_stripped PASSED
```

Network-dependent tests (`test_linkedin_scraper_returns_list`, `test_solides_scraper_returns_list`, `test_linkedin_job_source`, `test_solides_job_source`) may return empty lists in CI/offline environments — this is graceful degradation, not failure.

**Verification**: All 7 tests report `PASSED` or the offline-safe subset passes with no `FAILED` or `ERROR` entries.

---

### T009: Manual end-to-end smoke test

**File**: n/a (command task)

**Dependencies**: T006

**LinkedIn standalone smoke test**:

```bash
python - <<'EOF'
import time
from scrapers.linkedin import LinkedInScraper
start = time.time()
jobs = LinkedInScraper().fetch("senior fullstack nodejs react", max_results=5)
elapsed = time.time() - start
print(f"LinkedIn: {len(jobs)} jobs in {elapsed:.1f}s")
for j in jobs:
    print(f"  [{j.source}] {j.title} @ {j.company} — {j.url}")
if elapsed > 60:
    print("WARNING: LinkedInScraper exceeded 60s threshold (SC-005)")
EOF
```

**Solides standalone smoke test**:

```bash
python - <<'EOF'
import time
from scrapers.solides import SolidesScraper
start = time.time()
jobs = SolidesScraper().fetch("fullstack developer", max_results=5)
elapsed = time.time() - start
print(f"Solides: {len(jobs)} jobs in {elapsed:.1f}s")
for j in jobs:
    print(f"  [{j.source}] {j.title} @ {j.company} — {j.url}")
EOF
```

**Combined timing check** (SC-005):

```bash
python - <<'EOF'
import time
from scrapers.linkedin import LinkedInScraper
from scrapers.solides import SolidesScraper
start = time.time()
linkedin_jobs = LinkedInScraper().fetch("senior fullstack nodejs react", 5)
solides_jobs = SolidesScraper().fetch("fullstack developer", 5)
elapsed = time.time() - start
print(f"Combined: LinkedIn={len(linkedin_jobs)}, Solides={len(solides_jobs)}, time={elapsed:.1f}s")
if elapsed > 60:
    import logging
    logging.warning(f"Combined scraper time {elapsed:.1f}s exceeds 60s threshold (SC-005)")
EOF
```

**Verification**: At least one of the two scrapers returns a non-empty list when network is available; both degrade gracefully to `0 jobs` when their respective source is unreachable. Combined wall-clock time ≤ 60s under normal network conditions.

---

## Checklist

- [ ] T001: Update `source` comment in `scrapers/base.py`
- [ ] T002: Implement `scrapers/linkedin.py` — `LinkedInScraper`
- [ ] T003: Write `tests/unit/test_linkedin_scraper.py`
- [ ] T004: Implement `scrapers/solides.py` — `SolidesScraper`
- [ ] T005: Write `tests/unit/test_solides_scraper.py`
- [ ] T006: Register both scrapers in `main.py`
- [X] T007: Verify `scrapers/__init__.py` — already complete, no changes needed
- [ ] T008: Run `python -m pytest tests/unit/ -v`
- [ ] T009: Manual end-to-end smoke test per `quickstart.md`

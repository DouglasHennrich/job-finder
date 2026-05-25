---
name: scraper-provider-investigation
description: >
  Use agent-browser to investigate a new job board provider before implementing its scraper.
  Discovers the real REST API or selectors via HAR capture and browser eval.
  Use when: adding a new scraper provider, fixing a broken scraper that returns 0 jobs,
  a job board is a SPA/React/JS-rendered page, or before writing any scraper code for a new site.
  Triggers: "novo provider", "novo scraper", "implementar scraper", "adicionar site de vagas",
  "scraper retorna 0", "job board SPA", "investigar provider".
---

# Scraper Provider Investigation

## When to Use

Load this skill **before writing any scraper code** whenever:

- Adding a new job board provider to `src/scrapers/`
- An existing scraper returns 0 results (possible SPA/JS-rendered page)
- The target site is known to be a React, Vue, or Angular SPA
- You need to confirm what API or selectors power the job listings

> **Key lesson:** Many job boards (e.g., Capgemini, LinkedIn) render listings client-side via JavaScript. `requests.get` on the main URL returns only a static shell — 0 job links. Always investigate with a real browser before writing the scraper.

---

## Phase 1 — Open and Snapshot the Page

```bash
# 1. Open the job search URL (substitute real URL and query)
agent-browser open "https://provider.com/jobs?q=fullstack"

# 2. Wait until all XHR/fetch calls finish
agent-browser wait --load networkidle

# 3. Capture accessibility snapshot to find visible job links
agent-browser snapshot -i -u | grep -i "job\|vagas\|career\|position" | head -20
```

**What to look for in the snapshot:**

- Direct `https://` job URLs → site is SSR, HTML scraping may work
- No job links found → site is a SPA, must find the underlying API (go to Phase 2)

---

## Phase 2 — Capture Network Traffic (HAR)

```bash
# 1. Start HAR recording
agent-browser network har start /tmp/provider_investigation.har

# 2. Re-open the page to capture all requests
agent-browser open "https://provider.com/jobs?q=fullstack"
agent-browser wait --load networkidle

# 3. Stop and analyze the HAR
agent-browser network har stop
```

**Analyze the HAR for API calls:**

```bash
python3 - <<'EOF'
import json, re

with open("/tmp/provider_investigation.har") as f:
    har = json.load(f)

entries = har["log"]["entries"]
# Filter for JSON API calls that likely serve job data
for e in entries:
    url = e["request"]["url"]
    status = e["response"]["status"]
    content_type = e["response"]["content"].get("mimeType", "")
    if status == 200 and "json" in content_type:
        if any(kw in url.lower() for kw in ["job", "career", "vagas", "search", "position", "listing"]):
            print(f"[{status}] {url}")
EOF
```

**Alternatively, filter directly in agent-browser:**

```bash
agent-browser network requests --filter "job\|search\|career\|api" 2>&1 | head -20
```

---

## Phase 3 — Inspect the API Response

Once you identify the API endpoint URL from Phase 2:

```bash
# Store result in a browser global to read back (async APIs need this pattern)
agent-browser eval "
fetch('https://discovered-api.example.com/jobs?page=1&size=2&q=fullstack')
  .then(r => r.json())
  .then(d => { window.__apiResult = JSON.stringify(d); });
'triggered'
"

# Wait for the async fetch to complete
agent-browser wait 2000

# Read the result
agent-browser eval "window.__apiResult"
```

**From the response, determine:**

| Need to find | What to look for                                         |
| ------------ | -------------------------------------------------------- |
| Job title    | `title`, `jobTitle`, `name`, `position`                  |
| Location     | `location`, `city`, `country`, `site`                    |
| Apply URL    | `url`, `apply_url`, `apply_job_url`, `link`, `wp_url`    |
| Description  | `description`, `description_stripped`, `summary`, `body` |
| Company      | `company`, `brand`, `employer`                           |

**Inspect all field names:**

```bash
agent-browser eval "
fetch('https://discovered-api.example.com/jobs?page=1&size=1&q=fullstack')
  .then(r => r.json())
  .then(d => { window.__fields = JSON.stringify(Object.keys(d.data ? d.data[0] : d.results ? d.results[0] : d[0])); });
'triggered'
"
agent-browser wait 1500
agent-browser eval "window.__fields"
```

---

## Phase 4 — Write the Scraper

### Pattern: REST API (most SPAs)

```python
# src/scrapers/provider_name.py
from __future__ import annotations
import logging
import requests
from scrapers.base import BaseScraper, Job

logger = logging.getLogger(__name__)

_API_URL = "https://discovered-api.example.com/jobs"

class ProviderNameScraper(BaseScraper):
    """Provider Name job scraper using the REST API discovered via HAR capture."""

    def fetch(self, query: str, max_results: int) -> list[Job]:
        try:
            response = requests.get(
                _API_URL,
                params={"page": 1, "size": max_results, "search": query},
                timeout=15,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            logger.warning("[ProviderNameScraper] fetch failed: %s", exc)
            return []

        jobs: list[Job] = []
        # Adjust key path based on actual response structure
        for item in payload.get("data", [])[:max_results]:
            title = item.get("title", "").strip()
            if not title:
                continue
            jobs.append(
                Job(
                    title=title,
                    company="Provider Name",
                    location=item.get("location", "") or "",
                    description=(item.get("description_stripped", "") or "")[:2000],
                    url=item.get("apply_job_url") or item.get("url") or "",
                    source="provider_name",
                )
            )
        return jobs
```

### Pattern: SSR HTML (when Phase 1 found real job links)

```python
# Use requests + BeautifulSoup only when the page IS server-rendered
import requests
from bs4 import BeautifulSoup

class ProviderNameScraper(BaseScraper):
    def fetch(self, query: str, max_results: int) -> list[Job]:
        try:
            resp = requests.get(f"https://provider.com/jobs?q={query}", timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.select("selector-for-job-card")[:max_results]
            # ... extract fields
        except Exception as exc:
            logger.warning("[ProviderNameScraper] fetch failed: %s", exc)
            return []
```

---

## Phase 5 — Register the Scraper

1. **`src/scrapers/base.py`** — add `"provider_name"` to the `source` comment in `Job` dataclass
2. **`src/main.py`** — import and add to `scraper_pairs`
3. **`requirements.txt`** — add any new dependencies (only add `beautifulsoup4` if using SSR pattern)

---

## Phase 6 — Tests

### Unit test (mocked)

```python
# tests/unit/test_provider_name_scraper.py
from unittest.mock import MagicMock, patch
from scrapers.provider_name import ProviderNameScraper

_FAKE_PAYLOAD = {
    "count": 1,
    "data": [{
        "title": "Fullstack Developer",
        "location": "Remote",
        "apply_job_url": "https://provider.com/jobs/123",
        "description_stripped": "Great role.",
    }],
}

def test_fetch_returns_list():
    with patch("scrapers.provider_name.requests.get") as mock_get:
        resp = MagicMock()
        resp.json.return_value = {"count": 0, "data": []}
        resp.raise_for_status = MagicMock()
        mock_get.return_value = resp
        assert isinstance(ProviderNameScraper().fetch("fullstack", 10), list)

def test_fetch_graceful_failure():
    with patch("scrapers.provider_name.requests.get", side_effect=RuntimeError("down")):
        assert ProviderNameScraper().fetch("fullstack", 10) == []

def test_fetch_maps_fields():
    with patch("scrapers.provider_name.requests.get") as mock_get:
        resp = MagicMock()
        resp.json.return_value = _FAKE_PAYLOAD
        resp.raise_for_status = MagicMock()
        mock_get.return_value = resp
        jobs = ProviderNameScraper().fetch("fullstack", 10)
    assert len(jobs) == 1
    assert jobs[0].source == "provider_name"
    assert jobs[0].company == "Provider Name"
```

### Integration test (live, add to `tests/integration/test_scrapers_integration.py`)

```python
@pytest.mark.integration
def test_provider_name_fetches_jobs():
    scraper = ProviderNameScraper()
    jobs = scraper.fetch(_QUERY, _MAX)
    _assert_valid(jobs, "provider_name")
    assert len(jobs) >= 1
```

Run with: `pytest tests/integration/ -v -m integration -k "provider_name"`

---

## Checklist

- [ ] Phase 1: Opened page and captured snapshot
- [ ] Phase 2: HAR captured and analyzed — API endpoint found
- [ ] Phase 3: API response inspected — all fields mapped
- [ ] Phase 4: Scraper written using discovered API (REST or SSR pattern)
- [ ] Phase 5: Registered in `base.py`, `main.py`, `requirements.txt`
- [ ] Phase 6: Unit tests written (mocked) — all pass
- [ ] Phase 6: Integration test written and passes with ≥1 job
- [ ] Browser session closed: `agent-browser close`

---

## Real Example — Capgemini (discovered 2026-05-25)

The Capgemini job search page (`capgemini.com/careers/.../job-search/`) is a React SPA.
`requests.get` returns 0 job links. HAR capture revealed the real API:

```
GET https://cg-jobstream-api.azurewebsites.net/api/job-search?page=1&size={size}&search={query}
Response: {"count": 97, "data": [{"id":"...", "title":"...", "location":"...", "apply_job_url":"..."}]}
```

Key fields: `title`, `location`, `apply_job_url` (direct apply URL), `description_stripped`.

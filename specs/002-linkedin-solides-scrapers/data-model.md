# Data Model: LinkedIn & Solides Job Scrapers

**Phase 1 output** | **Branch**: `002-linkedin-solides-scrapers` | **Date**: 2026-05-24

---

## Overview

No new entities are introduced by this feature. Both scrapers produce instances of the existing `Job` dataclass defined in `scrapers/base.py`. The only model change is an update to the `source` field comment.

---

## Existing Entity: Job (updated)

**File**: `scrapers/base.py`

```python
@dataclass
class Job:
    title: str
    company: str
    location: str
    description: str
    url: str
    source: str  # "google_jobs" | "indeed" | "himalayas" | "linkedin" | "solides"
    salary: Optional[str] = None
    posted_date: Optional[str] = None
```

**Change**: `source` comment extended with `"linkedin"` and `"solides"` as valid values.

---

## New Files

### `scrapers/linkedin.py` — LinkedInScraper

Implements `BaseScraper`. Uses Playwright + playwright-stealth.

**Class**: `LinkedInScraper`
**Method**: `fetch(query: str, max_results: int) -> list[Job]`
**Internal**: `_async_fetch(query, max_results) -> list[Job]` (called via `asyncio.run`)

**State**: Stateless — no stored credentials, cookies, or session.

**Field defaults when not found:**
- `location`: `"Remote"` if not present
- `description`: `""` (no detail page navigation — avoids additional requests)
- `salary`: `None`
- `posted_date`: ISO date string from `time[datetime]` attribute, or `None`

---

### `scrapers/solides.py` — SolidesScraper

Implements `BaseScraper`. Uses `requests` only (no browser).

**Class**: `SolidesScraper`
**Method**: `fetch(query: str, max_results: int) -> list[Job]`

**State**: Stateless.

**Field mappings:**
| `Job` field | Source |
|-------------|--------|
| `title` | `item["title"]` |
| `company` | `item["companyName"]` |
| `location` | `"Remote"` if `homeOffice=true`; otherwise `"{city.name}, {state.code}"` |
| `description` | `item["description"]` stripped of HTML tags, truncated to 2000 chars |
| `url` | `item["redirectLink"]` |
| `posted_date` | `item["createdAt"]` |
| `salary` | `None` (salary data present but rarely populated; excluded for simplicity) |

---

## State Transitions

None — scrapers are stateless. All output is passed directly into the scoring pipeline via `main.py` without intermediate persistence.

---

## Validation Rules

- `url` MUST be non-empty; jobs with empty URLs are skipped
- `title` MUST be non-empty; jobs with empty titles are skipped
- `source` MUST be the string literal `"linkedin"` or `"solides"` respectively
- `description` truncated at 2000 characters (consistent with existing scrapers)

---

## No New Config

Neither scraper introduces new environment variables. Both are credential-free.

- `LinkedInScraper()` — no constructor args
- `SolidesScraper()` — no constructor args

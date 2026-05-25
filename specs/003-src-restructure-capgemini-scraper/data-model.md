# Data Model: Source Restructure & Capgemini Scraper

**Phase 1 output** | **Branch**: `feature/003-src-restructure-capgemini-scraper` | **Date**: 2026-05-25

---

## Overview

This feature introduces no new domain entities. All scrapers continue to produce instances of the existing `Job` dataclass. The changes are:

1. **File layout**: All Python source files relocate from project root into `src/`; the `Job` dataclass and `BaseScraper` remain in `src/scrapers/base.py` at the same relative path within the package.
2. **Source field extension**: The `source` comment in `src/scrapers/base.py` gains `"capgemini"`.
3. **New scraper**: `src/scrapers/capgemini.py` — a new `CapgeminiScraper` class implementing `BaseScraper`.

---

## Existing Entity: Job (updated comment only)

**File**: `src/scrapers/base.py` (moved from `scrapers/base.py`)

```python
@dataclass
class Job:
    title: str
    company: str
    location: str
    description: str
    url: str
    source: str  # "google_jobs" | "indeed" | "himalayas" | "linkedin" | "solides" | "capgemini"
    salary: Optional[str] = None
    posted_date: Optional[str] = None
```

**Change**: `source` comment extended with `"capgemini"` as a valid value.

---

## New File: `src/scrapers/capgemini.py` — CapgeminiScraper

Implements `BaseScraper`. Uses `requests` + `BeautifulSoup` (html.parser).

**Class**: `CapgeminiScraper`
**Method**: `fetch(query: str, max_results: int) -> list[Job]`

**State**: Stateless — no session, no cookies, no credentials.

**URL composition:**
```python
BASE_URL = "https://www.capgemini.com/careers/join-capgemini/job-search/"
params = {"page": 1, "size": 11, "keyword": query}
```

**BeautifulSoup parsing:**
```python
links = soup.find_all("a", href=lambda h: h and "/jobs/" in h)
```

**Field mappings:**

| `Job` field   | Source |
|---------------|--------|
| `title`       | First non-empty line of `a.get_text(separator="\n", strip=True)` |
| `company`     | `"Capgemini"` (hardcoded — all listings belong to Capgemini) |
| `location`    | Second non-empty line of text split, or `""` if not present |
| `description` | `""` (no detail page — avoids extra requests per constitution §V) |
| `url`         | `"https://www.capgemini.com" + a["href"]` |
| `source`      | `"capgemini"` |
| `salary`      | `None` |
| `posted_date` | `None` |

**Error handling:**
- Any `requests.RequestException` or parsing exception → log warning, return `[]`
- Individual card parse failures → skip card, continue loop

---

## File Migration Map

| Old path (root) | New path |
|-----------------|----------|
| `analyzer.py`   | `src/analyzer.py` |
| `config.py`     | `src/config.py` |
| `main.py`       | `src/main.py` |
| `llm/`          | `src/llm/` |
| `obsidian/`     | `src/obsidian/` |
| `resume/`       | `src/resume/` |
| `scrapers/`     | `src/scrapers/` |

**Files that do NOT move:**
- `tests/` — stays at project root
- `requirements.txt`, `.env`, `.env.example`, `.gitignore` — root config/meta
- `com.douglashennrich.jobfinder.plist`, `install_launchd.sh` — infrastructure scripts
- `squad.config.ts`, `skills-lock.json` — tooling

**New files:**
- `src/scrapers/capgemini.py` — new scraper
- `pytest.ini` — pytest configuration (`pythonpath = src`)

**Updated files:**
- `com.douglashennrich.jobfinder.plist` — `ProgramArguments` path updated to `src/main.py`
- `requirements.txt` — add `beautifulsoup4>=4.12`
- `src/scrapers/base.py` — `source` comment updated
- `src/main.py` — register `CapgeminiScraper`

---

## State Transitions

None — scrapers remain stateless. All output passed directly to the scoring pipeline.

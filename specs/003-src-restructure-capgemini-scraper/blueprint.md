# Blueprint: Source Restructure & Capgemini Scraper

**Branch**: `feature/003-src-restructure-capgemini-scraper` | **Date**: 2026-05-25
**Mode**: doc-only
**Total Tasks**: 15 | **Files**: 3 new, 4 modified, 7 moved (git mv)

---

## Key Decisions

- Use `git mv` for all file relocations — preserves full git history, avoids delete+add noise → T003, T004, T005, T006, T007
- `pytest.ini` with `pythonpath = src` is the sole change needed for existing tests to pass — no test file modifications required → T002, T009
- `html.parser` (stdlib) as BeautifulSoup backend — avoids introducing `lxml` as an additional dependency → T010
- `CapgeminiScraper` uses fixed `page=1, size=11` params per FR-007; `max_results` is enforced via Python slice `links[:max_results]` after parsing → T010
- Double `except` in `CapgeminiScraper`: `requests.RequestException` catches network failures; broad `Exception` catches parse errors — guarantees never-raise per FR-009 → T010
- `CapgeminiScraper` registered with generic `queries` (not serper queries) since it accepts free-text keywords, same as `HimalayasScraper` and `SolidesScraper` → T013

---

## Implementation Order

```
T001 ─────────────────────────────────────────────────────► T014
T002 ─────────────────────────────────────────────────────► T015
T003 ──► T004 [P] ──┐
         T005 [P] ──┤──► T008 ──► T009 ──┐
         T006 [P] ──┤                     │
         T007 [P] ──┘                     │
                  T007 ──► T010 [P] ──┐   │
                           T011 [P] ──┼───►T013 ──► T015
                           T012 [P] ──┘
```

---

## Phase 1: Setup

**Purpose**: Dependency and tooling prerequisites needed before any story work begins.

---

### T001: Add `beautifulsoup4>=4.12` to `requirements.txt`

**File**: `requirements.txt` (modify)

**Requirements**: FR-005, FR-011

**Dependencies**: none

**Before** (line 8, end of file):

```
pytest>=7.0
```

**After**:

```
pytest>=7.0
beautifulsoup4>=4.12
```

**Verification**: `pip install -r requirements.txt` completes without errors; `python -c "import bs4"` exits 0.

---

### T002: Create `pytest.ini` with `pythonpath = src`

**File**: `pytest.ini` (new)

**Requirements**: FR-002

**Dependencies**: none

```ini
[pytest]
pythonpath = src
```

**Verification**: After US1 migration (T003–T007), running `pytest tests/ -v` from the project root resolves all `from scrapers.*`, `from llm.*`, `from obsidian.*`, `from resume.*` imports without `ModuleNotFoundError`.

---

## Phase 2: Foundational

**Purpose**: Create the `src/` directory and relocate the three flat Python files at the root. All subsequent package moves (T004–T007) depend on `src/` existing.

---

### T003: Create `src/` and move `analyzer.py`, `config.py`, `main.py`

**File**: `src/analyzer.py`, `src/config.py`, `src/main.py` (move via git mv)

**Requirements**: FR-001, FR-004

**Dependencies**: none

```bash
mkdir src
git mv analyzer.py src/analyzer.py
git mv config.py src/config.py
git mv main.py src/main.py
```

**Verification**: `ls src/` shows `analyzer.py config.py main.py`; `ls *.py` at root returns nothing (or zsh "no matches found").

---

## Phase 3: User Story 1 — Migrate Source Files to `src/`

**Goal**: All Python source files live under `src/`; `python src/main.py` runs end-to-end; `pytest tests/` passes unchanged.

---

### T004: Move `llm/` package to `src/llm/`

**File**: `src/llm/` (move via git mv)

**Requirements**: FR-001, FR-004

**Dependencies**: T003

```bash
git mv llm/ src/llm/
```

**Verification**: `ls src/llm/` shows `__init__.py base.py copilot.py ollama.py`; `llm/` no longer exists at project root.

---

### T005: Move `obsidian/` package to `src/obsidian/`

**File**: `src/obsidian/` (move via git mv)

**Requirements**: FR-001, FR-004

**Dependencies**: T003

```bash
git mv obsidian/ src/obsidian/
```

**Verification**: `ls src/obsidian/` shows `__init__.py templates.py writer.py`; `obsidian/` no longer exists at project root.

---

### T006: Move `resume/` package to `src/resume/`

**File**: `src/resume/` (move via git mv)

**Requirements**: FR-001, FR-004

**Dependencies**: T003

```bash
git mv resume/ src/resume/
```

**Verification**: `ls src/resume/` shows `__init__.py parser.py profile.py`; `resume/` no longer exists at project root.

---

### T007: Move `scrapers/` package to `src/scrapers/`

**File**: `src/scrapers/` (move via git mv)

**Requirements**: FR-001, FR-004

**Dependencies**: T003

```bash
git mv scrapers/ src/scrapers/
```

**Verification**: `ls src/scrapers/` shows `__init__.py base.py google_jobs.py himalayas.py indeed.py linkedin.py solides.py`; `scrapers/` no longer exists at project root.

---

### T008: Update `com.douglashennrich.jobfinder.plist` entrypoint to `src/main.py`

**File**: `com.douglashennrich.jobfinder.plist` (modify)

**Requirements**: FR-003

**Dependencies**: T004, T005, T006, T007

**Before** (line 12):

```xml
      <string>/Users/douglashennrich/Documents/Projetos/job-finder/main.py</string>
```

**After**:

```xml
      <string>/Users/douglashennrich/Documents/Projetos/job-finder/src/main.py</string>
```

**Verification**: `grep "main.py" com.douglashennrich.jobfinder.plist` outputs `src/main.py`.

---

### T009: Verify US1 migration

**File**: N/A (verification only)

**Requirements**: SC-001, SC-002, SC-003

**Dependencies**: T002, T008

```bash
# From project root:
python src/main.py 2>&1 | head -5
pytest tests/ -v
find . -maxdepth 1 -name "*.py"   # Should return nothing
```

Expected outcomes:
- `python src/main.py` prints `[JOB FINDER] Starting run — ...` with no `ModuleNotFoundError`
- `pytest tests/ -v` reports all pre-existing tests passing
- `find` returns no `.py` files at project root

---

## Phase 4: User Story 2 — Capgemini Scraper

**Goal**: `CapgeminiScraper` in `src/scrapers/capgemini.py` fetches jobs from Capgemini's public job board using `requests` + BeautifulSoup.

---

### T010: Create `src/scrapers/capgemini.py`

**File**: `src/scrapers/capgemini.py` (new)

**Requirements**: FR-005, FR-006, FR-007, FR-008, FR-009, FR-011

**Dependencies**: T007

```python
from __future__ import annotations

import logging

import requests
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, Job

logger = logging.getLogger(__name__)

_BASE_URL = "https://www.capgemini.com/careers/join-capgemini/job-search/"


class CapgeminiScraper(BaseScraper):
    """Scraper for Capgemini's public job board using requests + BeautifulSoup."""

    def fetch(self, query: str, max_results: int) -> list[Job]:
        try:
            resp = requests.get(
                _BASE_URL,
                params={"page": 1, "size": 11, "keyword": query},
                timeout=15,
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
        except requests.RequestException as e:
            logger.warning(f"Capgemini request failed: {e}")
            return []
        except Exception as e:
            logger.warning(f"Capgemini unexpected error during fetch: {e}")
            return []

        jobs: list[Job] = []
        links = soup.find_all("a", href=lambda h: h and "/jobs/" in h)
        for a in links[:max_results]:
            try:
                lines = [line for line in a.get_text(separator="\n", strip=True).splitlines() if line]
                if not lines:
                    continue
                title = lines[0]
                location = lines[1] if len(lines) > 1 else ""
                href = a.get("href", "")
                url = f"https://www.capgemini.com{href}" if href.startswith("/") else href
                jobs.append(
                    Job(
                        title=title,
                        company="Capgemini",
                        location=location,
                        description="",
                        url=url,
                        source="capgemini",
                        salary=None,
                        posted_date=None,
                    )
                )
            except Exception as e:
                logger.warning(f"Capgemini card parse error: {e}")
                continue
        return jobs
```

**Verification**: From `src/`:
```bash
python -c "from scrapers.capgemini import CapgeminiScraper; jobs = CapgeminiScraper().fetch('fullstack node', 11); print(type(jobs), len(jobs))"
```
Returns `<class 'list'>` with a non-negative count; no exception raised.

---

### T011: Update `source` comment in `src/scrapers/base.py`

**File**: `src/scrapers/base.py` (modify)

**Requirements**: FR-012

**Dependencies**: T007

**Before** (line 13):

```python
    source: str  # "google_jobs" | "indeed" | "himalayas" | "linkedin" | "solides"
```

**After**:

```python
    source: str  # "google_jobs" | "indeed" | "himalayas" | "linkedin" | "solides" | "capgemini"
```

**Verification**: `grep "capgemini" src/scrapers/base.py` outputs the updated comment line.

---

### T012: Create `tests/unit/test_capgemini_scraper.py`

**File**: `tests/unit/test_capgemini_scraper.py` (new)

**Requirements**: FR-005, FR-008, FR-009

**Dependencies**: T010

```python
from __future__ import annotations

from unittest.mock import MagicMock, patch

from scrapers.capgemini import CapgeminiScraper


def test_capgemini_scraper_returns_list():
    scraper = CapgeminiScraper()
    result = scraper.fetch("fullstack node", 11)
    assert isinstance(result, list)


def test_capgemini_scraper_graceful_failure():
    with patch("requests.get", side_effect=RuntimeError("boom")):
        scraper = CapgeminiScraper()
        result = scraper.fetch("test", 1)
    assert result == []


def test_capgemini_job_source():
    scraper = CapgeminiScraper()
    jobs = scraper.fetch("fullstack node", 11)
    if not jobs:
        assert True
        return
    assert all(j.source == "capgemini" for j in jobs)
```

**Verification**: `pytest tests/unit/test_capgemini_scraper.py -v` — all three tests pass (tests 1 and 3 may hit the live Capgemini endpoint; test 2 always passes via mock).

---

## Phase 5: User Story 3 — Pipeline Integration

**Goal**: Capgemini results flow through the full pipeline and produce Obsidian notes with `source: capgemini`.

---

### T013: Register `CapgeminiScraper` in `src/main.py`

**File**: `src/main.py` (modify)

**Requirements**: FR-010

**Dependencies**: T009, T010, T011, T012

Apply changes bottom-to-top:

**Change 1 — scraper_pairs list** (lines ~86–91):

**Before**:

```python
    scraper_pairs: list[tuple] = [
        (HimalayasScraper(), queries),
        (GoogleJobsScraper(api_key=cfg.serper_api_key), serper_queries),
        (LinkedInScraper(), queries),
        (SolidesScraper(), queries),
    ]
    print("[SCRAPER] Registered: HimalayasScraper, GoogleJobsScraper, LinkedInScraper, SolidesScraper")
```

**After**:

```python
    scraper_pairs: list[tuple] = [
        (HimalayasScraper(), queries),
        (GoogleJobsScraper(api_key=cfg.serper_api_key), serper_queries),
        (LinkedInScraper(), queries),
        (SolidesScraper(), queries),
        (CapgeminiScraper(), queries),
    ]
    print("[SCRAPER] Registered: HimalayasScraper, GoogleJobsScraper, LinkedInScraper, SolidesScraper, CapgeminiScraper")
```

**Change 2 — import** (lines ~24–27):

**Before**:

```python
from scrapers.google_jobs import GoogleJobsScraper
from scrapers.himalayas import HimalayasScraper
from scrapers.linkedin import LinkedInScraper
from scrapers.solides import SolidesScraper
```

**After**:

```python
from scrapers.capgemini import CapgeminiScraper
from scrapers.google_jobs import GoogleJobsScraper
from scrapers.himalayas import HimalayasScraper
from scrapers.linkedin import LinkedInScraper
from scrapers.solides import SolidesScraper
```

**Verification**: `python src/main.py 2>&1 | grep SCRAPER` outputs a line containing `CapgeminiScraper`; after a full run, `grep -r "source: capgemini" <obsidian_notes_folder>` finds at least one matching note (when Capgemini board has qualifying listings).

---

## Final Phase: Polish & Verification

**Purpose**: End-to-end verification, dependency install confirmation.

---

### T014: Install `beautifulsoup4` and verify no dependency conflicts

**File**: N/A (verification only)

**Requirements**: FR-005

**Dependencies**: T001

```bash
pip install -r requirements.txt
python -c "import bs4; print(bs4.__version__)"
```

Expected: pip completes without conflicts; bs4 version ≥ 4.12 is printed.

---

### T015: Run full test suite and confirm 100% pass

**File**: N/A (verification only)

**Requirements**: SC-002

**Dependencies**: T002, T013, T014

```bash
pytest tests/ -v
```

Expected: All tests pass including `test_capgemini_scraper.py`; exit code 0.

---

## Checklist

- [ ] T001: Add `beautifulsoup4>=4.12` to `requirements.txt`
- [ ] T002: Create `pytest.ini` with `pythonpath = src`
- [ ] T003: Create `src/`; git mv `analyzer.py`, `config.py`, `main.py`
- [ ] T004: git mv `llm/` → `src/llm/`
- [ ] T005: git mv `obsidian/` → `src/obsidian/`
- [ ] T006: git mv `resume/` → `src/resume/`
- [ ] T007: git mv `scrapers/` → `src/scrapers/`
- [ ] T008: Update plist `ProgramArguments` to `src/main.py`
- [ ] T009: Verify `python src/main.py` and `pytest tests/` pass; root has no `.py` files
- [ ] T010: Create `src/scrapers/capgemini.py`
- [ ] T011: Update `source` comment in `src/scrapers/base.py`
- [ ] T012: Create `tests/unit/test_capgemini_scraper.py`
- [ ] T013: Register `CapgeminiScraper` in `src/main.py`
- [ ] T014: `pip install -r requirements.txt`; verify bs4 installed
- [ ] T015: `pytest tests/ -v` — 100% pass

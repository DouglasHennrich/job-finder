# Blueprint: Job Finder Automation

**Branch**: `001-job-finder` | **Date**: 2026-05-24
**Mode**: scaffold
**Total Tasks**: 39 | **Files**: 22 new, 0 modified, 0 deleted

## Key Decisions

- PDF text extraction uses `pdfplumber` (pure Python, multi-page, text-layer) → T011
- Both LLM providers use the `openai` SDK — Ollama exposes an OpenAI-compatible endpoint → T015, T016
- Deduplication is slug-based file existence: `slugify(title + company)` → `{slug}.md` → T029, T032, T033
- `COPILOT_TOKEN` auto-detected via `gh auth token` subprocess when env var is unset → T007
- Tier labels are derived from score after LLM response is parsed (authoritative override) → T017
- LLM JSON parse has a three-stage fallback: `json.loads` → regex `\{.*\}` → sentinel object → T017
- Serper.dev is the primary Google Jobs source; Playwright is the fallback when key is empty → T022
- Index.md is fully regenerated each run from all existing vault notes → T028, T035
- `OBSIDIAN_VAULT_PATH` must exist on disk; missing → `ValueError` at startup → T007
- launchd scheduling is the last phase, only after full pipeline manual validation → T037, T038

## Implementation Order

```
T001-T006 (Setup — sequential)
    └── T007-T008 (Config — foundational, sequential)
            ├── T009 T010 T011 T012  (US1: Resume)
            ├── T013 T014 T015 T016  (US3: LLM — T014/T015/T016 parallel)
            │       └── T017 T018   (US3: Analyzer)
            ├── T019 T020            (US2: Scrapers base)
            │       └── T021 T022 T023  (US2: Scrapers — parallel)
            │               └── T024 T025 T026  (US2: smoke tests)
            └── T027 T028 T029       (US4: Obsidian — T028/T029 parallel)
                    └── T030 T031
                            └── T032 T033 T034  (US5: Dedup)
                                        └── T035 T036  (Integration: main.py)
                                                    └── T037 T038 T039  (launchd)
```

---

## Phase 1: Setup (Shared Infrastructure)

### T001: Create project directory structure

**File**: multiple directories (new)

**Requirements**: Setup prerequisite for all other tasks

**Dependencies**: none

```bash
mkdir -p resume scrapers llm obsidian logs tests/unit
```

**Verification**: `ls` shows all six directories at project root.

---

### T002: Create `requirements.txt`

**File**: `requirements.txt` (new)

**Requirements**: Pinned deps for reproducible installs

**Dependencies**: T001

```text
pdfplumber==0.11.4
playwright==1.44.0
playwright-stealth==1.0.6
openai==1.30.1
requests==2.32.3
python-dotenv==1.0.1
python-slugify==8.0.4
pytest>=7.0
```

**Verification**: `cat requirements.txt` shows 8 lines with pinned versions.

---

### T003: Create `.env.example`

**File**: `.env.example` (new)

**Requirements**: All env vars documented with defaults and descriptions

**Dependencies**: T001

```bash
# LLM Configuration
# Which backend to use: "copilot" (GitHub Models) or "ollama" (local)
LLM_PROVIDER=copilot

# GitHub Models token — leave empty to auto-detect via `gh auth token`
COPILOT_TOKEN=

# Model name on GitHub Models endpoint
COPILOT_MODEL=claude-sonnet-4-6

# Ollama endpoint (OpenAI-compatible)
OLLAMA_BASE_URL=http://localhost:11434/v1

# Ollama model name
OLLAMA_MODEL=llama3

# Serper.dev API key for Google Jobs — empty = use Playwright fallback
SERPER_API_KEY=your-serper-api-key-here

# Absolute path to your Obsidian vault root (REQUIRED)
OBSIDIAN_VAULT_PATH=/path/to/your/obsidian/vault

# Subfolder inside vault where job notes are stored
JOB_FINDER_FOLDER=Job Finder

# Minimum fit score (0-100) to save a job note
MIN_SCORE=60

# Maximum job listings fetched per scraper per search query
MAX_JOBS_PER_SOURCE=20
```

**Verification**: File contains all 10 variable names from the env contract.

---

### T004: Install Python dependencies

**File**: none (shell command)

**Requirements**: All packages from requirements.txt installed in active Python env

**Dependencies**: T002

```bash
pip install -r requirements.txt
```

**Verification**: `pip show pdfplumber openai playwright` shows installed versions.

---

### T005: Install Playwright Chromium browser

**File**: none (shell command)

**Requirements**: Chromium binary available for Playwright

**Dependencies**: T004

```bash
playwright install chromium
```

**Verification**: `playwright install --dry-run chromium` exits 0 with "already installed".

---

### T006: Copy `.env.example` to `.env` and fill required values

**File**: `.env` (created from template — git-ignored)

**Requirements**: `OBSIDIAN_VAULT_PATH` and `SERPER_API_KEY` filled with real values

**Dependencies**: T003

```bash
cp .env.example .env
# Then edit .env: set OBSIDIAN_VAULT_PATH and optionally SERPER_API_KEY
```

**Verification**: `python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('OBSIDIAN_VAULT_PATH'))"` prints a non-empty path.

---

## Phase 2: Foundational (Blocking Prerequisites)

### T007: Create `config.py`

**File**: `config.py` (new)

**Requirements**: Config dataclass loading all env vars, auto-detecting token, validating vault path and provider

**Dependencies**: T006

```python
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class Config:
    llm_provider: str
    copilot_token: str
    copilot_model: str
    ollama_base_url: str
    ollama_model: str
    serper_api_key: str
    obsidian_vault_path: str
    job_finder_folder: str
    obsidian_job_folder: str
    min_score: int
    max_jobs_per_source: int

    @classmethod
    def load(cls) -> "Config":
        load_dotenv()

        llm_provider = os.getenv("LLM_PROVIDER", "copilot")

        copilot_token = os.getenv("COPILOT_TOKEN", "")
        if not copilot_token:
            result = subprocess.run(
                ["gh", "auth", "token"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                copilot_token = result.stdout.strip()

        copilot_model = os.getenv("COPILOT_MODEL", "claude-sonnet-4-6")
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3")
        serper_api_key = os.getenv("SERPER_API_KEY", "")

        obsidian_vault_path = os.getenv("OBSIDIAN_VAULT_PATH", "")
        job_finder_folder = os.getenv("JOB_FINDER_FOLDER", "Job Finder")
        min_score = int(os.getenv("MIN_SCORE", "60"))
        max_jobs_per_source = int(os.getenv("MAX_JOBS_PER_SOURCE", "20"))

        if not obsidian_vault_path or not os.path.exists(obsidian_vault_path):
            raise ValueError(
                f"[ERROR] Obsidian vault not found: {obsidian_vault_path}"
                " — set OBSIDIAN_VAULT_PATH correctly"
            )

        if llm_provider not in ("copilot", "ollama"):
            raise ValueError(
                f'[ERROR] LLM_PROVIDER must be "copilot" or "ollama",'
                f' got: "{llm_provider}"'
            )

        if llm_provider == "copilot" and not copilot_token:
            raise RuntimeError(
                '[ERROR] Could not resolve COPILOT_TOKEN.'
                ' Run "gh auth login" or set COPILOT_TOKEN in .env'
            )

        obsidian_job_folder = os.path.join(obsidian_vault_path, job_finder_folder)

        return cls(
            llm_provider=llm_provider,
            copilot_token=copilot_token,
            copilot_model=copilot_model,
            ollama_base_url=ollama_base_url,
            ollama_model=ollama_model,
            serper_api_key=serper_api_key,
            obsidian_vault_path=obsidian_vault_path,
            job_finder_folder=job_finder_folder,
            obsidian_job_folder=obsidian_job_folder,
            min_score=min_score,
            max_jobs_per_source=max_jobs_per_source,
        )
```

**Verification**: Smoke test T008 passes.

---

### T008: Smoke test `config.py`

**File**: none (shell command)

**Requirements**: Config loads without error; prints provider and job folder path

**Dependencies**: T007

```bash
python -c "from config import Config; cfg = Config.load(); print('OK:', cfg.llm_provider, cfg.obsidian_job_folder)"
```

**Verification**: Output begins with `OK: copilot` (or `ollama`) followed by a filesystem path.

---

## Phase 3: User Story 1 — Resume Profile Extraction

### T009: Create `resume/__init__.py`

**File**: `resume/__init__.py` (new)

**Requirements**: Package marker for resume module

**Dependencies**: T001

```python
```

**Verification**: `python -c "import resume"` exits 0 without error.

---

### T010: Create `resume/profile.py`

**File**: `resume/profile.py` (new)

**Requirements**: Immutable Profile dataclass holding raw resume text and source path

**Dependencies**: T009

```python
from dataclasses import dataclass


@dataclass
class Profile:
    raw_text: str  # full text from all PDF pages joined with "\n\n"
    pdf_path: str  # absolute path to the source PDF
```

**Verification**: `python -c "from resume.profile import Profile; p = Profile('text', 'path'); print(p)"` prints without error.

---

### T011: Create `resume/parser.py`

**File**: `resume/parser.py` (new)

**Requirements**: parse_pdf extracts multi-page text, raises FileNotFoundError if missing, raises ValueError if empty

**Dependencies**: T010

```python
import os

import pdfplumber

from resume.profile import Profile


def parse_pdf(pdf_path: str) -> Profile:
    """Extract text from all pages of a PDF résumé.

    Raises:
        FileNotFoundError: if the file does not exist at pdf_path.
        ValueError: if the extracted text is empty (e.g. image-only PDF).
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(
            f"[ERROR] PDF not found: {pdf_path}"
            " — check the file exists and the path is correct"
        )

    pages_text: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            pages_text.append(page.extract_text() or "")

    raw_text = "\n\n".join(pages_text).strip()

    if not raw_text:
        raise ValueError(
            "[ERROR] PDF produced no extractable text."
            " The file may be image-only (scanned). Use a text-layer PDF."
        )

    return Profile(raw_text=raw_text, pdf_path=os.path.abspath(pdf_path))
```

**Verification**: Smoke test T012 passes.

---

### T012: Smoke test `resume/parser.py`

**File**: none (shell command)

**Requirements**: parse_pdf successfully extracts >0 chars from the résumé PDF

**Dependencies**: T011

```bash
python -c "from resume.parser import parse_pdf; p = parse_pdf('Douglas Hennrich.pdf'); print(p.raw_text[:300])"
```

**Verification**: Output shows readable text content from the résumé (not empty, not an error).

---

## Phase 4: User Story 3 — AI-Powered Job Fit Scoring

### T013: Create `llm/__init__.py`

**File**: `llm/__init__.py` (new)

**Requirements**: build_llm factory function; returns OllamaLLM or CopilotLLM based on config; raises RuntimeError if copilot token is empty

**Dependencies**: T014, T015, T016

```python
from config import Config
from llm.base import BaseLLM
from llm.copilot import CopilotLLM
from llm.ollama import OllamaLLM


def build_llm(config: Config) -> BaseLLM:
    """Instantiate the configured LLM provider.

    Raises:
        RuntimeError: if provider is copilot and token is empty.
    """
    if config.llm_provider == "ollama":
        return OllamaLLM(base_url=config.ollama_base_url, model=config.ollama_model)

    if not config.copilot_token:
        raise RuntimeError(
            '[ERROR] Could not resolve COPILOT_TOKEN.'
            ' Run "gh auth login" or set COPILOT_TOKEN in .env'
        )
    return CopilotLLM(token=config.copilot_token, model=config.copilot_model)
```

**Verification**: `python -c "from llm import build_llm"` exits 0 without import error.

---

### T014: Create `llm/base.py`

**File**: `llm/base.py` (new)

**Requirements**: BaseLLM ABC with abstract chat(system, user) -> str method

**Dependencies**: T001

```python
from abc import ABC, abstractmethod


class BaseLLM(ABC):
    """Abstract base class for LLM provider implementations."""

    @abstractmethod
    def chat(self, system: str, user: str) -> str:
        """Send a system+user prompt and return the text response."""
```

**Verification**: `python -c "from llm.base import BaseLLM"` exits 0.

---

### T015: Create `llm/ollama.py`

**File**: `llm/ollama.py` (new)

**Requirements**: OllamaLLM using openai SDK against Ollama's OpenAI-compatible endpoint; temperature=0.2

**Dependencies**: T014

```python
import openai

from llm.base import BaseLLM


class OllamaLLM(BaseLLM):
    """LLM provider backed by a local Ollama instance."""

    def __init__(self, base_url: str, model: str) -> None:
        self.model = model
        self.client = openai.OpenAI(base_url=base_url, api_key="ollama")

    def chat(self, system: str, user: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content
```

**Verification**: `python -c "from llm.ollama import OllamaLLM"` exits 0.

---

### T016: Create `llm/copilot.py`

**File**: `llm/copilot.py` (new)

**Requirements**: CopilotLLM using openai SDK against GitHub Models endpoint; temperature=0.2

**Dependencies**: T014

```python
import openai

from llm.base import BaseLLM

_GITHUB_MODELS_BASE_URL = "https://models.inference.ai.azure.com"


class CopilotLLM(BaseLLM):
    """LLM provider backed by GitHub Models (claude-sonnet-4-6 or similar)."""

    def __init__(self, token: str, model: str) -> None:
        self.model = model
        self.client = openai.OpenAI(
            base_url=_GITHUB_MODELS_BASE_URL,
            api_key=token,
        )

    def chat(self, system: str, user: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content
```

**Verification**: `python -c "from llm.copilot import CopilotLLM"` exits 0.

---

### T017: Create `analyzer.py`

**File**: `analyzer.py` (new)

**Requirements**: JobAnalysis dataclass + analyze() function; three-stage JSON parse fallback; tier derived from score after parse; justification in pt-BR

**Dependencies**: T013, T010, T020

```python
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from llm.base import BaseLLM
from resume.profile import Profile
from scrapers.base import Job

_SYSTEM_PROMPT = (
    "You are an expert technical recruiter. Given a resume and a job description, "
    "evaluate the candidate's fit for the position. "
    "Respond ONLY with a valid JSON object containing these exact fields: "
    '"score" (integer 0-100), '
    '"tier" (string), '
    '"justification" (string in Brazilian Portuguese, 2-3 sentences), '
    '"matching_skills" (array of strings), '
    '"missing_skills" (array of strings). '
    "No markdown, no extra text outside the JSON object."
)


@dataclass
class JobAnalysis:
    score: int
    tier: str
    justification: str
    matching_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)


def _derive_tier(score: int) -> str:
    if score >= 80:
        return "🔥 Must Apply"
    if score >= 60:
        return "✅ Good Fit"
    if score >= 40:
        return "🤔 Maybe"
    return "❌ Skip"


def analyze(job: Job, profile: Profile, llm: BaseLLM) -> JobAnalysis:
    """Score a job against the candidate's profile using the given LLM.

    Returns a sentinel JobAnalysis with score=0 if the LLM response cannot be parsed.
    Never raises — parse failures degrade gracefully.
    """
    user_prompt = (
        f"Resume:\n{profile.raw_text}\n\n"
        f"Job Title: {job.title}\n"
        f"Company: {job.company}\n"
        f"Location: {job.location}\n"
        f"Description:\n{job.description}"
    )

    raw_response = llm.chat(system=_SYSTEM_PROMPT, user=user_prompt)

    # Stage 1: direct JSON parse
    data: dict | None = None
    try:
        data = json.loads(raw_response)
    except json.JSONDecodeError:
        pass

    # Stage 2: regex extraction of first {...} block
    if data is None:
        match = re.search(r"\{.*\}", raw_response, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
            except json.JSONDecodeError:
                pass

    # Stage 3: sentinel fallback
    if data is None:
        return JobAnalysis(
            score=0,
            tier="❌ Skip",
            justification="[parse error]",
            matching_skills=[],
            missing_skills=[],
        )

    score = max(0, min(100, int(data.get("score", 0))))
    tier = _derive_tier(score)  # authoritative override from score

    return JobAnalysis(
        score=score,
        tier=tier,
        justification=data.get("justification", ""),
        matching_skills=data.get("matching_skills", []),
        missing_skills=data.get("missing_skills", []),
    )
```

**Verification**: Smoke test T018 passes; score is between 0–100, tier matches score bracket.

---

### T018: Smoke test analyzer with hardcoded NestJS job sample

**File**: none (shell command)

**Requirements**: analyze() returns valid score and Portuguese justification for a sample job

**Dependencies**: T017, T012

```bash
python -c "
from config import Config
from llm import build_llm
from resume.parser import parse_pdf
from scrapers.base import Job
from analyzer import analyze

cfg = Config.load()
llm = build_llm(cfg)
profile = parse_pdf('Douglas Hennrich.pdf')
job = Job(
    title='Senior NestJS Developer',
    company='Acme',
    location='Remote LATAM',
    description='5+ years Node.js NestJS TypeScript PostgreSQL Redis. Remote LATAM.',
    url='https://example.com',
    source='test',
)
result = analyze(job, profile, llm)
print(f'Score: {result.score} | Tier: {result.tier}')
print(f'Justification: {result.justification}')
"
```

**Verification**: Prints `Score: N | Tier: ...` where N is 0–100, followed by a non-empty Portuguese sentence.

---

## Phase 5: User Story 2 — Multi-Source Job Discovery

### T019: Create `scrapers/__init__.py`

**File**: `scrapers/__init__.py` (new)

**Requirements**: Package marker for scrapers module

**Dependencies**: T001

```python
```

**Verification**: `python -c "import scrapers"` exits 0.

---

### T020: Create `scrapers/base.py`

**File**: `scrapers/base.py` (new)

**Requirements**: Job dataclass with all fields including optional salary and posted_date; BaseScraper ABC with abstract fetch()

**Dependencies**: T019

```python
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class Job:
    title: str
    company: str
    location: str
    description: str
    url: str
    source: str  # "google_jobs" | "indeed" | "himalayas"
    salary: Optional[str] = None
    posted_date: Optional[str] = None


class BaseScraper(ABC):
    """Base class for all job source scrapers."""

    @abstractmethod
    def fetch(self, query: str, max_results: int) -> list[Job]:
        """Fetch job listings for the given query.

        Must never raise — callers expect an empty list on failure.
        """
```

**Verification**: `python -c "from scrapers.base import Job, BaseScraper"` exits 0.

---

### T021: Create `scrapers/himalayas.py`

**File**: `scrapers/himalayas.py` (new)

**Requirements**: HimalayasScraper using Himalayas REST API; remote-only filter; graceful error handling

**Dependencies**: T020

```python
from __future__ import annotations

import logging

import requests

from scrapers.base import BaseScraper, Job

logger = logging.getLogger(__name__)

_BASE_URL = "https://himalayas.app/jobs/api"


class HimalayasScraper(BaseScraper):
    """Scraper for Himalayas.app public REST API."""

    def fetch(self, query: str, max_results: int) -> list[Job]:
        try:
            resp = requests.get(
                _BASE_URL,
                params={"q": query, "limit": max_results},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            logger.warning("[SCRAPER] ERROR: himalayas — %s", exc)
            return []

        jobs: list[Job] = []
        for item in data.get("jobs", []):
            if not item.get("remote"):
                continue
            company_obj = item.get("company") or {}
            restrictions = item.get("locationRestrictions") or []
            location = ", ".join(restrictions) if restrictions else "Remote"
            description = (item.get("description") or "")[:2000]
            jobs.append(
                Job(
                    title=item.get("title", ""),
                    company=company_obj.get("name", ""),
                    location=location,
                    description=description,
                    url=item.get("applicationLink", ""),
                    source="himalayas",
                    salary=item.get("salary"),
                    posted_date=item.get("postedAt"),
                )
            )
        return jobs
```

**Verification**: Smoke test T024 returns ≥1 job with non-empty title and company.

---

### T022: Create `scrapers/google_jobs.py`

**File**: `scrapers/google_jobs.py` (new)

**Requirements**: Serper.dev primary path; Playwright async fallback when key is empty or Serper raises; stealth + random delays

**Dependencies**: T020

```python
from __future__ import annotations

import asyncio
import logging
import random
import urllib.parse

import requests

from scrapers.base import BaseScraper, Job

logger = logging.getLogger(__name__)

_SERPER_URL = "https://google.serper.dev/jobs"


class GoogleJobsScraper(BaseScraper):
    """Scraper for Google Jobs via Serper.dev (primary) or Playwright (fallback)."""

    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key

    def fetch(self, query: str, max_results: int) -> list[Job]:
        if self.api_key:
            try:
                return self._fetch_serper(query, max_results)
            except Exception as exc:
                logger.warning(
                    "[SCRAPER] google_jobs Serper failed (%s), falling back to Playwright",
                    exc,
                )
        return asyncio.get_event_loop().run_until_complete(
            self._fetch_playwright(query, max_results)
        )

    def _fetch_serper(self, query: str, max_results: int) -> list[Job]:
        resp = requests.post(
            _SERPER_URL,
            json={"q": query, "gl": "br", "hl": "pt-br", "num": max_results},
            headers={"X-API-KEY": self.api_key},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        jobs: list[Job] = []
        for item in data.get("jobs", []):
            jobs.append(
                Job(
                    title=item.get("title", ""),
                    company=item.get("company", ""),
                    location=item.get("location", ""),
                    description=(item.get("description") or "")[:2000],
                    url=item.get("link", ""),
                    source="google_jobs",
                    posted_date=item.get("date"),
                )
            )
        return jobs

    async def _fetch_playwright(self, query: str, max_results: int) -> list[Job]:
        from playwright.async_api import async_playwright
        from playwright_stealth import stealth_async

        jobs: list[Job] = []
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.google.com/search?q={encoded_query}&ibp=htl;jobs"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await stealth_async(page)
            await page.goto(url, wait_until="networkidle")
            await asyncio.sleep(random.uniform(2, 4))

            cards = await page.query_selector_all("div[data-jiz]")
            for card in cards[:max_results]:
                try:
                    title_el = await card.query_selector("h2")
                    title = await title_el.inner_text() if title_el else ""
                    company_el = await card.query_selector("[class*='company']")
                    company = await company_el.inner_text() if company_el else ""
                    link_el = await card.query_selector("a")
                    link = await link_el.get_attribute("href") if link_el else ""
                    if title:
                        jobs.append(
                            Job(
                                title=title.strip(),
                                company=company.strip(),
                                location="Remote",
                                description="",
                                url=link or "",
                                source="google_jobs",
                            )
                        )
                except Exception:
                    continue

            await browser.close()
        return jobs
```

**Verification**: Smoke test T025 with SERPER_API_KEY set returns ≥1 job.

---

### T023: Create `scrapers/indeed.py`

**File**: `scrapers/indeed.py` (new)

**Requirements**: IndeedScraper with Playwright stealth, humanisation (random delays + mouse move + incremental scroll), fetches full description from detail pages; never raises

**Dependencies**: T020

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


class IndeedScraper(BaseScraper):
    """Playwright-based scraper for Indeed with humanisation and stealth."""

    def fetch(self, query: str, max_results: int) -> list[Job]:
        try:
            return asyncio.get_event_loop().run_until_complete(
                self._async_fetch(query, max_results)
            )
        except Exception as exc:
            logger.warning("[SCRAPER] ERROR: indeed — %s", exc)
            return []

    async def _async_fetch(self, query: str, max_results: int) -> list[Job]:
        from playwright.async_api import async_playwright
        from playwright_stealth import stealth_async

        jobs: list[Job] = []
        encoded_query = urllib.parse.quote(query)
        url = (
            f"https://www.indeed.com/jobs?q={encoded_query}&remotejobs=1&sort=date"
        )

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=_USER_AGENT)
            page = await context.new_page()
            await stealth_async(page)

            await page.goto(url, wait_until="networkidle")
            await asyncio.sleep(random.uniform(1.5, 3.5))
            await page.mouse.move(
                random.randint(200, 800), random.randint(200, 600)
            )

            # Incremental scroll to trigger lazy-loaded cards
            for _ in range(3):
                await page.evaluate("window.scrollBy(0, 400)")
                await asyncio.sleep(random.uniform(0.5, 1.5))

            cards = await page.query_selector_all(".job_seen_beacon")
            for card in cards[:max_results]:
                try:
                    title_el = await card.query_selector(".jobTitle")
                    company_el = await card.query_selector(".companyName")
                    location_el = await card.query_selector(".companyLocation")
                    link_el = await card.query_selector("a.jcs-JobTitle")

                    title = await title_el.inner_text() if title_el else ""
                    company = await company_el.inner_text() if company_el else ""
                    location = await location_el.inner_text() if location_el else ""
                    href = await link_el.get_attribute("href") if link_el else ""

                    description = ""
                    if href:
                        full_url = (
                            f"https://www.indeed.com{href}"
                            if href.startswith("/")
                            else href
                        )
                        detail = await context.new_page()
                        await stealth_async(detail)
                        try:
                            await detail.goto(
                                full_url,
                                wait_until="domcontentloaded",
                                timeout=10_000,
                            )
                            await asyncio.sleep(random.uniform(1, 2))
                            desc_el = await detail.query_selector(
                                "#jobDescriptionText"
                            )
                            if desc_el:
                                description = (await desc_el.inner_text())[:2000]
                        except Exception:
                            pass
                        finally:
                            await detail.close()

                    if title and company:
                        job_url = (
                            f"https://www.indeed.com{href}"
                            if href.startswith("/")
                            else href
                        )
                        jobs.append(
                            Job(
                                title=title.strip(),
                                company=company.strip(),
                                location=location.strip(),
                                description=description,
                                url=job_url,
                                source="indeed",
                            )
                        )
                except Exception:
                    continue

            await browser.close()
        return jobs
```

**Verification**: Smoke test T026 returns ≥1 job with non-empty title (browser opens, manual verification).

---

### T024: Smoke test Himalayas scraper

**File**: none (shell command)

**Requirements**: HimalayasScraper.fetch() returns ≥1 job with title and company

**Dependencies**: T021

```bash
python -c "
from scrapers.himalayas import HimalayasScraper
jobs = HimalayasScraper().fetch('nodejs nestjs react', 5)
[print(j.title, '|', j.company) for j in jobs]
"
```

**Verification**: Output shows at least one `title | company` line.

---

### T025: Smoke test Google Jobs scraper

**File**: none (shell command)

**Requirements**: GoogleJobsScraper returns ≥1 job when SERPER_API_KEY is set

**Dependencies**: T022

```bash
python -c "
from config import Config
from scrapers.google_jobs import GoogleJobsScraper
cfg = Config.load()
jobs = GoogleJobsScraper(api_key=cfg.serper_api_key).fetch('senior nodejs remote', 5)
[print(j.title, '|', j.company) for j in jobs]
"
```

**Verification**: Output shows at least one `title | company` line (requires SERPER_API_KEY set in .env).

---

### T026: Smoke test Indeed scraper

**File**: none (shell command)

**Requirements**: IndeedScraper.fetch() returns ≥1 job (browser opens, manual verification)

**Dependencies**: T023

```bash
python -c "
from scrapers.indeed import IndeedScraper
jobs = IndeedScraper().fetch('senior fullstack nodejs', 3)
[print(j.title) for j in jobs]
"
```

**Verification**: Output shows at least one job title; no unhandled exceptions.

---

## Phase 6: User Story 4 — Obsidian Vault Note Creation

### T027: Create `obsidian/__init__.py`

**File**: `obsidian/__init__.py` (new)

**Requirements**: Package marker for obsidian module

**Dependencies**: T001

```python
```

**Verification**: `python -c "import obsidian"` exits 0.

---

### T028: Create `obsidian/templates.py`

**File**: `obsidian/templates.py` (new)

**Requirements**: render_job_note() generates full Markdown with YAML frontmatter; render_index() generates Index.md with tier sections sorted by score descending; ❌ tier not shown in index

**Dependencies**: T027, T017, T020

```python
from __future__ import annotations

from datetime import datetime

from analyzer import JobAnalysis
from scrapers.base import Job


def render_job_note(job: Job, analysis: JobAnalysis, date_str: str) -> str:
    """Render a complete Markdown note for a job with YAML frontmatter."""
    matching = ", ".join(analysis.matching_skills) if analysis.matching_skills else "N/A"
    missing = ", ".join(analysis.missing_skills) if analysis.missing_skills else "N/A"

    return (
        f"---\n"
        f"score: {analysis.score}\n"
        f'tier: "{analysis.tier}"\n'
        f"company: {job.company}\n"
        f"source: {job.source}\n"
        f"date_found: {date_str}\n"
        f"status: new\n"
        f"---\n"
        f"\n"
        f"# {job.title} — {job.company}\n"
        f"\n"
        f"{analysis.tier} **Score: {analysis.score}/100**\n"
        f"\n"
        f"> {analysis.justification}\n"
        f"\n"
        f"## Skills\n"
        f"- ✅ **Match:** {matching}\n"
        f"- ❌ **Gap:** {missing}\n"
        f"\n"
        f"## Details\n"
        f"| Field | Value |\n"
        f"|-------|-------|\n"
        f"| Company | {job.company} |\n"
        f"| Location | {job.location} |\n"
        f"| Source | {job.source} |\n"
        f"| Found | {date_str} |\n"
        f"| Apply | [{job.url}]({job.url}) |\n"
        f"\n"
        f"## Job Description\n"
        f"{job.description}\n"
    )


def render_index(jobs_data: list[dict]) -> str:
    """Render Index.md with all saved jobs grouped by tier, sorted by score."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    tier_order = ["🔥 Must Apply", "✅ Good Fit", "🤔 Maybe"]
    tiers: dict[str, list[dict]] = {t: [] for t in tier_order}

    for job in jobs_data:
        tier = job.get("tier", "")
        if tier in tiers:
            tiers[tier].append(job)

    for tier_list in tiers.values():
        tier_list.sort(key=lambda j: int(j.get("score", 0)), reverse=True)

    total = sum(len(v) for v in tiers.values())

    lines = [
        "# Job Finder — Index",
        "",
        f"**Last updated**: {now} | **Total saved jobs**: {total}",
        "",
    ]

    for tier_name in tier_order:
        tier_jobs = tiers[tier_name]
        if not tier_jobs:
            continue
        lines += [
            f"## {tier_name}",
            "",
            "| Score | Title | Company | Source | Date |",
            "|-------|-------|---------|--------|------|",
        ]
        for job in tier_jobs:
            slug = job.get("slug", "")
            title_link = f"[[{slug}]]" if slug else job.get("title", "")
            lines.append(
                f"| {job.get('score', '')} | {title_link}"
                f" | {job.get('company', '')}"
                f" | {job.get('source', '')}"
                f" | {job.get('date_found', '')} |"
            )
        lines.append("")

    return "\n".join(lines)
```

**Verification**: `python -c "from obsidian.templates import render_job_note, render_index"` exits 0.

---

### T029: Create `obsidian/writer.py`

**File**: `obsidian/writer.py` (new)

**Requirements**: slugify_job, note_exists, save_note, update_index, load_existing_jobs; YAML frontmatter parsed with regex (no external YAML lib)

**Dependencies**: T027

```python
from __future__ import annotations

import glob
import os
import re

from slugify import slugify as _slugify


def slugify_job(title: str, company: str) -> str:
    """Generate a deterministic filesystem-safe slug from job title and company."""
    return _slugify(f"{title} {company}")


def note_exists(slug: str, job_folder: str) -> bool:
    """Return True if a note file for this slug already exists in the vault."""
    return os.path.exists(os.path.join(job_folder, f"{slug}.md"))


def save_note(slug: str, content: str, job_folder: str) -> str:
    """Write the note content to {job_folder}/{slug}.md, creating dirs as needed.

    Returns the absolute path of the written file.
    """
    os.makedirs(job_folder, exist_ok=True)
    path = os.path.join(job_folder, f"{slug}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return os.path.abspath(path)


def update_index(job_folder: str, index_content: str) -> None:
    """Overwrite Index.md in the job folder with the given content."""
    os.makedirs(job_folder, exist_ok=True)
    path = os.path.join(job_folder, "Index.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(index_content)


def load_existing_jobs(job_folder: str) -> list[dict]:
    """Load YAML frontmatter from all *.md files in the job folder (excluding Index.md).

    Returns a list of dicts with keys: score, tier, company, source, date_found, slug.
    """
    if not os.path.isdir(job_folder):
        return []

    jobs: list[dict] = []
    for filepath in glob.glob(os.path.join(job_folder, "*.md")):
        filename = os.path.basename(filepath)
        if filename == "Index.md":
            continue
        slug = filename[:-3]  # strip .md
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        frontmatter: dict[str, str] = {}
        fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if fm_match:
            for line in fm_match.group(1).splitlines():
                if ":" in line:
                    key, _, value = line.partition(":")
                    frontmatter[key.strip()] = value.strip().strip('"')

        frontmatter["slug"] = slug
        jobs.append(frontmatter)

    return jobs
```

**Verification**: Smoke test T030 prints a valid slug string.

---

### T030: Smoke test `obsidian/writer.py`

**File**: none (shell command)

**Requirements**: slugify_job returns expected slug format

**Dependencies**: T029

```bash
python -c "from obsidian.writer import slugify_job; print(slugify_job('Senior NestJS Developer', 'Acme Corp'))"
```

**Verification**: Output is `senior-nestjs-developer-acme-corp`.

---

### T031: Smoke test full note save

**File**: none (shell command)

**Requirements**: render_job_note + save_note creates a .md file with YAML frontmatter; open in Obsidian to verify rendering

**Dependencies**: T028, T029

```bash
python -c "
from scrapers.base import Job
from analyzer import JobAnalysis
from obsidian.templates import render_job_note
from obsidian.writer import slugify_job, save_note
from config import Config

cfg = Config.load()
job = Job(title='Senior NestJS Developer', company='Acme Corp', location='Remote',
          description='Build microservices with NestJS and TypeScript.', url='https://example.com', source='test')
analysis = JobAnalysis(score=82, tier='🔥 Must Apply', justification='Ótima compatibilidade.',
                       matching_skills=['NestJS', 'TypeScript'], missing_skills=['Kubernetes'])
content = render_job_note(job, analysis, '2026-05-24')
slug = slugify_job(job.title, job.company)
path = save_note(slug, content, cfg.obsidian_job_folder)
print('Saved to:', path)
"
```

**Verification**: `path` exists on disk; open in Obsidian and confirm YAML frontmatter renders with score, tier, company, justification, and skill sections.

---

## Phase 7: User Story 5 — Deduplication Across Runs

### T032: In-memory deduplication in `main.py`

**File**: `main.py` (incorporated into T035 below)

**Requirements**: `seen_slugs: set[str]` prevents same job appearing twice in one run (across sources and queries)

**Dependencies**: T029

*This task is implemented as part of T035 (`main.py`). See T035, step 5 in the orchestration flow.*

**Verification**: Running with two queries that return overlapping results → `[DEDUP] N raw → M unique` where M < N.

---

### T033: Vault deduplication in `main.py`

**File**: `main.py` (incorporated into T035 below)

**Requirements**: After in-memory dedup, skip jobs whose slug file already exists in vault; log count

**Dependencies**: T032, T029

*This task is implemented as part of T035 (`main.py`). See T035, step 6 in the orchestration flow.*

**Verification**: Running a second time with same queries → `[DEDUP] N unique → 0 new` if no new jobs found.

---

### T034: Manual deduplication validation

**File**: none (manual test)

**Requirements**: Second run for same query creates 0 new notes for jobs from first run

**Dependencies**: T033

```bash
python main.py   # run 1 — creates N notes
python main.py   # run 2 — "Skipped (dup): N" equals notes saved in run 1
```

**Verification**: Second run summary prints `Skipped (dup): N` matching exactly the notes created in run 1.

---

## Phase 8: User Story 1+2+3+4+5 Integration — Full Pipeline

### T035: Create `main.py`

**File**: `main.py` (new)

**Requirements**: Orchestrates all phases; implements dedup (T032, T033); exits 1 on fatal errors; stdout protocol matches contracts/cli.md

**Dependencies**: T007, T011, T013, T017, T021, T022, T023, T028, T029

```python
from __future__ import annotations

import sys
import time
from datetime import datetime

from analyzer import analyze
from config import Config
from llm import build_llm
from obsidian.templates import render_index, render_job_note
from obsidian.writer import (
    load_existing_jobs,
    note_exists,
    save_note,
    slugify_job,
    update_index,
)
from resume.parser import parse_pdf
from scrapers.google_jobs import GoogleJobsScraper
from scrapers.himalayas import HimalayasScraper
from scrapers.indeed import IndeedScraper

_QUERIES = [
    "senior nodejs nestjs typescript remote",
    "desenvolvedor senior nodejs nestjs typescript remoto",
]


def main() -> None:
    start_time = time.time()
    run_date = datetime.now().strftime("%Y-%m-%d")
    run_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"[JOB FINDER] Starting run — {run_ts}")

    # 1. Config — fail-fast
    try:
        cfg = Config.load()
    except (ValueError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    # 2. LLM client — instantiate only; no test call
    try:
        llm = build_llm(cfg)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    model_name = cfg.copilot_model if cfg.llm_provider == "copilot" else cfg.ollama_model
    print(f"[LLM] Provider: {cfg.llm_provider} ({model_name})")

    # 3. Resume — fail-fast
    try:
        profile = parse_pdf("Douglas Hennrich.pdf")
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    print(
        f"[RESUME] Loaded profile from: Douglas Hennrich.pdf"
        f" ({len(profile.raw_text)} chars)"
    )

    # 4. Scrapers
    scrapers = [
        HimalayasScraper(),
        GoogleJobsScraper(api_key=cfg.serper_api_key),
        IndeedScraper(),
    ]

    all_jobs = []
    errors = 0
    for scraper in scrapers:
        source_label = type(scraper).__name__.replace("Scraper", "").lower()
        for i, query in enumerate(_QUERIES, 1):
            print(f"[SCRAPER] {source_label} — fetching query {i}/{len(_QUERIES)}...")
            batch = scraper.fetch(query, cfg.max_jobs_per_source)
            if batch:
                print(f"[SCRAPER] {source_label} — {len(batch)} results")
            else:
                print(f"[SCRAPER] ERROR: {source_label} (query {i}) — 0 results or failed, skipping")
                errors += 1
            all_jobs.extend(batch)

    # 5. In-memory dedup (T032)
    seen_slugs: set[str] = set()
    unique_pairs: list[tuple[str, object]] = []
    for job in all_jobs:
        slug = slugify_job(job.title, job.company)
        if slug not in seen_slugs:
            seen_slugs.add(slug)
            unique_pairs.append((slug, job))

    print(
        f"[DEDUP] {len(all_jobs)} raw → {len(unique_pairs)} unique (in-memory dedup)"
    )

    # 6. Vault dedup (T033)
    new_pairs: list[tuple[str, object]] = []
    skipped_dup = 0
    for slug, job in unique_pairs:
        if note_exists(slug, cfg.obsidian_job_folder):
            skipped_dup += 1
        else:
            new_pairs.append((slug, job))

    print(
        f"[DEDUP] {len(unique_pairs)} unique → {len(new_pairs)} new"
        f" (vault dedup — {skipped_dup} already in vault)"
    )

    # 7. Score and save
    saved = 0
    skipped_score = 0

    for slug, job in new_pairs:
        analysis = analyze(job, profile, llm)
        print(
            f"[SCORE] {analysis.tier} ({analysis.score})"
            f" — {job.title} @ {job.company}"
        )

        if analysis.score >= cfg.min_score:
            content = render_job_note(job, analysis, run_date)
            save_note(slug, content, cfg.obsidian_job_folder)
            print(
                f"[SAVED] {analysis.tier} ({analysis.score})"
                f" — {job.title} @ {job.company} → {slug}.md"
            )
            saved += 1
        else:
            skipped_score += 1

    # 8. Regenerate Index.md
    existing = load_existing_jobs(cfg.obsidian_job_folder)
    index_content = render_index(existing)
    update_index(cfg.obsidian_job_folder, index_content)
    print(f"[INDEX] Index.md updated — {len(existing)} total notes across all runs")

    # 9. Summary
    elapsed = round(time.time() - start_time)
    minutes, seconds = divmod(elapsed, 60)
    time_str = f"{minutes}m {seconds}s" if minutes else f"{seconds}s"
    print(f"\nDone in {time_str}.")
    print(
        f"Saved: {saved}"
        f" | Skipped (dup): {skipped_dup}"
        f" | Skipped (score): {skipped_score}"
        f" | Errors: {errors} source(s)"
    )

    sys.exit(0)


if __name__ == "__main__":
    main()
```

**Verification**: `python main.py` completes without exception; ≥1 `.md` file appears in vault; `Index.md` is created/updated.

---

### T036: End-to-end smoke test

**File**: none (shell command)

**Requirements**: Full pipeline run matches stdout protocol; at least one .md file appears in vault

**Dependencies**: T035

```bash
python main.py
```

**Verification**: Stdout contains `[JOB FINDER]`, `[RESUME]`, `[LLM]`, `[SCRAPER]`, `[DEDUP]`, `[SCORE]`, `[SAVED]`, `[INDEX]`, and `Done in ...` summary lines; vault folder contains `.md` files and `Index.md`.

---

## Phase 9: Polish & Scheduling

### T037: Create `com.douglashennrich.jobfinder.plist`

**File**: `com.douglashennrich.jobfinder.plist` (new)

**Requirements**: launchd plist running at 09:00 and 18:00 daily; stdout/stderr to logs/; COPILOT_TOKEN as env var placeholder (replaced by install_launchd.sh)

**Dependencies**: T036 (manually validated)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.douglashennrich.jobfinder</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/douglashennrich/Documents/Projetos/job-finder/main.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/Users/douglashennrich/Documents/Projetos/job-finder</string>

    <key>StartCalendarInterval</key>
    <array>
        <dict>
            <key>Hour</key>
            <integer>9</integer>
            <key>Minute</key>
            <integer>0</integer>
        </dict>
        <dict>
            <key>Hour</key>
            <integer>18</integer>
            <key>Minute</key>
            <integer>0</integer>
        </dict>
    </array>

    <key>StandardOutPath</key>
    <string>/Users/douglashennrich/Documents/Projetos/job-finder/logs/job-finder.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/douglashennrich/Documents/Projetos/job-finder/logs/job-finder-error.log</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>COPILOT_TOKEN</key>
        <string>REPLACE_WITH_GH_AUTH_TOKEN</string>
    </dict>
</dict>
</plist>
```

**Verification**: `plutil -lint com.douglashennrich.jobfinder.plist` exits 0 with "OK".

---

### T038: Create `install_launchd.sh`

**File**: `install_launchd.sh` (new)

**Requirements**: Fetches live token via `gh auth token`, injects into plist copy, copies to `~/Library/LaunchAgents/`, runs `launchctl load`

**Dependencies**: T037

```bash
#!/bin/bash
set -euo pipefail

PLIST_NAME="com.douglashennrich.jobfinder"
PROJECT_DIR="/Users/douglashennrich/Documents/Projetos/job-finder"
PLIST_SRC="${PROJECT_DIR}/${PLIST_NAME}.plist"
PLIST_DEST="${HOME}/Library/LaunchAgents/${PLIST_NAME}.plist"

TOKEN=$(gh auth token 2>/dev/null || true)
if [ -z "$TOKEN" ]; then
    echo "ERROR: Could not fetch token via 'gh auth token'. Run 'gh auth login' first." >&2
    exit 1
fi

sed "s/REPLACE_WITH_GH_AUTH_TOKEN/${TOKEN}/" "${PLIST_SRC}" > "${PLIST_DEST}"
chmod 644 "${PLIST_DEST}"

launchctl load "${PLIST_DEST}"

echo "Installed and loaded ${PLIST_NAME}"
echo "Logs: ${PROJECT_DIR}/logs/job-finder.log"
```

**Verification**: `bash install_launchd.sh` prints `Installed and loaded com.douglashennrich.jobfinder`; `launchctl list | grep jobfinder` shows the agent.

---

### T039: Validate launchd scheduling

**File**: none (shell command)

**Requirements**: Manual trigger confirms pipeline runs and logs appear in logs/

**Dependencies**: T038

```bash
launchctl start com.douglashennrich.jobfinder
sleep 5
tail -f logs/job-finder.log
```

**Verification**: `logs/job-finder.log` contains expected `[JOB FINDER] Starting run` output.

---

## Checklist

- [ ] T001: Create project directory structure
- [ ] T002: Create `requirements.txt`
- [ ] T003: Create `.env.example`
- [ ] T004: Install Python dependencies
- [ ] T005: Install Playwright Chromium browser
- [ ] T006: Copy `.env.example` to `.env` and fill required values
- [ ] T007: Create `config.py`
- [ ] T008: Smoke test `config.py`
- [ ] T009: Create `resume/__init__.py`
- [ ] T010: Create `resume/profile.py`
- [ ] T011: Create `resume/parser.py`
- [ ] T012: Smoke test `resume/parser.py`
- [ ] T013: Create `llm/__init__.py`
- [ ] T014: Create `llm/base.py`
- [ ] T015: Create `llm/ollama.py`
- [ ] T016: Create `llm/copilot.py`
- [ ] T017: Create `analyzer.py`
- [ ] T018: Smoke test analyzer
- [ ] T019: Create `scrapers/__init__.py`
- [ ] T020: Create `scrapers/base.py`
- [ ] T021: Create `scrapers/himalayas.py`
- [ ] T022: Create `scrapers/google_jobs.py`
- [ ] T023: Create `scrapers/indeed.py`
- [ ] T024: Smoke test Himalayas scraper
- [ ] T025: Smoke test Google Jobs scraper
- [ ] T026: Smoke test Indeed scraper
- [ ] T027: Create `obsidian/__init__.py`
- [ ] T028: Create `obsidian/templates.py`
- [ ] T029: Create `obsidian/writer.py`
- [ ] T030: Smoke test `obsidian/writer.py`
- [ ] T031: Smoke test full note save
- [ ] T032: In-memory dedup in `main.py`
- [ ] T033: Vault dedup in `main.py`
- [ ] T034: Manual deduplication validation
- [ ] T035: Create `main.py`
- [ ] T036: End-to-end smoke test
- [ ] T037: Create `com.douglashennrich.jobfinder.plist`
- [ ] T038: Create `install_launchd.sh`
- [ ] T039: Validate launchd scheduling

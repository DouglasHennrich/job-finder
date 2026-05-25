# Feature Specification: LinkedIn & Solides Job Scrapers

**Feature Branch**: `002-linkedin-solides-scrapers`

**Created**: 2026-05-24

**Status**: Draft

**Input**: Implementar scraping direto do LinkedIn e adicionar vagas.solides.com.br como nova fonte de vagas no pipeline do Job Finder.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — LinkedIn Direct Scraping (Priority: P1)

As a job seeker, I want the tool to search LinkedIn's public job listings directly using a headless browser so that I receive fresh, real-time job opportunities from LinkedIn without depending on third-party search intermediaries.

**Why this priority**: LinkedIn is the largest professional job network in Brazil and LATAM. The current approach (parsing LinkedIn URLs from Google/Serper search results) is broken — the GoogleJobsScraper is inoperative. A direct LinkedIn scraper delivers the highest-value job source from the start.

**Independent Test**: Can be fully tested by running only the LinkedIn scraper with a search query and verifying it returns a list of `Job` objects containing title, company, location, description, and URL — with `source="linkedin"` — without any other scraper or scoring involved.

**Acceptance Scenarios**:

1. **Given** a search query is provided, **When** the LinkedIn scraper runs, **Then** it returns a list of job listings from LinkedIn's public job search page (`/jobs/search?keywords=...`)
2. **Given** a search query is provided, **When** LinkedIn returns no results for that query, **Then** the scraper returns an empty list without raising an error
3. **Given** the LinkedIn job search page is unreachable (network error, bot detection, CAPTCHA), **When** the scraper runs, **Then** it logs a warning and returns an empty list — the pipeline continues with other sources
4. **Given** the scraper runs successfully, **When** a job listing is collected, **Then** each job has at minimum: title, company name, and the LinkedIn job URL; missing optional fields (location, description) default to empty string or "Remote"
5. **Given** the scraper runs, **When** accessing LinkedIn without any authentication, **Then** it uses only publicly accessible job search pages — no account credentials are required or used

---

### User Story 2 — Solides Job Board Scraping (Priority: P2)

As a job seeker, I want the tool to search vagas.solides.com.br for remote job opportunities so that I cover Brazilian companies that publish exclusively on this local platform.

**Why this priority**: vagas.solides.com.br is a Brazilian-specific job board used by companies that may not post on global platforms, expanding coverage for Brazil/LATAM remote roles.

**Independent Test**: Can be fully tested by running only the Solides scraper with a search query and verifying it returns `Job` objects with `source="solides"` — independently of the LinkedIn scraper or any other pipeline step.

**Acceptance Scenarios**:

1. **Given** a search query is provided, **When** the Solides scraper runs, **Then** it returns job listings from vagas.solides.com.br containing at minimum title, company, and URL
2. **Given** the Solides site is unreachable or returns an error, **When** the scraper runs, **Then** it logs a warning and returns an empty list without crashing the pipeline
3. **Given** the Solides site has no results for a query, **When** the scraper runs, **Then** it returns an empty list gracefully
4. **Given** a job is collected from Solides, **When** the Job object is created, **Then** `source` is set to `"solides"`

---

### User Story 3 — Pipeline Integration (Priority: P3)

As a job seeker, I want both new scrapers (LinkedIn and Solides) to be fully integrated into the existing job-finding pipeline so that their results are automatically scored against my resume and saved to Obsidian alongside results from existing sources.

**Why this priority**: The scrapers have no value unless they feed into the existing scoring and note-saving pipeline. Integration is required for end-to-end value delivery.

**Independent Test**: Can be fully tested by running the full pipeline (`main.py`) and verifying that Obsidian notes appear with `source: linkedin` and `source: solides` in their frontmatter — confirming the full flow works end-to-end.

**Acceptance Scenarios**:

1. **Given** the full pipeline runs, **When** LinkedIn and Solides scrapers are enabled, **Then** their results are merged with results from other sources before scoring
2. **Given** a job from LinkedIn or Solides scores above `MIN_SCORE`, **When** the pipeline runs, **Then** a corresponding Obsidian note is created with the correct source identified
3. **Given** both LinkedIn and Solides return zero results (e.g., both blocked), **When** the pipeline runs, **Then** the pipeline continues with other sources and does not crash

---

### Edge Cases

- What happens when LinkedIn detects the headless browser and returns a CAPTCHA or login wall? → Scraper logs a warning and returns an empty list; pipeline continues
- What happens when vagas.solides.com.br changes its page structure? → Scraper fails gracefully with a warning; results may be empty until the scraper is updated
- What happens when a LinkedIn job listing is missing the company name? → Field defaults to empty string; the job is still included
- What happens when duplicate jobs appear across LinkedIn and an existing source? → Existing deduplication logic in the pipeline handles this — no scraper-level deduplication needed
- What happens when the LinkedIn public job page requires JavaScript rendering? → Playwright handles JS rendering; this is expected behavior

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST include a `LinkedInScraper` that implements `BaseScraper.fetch(query, max_results) -> list[Job]`
- **FR-002**: `LinkedInScraper` MUST use a headless browser with stealth techniques to access LinkedIn's public job search pages without credentials
- **FR-003**: `LinkedInScraper` MUST return `Job` objects with `source="linkedin"` and at minimum: `title`, `company`, `url`
- **FR-004**: `LinkedInScraper` MUST never raise an exception — on any failure it logs a warning and returns an empty list
- **FR-005**: The system MUST include a `SolidesScraper` that implements `BaseScraper.fetch(query, max_results) -> list[Job]`
- **FR-006**: `SolidesScraper` MUST use the public REST API at `https://apigw.solides.com.br/jobs/v3/portal-vacancies-new` — confirmed by `research.md` Phase 0; no Playwright required
- **FR-007**: `SolidesScraper` MUST return `Job` objects with `source="solides"` and at minimum: `title`, `company`, `url`
- **FR-008**: `SolidesScraper` MUST never raise an exception — on any failure it logs a warning and returns an empty list
- **FR-009**: Both scrapers MUST be registered in `main.py` so their results are included in the scoring and note-saving pipeline
- **FR-010**: The `Job.source` field documentation MUST be updated to include `"linkedin"` and `"solides"` as valid values
- **FR-011**: Both scrapers MUST respect the `max_results` parameter and return no more than the requested number of jobs
- **FR-012**: The existing `_parse_linkedin` method in `GoogleJobsScraper` MAY be kept as a fallback but the new `LinkedInScraper` is the primary LinkedIn source

### Key Entities

- **LinkedInScraper**: Implements `BaseScraper`; scrapes `linkedin.com/jobs/search` public pages; lives at `scrapers/linkedin.py`
- **SolidesScraper**: Implements `BaseScraper`; scrapes `vagas.solides.com.br`; lives at `scrapers/solides.py`
- **Job**: Existing data class — `source` field extended to accept `"linkedin"` and `"solides"`

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least one LinkedIn job listing is returned per run when LinkedIn's public job search pages are accessible
- **SC-002**: At least one Solides job listing is returned per run when vagas.solides.com.br is accessible
- **SC-003**: A full pipeline run with both new scrapers enabled completes without crashing, even when one or both new scrapers return zero results
- **SC-004**: Jobs from LinkedIn and Solides appear as Obsidian notes with their correct source identified when they score above the configured threshold
- **SC-005**: The addition of two new scrapers does not increase total pipeline runtime by more than 60 seconds under normal network conditions

---

## Assumptions

- LinkedIn's public job search pages (`/jobs/search?keywords=...`) remain accessible without authentication at the time of implementation
- vagas.solides.com.br has a searchable job listing page or API; if the site structure changes significantly, the scraper may require maintenance
- The Playwright + playwright-stealth stack already used by `IndeedScraper` is available and will be reused by `LinkedInScraper`
- LinkedIn bot detection may cause intermittent failures; this is accepted as a known risk for this tool (personal automation, low request volume)
- The existing deduplication logic in the pipeline (based on URL/slug) handles jobs that appear on both LinkedIn and other sources
- Solides scraper implementation approach (API vs. browser) is determined during implementation based on what the site exposes
- Mobile support and multi-language queries are out of scope; English and Portuguese queries are used as-is from the existing query builders

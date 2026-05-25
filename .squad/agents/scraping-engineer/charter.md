# scraping-engineer — Web Scraping Engineer

Web scraping specialist responsible for building humanized, bot-resilient scrapers across all job sources.

## Project Context

**Project:** job-finder
**Stack:** Python 3.11+, Playwright, playwright-stealth, requests, BeautifulSoup4, Serper.dev API

## Responsibilities

- Implement `src/scrapers/base.py` — `Job` dataclass and `BaseScraper` ABC; keep `source` comment up-to-date with all known sources
- Implement `src/scrapers/google_jobs.py` — Serper.dev primary + Playwright fallback for Google Jobs
- Implement `src/scrapers/indeed.py` — Playwright humanized scraper for indeed.com and indeed.com.br
- Implement `src/scrapers/himalayas.py` — Himalayas REST API client
- Implement `src/scrapers/linkedin.py` — Playwright + playwright-stealth against LinkedIn public job search pages (`/jobs/search`), no credentials
- Implement `src/scrapers/solides.py` — `requests`-based REST API client for `apigw.solides.com.br/jobs/v3/portal-vacancies-new`; strips HTML from description; filters remote/home-office
- **[spec-003]** Implement `src/scrapers/capgemini.py` — `requests` + `BeautifulSoup(html.parser)` HTTP scraper against `https://www.capgemini.com/careers/join-capgemini/job-search/?page=1&size=11&keyword={query}`; parse `<a href>` elements containing `/jobs/`; set `source="capgemini"`, `company="Capgemini"`; never raise (return `[]` + log warning on error) (T010)
- **[spec-003]** Update `source` comment in `src/scrapers/base.py` to include `"capgemini"` (T011)
- **[spec-003]** Write `tests/unit/test_capgemini_scraper.py` with three smoke tests: fetch returns list, graceful failure on RuntimeError mock, returned jobs have `source=="capgemini"` (T012)
- Ensure all scrapers handle network failures gracefully (return empty list, log warning)
- Apply humanization: playwright-stealth, random delays (1.5–3.5s), mouse simulation, realistic user-agents

## Capabilities

- Playwright async (expert)
- playwright-stealth / bot evasion (expert)
- REST API integration / requests (expert)
- LinkedIn public job search scraping (expert)
- BeautifulSoup4 / HTML parsing (proficient)
- Serper.dev / Google Jobs API (proficient)
- HTML DOM parsing / CSS selectors (proficient)
- Anti-bot countermeasures (proficient)
- Async Python (proficient)

## Work Style

- Read `specs/001-job-finder/spec.md`, `specs/002-linkedin-solides-scrapers/spec.md`, and `specs/003-src-restructure-capgemini-scraper/spec.md` for acceptance criteria
- Test scrapers independently with smoke tests before integrating into main pipeline
- For LinkedIn and Indeed: apply `Stealth()` + `uniform(1.5, 3.5)s` humanization delays (constitution §Quality Gates)
- For Capgemini: use plain `requests.get` (no Playwright needed — server-side HTML render); respect `max_results` to cap pages
- Each scraper must return a `list[Job]` — never raise unhandled exceptions

## Status

active

# Research: LinkedIn & Solides Job Scrapers

**Phase 0 output** | **Branch**: `002-linkedin-solides-scrapers` | **Date**: 2026-05-24

---

## 1. LinkedIn Public Job Search Scraping

### Decision
Use **Playwright + playwright-stealth** with a headless Chromium browser to access LinkedIn's public job search pages. No authentication required. CSS selectors are stable and confirmed against live pages.

### Rationale
LinkedIn public job search pages load fully without a login wall. The `.contextual-sign-in-modal` element is present in the DOM but has `visibility: hidden` and does not block access to job cards. This matches the architecture of the existing `IndeedScraper` — reusing the same Playwright + stealth stack minimises dependency surface.

### Alternatives Considered
- **LinkedIn API (OAuth)**: Requires application approval from LinkedIn; not feasible for a personal CLI tool.
- **Scraping via Google/Serper results** (existing `_parse_linkedin` approach): Already proven broken in `docs/limitations.md`. Abandoned.
- **Third-party RapidAPI LinkedIn scraper**: Introduces paid dependency; overkill for personal automation.

---

### Implementation Details

**Search URL pattern:**
```
https://www.linkedin.com/jobs/search?keywords={TERM}&location={LOCATION}&f_WT=2&start={OFFSET}
```

Key params:
| Param | Values |
|-------|--------|
| `keywords` | URL-encoded job title / skills |
| `location` | `Brazil`, `São Paulo`, etc. |
| `f_WT` | `2` = remote only |
| `start` | `0`, `25`, `50`… (pagination, 25 jobs/page) |
| `f_TPR` | `r86400`=last 24h, `r604800`=last week |

**CSS Selectors (confirmed):**
```python
CARD_SELECTOR     = ".job-search-card"
TITLE_SELECTOR    = "h3.base-search-card__title"
COMPANY_SELECTOR  = "h4.base-search-card__subtitle"
LOCATION_SELECTOR = ".job-search-card__location"
LINK_SELECTOR     = "a.base-card__full-link"
DATE_SELECTOR     = "time[datetime]"
```

**HTML structure:**
```html
<ul class="jobs-search__results-list">
  <li>
    <div class="base-card job-search-card" data-entity-urn="urn:li:jobPosting:4414050895">
      <a class="base-card__full-link" href="...">...</a>
      <h3 class="base-search-card__title">React Developer</h3>
      <h4 class="base-search-card__subtitle"><a href="...">Company Name</a></h4>
      <span class="job-search-card__location">Brazil</span>
      <time datetime="2026-05-22">Há 2 dias</time>
    </div>
  </li>
</ul>
```

**Fields available per card (no detail page needed):**
| Field | Selector |
|-------|----------|
| `title` | `h3.base-search-card__title` inner text |
| `company` | `h4.base-search-card__subtitle` inner text |
| `location` | `.job-search-card__location` inner text |
| `url` | `a.base-card__full-link[href]` (strip query params) |
| `posted_date` | `time[datetime]` attribute (ISO date) |

**Known risks:**
- LinkedIn rate limits aggressively at high frequency; use `uniform(1.5, 3.5)s` delays (already required by constitution)
- Pagination beyond ~1000 results triggers auth wall — irrelevant for `max_results ≤ 20`
- CSS class names may change without notice; scraper must fail gracefully

---

## 2. Solides Job Board Scraping

### Decision
Use **`requests` with the public REST API** (`apigw.solides.com.br/jobs/v3/portal-vacancies-new`). **No Playwright required.** This is functionally equivalent to `HimalayasScraper`.

### Rationale
vagas.solides.com.br is a SPA that loads job data exclusively from a public, unauthenticated REST API. The API requires no auth token, no CAPTCHA, and responds with rich structured JSON. Using `requests` directly is simpler, faster, and more reliable than a headless browser approach.

### Alternatives Considered
- **Playwright (HTML scraping)**: Site is a SPA — all job data comes from the API, not server-rendered HTML. Playwright would still need to call the same API internally.
- **BeautifulSoup on HTML**: Not applicable — the page HTML is an empty shell at load time.

---

### Implementation Details

**API Endpoint:**
```
GET https://apigw.solides.com.br/jobs/v3/portal-vacancies-new
```

**Query parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `title` | string | Job title keyword |
| `locations` | string | City/state (optional) |
| `take` | int | Page size (default 14, max tested 50) |
| `page` | int | Page number (1-indexed) |

**Required headers:**
```python
headers = {
    "Origin": "https://vagas.solides.com.br",
    "Referer": "https://vagas.solides.com.br/"
}
```
No auth required — `Authorization` header is empty in real browser requests.

**Response structure:**
```json
{
  "success": true,
  "data": {
    "totalPages": 14859,
    "currentPage": 1,
    "count": 74291,
    "data": [
      {
        "id": 853830,
        "title": "Desenvolvedor Full Stack Sênior",
        "description": "<html>...</html>",
        "companyName": "Company Name",
        "city": { "name": "São Paulo" },
        "state": { "code": "SP" },
        "homeOffice": true,
        "jobType": "home-office",
        "salary": { "type": "simple", "negotiable": false, "initialRange": 0 },
        "seniority": [{ "name": "Sênior" }],
        "recruitmentContractType": [{ "name": "CLT" }],
        "redirectLink": "https://company.solides.jobs/vacancies/853830?origem=portal",
        "createdAt": "2026-05-24"
      }
    ]
  }
}
```

**Key field mappings to `Job` dataclass:**
| `Job` field | Solides API field |
|-------------|-------------------|
| `title` | `title` |
| `company` | `companyName` |
| `location` | `city.name` + ` – ` + `state.code`; or `"Remote"` if `homeOffice=true` |
| `description` | `description` (HTML; strip tags or truncate to 2000 chars) |
| `url` | `redirectLink` |
| `posted_date` | `createdAt` |
| `source` | `"solides"` |

**Note on remote filter:** Solides `homeOffice` field is `true` for remote/hybrid jobs. Use `jobType=home-office` param or filter in Python post-response. The API does not appear to support a direct `homeOffice=true` query param — confirm during implementation.

---

## 3. Integration in main.py

The existing `main.py` pattern for scraper registration:
```python
scrapers = [
    GoogleJobsScraper(api_key=cfg.serper_api_key),
    HimalayasScraper(),
    IndeedScraper(),
]
```
Both new scrapers follow the same pattern and will be appended:
```python
scrapers += [LinkedInScraper(), SolidesScraper()]
```

No config changes required — both scrapers have no credentials.

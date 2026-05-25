# Research: Source Restructure & Capgemini Scraper

**Phase 0 output** | **Branch**: `feature/003-src-restructure-capgemini-scraper` | **Date**: 2026-05-25

---

## 1. Python `src/` Layout — sys.path Behaviour

### Decision
Move all Python source files into `src/` and invoke the entrypoint as `python src/main.py` from the project root. No changes to import statements are required.

### Rationale
When Python runs `python src/main.py`, it automatically inserts the **containing directory of the script** (`src/`) at `sys.path[0]` before starting execution. This means all existing flat imports (`from analyzer import analyze`, `from config import Config`, `from scrapers.base import Job`, etc.) continue to resolve correctly without any modification.

The launchd plist sets `WorkingDirectory` to the project root, which means:
- `.env` loading (`load_dotenv()` in `config.py`) continues to find `.env` at the CWD (project root)
- `logs/` directory remains at the project root, so log file paths are unaffected
- `ProgramArguments` in the plist is the only field that needs updating (path changes from `main.py` → `src/main.py`)

### Alternatives Considered
- **Add `src/` to PYTHONPATH via plist environment key**: Works but adds non-obvious indirection in the plist; unnecessary since script-dir injection is automatic.
- **Stub `main.py` at root calling `src/main.py`**: Creates a two-file entrypoint maintenance burden; adds noise without benefit.
- **`pyproject.toml` editable install with `packages = [{include = "src"}]`**: Overkill for a single-machine CLI with no packaging requirements.

---

## 2. pytest `pythonpath` Configuration

### Decision
Create `pytest.ini` at the project root with:
```ini
[pytest]
pythonpath = src
```

### Rationale
pytest does not automatically replicate Python's sys.path injection for tests. Without this setting, `from scrapers.linkedin import LinkedInScraper` in `tests/unit/test_linkedin_scraper.py` would fail with `ModuleNotFoundError` after the migration. The `pythonpath` ini option (added in pytest ≥ 7.0, already required in `requirements.txt`) prepends `src/` to sys.path before collecting tests — zero test file changes required.

### Alternatives Considered
- **`conftest.py` at root with `sys.path.insert(0, 'src')`**: Works but is a legacy pattern; `pytest.ini` is the idiomatic modern approach.
- **`pyproject.toml [tool.pytest.ini_options] pythonpath = ["src"]`**: Equivalent but introduces a `pyproject.toml` that doesn't exist yet; a single-purpose `pytest.ini` is simpler.
- **Move `tests/` into `src/tests/`**: Non-standard; breaks pytest's default discovery and the project convention.

---

## 3. Capgemini Job Board — Scraping Approach

### Decision
Use **`requests` + `BeautifulSoup`** (html.parser). No Playwright required.

### Rationale
The Capgemini job search page at `https://www.capgemini.com/careers/join-capgemini/job-search/` serves job listings in **server-side rendered HTML**. A direct HTTP GET (verified via `fetch_webpage`) returns job cards as `<a>` elements linking to `https://www.capgemini.com/jobs/{id}`. No JavaScript execution is needed to obtain the listing data.

This is consistent with the `SolidesScraper` approach and avoids the Playwright startup overhead (~5–10s) for a page that doesn't require it.

### URL Structure
```
https://www.capgemini.com/careers/join-capgemini/job-search/?page=1&size=11&keyword={encoded_query}
```

| Param | Value | Notes |
|-------|-------|-------|
| `page` | `1` | First page; pagination can be added later |
| `size` | `11` | Results per page as specified |
| `keyword` | URL-encoded query | Mapped from `BaseScraper.fetch(query, ...)` |

### HTML Structure (observed)
Job listings are rendered as anchor elements whose `href` matches the pattern `/jobs/{id}`:
```html
<a href="/jobs/381336-en_GB+sap_btp">
  RF Analog Layout Engineer - FinFET Technology
  Ampelokipoi, Athens
  Permanent
  Experienced
</a>
```

**BeautifulSoup selector:**
```python
soup.find_all("a", href=lambda h: h and "/jobs/" in h)
```

**Field parsing strategy:**
- `url`: `"https://www.capgemini.com" + a["href"]`
- `title`: First line of `a.get_text(separator="\n", strip=True)` (split on `\n`)
- `location`: Second line of the text split (if present)
- `company`: `"Capgemini"` (hardcoded — all listings on this board are Capgemini positions)
- `description`: `""` (no detail page needed for pipeline intake)
- `source`: `"capgemini"`

### Alternatives Considered
- **Playwright**: Unnecessary overhead; page is SSR. Contradicts Constitution Principle V (simplicity).
- **Direct API endpoint reverse-engineering**: Capgemini's job board does not appear to expose a public REST API. HTML parsing is simpler and more stable for this page.

---

## 4. `beautifulsoup4` Dependency

### Decision
Add `beautifulsoup4>=4.12` to `requirements.txt`.

### Rationale
`beautifulsoup4` is NOT currently in `requirements.txt`. It is required for parsing the Capgemini HTML response. The `html.parser` backend is used (Python stdlib), so no additional parser package (`lxml`, `html5lib`) is needed.

### Alternatives Considered
- **`lxml`**: Faster parser but adds a C extension dependency; unnecessary for a small HTML page scraped once per run.
- **`html.parser` via stdlib `html.parser` module directly**: Significantly more verbose than BeautifulSoup for element selection; not worth the additional code complexity.
- **`re` regex parsing**: Brittle against minor HTML changes; rejected.

---

## 5. Summary of Resolved Unknowns

| Unknown | Resolution |
|---------|------------|
| Import compatibility after `src/` move | No import changes needed; Python injects `src/` to sys.path automatically |
| pytest test resolution after move | `pytest.ini` with `pythonpath = src` |
| Capgemini page rendering model | SSR HTML — `requests` sufficient, no Playwright |
| Capgemini HTML parsing | BeautifulSoup on `<a href="/jobs/...">` elements |
| Missing dependency | Add `beautifulsoup4>=4.12` to `requirements.txt` |

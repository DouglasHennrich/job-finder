# Research: Job Finder Automation

**Feature**: `001-job-finder` | **Date**: 2026-05-24

All NEEDS CLARIFICATION items resolved below. Each decision documents the choice, rationale, and alternatives considered.

---

## 1. PDF Text Extraction

**Decision**: `pdfplumber`

**Rationale**:
- Handles multi-page PDFs with a single `page.extract_text()` per page
- Pure Python — no JVM, no native binaries, macOS-compatible
- Best accuracy on text-layer PDFs (our résumé is text-based, not scanned)
- Active maintenance; works with pdfminer.six under the hood

**Alternatives Considered**:
- `PyMuPDF (fitz)`: Fast, but requires compiled native extension; adds build complexity
- `pdfminer.six` directly: More verbose API; pdfplumber wraps it more ergonomically
- `pypdf`: Less accurate text extraction; drops whitespace in some layouts
- OCR (Tesseract): Only needed for image-only PDFs; our résumé has a text layer

**Edge case handled**: If `page.extract_text()` returns `None` (image-only page), the parser skips the page and logs a warning rather than raising.

---

## 2. LLM Provider Abstraction

**Decision**: `openai` Python SDK for both Ollama and GitHub Models (claude-sonnet-4-6)

**Rationale**:
- Ollama exposes an OpenAI-compatible REST endpoint at `http://localhost:11434/v1`
- GitHub Models (Azure) also exposes an OpenAI-compatible endpoint at `https://models.inference.ai.azure.com`
- Single SDK, zero provider-switch cost: only `base_url` and `api_key` differ between providers
- `temperature=0.2` used for both — deterministic enough for scoring, small variance allowed

**Alternatives Considered**:
- `anthropic` SDK directly: Would require separate code path for Claude; rejected for uniformity
- `langchain`: Heavyweight abstraction; over-engineered for 1 prompt template
- `httpx` raw calls: More control but duplicates what openai SDK handles (retries, streaming, serialisation)

**Provider configuration**:
```
"ollama"  → base_url=http://localhost:11434/v1  api_key="ollama"  model=llama3
"copilot" → base_url=https://models.inference.ai.azure.com  api_key=COPILOT_TOKEN  model=claude-sonnet-4-6
```

---

## 3. Authentication — GitHub Models (cloud LLM)

**Decision**: Auto-detect via `subprocess.run(["gh", "auth", "token"], capture_output=True)`

**Rationale**:
- `gh` CLI is already installed and authenticated on the user's machine
- No manual token rotation; token is fetched fresh each run
- Falls back to `COPILOT_TOKEN` env var if explicitly set (e.g., in CI or launchd plist)
- Security: token never written to disk by the tool itself; only held in memory

**Alternatives Considered**:
- Hardcode `COPILOT_TOKEN` in `.env`: Works but requires manual refresh when token expires
- OAuth device flow: Too complex for a personal CLI tool
- Keychain access via macOS APIs: Complex; `gh auth token` already uses the keychain internally

---

## 4. Google Jobs Source

**Decision**: Serper.dev REST API as primary; Playwright-based Google Jobs scraper as fallback

**Rationale**:
- Serper.dev provides structured JSON from Google Jobs with `{"q": ..., "gl": "br", "hl": "pt-br"}`
- 2,500 free queries/month is sufficient (2 queries/run × 2×/day = ~120/month)
- Fallback Playwright path used when `SERPER_API_KEY` is unset or quota exceeded
- Clean separation: if `api_key` is empty string, skip Serper and go straight to fallback

**Alternatives Considered**:
- SerpAPI: More expensive; Serper.dev has equivalent Google Jobs support at lower cost
- Direct Google scraping only: Too brittle; anti-bot measures change frequently
- Adzuna API: Doesn't index Google Jobs; separate data set

---

## 5. Indeed Scraping

**Decision**: Playwright async + playwright-stealth with humanisation techniques

**Humanisation techniques**:
- Random delay `uniform(1.5, 3.5)` seconds between page actions
- `page.mouse.move(x, y)` to random coordinates before clicking
- Incremental scroll via `page.evaluate("window.scrollBy(0, N)")`
- Realistic user-agent: Chrome 124 on macOS
- `headless=False` during development; `headless=True` with stealth in production

**Rationale**:
- Indeed uses bot detection (Cloudflare + proprietary); standard headless Playwright is blocked
- `playwright-stealth` patches JS fingerprints (`navigator.webdriver`, `plugins`, `languages`, etc.)
- Humanisation reduces detection rate; not guaranteed but sufficient for personal use

**Alternatives Considered**:
- Indeed unofficial API: Deprecated; no longer returns job data
- Scraping via proxy rotation: Over-engineered for personal tool; adds cost
- ScrapingBee / BrightData: Paid service; unnecessary given personal usage volume

**Targets**: `indeed.com` (global remote) and `indeed.com.br` (Brazil-specific)

---

## 6. Himalayas API

**Decision**: Direct REST GET to `https://himalayas.app/jobs/api`

**Parameters**: `{"q": query, "limit": max_results}`

**Response fields used**: `title`, `company.name`, `locationRestrictions` (mapped to location), `description`, `applicationLink`, `remote` (filter: only `remote=true`)

**Rationale**:
- Public undocumented API; cleanest JSON data source available
- No authentication required
- Himalayas specialises in remote tech jobs — high signal for LATAM/global remote roles

**Alternatives Considered**:
- Himalayas Playwright scraping: Unnecessary given the API works; more fragile
- Wellfound (AngelList): Requires account login for API access

**Error handling**: `requests.get` wrapped in try/except; network errors return empty list with warning log

---

## 7. Deduplication Strategy

**Decision**: Slug-based filename existence check

**Implementation**:
```python
slug = slugify(f"{job.title} {job.company}")  # e.g. "senior-nestjs-dev-acme-corp"
path = os.path.join(vault_folder, f"{slug}.md")
exists = os.path.exists(path)
```

**Rationale**:
- O(1) filesystem check; no database, no state file, no lock files
- Survives restarts, crashes, and manual vault edits
- `python-slugify` is deterministic: same title+company always produces the same slug
- Cross-run dedup: if the note exists from a previous run, the job is skipped entirely (no re-scoring)
- Cross-source dedup: if two scrapers return the same job (same title + company), the second is skipped in the in-memory dedup pass before vault check

**Alternatives Considered**:
- Hash of URL: URL can differ per source for the same job (Indeed vs Himalayas links)
- SQLite DB: Adds dependency; slug approach is simpler and already self-contained
- In-memory set across runs: Doesn't survive restarts

---

## 8. Obsidian Vault Format

**Decision**: Plain Markdown with YAML frontmatter; no Dataview or plugin dependency

**Note file format**: YAML frontmatter block + structured Markdown body

**Index format**: Standard Markdown table (`| Score | Title | Company | Source | Date | Note |`) grouped by tier, regenerated from frontmatter of all `.md` files in vault folder each run

**Rationale**:
- Works in all Obsidian versions, even without community plugins
- YAML frontmatter allows future Dataview adoption if desired
- Regenerating Index.md each run is simpler than incremental updates; vault size is small (< 500 notes)

**Alternatives Considered**:
- Dataview queries: Requires plugin; breaks in basic Obsidian installs
- Appending to Index: Complex diff logic; stale entries on manual deletions
- JSON sidecar file: Loses human-readable property

---

## 9. Scheduling

**Decision**: launchd (`com.douglashennrich.jobfinder.plist`) — configured ONLY after manual pipeline validation

**Schedule**: 09:00 and 18:00 daily

**Rationale**:
- macOS-native; no cron weirdness with iCloud paths
- `install_launchd.sh` fetches a fresh `gh auth token` at install time and injects into plist
- Log files at `logs/job-finder.log` and `logs/job-finder-error.log`

**Alternatives Considered**:
- cron: Works but has path/env issues on macOS with iCloud drives
- Schedule library (Python): Requires the process to stay alive; not reliable for daily jobs
- GitHub Actions: Would require internet access to iCloud vault; not viable for local Obsidian

---

## 10. Score Tier Mapping

| Score Range | Tier | Emoji | Action |
|-------------|------|-------|--------|
| ≥ 80 | Excellent | 🔥 Must Apply | Save note |
| 60 – 79 | Good | ✅ Good Fit | Save note |
| 40 – 59 | Marginal | 🤔 Maybe | Skip (logged) |
| < 40 | Poor | ❌ Skip | Skip (logged) |

`MIN_SCORE` default = 60. Jobs scoring below threshold are logged to stdout but no note is created.

---

## Unresolved Items

None. All NEEDS CLARIFICATION items from Technical Context are resolved.

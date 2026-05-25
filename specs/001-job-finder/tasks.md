# Tasks: Job Finder Automation

**Feature**: `001-job-finder` | **Date**: 2026-05-24

**Input**: Design documents from `/specs/001-job-finder/`

**Prerequisites used**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/cli.md ✅ | quickstart.md ✅

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no shared dependencies on in-progress tasks)
- **[Story]**: User story this task serves (US1–US5)
- Paths are relative to the project root (`/Users/douglashennrich/Documents/Projetos/job-finder/`)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization — scaffolding, deps, and config. Must be complete before any other work begins.

- [ ] T001 Create project directory structure: `resume/`, `scrapers/`, `llm/`, `obsidian/`, `logs/`
- [ ] T002 Create `requirements.txt` with pinned deps: pdfplumber==0.11.4, playwright==1.44.0, playwright-stealth==1.0.6, openai==1.30.1, requests==2.32.3, python-dotenv==1.0.1, python-slugify==8.0.4, pytest>=7.0 (dev/test)
- [ ] T003 Create `.env.example` with all variables documented (LLM_PROVIDER, COPILOT_TOKEN, COPILOT_MODEL, OLLAMA_BASE_URL, OLLAMA_MODEL, SERPER_API_KEY, OBSIDIAN_VAULT_PATH, JOB_FINDER_FOLDER, MIN_SCORE, MAX_JOBS_PER_SOURCE)
- [ ] T004 Install Python dependencies: `pip install -r requirements.txt`
- [ ] T005 Install Playwright Chromium browser: `playwright install chromium`
- [ ] T006 Copy `.env.example` to `.env` and fill in OBSIDIAN_VAULT_PATH and SERPER_API_KEY

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: `Config` dataclass — required by all other modules. Must pass smoke test before US1+ begin.

- [ ] T007 Create `config.py` with `Config` dataclass that:
  - Loads `.env` via `python-dotenv`
  - Applies defaults BEFORE validation: `LLM_PROVIDER = os.getenv("LLM_PROVIDER", "copilot")`; `MIN_SCORE = int(os.getenv("MIN_SCORE", "60"))`; etc. Missing env vars → default, never ValueError
  - Auto-detects `COPILOT_TOKEN` via `subprocess.run(["gh", "auth", "token"], capture_output=True)` if env var is empty
  - Validates `OBSIDIAN_VAULT_PATH` exists on disk (raises `ValueError` with clear message if not)
  - Validates `LLM_PROVIDER` is `"copilot"` or `"ollama"` (raises `ValueError` otherwise — only after default applied)
  - Exposes `obsidian_job_folder = os.path.join(vault_path, job_finder_folder)`
  - All fields typed; defaults per contracts/cli.md
- [ ] T008 Smoke test `config.py`: `python -c "from config import Config; cfg = Config.load(); print('OK:', cfg.llm_provider, cfg.obsidian_job_folder)"`

---

## Phase 3: User Story 1 — Resume Profile Extraction

**Goal**: Parse `Douglas Hennrich.pdf` → `Profile(raw_text, pdf_path)` with clear errors on failure.

**Independent test criterion**: Run `python -c "from resume.parser import parse_pdf; p = parse_pdf('Douglas Hennrich.pdf'); print(len(p.raw_text))"` → prints a number > 0.

- [ ] T009 [US1] Create `resume/__init__.py` (empty)
- [ ] T010 [US1] Create `resume/profile.py` with `Profile` dataclass: `raw_text: str`, `pdf_path: str`
- [ ] T011 [US1] Create `resume/parser.py` with `parse_pdf(pdf_path: str) -> Profile`:
  - Opens PDF with `pdfplumber.open(pdf_path)`
  - Raises `FileNotFoundError` with path in message if file not found
  - Calls `page.extract_text() or ""` for each page (handles None safely)
  - Concatenates pages with `"\n\n"`
  - Raises `ValueError("PDF produced no extractable text")` if result is empty
- [ ] T012 [US1] Smoke test: `python -c "from resume.parser import parse_pdf; p = parse_pdf('Douglas Hennrich.pdf'); print(p.raw_text[:300])"`

---

## Phase 4: User Story 3 — AI-Powered Job Fit Scoring

**Goal**: Given a `Job` + `Profile` + LLM, return `JobAnalysis(score, tier, justification, matching_skills, missing_skills)`.

**Independent test criterion**: Run smoke test with a hardcoded sample job → get a `score` between 0–100, a non-empty Portuguese `justification`, and a correct `tier` label.

**Why before US2**: US2 (scrapers) can be implemented in parallel with US3. US3 depends only on US1 (Profile) + foundational Config. The analyzer must exist before US4 (vault writing) can be integrated.

- [ ] T013 [US3] Create `llm/__init__.py` with `build_llm(config: Config) -> BaseLLM` factory:
  - If `config.llm_provider == "ollama"` → returns `OllamaLLM`
  - Otherwise → returns `CopilotLLM` (raises `RuntimeError` if token is empty)
- [ ] T014 [P] [US3] Create `llm/base.py` with `BaseLLM` ABC and abstract method `chat(system: str, user: str) -> str`
- [ ] T015 [P] [US3] Create `llm/ollama.py` with `OllamaLLM(base_url: str, model: str)`:
  - Uses `openai.OpenAI(base_url=base_url, api_key="ollama")`
  - `temperature=0.2`
  - Implements `chat()` → `client.chat.completions.create(...).choices[0].message.content`
- [x] T016 [P] [US3] Create `llm/copilot.py` with `CopilotLLM(token: str, model: str)`:
  - `base_url = "https://api.githubcopilot.com"` (**intentional** — uses GitHub Copilot Pro+ API directly, not Azure inference)
  - `openai.OpenAI(base_url=..., api_key=token, default_headers={"Copilot-Integration-Id": "vscode-chat"})`
  - `temperature=0.2`
  - Implements `chat()` identically to OllamaLLM
- [ ] T017 [US3] Create `analyzer.py` with `JobAnalysis` dataclass and `analyze(job, profile, llm) -> JobAnalysis`:
  - System prompt: `"You are an expert technical recruiter... Respond ONLY with a valid JSON object"`
  - User prompt includes `profile.raw_text`, `job.title`, `job.company`, `job.location`, `job.description`
  - JSON response fields: `score` (int), `tier` (str), `justification` (str in pt-BR), `matching_skills` (list), `missing_skills` (list)
  - Parse chain: `json.loads()` → regex `re.search(r'\{.*\}', resp, re.DOTALL)` → sentinel `score=0, tier="❌ Skip", justification="[parse error]"`
  - Clamp `score` to `[0, 100]` after parse
  - Override `tier` from score: ≥80 → `"🔥 Must Apply"`, ≥60 → `"✅ Good Fit"`, ≥40 → `"🤔 Maybe"`, <40 → `"❌ Skip"`
- [ ] T018 [US3] Smoke test analyzer with hardcoded NestJS job sample:
  ```bash
  python -c "
  from config import Config; from llm import build_llm; from resume.parser import parse_pdf
  from scrapers.base import Job; from analyzer import analyze
  cfg = Config.load(); llm = build_llm(cfg); profile = parse_pdf('Douglas Hennrich.pdf')
  job = Job(title='Senior NestJS Developer', company='Acme', location='Remote LATAM',
            description='5+ years Node.js NestJS TypeScript PostgreSQL Redis. Remote LATAM.', url='https://x.com', source='test')
  r = analyze(job, profile, llm)
  print(f'Score: {r.score} | Tier: {r.tier}')
  print(f'Justification: {r.justification}')
  "
  ```

---

## Phase 5: User Story 2 — Multi-Source Job Discovery

**Goal**: 3 independent scrapers each return `list[Job]` with title, company, location, description, url, source.

**Independent test criterion**: Each scraper can be called standalone and returns ≥1 job with non-empty title, company, and url.

**Note**: T019–T026 (base + Himalayas + Google Jobs + Indeed) can all be developed in parallel after T007 (Config) is done.

- [ ] T019 [US2] Create `scrapers/__init__.py` (empty)
- [ ] T020 [US2] Create `scrapers/base.py` with:
  - `Job` dataclass: `title`, `company`, `location`, `description`, `url`, `source`, `salary: Optional[str] = None`, `posted_date: Optional[str] = None`
  - `BaseScraper` ABC with abstract method `fetch(query: str, max_results: int) -> list[Job]`
- [x] T021 [P] [US2] Create `scrapers/himalayas.py` with `HimalayasScraper(BaseScraper)`:
  - GET `https://himalayas.app/jobs/api` with params `{"q": query, "limit": max_results}`
  - Map JSON fields: `title`, `companyName` → `company` (API returns flat field, not nested `company.name`), `locationRestrictions` → `location`, `description`, `applicationLink` → `url`
  - Remote filter: `if item.get("remote") is False: continue` — Himalayas is a remote-only platform; the `remote` field is absent in practice (intentional no-op guard for future-proofing)
  - Wrap in `try/except requests.RequestException` → log warning, return `[]`
  - `source = "himalayas"`
  - ✅ Confirmed by T024 smoke test: 5 real jobs returned with correct company names via `companyName` field
- [x] T022 [P] [US2] Create `scrapers/google_jobs.py` with `GoogleJobsScraper(api_key: str)` implementing `BaseScraper`:
  - Constructor: `self.api_key = api_key`
  - **Implementation** (**intentional redesign**): POST `https://google.serper.dev/search` with site-operator queries (built by `_build_serper_queries()` in `main.py`); parses `organic[]` results with site-specific logic: `inhire.app`, `linkedin.com`, `indeed.com`
  - **No-key fallback**: returns `[]` immediately with a warning log — Playwright fallback dropped in favour of site-search approach
  - `source` is per-site (`"inhire"`, `"linkedin"`, `"indeed"`) derived from URL
- [ ] T023 [P] [US2] Create `scrapers/indeed.py` with `IndeedScraper(BaseScraper)`:
  - Implements sync `fetch(query, max_results) -> list[Job]` from `BaseScraper` by calling `asyncio.get_event_loop().run_until_complete(self._async_fetch(query, max_results))`
  - `_async_fetch()` is the actual async implementation:
    - Async Playwright with `playwright-stealth` applied before navigation
    - Chromium launch: `headless=True` (stealth active)
    - User-agent: realistic Chrome/macOS string
    - Target: `https://www.indeed.com/jobs?q={query}&remotejobs=1&sort=date`
    - Humanisation: `random.uniform(1.5, 3.5)` delay, `page.mouse.move()` to random coords, incremental scroll
    - Extract job cards: `.jobTitle`, `.companyName`, `.companyLocation`, `.jcs-JobTitle`
    - For each card up to `max_results`: navigate job detail page, extract full description
  - Wrap `fetch()` entire flow in `try/except Exception` → log warning, return partial results (never raise)
  - `source = "indeed"`
- [ ] T024 [US2] Smoke test Himalayas: `python -c "from scrapers.himalayas import HimalayasScraper; jobs = HimalayasScraper().fetch('nodejs nestjs react', 5); [print(j.title, '|', j.company) for j in jobs]"`
- [ ] T025 [US2] Smoke test Google Jobs: run with SERPER_API_KEY set; confirm ≥1 job returned with title and company
- [ ] T026 [US2] Smoke test Indeed (opens browser, manual verification): `python -c "from scrapers.indeed import IndeedScraper; jobs = IndeedScraper().fetch('senior fullstack nodejs', 3); [print(j.title) for j in jobs]"`

---

## Phase 6: User Story 4 — Obsidian Vault Note Creation

**Goal**: Qualifying jobs are saved as `.md` files in the vault; `Index.md` is regenerated after each run.

**Independent test criterion**: Provide a pre-scored `Job + JobAnalysis` → call `save_note()` → verify `.md` file exists in vault with YAML frontmatter and score in body.

- [ ] T027 [US4] Create `obsidian/__init__.py` (empty)
- [ ] T028 [P] [US4] Create `obsidian/templates.py` with two functions:
  - `render_job_note(job: Job, analysis: JobAnalysis, date_str: str) -> str`: generates full Markdown with YAML frontmatter (`score`, `tier`, `company`, `source`, `date_found`, `status: new`) + body sections (tier+score header, quoted justification, Skills match/gap, Details table, Job Description)
  - `render_index(jobs_data: list[dict]) -> str`: generates `Index.md` with header, timestamp, and 3 tier sections (🔥/✅/🤔) as Markdown tables; ❌ tier not shown
- [ ] T029 [P] [US4] Create `obsidian/writer.py` with functions:
  - `slugify_job(title: str, company: str) -> str` — uses `python-slugify`; e.g. `"senior-nestjs-dev-acme-corp"`
  - `note_exists(slug: str, job_folder: str) -> bool` — `os.path.exists(os.path.join(job_folder, f"{slug}.md"))`
  - `save_note(slug: str, content: str, job_folder: str) -> str` — `os.makedirs(job_folder, exist_ok=True)`; writes file; returns absolute path
  - `update_index(job_folder: str, index_content: str) -> None` — writes `Index.md` to `job_folder`
  - `load_existing_jobs(job_folder: str) -> list[dict]` — glob `*.md` (exclude `Index.md`); parse YAML frontmatter with `re` (no external YAML lib needed for simple frontmatter); return list of dicts with `score`, `tier`, `company`, `source`, `date_found`, `slug` (derived from filename)
- [ ] T030 [US4] Smoke test writer: `python -c "from obsidian.writer import slugify_job; print(slugify_job('Senior NestJS Developer', 'Acme Corp'))"`
- [ ] T031 [US4] Smoke test full note save: provide hardcoded job + analysis → call `render_job_note` + `save_note` → open resulting `.md` in Obsidian and verify rendering

---

## Phase 7: User Story 5 — Deduplication Across Runs

**Goal**: Jobs already in the vault (by slug) are skipped; in-run duplicates across sources are also deduplicated.

**Independent test criterion**: Run pipeline twice with same query; second run creates 0 new notes for previously saved jobs.

- [ ] T032 [US5] Add in-memory dedup to `main.py` pipeline: maintain `seen_slugs: set[str]`; for each job after aggregation, compute slug and skip if already in set (add to set otherwise)
- [ ] T033 [US5] Add vault dedup in `main.py`: after in-memory dedup, call `note_exists(slug, cfg.obsidian_job_folder)`; increment `skipped_dup` counter and `continue` if exists
- [ ] T034 [US5] Manual validation: run pipeline once (creates notes), run again with same env → verify `Skipped (dup): N` in summary equals number of notes saved in first run

---

## Phase 8: User Story 1+2+3+4+5 Integration — Full Pipeline (`main.py`)

**Goal**: Orchestrate all modules into a single `python main.py` command that runs the complete pipeline end-to-end.

**Independent test criterion**: `python main.py` completes without exception; at least one note appears in vault; `Index.md` is created/updated.

- [x] T035 Create `main.py` that orchestrates:
  1. `Config.load()` → fail-fast with code 1 on bad config
  2. `build_llm(cfg)` → instantiate client only (no test call); raises `RuntimeError` if copilot token empty
  3. Resume loading: cache-first strategy — `load_profile_cache()` → if miss, `parse_pdf("Douglas Hennrich.pdf")` + `save_profile_cache()` + `save_profile_note()` → fail-fast code 1 if no PDF and no cache (**intentional**: avoids re-parsing PDF on every run)
  4. Instantiate `HimalayasScraper()` and `GoogleJobsScraper(api_key=cfg.serper_api_key)` (**IndeedScraper excluded** pending T023 fix); separate query lists: `_build_queries()` for Himalayas, `_build_serper_queries()` for Google
  5. Run each `scraper.fetch(query, cfg.max_jobs_per_source)` per query; aggregate `all_jobs`
  6. Log `[SCRAPER]` lines per source including count or error per contracts/cli.md
  7. In-memory dedup (`seen_slugs` set) → log dedup count
  8. Vault dedup (`note_exists()`) → log dedup count
  9. For each unique new job: call `analyze()`; log `[SCORE]` line; handle `RateLimitError` gracefully (stops scoring, logs warn, completes run)
  10. If `analysis.score >= cfg.min_score`: call `save_note()`; log `[SAVED]` line; else increment `skipped_score`
  11. `load_existing_jobs()` + `render_index()` + `update_index()` → log `[INDEX]` line
  12. Print summary: `Done in Xs. Saved: N | Skipped (dup): N | Skipped (score): N | Errors: N source(s)`
  13. `sys.exit(0)` on success, `sys.exit(1)` on fatal error
- [ ] T036 End-to-end smoke test: `python main.py` → verify stdout matches protocol in contracts/cli.md and at least one `.md` file appears in vault

---

## Phase 9: Polish & Scheduling

**Goal**: launchd scheduling for unattended daily runs (only after manual pipeline validation).

- [ ] T037 Create `com.douglashennrich.jobfinder.plist` with launchd configuration: runs at 09:00 and 18:00 daily; WorkingDirectory = project root; stdout/stderr → `logs/job-finder.log` / `logs/job-finder-error.log`
- [ ] T038 Create `install_launchd.sh`: fetches `gh auth token`, injects into plist ENVIRONMENTVARIABLES block, copies to `~/Library/LaunchAgents/`, runs `launchctl load`
- [ ] T039 Validate launchd: `launchctl start com.douglashennrich.jobfinder`; check `logs/job-finder.log` for expected output

---

## Dependencies

```
T001–T006 (Setup)
    └── T007–T008 (Config — foundational)
            ├── T009–T012 (US1: Resume) ──────────────────┐
            ├── T013–T018 (US3: LLM + Analyzer) ──────────┤
            │   (T014, T015, T016 parallelizable)          │
            ├── T019–T026 (US2: Scrapers) ─────────────────┤
            │   (T021, T022, T023 parallelizable)          │
            └── T027–T031 (US4: Obsidian writer) ──────────┤
                (T028, T029 parallelizable)                │
                                                           ▼
                                               T032–T034 (US5: Dedup)
                                                           │
                                                           ▼
                                               T035–T036 (Integration: main.py)
                                                           │
                                                           ▼
                                               T037–T039 (launchd — AFTER validation)
```

---

## Parallel Execution Plan

### Phase 1 (sequential — setup)
All setup tasks must run in order: T001 → T002 → T003 → T004 → T005 → T006

### Phase 2 (sequential — foundational)
T007 → T008

### Phases 3–6 (parallel after Phase 2)
After T008 passes, these user story phases can run in parallel:

| Stream A | Stream B | Stream C | Stream D |
|----------|----------|----------|----------|
| T009 US1 | T013 US3 | T019 US2 | T027 US4 |
| T010 [P] | T014 [P] | T020 US2 | T028 [P] |
| T011 [P] | T015 [P] | T021 [P] | T029 [P] |
| T012     | T016 [P] | T022 [P] | T030     |
|          | T017     | T023 [P] | T031     |
|          | T018     | T024     |          |
|          |          | T025     |          |
|          |          | T026     |          |

### Phase 7 (after US1 + US4 foundations done)
T032 → T033 → T034

### Phase 8 (after all US1–US5 done)
T035 → T036

### Phase 9 (after T036 manually validated)
T037 → T038 → T039

---

## Implementation Strategy

**MVP scope (US1 + US3 + US4 only)**:
1. Complete T001–T012 (setup + config + resume parsing)
2. Complete T013–T018 (LLM + analyzer)
3. Complete T027–T031 (Obsidian writer)
4. Write a minimal `main.py` that hardcodes one sample job → analyze → save to vault
5. Validate Obsidian note renders correctly

**Full pipeline (add US2 + US5)**:
6. Complete T019–T026 (all 3 scrapers)
7. Complete T032–T034 (dedup)
8. Replace hardcoded job in `main.py` with live scraper output (T035–T036)

**Automation (Phase 9)**:
9. Only after T036 passes manual validation

---

## Summary

| Metric | Value |
|--------|-------|
| Total tasks | 39 |
| US1 (Resume) | 4 tasks (T009–T012) |
| US2 (Scrapers) | 8 tasks (T019–T026) |
| US3 (LLM/Scoring) | 6 tasks (T013–T018) |
| US4 (Obsidian) | 5 tasks (T027–T031) |
| US5 (Dedup) | 3 tasks (T032–T034) |
| Integration | 2 tasks (T035–T036) |
| Setup/Foundational | 8 tasks (T001–T008) |
| Polish/launchd | 3 tasks (T037–T039) |
| Parallelizable tasks | 11 (marked [P]) |
| MVP scope (validate pipeline) | T001–T018, T027–T031 (~21 tasks) |

# Task Routing: 001-job-finder

**Generated**: 2026-05-24  
**Feature**: `001-job-finder` (T001–T039)  
**Strategy**: capability-match  
**Agents**: python-engineer · scraping-engineer · ai-engineer · obsidian-engineer

---

## Routing Table

```
Task Routing Summary — 001-job-finder
──────────────────────────────────────────────────────────────────────────────────
Task   Description                                       Agent                Tier
──────────────────────────────────────────────────────────────────────────────────
── Phase 1: Setup (sequential — must complete before all other work) ────────────
T001   Create project directory structure                python-engineer      lightweight
T002   Create requirements.txt with pinned deps          python-engineer      lightweight
T003   Create .env.example with all variables            python-engineer      lightweight
T004   Install Python dependencies                       python-engineer      lightweight
T005   Install Playwright Chromium browser               python-engineer      lightweight
T006   Copy .env.example → .env and fill vars            python-engineer      lightweight

── Phase 2: Foundational (sequential — blocks all downstream phases) ────────────
T007   Create config.py with Config dataclass            python-engineer      full
T008   Smoke test config.py                              python-engineer      lightweight

── Phase 3: US1 — Resume Profile (Stream A, parallel with B/C/D) ────────────────
T009   Create resume/__init__.py                         python-engineer      lightweight
T010   Create resume/profile.py (Profile dataclass)      python-engineer      lightweight
T011   Create resume/parser.py (parse_pdf)               python-engineer      standard
T012   Smoke test resume parser                          python-engineer      lightweight

── Phase 4: US3 — LLM + Analyzer (Stream B, parallel with A/C/D) ───────────────
T013   Create llm/__init__.py (build_llm factory)        ai-engineer          standard
T014 ◆ Create llm/base.py (BaseLLM ABC)                  ai-engineer          lightweight
T015 ◆ Create llm/ollama.py (OllamaLLM)                  ai-engineer          standard
T016 ◆ Create llm/copilot.py (CopilotLLM)                ai-engineer          standard
T017   Create analyzer.py (JobAnalysis + analyze())      ai-engineer          full
T018   Smoke test analyzer with hardcoded NestJS job     ai-engineer          lightweight

── Phase 5: US2 — Scrapers (Stream C, parallel with A/B/D) ─────────────────────
T019   Create scrapers/__init__.py                       scraping-engineer    lightweight
T020   Create scrapers/base.py (Job + BaseScraper)       scraping-engineer    standard
T021 ◆ Create scrapers/himalayas.py                      scraping-engineer    standard
T022 ◆ Create scrapers/google_jobs.py (Serper+Playwright) scraping-engineer   full
T023 ◆ Create scrapers/indeed.py (stealth Playwright)    scraping-engineer    full
T024   Smoke test Himalayas scraper                      scraping-engineer    lightweight
T025   Smoke test Google Jobs scraper                    scraping-engineer    lightweight
T026   Smoke test Indeed scraper                         scraping-engineer    lightweight

── Phase 6: US4 — Obsidian Vault (Stream D, parallel with A/B/C) ────────────────
T027   Create obsidian/__init__.py                       obsidian-engineer    lightweight
T028 ◆ Create obsidian/templates.py (render_job_note,    obsidian-engineer    standard
       render_index)
T029 ◆ Create obsidian/writer.py (slugify_job,           obsidian-engineer    standard
       save_note, update_index, load_existing_jobs)
T030   Smoke test writer slugify                         obsidian-engineer    lightweight
T031   Smoke test full note save → verify Obsidian render obsidian-engineer   standard

── Phase 7: US5 — Deduplication (after US1 + US4 foundations) ──────────────────
T032   Add in-memory dedup (seen_slugs) to main.py       python-engineer      standard
T033   Add vault dedup (note_exists) to main.py          python-engineer      standard
T034   Manual validation: run pipeline twice             python-engineer      lightweight

── Phase 8: Integration — Full Pipeline (after all US1–US5 done) ────────────────
T035   Create main.py full orchestration (13 steps)      python-engineer      full
T036   End-to-end smoke test: python main.py             python-engineer      lightweight

── Phase 9: Polish & Scheduling (after T036 manually validated) ─────────────────
T037   Create com.douglashennrich.jobfinder.plist         python-engineer      standard
T038   Create install_launchd.sh                         python-engineer      standard
T039   Validate launchd start + log output               python-engineer      lightweight
──────────────────────────────────────────────────────────────────────────────────
Routed: 39 / 39   Unrouted: 0
◆ = can be parallelized within the phase (independent files, no shared deps)
```

---

## Agent Summary

| Agent              | Tasks                                              | Count |
|--------------------|----------------------------------------------------|-------|
| python-engineer    | T001–T012, T032–T039                               | 22    |
| scraping-engineer  | T019–T026                                          | 8     |
| ai-engineer        | T013–T018                                          | 6     |
| obsidian-engineer  | T027–T031                                          | 5     |

---

## Phase-by-Phase Parallelization Plan

### Phase 1 — Sequential (all agents blocked until done)
```
T001 → T002 → T003 → T004 → T005 → T006
```
**Who**: python-engineer alone. No parallelism possible; each step is a prerequisite for the next.

### Phase 2 — Sequential (all agents blocked until T008 passes)
```
T007 → T008
```
**Who**: python-engineer alone. Config is the single shared foundation; T008 must pass smoke test before any downstream work starts.

### Phases 3–6 — Full Parallel (4 streams after T008 ✅)

All four streams are **independent** — different directories, no cross-imports at this stage.

```
Stream A (python-engineer)    Stream B (ai-engineer)       Stream C (scraping-engineer)   Stream D (obsidian-engineer)
──────────────────────────    ──────────────────────       ─────────────────────────────  ────────────────────────────
T009 resume/__init__.py       T013 llm/__init__.py         T019 scrapers/__init__.py       T027 obsidian/__init__.py
T010 resume/profile.py        T014 ◆ llm/base.py           T020 scrapers/base.py           T028 ◆ obsidian/templates.py
T011 resume/parser.py         T015 ◆ llm/ollama.py         T021 ◆ scrapers/himalayas.py    T029 ◆ obsidian/writer.py
T012 smoke test               T016 ◆ llm/copilot.py        T022 ◆ scrapers/google_jobs.py  T030 smoke test slugify
                              T017 analyzer.py             T023 ◆ scrapers/indeed.py       T031 smoke test full save
                              T018 smoke test              T024 smoke test himalayas
                                                           T025 smoke test google_jobs
                                                           T026 smoke test indeed
```

**Intra-stream parallelism** (◆ tasks with no shared deps within a stream):
- Stream B: T014 / T015 / T016 can all start simultaneously after T013 (`BaseLLM` declared)
- Stream C: T021 / T022 / T023 can all start simultaneously after T020 (`BaseScraper` declared)
- Stream D: T028 / T029 can start simultaneously after T027

### Phase 7 — Sequential (needs US1 + US4 done; python-engineer)
```
T032 → T033 → T034
```
Requires: T012 ✅ (Profile exists), T030 ✅ (writer functions exist), T028 ✅ (templates exist).

### Phase 8 — Sequential (needs all US1–US5 done; python-engineer)
```
T035 → T036
```
Requires: All of Streams A–D complete + T034 ✅.

### Phase 9 — Sequential (only after T036 manually validated; python-engineer)
```
T037 → T038 → T039
```

---

## Critical Path

```
T001–T006 → T007 → T008
                       ├── [A] T009→T010→T011→T012
                       ├── [B] T013→{T014,T015,T016}→T017→T018
                       ├── [C] T019→T020→{T021,T022,T023}→T024→T025→T026
                       └── [D] T027→{T028,T029}→T030→T031
                                                            ↓ (all streams done)
                                             T032→T033→T034
                                                    ↓
                                             T035→T036
                                                    ↓ (manual validation)
                                             T037→T038→T039
```

Longest path: **Setup → Config → Scraper stream C** (most tasks).  
Minimum calendar phases with full parallelism: **7 gates** (phases 1→2→{3-6 in parallel}→7→8→9).

---

## Routing Rules Inferred (new patterns for routing.md)

| Pattern                                      | Agent              |
|----------------------------------------------|--------------------|
| `resume/`, PDF parsing, pdfplumber           | python-engineer    |
| `requirements.txt`, `.env.example`, launchd  | python-engineer    |
| `main.py` orchestration, deduplication logic | python-engineer    |
| `llm/base.py`, ABC/factory patterns for LLM  | ai-engineer        |
| `analyzer.py`, prompt design, JSON parse     | ai-engineer        |
| `scrapers/base.py`, Job dataclass            | scraping-engineer  |
| `playwright-stealth`, bot evasion, humanise  | scraping-engineer  |
| Serper.dev API, Google Jobs fallback         | scraping-engineer  |
| `obsidian/templates.py`, YAML frontmatter    | obsidian-engineer  |
| `obsidian/writer.py`, slug, glob, vault I/O  | obsidian-engineer  |

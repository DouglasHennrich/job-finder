# Data Model: Job Finder Automation

**Feature**: `001-job-finder` | **Date**: 2026-05-24

---

## Entities

### 1. `Config`

Loaded once at startup via `Config.load()`. All fields sourced from environment variables (via `.env`).

| Field | Type | Source Env Var | Default | Notes |
|-------|------|----------------|---------|-------|
| `llm_provider` | `str` | `LLM_PROVIDER` | `"copilot"` | `"copilot"` or `"ollama"` |
| `copilot_token` | `str` | `COPILOT_TOKEN` | auto-detected | Falls back to `gh auth token` subprocess |
| `copilot_model` | `str` | `COPILOT_MODEL` | `"claude-sonnet-4-6"` | GitHub Models model name |
| `ollama_base_url` | `str` | `OLLAMA_BASE_URL` | `"http://localhost:11434/v1"` | Ollama OpenAI-compatible endpoint |
| `ollama_model` | `str` | `OLLAMA_MODEL` | `"llama3"` | Ollama model name |
| `serper_api_key` | `str` | `SERPER_API_KEY` | `""` | Empty → use Playwright fallback |
| `obsidian_vault_path` | `str` | `OBSIDIAN_VAULT_PATH` | — | Required; path to vault root |
| `job_finder_folder` | `str` | `JOB_FINDER_FOLDER` | `"Job Finder"` | Subfolder name within vault |
| `obsidian_job_folder` | `str` | derived | — | `os.path.join(vault_path, folder)` |
| `min_score` | `int` | `MIN_SCORE` | `60` | Jobs below this score are not saved |
| `max_jobs_per_source` | `int` | `MAX_JOBS_PER_SOURCE` | `20` | Per scraper per query |

**Validation rules**:
- `obsidian_vault_path` must exist on disk at startup; raise `ValueError` with clear message if not
- `llm_provider` must be `"copilot"` or `"ollama"`; raise `ValueError` otherwise
- If `llm_provider == "copilot"` and token resolution fails, raise `RuntimeError`

---

### 2. `Profile`

Represents the structured output of PDF résumé parsing.

```python
@dataclass
class Profile:
    raw_text: str    # Full text extracted from all pages, joined with "\n\n"
    pdf_path: str    # Absolute path to source PDF
```

**Validation rules**:
- `raw_text` must be non-empty; if empty after extraction, raise `ValueError("PDF produced no extractable text")`
- `pdf_path` must exist; raise `FileNotFoundError` with path in message if not

**State transitions**: Immutable after creation. Never modified during pipeline run.

---

### 3. `Job`

Represents a single job posting discovered from any source scraper.

```python
@dataclass
class Job:
    title: str
    company: str
    location: str
    description: str
    url: str
    source: str              # "google_jobs" | "indeed" | "himalayas"
    salary: Optional[str] = None
    posted_date: Optional[str] = None
```

**Validation rules**:
- `title`, `company`, `url` must be non-empty (scrapers should filter out incomplete records)
- `description` should be as complete as possible; scrapers truncate to ~2,000 chars if description is very long to keep prompt size manageable
- `source` must be one of the known source identifiers

**Relationships**:
- One `Job` is input to `analyze()` → produces one `JobAnalysis`
- One `Job` (if score qualifies) → produces one `VaultNote`

---

### 4. `JobAnalysis`

The result of LLM-based fit evaluation for a single `Job` against the `Profile`.

```python
@dataclass
class JobAnalysis:
    score: int               # 0–100
    tier: str                # "🔥 Must Apply" | "✅ Good Fit" | "🤔 Maybe" | "❌ Skip"
    justification: str       # 2–3 sentences in Brazilian Portuguese
    matching_skills: list[str]
    missing_skills: list[str]
```

**Validation rules**:
- `score` is clamped to `[0, 100]` after parsing (in case LLM returns out-of-range)
- If JSON parse fails, returns sentinel: `score=0, tier="❌ Skip", justification="[parse error]", matching_skills=[], missing_skills=[]`
- Parse fallback chain: `json.loads()` → regex `\{.*\}` (re.DOTALL) → sentinel

**Tier derivation from score** (applied after parse as authoritative override):
```
score >= 80 → "🔥 Must Apply"
score >= 60 → "✅ Good Fit"
score >= 40 → "🤔 Maybe"
score  < 40 → "❌ Skip"
```

---

### 5. `VaultNote` (file artifact)

A Markdown file written to the Obsidian vault for a qualifying job.

**Filename**: `{slug}.md` where `slug = slugify(f"{job.title} {job.company}")`

**Location**: `{Config.obsidian_job_folder}/{slug}.md`

**Format** (YAML frontmatter + Markdown body):
```markdown
---
score: 85
tier: "🔥 Must Apply"
company: Acme Corp
source: google_jobs
date_found: 2026-05-24
status: new
---

# Senior NestJS Developer — Acme Corp

🔥 Must Apply **Score: 85/100**

> Excelente compatibilidade. O candidato possui experiência sólida em Node.js, NestJS e TypeScript, que são os requisitos principais da vaga...

## Skills
- ✅ **Match:** Node.js, NestJS, TypeScript, PostgreSQL, Redis
- ❌ **Gap:** Kubernetes, AWS Lambda

## Details
| Field | Value |
|-------|-------|
| Company | Acme Corp |
| Location | Remote LATAM |
| Source | google_jobs |
| Found | 2026-05-24 |
| Apply | [https://...](https://...) |

## Job Description
[full job description text]
```

**Deduplication check**: `os.path.exists(path)` before any scoring; skip entire job if file exists.

---

### 6. `IndexNote` (file artifact)

A Markdown summary file regenerated each run in the vault root.

**Location**: `{Config.obsidian_job_folder}/Index.md`

**Format**:
```markdown
# 🔍 Job Finder — Index

*Last updated: 2026-05-24 18:02*

## 🔥 Must Apply (≥80)
| Score | Title | Company | Source | Date | Note |
|-------|-------|---------|--------|------|------|
| 85 | Senior NestJS Developer | Acme Corp | google_jobs | 2026-05-24 | [[senior-nestjs-developer-acme-corp]] |

## ✅ Good Fit (60–79)
| Score | Title | Company | Source | Date | Note |
|-------|-------|---------|--------|------|------|
| 72 | Fullstack Engineer | Beta Inc | himalayas | 2026-05-23 | [[fullstack-engineer-beta-inc]] |

## 🤔 Maybe (40–59)
*No jobs in this tier.*

## ❌ Skip (<40)
*Not shown in index (below threshold).*
```

**Generation**: `load_existing_jobs()` reads YAML frontmatter from all `*.md` files (excluding `Index.md`) in the vault folder, then `render_index()` produces the full Markdown. Written by `update_index()`.

---

## Relationships Diagram

```
PDF file
   │
   ▼
parse_pdf() ──► Profile
                   │
                   │ (used by analyze() for every job)
                   │
Scrapers ──────► [Job, Job, Job, ...]
                   │
                   ├── dedup (in-memory slug check)
                   ├── dedup (vault file existence check)
                   │
                   ▼
               analyze(job, profile, llm)
                   │
                   ▼
               JobAnalysis
                   │
                   ├── score < MIN_SCORE → log + skip
                   │
                   ▼
               render_job_note() ──► VaultNote (.md file)
                   │
                   ▼
               load_existing_jobs() + render_index() ──► IndexNote (Index.md)
```

---

## State Transitions

| State | Trigger | Result |
|-------|---------|--------|
| Raw PDF | `parse_pdf()` | `Profile` with `raw_text` |
| Job discovered | scraper `fetch()` | `Job` dataclass |
| Job (in-memory dedup) | slug in `seen_slugs` set | Dropped silently |
| Job (vault dedup) | `note_exists()` returns True | `skipped_dup += 1`, move to next |
| Job (scored) | `analyze()` returns `score < MIN_SCORE` | `skipped_score += 1`, logged |
| Job (qualified) | `score >= MIN_SCORE` | `VaultNote` written, `saved += 1` |
| Run complete | all jobs processed | `IndexNote` regenerated |

# CLI Contract: Job Finder

**Feature**: `001-job-finder` | **Date**: 2026-05-24

This document defines the command-line interface contract for `main.py` — the only public entry point of the job-finder tool.

---

## Invocation

```bash
python main.py
```

No positional arguments. No flags. All configuration is supplied via environment variables (`.env` file or shell environment).

---

## Environment Variables Contract

All configuration is consumed at startup via `Config.load()`. The tool fails immediately with a clear error if required variables are missing or invalid.

| Variable | Required | Default | Accepted Values | Description |
|----------|----------|---------|-----------------|-------------|
| `LLM_PROVIDER` | No | `copilot` | `copilot`, `ollama` | Which LLM backend to use |
| `COPILOT_TOKEN` | If `LLM_PROVIDER=copilot` | auto-detected | any GitHub token string | Auto-fetched via `gh auth token` if empty |
| `COPILOT_MODEL` | No | `claude-sonnet-4-6` | any GitHub Models model name | Model to call via GitHub Models endpoint |
| `OLLAMA_BASE_URL` | No | `http://localhost:11434/v1` | any URL | Ollama OpenAI-compatible endpoint |
| `OLLAMA_MODEL` | No | `llama3` | any Ollama model name | Ollama model to use |
| `SERPER_API_KEY` | No | `""` (empty) | any Serper.dev API key | Empty = skip Serper, use Playwright fallback |
| `OBSIDIAN_VAULT_PATH` | **Yes** | — | absolute filesystem path | Root of the Obsidian vault |
| `JOB_FINDER_FOLDER` | No | `Job Finder` | any folder name | Subfolder inside vault for job notes |
| `MIN_SCORE` | No | `60` | integer 0–100 | Minimum score to save a note |
| `MAX_JOBS_PER_SOURCE` | No | `20` | positive integer | Max job listings fetched per scraper per query |

---

## Exit Codes

| Code | Meaning | Typical Cause |
|------|---------|---------------|
| `0` | Success | Pipeline completed; summary printed |
| `1` | Fatal error | PDF not found, vault path invalid, LLM misconfigured |

The tool does **not** exit with `1` for recoverable errors (e.g., one scraper failing). Recoverable errors are logged and the run continues.

---

## Standard Output Protocol

All progress output goes to **stdout**. Errors go to **stderr** only for fatal failures (which also exit with code 1).

### Startup

```
[JOB FINDER] Starting run — 2026-05-24 09:00:12
[RESUME] Loaded profile from: Douglas Hennrich.pdf (3 pages, 4821 chars)
[LLM] Provider: copilot (claude-sonnet-4-6)
```

### Scraping phase

```
[SCRAPER] google_jobs — fetching query 1/2...
[SCRAPER] google_jobs — 18 results
[SCRAPER] indeed      — fetching query 1/2...
[SCRAPER] indeed      — 12 results
[SCRAPER] himalayas   — 20 results
[SCRAPER] ERROR: indeed (query 2) — ConnectionError, skipping
[DEDUP] 50 raw → 38 unique (in-memory dedup)
[DEDUP] 38 unique → 31 new (vault dedup — 7 already in vault)
```

### Scoring phase

```
[SCORE] ✅ Good Fit (72) — Senior NestJS Developer @ Acme Corp
[SCORE] 🔥 Must Apply (88) — Staff Engineer @ Beta Inc
[SCORE] ❌ Skip (35, below 60) — Junior PHP Developer @ Gamma Ltd
```

### Saving phase

```
[SAVED] 🔥 Must Apply (88) — Staff Engineer @ Beta Inc → staff-engineer-beta-inc.md
[SAVED] ✅ Good Fit (72) — Senior NestJS Developer @ Acme Corp → senior-nestjs-developer-acme-corp.md
[INDEX] Index.md updated — 14 total notes across all runs
```

### Summary

```
Done in 4m 23s.
Saved: 2 | Skipped (dup): 7 | Skipped (score): 22 | Errors: 1 source
```

---

## Error Messages (Fatal — exits with code 1)

| Scenario | Error Message |
|----------|--------------|
| PDF not found | `[ERROR] PDF not found: /path/to/Douglas Hennrich.pdf — check the file exists and the path is correct` |
| Vault path missing | `[ERROR] Obsidian vault not found: /path/to/vault — set OBSIDIAN_VAULT_PATH correctly` |
| LLM provider invalid | `[ERROR] LLM_PROVIDER must be "copilot" or "ollama", got: "xyz"` |
| Copilot token unavailable | `[ERROR] Could not resolve COPILOT_TOKEN. Run "gh auth login" or set COPILOT_TOKEN in .env` |
| PDF produces no text | `[ERROR] PDF produced no extractable text. The file may be image-only (scanned). Use a text-layer PDF.` |

---

## Side Effects

The tool **only writes** to the Obsidian vault folder:
- Creates `{slug}.md` files for qualifying jobs
- Overwrites `Index.md` each run

The tool **never**:
- Modifies the PDF résumé
- Sends emails or notifications
- Submits job applications
- Writes outside the vault folder

---

## Smoke Test

```bash
# Dry run — validate config only (exit after startup checks)
python -c "from config import Config; cfg = Config.load(); print('Config OK:', cfg.llm_provider)"

# Full run
python main.py

# With explicit token
COPILOT_TOKEN="$(gh auth token)" python main.py
```

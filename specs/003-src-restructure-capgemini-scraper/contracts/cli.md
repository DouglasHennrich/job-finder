# CLI Contract: Source Restructure & Capgemini Scraper

**Phase 1 output** | **Branch**: `feature/003-src-restructure-capgemini-scraper` | **Date**: 2026-05-25

---

## Entrypoint Change

The CLI entrypoint changes from `python main.py` to `python src/main.py`.

### Before
```bash
# From project root
python main.py
```

### After
```bash
# From project root (required — WorkingDirectory must be project root for .env loading)
python src/main.py
```

> **Note**: Always run from the project root directory. Running from inside `src/` will cause `.env` loading to fail (dotenv looks in the current working directory).

---

## Invocation — No Arguments

The CLI interface is unchanged. The tool takes no command-line arguments. All configuration is via environment variables in `.env`.

```bash
python src/main.py
```

---

## Environment Variables (unchanged)

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `copilot` | LLM backend: `copilot` or `ollama` |
| `COPILOT_MODEL` | `claude-sonnet-4.6` | Model for Copilot provider |
| `OLLAMA_BASE_URL` | `http://localhost:11434/v1` | Ollama endpoint |
| `OLLAMA_MODEL` | `qwen3.6:27b` | Model for Ollama provider |
| `SERPER_API_KEY` | — | API key for Serper (Google Jobs source) |
| `OBSIDIAN_VAULT_PATH` | — | Absolute path to Obsidian vault |
| `JOB_FINDER_FOLDER` | `Job Finder` | Subfolder inside vault |
| `MIN_SCORE` | `60` | Minimum LLM score to save a job note |
| `MAX_JOBS_PER_SOURCE` | `20` | Max jobs fetched per scraper per query |

No new environment variables are introduced by this feature.

---

## Output (unchanged)

The tool prints progress to stdout and writes Obsidian notes. The Capgemini scraper adds output lines of the form:

```
[CapgeminiScraper] Fetched N jobs for query "..."
```

or on failure:

```
[CapgeminiScraper] <error description> — returning []
```

---

## Scheduled Invocation (launchd — updated)

The plist at `com.douglashennrich.jobfinder.plist` is updated:

```xml
<!-- Before -->
<string>/path/to/.venv/bin/python</string>
<string>/path/to/job-finder/main.py</string>

<!-- After -->
<string>/path/to/.venv/bin/python</string>
<string>/path/to/job-finder/src/main.py</string>
```

Re-run `install_launchd.sh` after updating the plist.

---

## Testing

```bash
# Run all tests (from project root)
pytest tests/

# Run only Capgemini scraper tests
pytest tests/unit/test_capgemini_scraper.py -v
```

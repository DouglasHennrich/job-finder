# Quickstart: Source Restructure & Capgemini Scraper

**Phase 1 output** | **Branch**: `feature/003-src-restructure-capgemini-scraper` | **Date**: 2026-05-25

---

## What Changed

1. All Python source files moved from project root into `src/`
2. New `CapgeminiScraper` added at `src/scrapers/capgemini.py`
3. `pytest.ini` added at project root for test discovery
4. `requirements.txt` updated with `beautifulsoup4>=4.12`
5. `com.douglashennrich.jobfinder.plist` updated to invoke `src/main.py`

---

## Quick Reference

### Run the pipeline
```bash
# Always from the project root
cd /path/to/job-finder
python src/main.py
```

### Run tests
```bash
pytest tests/
```

### Install dependencies (after pulling this branch)
```bash
pip install -r requirements.txt
```

### Re-install launchd schedule (after plist update)
```bash
bash install_launchd.sh
```

---

## Project Structure After Migration

```
job-finder/
├── src/                         # All Python source (NEW)
│   ├── analyzer.py
│   ├── config.py
│   ├── main.py                  # Entrypoint (was: main.py at root)
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── copilot.py
│   │   └── ollama.py
│   ├── obsidian/
│   │   ├── __init__.py
│   │   ├── templates.py
│   │   └── writer.py
│   ├── resume/
│   │   ├── __init__.py
│   │   ├── parser.py
│   │   └── profile.py
│   └── scrapers/
│       ├── __init__.py
│       ├── base.py
│       ├── capgemini.py         # NEW
│       ├── google_jobs.py
│       ├── himalayas.py
│       ├── indeed.py
│       ├── linkedin.py
│       └── solides.py
├── tests/                       # Unchanged
│   └── unit/
│       ├── test_capgemini_scraper.py   # NEW
│       ├── test_linkedin_scraper.py
│       └── test_solides_scraper.py
├── pytest.ini                   # NEW: pythonpath = src
├── requirements.txt             # Updated: +beautifulsoup4
├── com.douglashennrich.jobfinder.plist  # Updated: path → src/main.py
├── .env                         # Unchanged
└── ...                          # All other root files unchanged
```

---

## Capgemini Scraper — How It Works

The `CapgeminiScraper` makes a single HTTP GET request to:
```
https://www.capgemini.com/careers/join-capgemini/job-search/?page=1&size=11&keyword={query}
```

It parses the server-side rendered HTML using BeautifulSoup, targeting anchor elements linking to `/jobs/{id}`. Each job card yields a `Job` object with `source="capgemini"`.

The scraper is registered in `main.py` and runs automatically as part of the existing pipeline — no configuration changes needed.

---

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError` when running tests | `pythonpath` not configured | Ensure `pytest.ini` exists with `pythonpath = src` |
| `.env` not found at startup | Running `python main.py` from inside `src/` | Always run from project root: `python src/main.py` |
| Capgemini returns 0 results | No listings match the keyword | Normal — pipeline continues with other sources |
| launchd still runs old path | Plist not re-installed | Run `bash install_launchd.sh` |

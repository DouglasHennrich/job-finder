# Quickstart: Job Finder

**Feature**: `001-job-finder` | **Date**: 2026-05-24

Get the tool running from scratch in under 15 minutes.

---

## Prerequisites

| Requirement | Check |
|-------------|-------|
| Python 3.11+ | `python3 --version` |
| pip | `pip --version` |
| Playwright system deps | see step 3 |
| gh CLI (for Copilot auth) | `gh --version` + `gh auth status` |
| Serper.dev account | https://serper.dev (free tier) |
| Obsidian vault on local disk | path must be accessible |

---

## Step 1 — Clone and enter the project

```bash
cd /Users/douglashennrich/Documents/Projetos/job-finder
```

The PDF résumé (`Douglas Hennrich.pdf`) must be in this directory.

---

## Step 2 — Install Python dependencies

```bash
pip install -r requirements.txt
```

---

## Step 3 — Install Playwright browser

```bash
playwright install chromium
```

> On first run, this downloads ~130 MB. Required for Indeed scraping and Google Jobs fallback.

---

## Step 4 — Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in:

```dotenv
# Required
OBSIDIAN_VAULT_PATH=/Users/douglashennrich/Library/Mobile Documents/iCloud~md~obsidian/Documents/DHennrich/DHennrich
SERPER_API_KEY=your_key_here      # from https://serper.dev

# Optional (defaults shown)
LLM_PROVIDER=copilot              # "copilot" or "ollama"
MIN_SCORE=60
MAX_JOBS_PER_SOURCE=20
JOB_FINDER_FOLDER=Job Finder
```

Leave `COPILOT_TOKEN` empty — it is auto-detected via `gh auth token`.

---

## Step 5 — Verify configuration

```bash
python -c "from config import Config; cfg = Config.load(); print('OK:', cfg.llm_provider, '|', cfg.obsidian_job_folder)"
```

Expected output:
```
OK: copilot | /Users/douglashennrich/Library/Mobile Documents/.../Job Finder
```

---

## Step 6 — Verify résumé parsing

```bash
python -c "
from resume.parser import parse_pdf
p = parse_pdf('Douglas Hennrich.pdf')
print(f'Extracted {len(p.raw_text)} chars from {p.pdf_path}')
print(p.raw_text[:300])
"
```

---

## Step 7 — Test LLM connection

```bash
python -c "
from config import Config
from llm import build_llm
cfg = Config.load()
llm = build_llm(cfg)
print(llm.chat('You are helpful.', 'Say hello in exactly one word.'))
"
```

---

## Step 8 — Run the full pipeline

```bash
python main.py
```

Watch stdout for progress. After the run:
- Open Obsidian
- Navigate to `Job Finder/` folder
- Check new note files and `Index.md`

---

## Step 9 — Schedule with launchd (optional, after validation)

> ⚠️ Only do this after Step 8 completes successfully at least once.

```bash
chmod +x install_launchd.sh
./install_launchd.sh
```

This installs the launchd agent to run at 09:00 and 18:00 daily.

To verify it's loaded:
```bash
launchctl list | grep jobfinder
```

To check logs:
```bash
tail -f logs/job-finder.log
```

To unload:
```bash
launchctl unload ~/Library/LaunchAgents/com.douglashennrich.jobfinder.plist
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `FileNotFoundError: Douglas Hennrich.pdf` | PDF not in project root | Copy PDF to `job-finder/` |
| `ValueError: Obsidian vault not found` | Wrong `OBSIDIAN_VAULT_PATH` in `.env` | Verify path with `ls "$OBSIDIAN_VAULT_PATH"` |
| `RuntimeError: Could not resolve COPILOT_TOKEN` | gh CLI not logged in | Run `gh auth login` |
| Indeed returns 0 jobs | Bot detection triggered | Run with `headless=False` temporarily (dev mode) |
| Score always 0 / parse error | LLM returning non-JSON | Check LLM connectivity; try `ollama` provider as fallback |
| `playwright install` fails | Missing system deps | Run `playwright install-deps chromium` (Linux only; macOS: no extra deps needed) |

---

## Switching LLM Providers

```bash
# Use local Ollama (requires Ollama running: ollama serve)
LLM_PROVIDER=ollama python main.py

# Use GitHub Models / Claude (default)
LLM_PROVIDER=copilot python main.py
```

---

## Environment Variables Reference

See [contracts/cli.md](./contracts/cli.md#environment-variables-contract) for the full table.

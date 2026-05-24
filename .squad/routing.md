# Work Routing

How to decide who handles what.

## Routing Table

| Work Type | Route To | Examples |
|-----------|----------|----------|
| Config, env, main pipeline, PDF parsing, resume | python-engineer | config.py, main.py, resume/parser.py, requirements.txt, launchd setup |
| Web scraping, Playwright, Serper.dev, Himalayas, Indeed | scraping-engineer | scrapers/google_jobs.py, scrapers/indeed.py, scrapers/himalayas.py, bot evasion |
| LLM providers, prompt design, job fit scoring | ai-engineer | llm/ollama.py, llm/copilot.py, analyzer.py, prompt tuning |
| Obsidian notes, Markdown templates, vault I/O, index | obsidian-engineer | obsidian/templates.py, obsidian/writer.py, Index.md generation |
| Code review | ralph | Review PRs, check quality, suggest improvements |
| Testing | python-engineer | Smoke tests, integration tests, edge case validation |
| Tasks audit, speckit verification, implementation gap detection | tasks-auditor | Audit tasks.md vs codebase, report missing/broken tasks, route failures back to orchestrator |
| `speckit.implement`, "implement the tasks", "implement speckit tasks" | Squad fan-out (skill: speckit-implement-squad-route) | **NEVER execute sequentially** — read skill `.github/skills/speckit-implement-squad-route/SKILL.md`, group tasks by agent, spawn in parallel per phase |
| Scope & priorities | ralph | What to build next, trade-offs, decisions |
| Session logging | Scribe | Automatic — never needs routing |
| `resume/`, PDF parsing, pdfplumber | python-engineer | resume/parser.py, resume/profile.py |
| `requirements.txt`, `.env.example`, launchd | python-engineer | requirements.txt, .env.example, plist, install_launchd.sh |
| `main.py` orchestration, deduplication logic | python-engineer | main.py, seen_slugs dedup, pipeline wiring |
| `llm/base.py`, ABC/factory patterns for LLM | ai-engineer | llm/__init__.py, build_llm factory |
| `analyzer.py`, prompt design, JSON parse | ai-engineer | analyzer.py, scoring tiers, pt-BR justification |
| `scrapers/base.py`, Job dataclass | scraping-engineer | scrapers/base.py |
| `playwright-stealth`, bot evasion, humanise | scraping-engineer | scrapers/indeed.py, scrapers/google_jobs.py |
| Serper.dev API, Google Jobs fallback | scraping-engineer | scrapers/google_jobs.py |
| `obsidian/templates.py`, YAML frontmatter | obsidian-engineer | obsidian/templates.py, render_job_note, render_index |
| `obsidian/writer.py`, slug, glob, vault I/O | obsidian-engineer | obsidian/writer.py, save_note, update_index |

## Issue Routing

| Label | Action | Who |
|-------|--------|-----|
| `squad` | Triage: analyze issue, assign `squad:{member}` label | Lead |
| `squad:{name}` | Pick up issue and complete the work | Named member |

### How Issue Assignment Works

1. When a GitHub issue gets the `squad` label, the **Lead** triages it — analyzing content, assigning the right `squad:{member}` label, and commenting with triage notes.
2. When a `squad:{member}` label is applied, that member picks up the issue in their next session.
3. Members can reassign by removing their label and adding another member's label.
4. The `squad` label is the "inbox" — untriaged issues waiting for Lead review.

## Rules

1. **Eager by default** — spawn all agents who could usefully start work, including anticipatory downstream work.
2. **Scribe always runs** after substantial work, always as `mode: "background"`. Never blocks.
3. **Quick facts → coordinator answers directly.** Don't spawn an agent for "what port does the server run on?"
4. **When two agents could handle it**, pick the one whose domain is the primary concern.
5. **"Team, ..." → fan-out.** Spawn all relevant agents in parallel as `mode: "background"`.
6. **Anticipate downstream work.** If a feature is being built, spawn the tester to write test cases from requirements simultaneously.
7. **Issue-labeled work** — when a `squad:{member}` label is applied to an issue, route to that member. The Lead handles all `squad` (base label) triage.

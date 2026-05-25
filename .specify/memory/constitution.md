<!--
SYNC IMPACT REPORT
==================
Version change: 1.0.1 → 1.0.2
Modified principles:
  - V. CLI Simplicity: updated entrypoint reference from `python main.py` to
    `python src/main.py` to reflect spec 003 src/ restructure.
Added sections: none
Removed sections: none

Templates requiring updates:
  ✅ .specify/templates/constitution-template.md — source template, no change needed
  ✅ .specify/templates/plan-template.md — no constitution-specific change needed
  ✅ .specify/templates/spec-template.md — no change needed
  ✅ .specify/templates/tasks-template.md — no change needed
  ⚠ specs/001-job-finder/plan.md — still references `python main.py` (historical; pre-003)
  ⚠ specs/002-linkedin-solides-scrapers/plan.md — still references `python main.py` (historical; pre-003)
  ✅ specs/003-src-restructure-capgemini-scraper/plan.md — already uses `python src/main.py`

Follow-up TODOs: none
-->

# Job Finder Constitution

## Core Principles

### I. Configuration-First
All runtime behaviour is controlled through `.env` / environment variables. Hard-coded
secrets, file paths, and provider-specific values MUST NOT appear in source code.
Missing required configuration MUST fail fast with a clear, actionable error message
before any pipeline work begins. Defaults are applied at load time so missing optional
variables never raise unexpected errors.

**Rationale**: Single-user local tools are moved between machines and shared as examples.
Configuration-first ensures the tool is portable and auditable without code changes.

### II. Graceful Degradation
Each data source (scraper) is fully independent. A network failure, anti-bot block, or
parsing error in one source MUST NOT abort the pipeline — the tool MUST log a warning
and continue with the remaining sources. An empty result set from a source is a valid
outcome. A partial run delivering fewer results is always preferable to a failed run
delivering none.

**Rationale**: Remote job scraping is inherently unreliable. Stopping the pipeline on a
single source failure would make the tool useless on any network hiccup.

### III. AI Output Safety
LLM responses MUST be parsed through a three-stage fallback chain:
1. Direct `json.loads()` on the raw response
2. Regex extraction (`re.search(r'\{.*\}', resp, re.DOTALL)`) then `json.loads()`
3. Sentinel default: `score=0, tier="❌ Skip", justification="[parse error]"`

Scores MUST be clamped to `[0, 100]` after parsing. The tier label MUST be derived
authoritatively by application code from the clamped score — the LLM-provided tier
field is ignored. Temperature MUST be `0.2` for consistent, deterministic scoring.

**Rationale**: LLMs occasionally output markdown fences, extra prose, or malformed JSON.
The fallback chain ensures the pipeline always produces a usable result rather than
crashing on an unexpected model response.

### IV. Obsidian-Native Storage
Notes MUST use plain Markdown with YAML frontmatter only. No Obsidian plugins, custom
CSS, JavaScript, or proprietary syntax are permitted. Filenames MUST use
`slugify(f"{title} {company}")` for deterministic, filesystem-safe deduplication.
`Index.md` MUST be fully regenerated on every successful run from the current vault
state, never incrementally patched. Jobs rejected by score MUST be recorded as slugs in
`_discarded.txt` (one slug per line, append-only) within the job notes folder so they
are not re-scored on subsequent runs.

**Rationale**: Plain Markdown survives Obsidian version upgrades, vault migrations, and
non-Obsidian editors. Slug-based deduplication (notes + `_discarded.txt`) keeps the
storage model portable and auditable without a database.

### V. CLI Simplicity (YAGNI)
This is a single-user, single-machine local tool. No web server, no database, no
distributed systems, no REST API, no daemon processes beyond launchd scheduling.
Every added abstraction MUST be justified by an existing requirement. The full pipeline
run (3 sources × 2 queries × up to 20 jobs/source) MUST complete within 10 minutes on
the target macOS machine.

**Rationale**: Complexity compounds maintenance cost. This tool's value is in daily
automation, not architectural elegance. Keep it runnable by a single `python src/main.py`.

## Quality Gates

Every module MUST have at least one smoke test that validates its independent operation
before pipeline integration (defined in `specs/001-job-finder/tasks.md`).

All secrets MUST be excluded from version control. `.env` is git-ignored; `.env.example`
documents structure and defaults only — it MUST contain no real values.

Playwright scrapers MUST apply `playwright-stealth` and humanisation (random delays
`uniform(1.5, 3.5)s`, mouse simulation) before any page navigation.

New LLM provider integrations MUST implement `BaseLLM.chat(system, user) -> str` and
be registered in `llm/__init__.py::build_llm` before use in the analyzer.

## Development Workflow

All feature work begins with a Speckit branch (`{NNN}-{feature-slug}`).

Constitution amendments MUST increment `CONSTITUTION_VERSION` according to semantic
versioning (MAJOR: principle removal/redefinition; MINOR: new principle/section; PATCH:
wording/clarification). The Sync Impact Report comment at the top of this file MUST be
updated with every amendment.

The `specs/{feature}/plan.md` Constitution Check section MUST enumerate the specific
principle gates being evaluated before implementation of that feature begins.

## Governance

This constitution supersedes all other conventions and practices for this project.
All implementation decisions MUST be evaluated against principles I–V before proceeding.
Complexity that appears to violate Principle V (Simplicity) requires explicit justification
documented in the relevant `plan.md`.

**Version**: 1.0.2 | **Ratified**: 2026-05-24 | **Last Amended**: 2026-05-25

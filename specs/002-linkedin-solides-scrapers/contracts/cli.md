# CLI Contract Update: LinkedIn & Solides Scrapers

**Phase 1 output** | **Branch**: `002-linkedin-solides-scrapers` | **Date**: 2026-05-24

---

This document describes changes to the existing CLI contract introduced by the new scrapers.
The base CLI contract is defined in `specs/001-job-finder/contracts/cli.md`.

---

## Changes to Existing Contract

### New Sources in Pipeline Output

The pipeline now includes two additional sources in all outputs where `source` appears:

**Obsidian note frontmatter** (unchanged format, new source values):
```yaml
---
title: "Senior Full Stack Developer"
company: "Empresa ABC"
source: linkedin        # NEW — was only: google_jobs | indeed | himalayas
score: 78
tier: "✅ Good"
url: "https://br.linkedin.com/jobs/view/..."
date: "2026-05-24"
---
```

```yaml
---
source: solides         # NEW
url: "https://empresa.solides.jobs/vacancies/853830?origem=portal"
---
```

### Index.md Source Distribution

The regenerated `Index.md` will now include LinkedIn and Solides in the source breakdown section (if jobs from those sources score above `MIN_SCORE`).

---

## No New CLI Arguments

This feature adds no new command-line arguments, flags, or environment variables.

Both scrapers are **always active** when the pipeline runs — they cannot be individually disabled via CLI. (Individual disable is out of scope per the YAGNI principle.)

---

## Runtime Behavior Change

**Before** (3 active scrapers):
```
[SCRAPERS] Running: GoogleJobsScraper, HimalayasScraper, IndeedScraper
```

**After** (5 active scrapers):
```
[SCRAPERS] Running: GoogleJobsScraper, HimalayasScraper, IndeedScraper, LinkedInScraper, SolidesScraper
```

Maximum raw jobs per run increases from ~60–120 to ~110–200 (before dedup and scoring).

---

## Graceful Degradation (unchanged contract)

If LinkedIn or Solides return zero results (bot detection, network error, site changes):
- A warning is logged: `[SCRAPER] LinkedInScraper returned 0 results`
- The pipeline continues with the remaining sources
- No pipeline crash; exit code remains `0`

from __future__ import annotations

from datetime import datetime

from analyzer import JobAnalysis
from scrapers.base import Job


def render_job_note(job: Job, analysis: JobAnalysis, date_str: str) -> str:
    matching = ", ".join(analysis.matching_skills) or "N/A"
    missing = ", ".join(analysis.missing_skills) or "N/A"
    return f"""---
score: {analysis.score}
tier: "{analysis.tier}"
company: "{job.company}"
source: "{job.source}"
date_found: "{date_str}"
status: new
---

# {job.title} — {job.company}

{analysis.tier} **Score: {analysis.score}/100**

> {analysis.justification}

## Skills

✅ **Match:** {matching}
❌ **Gap:** {missing}

## Details

| Field | Value |
|-------|-------|
| Company | {job.company} |
| Location | {job.location} |
| Source | {job.source} |
| Found | {date_str} |
| Apply | [{job.url}]({job.url}) |

## Job Description

{job.description}
"""


def render_index(jobs_data: list[dict], discarded_count: int = 0, providers: list[str] | None = None) -> str:
    tiers = {
        "🔥 Must Apply": [],
        "✅ Good Fit": [],
        "🤔 Maybe": [],
    }
    for job in jobs_data:
        tier_val = job.get("tier", "")
        if "Must Apply" in tier_val:
            tiers["🔥 Must Apply"].append(job)
        elif "Good Fit" in tier_val:
            tiers["✅ Good Fit"].append(job)
        elif "Maybe" in tier_val:
            tiers["🤔 Maybe"].append(job)

    for key in tiers:
        tiers[key].sort(key=lambda j: int(j.get("score", 0)), reverse=True)

    if providers is None:
        providers = sorted({job.get("source", "") for job in jobs_data if job.get("source")})
    providers_str = ", ".join(providers) if providers else "—"

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Job Finder — Index",
        "",
        f"**Last updated:** {now}",
        f"**Total:** {len(jobs_data)} jobs saved",
        f"**Discarded:** {discarded_count} jobs below threshold",
        f"**Providers:** {providers_str}",
        "",
    ]

    for tier_name, jobs in tiers.items():
        if not jobs:
            continue
        lines.append(f"## {tier_name}")
        lines.append("")
        lines.append("| Score | Job | Company | Source | Date |")
        lines.append("|-------|-----|---------|--------|------|")
        for job in jobs:
            score = job.get("score", "")
            slug = job.get("slug", "")
            company = job.get("company", "")
            source = job.get("source", "")
            date_found = job.get("date_found", "")
            lines.append(f"| {score} | [[{slug}]] | {company} | {source} | {date_found} |")
        lines.append("")

    return "\n".join(lines)

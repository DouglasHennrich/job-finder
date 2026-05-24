from __future__ import annotations

from datetime import datetime

from analyzer import JobAnalysis
from scrapers.base import Job


def render_job_note(job: Job, analysis: JobAnalysis, date_str: str) -> str:
    # TODO (T028):
    # 1. Build YAML frontmatter: score, tier (quoted), company, source, date_found, status: new
    # 2. Build body: "# {title} — {company}" header
    # 3. Tier + score line: "{tier} **Score: {score}/100**"
    # 4. Quoted justification block: "> {justification}"
    # 5. Skills section: "✅ **Match:** {matching_skills joined}" and "❌ **Gap:** {missing_skills joined}"
    # 6. Details table: Company, Location, Source, Found, Apply (with URL link)
    # 7. Job Description section with full job.description text
    # 8. Return complete string
    raise NotImplementedError


def render_index(jobs_data: list[dict]) -> str:
    # TODO (T028):
    # 1. Build header: "# Job Finder — Index", last updated timestamp, total count
    # 2. Group jobs_data by tier into {"🔥 Must Apply": [], "✅ Good Fit": [], "🤔 Maybe": []}
    #    (❌ tier is excluded from the index)
    # 3. Sort each tier group by score descending (int)
    # 4. For each non-empty tier: section header + Markdown table with columns
    #    Score | Title (as [[slug]] wikilink) | Company | Source | Date
    # 5. Return complete string
    raise NotImplementedError

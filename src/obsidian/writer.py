from __future__ import annotations

import glob
import os
import re
from datetime import datetime

from slugify import slugify as _slugify


def slugify_job(title: str, company: str) -> str:
    """Generate a deterministic filesystem-safe slug from job title and company."""
    return _slugify(f"{title} {company}")


def note_exists(slug: str, job_folder: str) -> bool:
    """Return True if a note file for this slug already exists in the vault."""
    return os.path.exists(os.path.join(job_folder, f"{slug}.md"))


def save_note(slug: str, content: str, job_folder: str) -> str:
    os.makedirs(job_folder, exist_ok=True)
    path = os.path.join(job_folder, f"{slug}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return os.path.abspath(path)


def update_index(job_folder: str, index_content: str) -> None:
    os.makedirs(job_folder, exist_ok=True)
    with open(os.path.join(job_folder, "Index.md"), "w", encoding="utf-8") as f:
        f.write(index_content)


_DISCARDED_FILE = "Discarded.md"

_DISCARDED_HEADER = (
    "---\n"
    "description: Jobs analyzed and discarded (score below threshold). Auto-managed by job-finder.\n"
    "---\n\n"
    "# Discarded Jobs\n\n"
    "| Slug | Title | Company | Score | Tier | Source | Date | URL |\n"
    "|------|-------|---------|-------|------|--------|------|-----|\n"
)


def load_discarded_slugs(job_folder: str) -> set[str]:
    """Return set of slugs previously scored and rejected (score below threshold)."""
    path = os.path.join(job_folder, _DISCARDED_FILE)
    if not os.path.exists(path):
        return set()
    slugs: set[str] = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("| "):
                continue
            parts = line.split("|")
            if len(parts) < 2:
                continue
            slug = parts[1].strip()
            if slug and slug != "Slug" and not slug.startswith("---"):
                slugs.add(slug)
    return slugs


def mark_discarded(
    slug: str,
    job_folder: str,
    *,
    title: str = "",
    company: str = "",
    score: int = 0,
    tier: str = "",
    source: str = "",
    url: str = "",
) -> None:
    """Append a rejected job as a table row in Discarded.md so it appears in Obsidian."""
    os.makedirs(job_folder, exist_ok=True)
    path = os.path.join(job_folder, _DISCARDED_FILE)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(_DISCARDED_HEADER)
    date_str = datetime.now().strftime("%Y-%m-%d")
    safe_title = (title or slug).replace("|", "\\|")
    safe_company = company.replace("|", "\\|")
    url_cell = f"[link]({url})" if url else ""
    row = f"| {slug} | {safe_title} | {safe_company} | {score} | {tier} | {source} | {date_str} | {url_cell} |\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(row)


def load_existing_jobs(job_folder: str) -> list[dict]:
    if not os.path.isdir(job_folder):
        return []
    files = glob.glob(os.path.join(job_folder, "*.md"))
    jobs = []
    for file_path in files:
        slug = os.path.splitext(os.path.basename(file_path))[0]
        if slug == "Index":
            continue
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        data: dict = {}
        if match:
            for line in match.group(1).splitlines():
                if ": " in line:
                    key, value = line.split(": ", 1)
                    data[key.strip()] = value.strip().strip('"')
        data["slug"] = slug
        jobs.append(data)
    return jobs

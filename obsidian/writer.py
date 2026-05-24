from __future__ import annotations

import glob
import os
import re

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

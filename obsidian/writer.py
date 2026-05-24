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
    # TODO (T029):
    # 1. os.makedirs(job_folder, exist_ok=True)
    # 2. Write content to {job_folder}/{slug}.md (utf-8)
    # 3. Return os.path.abspath(path)
    raise NotImplementedError


def update_index(job_folder: str, index_content: str) -> None:
    # TODO (T029):
    # 1. os.makedirs(job_folder, exist_ok=True)
    # 2. Write index_content to {job_folder}/Index.md (utf-8)
    raise NotImplementedError


def load_existing_jobs(job_folder: str) -> list[dict]:
    # TODO (T029):
    # 1. If not os.path.isdir(job_folder), return []
    # 2. glob.glob(os.path.join(job_folder, "*.md"))
    # 3. For each file (skip Index.md):
    #    a. slug = filename without .md
    #    b. Read file content (utf-8)
    #    c. Parse YAML frontmatter with re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    #    d. For each "key: value" line, store in dict; strip quotes from value
    #    e. Add "slug": slug to dict
    #    f. Append to jobs list
    # 4. Return jobs list
    raise NotImplementedError

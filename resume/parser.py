import json
import os
from datetime import date

import pdfplumber

from resume.profile import Profile

_CACHE_FILENAME = "profile-cache.json"


def load_profile_cache(job_folder: str) -> Profile | None:
    """Return cached Profile from Obsidian vault, or None if not found."""
    path = os.path.join(job_folder, _CACHE_FILENAME)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return Profile(raw_text=data["raw_text"], pdf_path=data["pdf_path"])
    except Exception:
        return None


def save_profile_cache(profile: Profile, job_folder: str) -> None:
    """Persist Profile to Obsidian vault as a JSON cache file."""
    os.makedirs(job_folder, exist_ok=True)
    path = os.path.join(job_folder, _CACHE_FILENAME)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"raw_text": profile.raw_text, "pdf_path": profile.pdf_path}, f, ensure_ascii=False, indent=2)


def save_profile_note(profile: Profile, job_folder: str) -> None:
    """Write a human-readable Profile.md to the Obsidian vault (idempotent)."""
    os.makedirs(job_folder, exist_ok=True)
    note_path = os.path.join(job_folder, "Profile.md")
    name = os.path.splitext(os.path.basename(profile.pdf_path))[0]
    # Extract a clean summary from the first few non-empty lines
    lines = [l for l in profile.raw_text.splitlines() if l.strip()]
    header_lines = "\n".join(lines[:5]) if lines else ""
    with open(note_path, "w", encoding="utf-8") as f:
        f.write(f"---\ntype: profile\nupdated: {date.today()}\n---\n\n")
        f.write(f"# {name}\n\n")
        if header_lines:
            f.write(f"{header_lines}\n\n")
        f.write("## Full Text\n\n")
        f.write(f"```\n{profile.raw_text}\n```\n")


def parse_pdf(pdf_path: str) -> Profile:
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(
            f"[ERROR] PDF not found: {pdf_path} — check the file exists and the path is correct"
        )

    pages: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")

    raw_text = "\n\n".join(pages).strip()

    if not raw_text:
        raise ValueError(
            "[ERROR] PDF produced no extractable text. The file may be image-only (scanned). Use a text-layer PDF."
        )

    return Profile(raw_text=raw_text, pdf_path=os.path.abspath(pdf_path))

import json
import os
import re
from datetime import date

import pdfplumber

from llm.base import BaseLLM
from resume.profile import Profile

_KEYWORDS_PROMPT = (
    "You are a resume parser. Given the resume text below, extract the following information "
    "and respond ONLY with a valid JSON object containing these exact fields: "
    '"role" (string — the candidate\'s main job title in English, e.g. "fullstack developer"), '
    '"seniority" (string — one of: junior, mid, senior, lead, staff, principal), '
    '"skills" (array of 6-10 lowercase technology/tool names, most relevant first, '
    'e.g. ["nodejs", "react", "typescript", "postgresql"]). '
    "No markdown, no extra text outside the JSON object."
)

_CACHE_FILENAME = "profile-cache.json"


def load_profile_cache(job_folder: str) -> Profile | None:
    """Return cached Profile from Obsidian vault, or None if not found."""
    path = os.path.join(job_folder, _CACHE_FILENAME)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return Profile(
            raw_text=data["raw_text"],
            pdf_path=data["pdf_path"],
            role=data.get("role", ""),
            seniority=data.get("seniority", ""),
            skills=data.get("skills", []),
        )
    except Exception:
        return None


def save_profile_cache(profile: Profile, job_folder: str) -> None:
    """Persist Profile to Obsidian vault as a JSON cache file."""
    os.makedirs(job_folder, exist_ok=True)
    path = os.path.join(job_folder, _CACHE_FILENAME)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "raw_text": profile.raw_text,
                "pdf_path": profile.pdf_path,
                "role": profile.role,
                "seniority": profile.seniority,
                "skills": profile.skills,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )


def extract_profile_keywords(profile: Profile, llm: BaseLLM) -> Profile:
    """Use the LLM to extract role, seniority and skills from the resume text.

    Returns a new Profile with the keyword fields populated.
    The raw_text and pdf_path are preserved unchanged.
    """
    raw = llm.chat(system=_KEYWORDS_PROMPT, user=f"RESUME:\n{profile.raw_text}")

    data = None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
            except json.JSONDecodeError:
                data = None

    if not data:
        return profile  # fallback: leave fields empty, queries will use defaults

    return Profile(
        raw_text=profile.raw_text,
        pdf_path=profile.pdf_path,
        role=str(data.get("role", "")).lower().strip(),
        seniority=str(data.get("seniority", "")).lower().strip(),
        skills=[str(s).lower().strip() for s in data.get("skills", []) if s],
    )


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

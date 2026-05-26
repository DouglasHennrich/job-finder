from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from llm.base import BaseLLM
from resume.profile import Profile
from scrapers.base import Job

_SYSTEM_PROMPT = (
    "You are an expert technical recruiter evaluating a candidate's fit for a software engineering position.\n\n"
    "## Scoring rubric (stack-first)\n"
    "80-100: >=80% of required technical skills present; seniority aligned (+-1 level); missing skills are minor or quickly learnable.\n"
    "60-79: 50-79% of required skills present OR seniority off by 1 level; clear technical fit with notable but addressable gaps.\n"
    "40-59: 25-49% of required skills OR seniority off by 2 levels; partial fit, significant gaps but some transferable experience.\n"
    "0-39: <25% of required skills OR completely wrong domain or stack.\n\n"
    "## Language/technology rule\n"
    "If a programming language or framework is explicitly REQUIRED by the job and the candidate lacks it, cap the score at 50. "
    "If it is preferred or nice-to-have only, apply a minor deduction.\n\n"
    "## Output format\n"
    "Respond ONLY with a valid JSON object with these exact fields:\n"
    '"score" (integer 0-100), '
    '"justification" (string in Brazilian Portuguese, exactly 3 sentences: '
    "1st — main reason for the score; "
    "2nd — most critical gap or risk; "
    '3rd — objective recommendation starting with "Vale candidatar" or "Evitar"), '
    '"matching_skills" (array of up to 5 lowercase concrete technology names, most relevant first; exclude soft skills and generic tools like git or agile), '
    '"missing_skills" (array of up to 5 lowercase concrete technology names required or strongly preferred by the job; exclude soft skills).'
)


@dataclass
class JobAnalysis:
    score: int
    tier: str
    justification: str
    matching_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)


def _derive_tier(score: int) -> str:
    if score >= 80:
        return "🔥 Must Apply"
    if score >= 60:
        return "✅ Good Fit"
    if score >= 40:
        return "🤔 Maybe"
    return "❌ Skip"


def analyze(job: Job, profile: Profile, llm: BaseLLM) -> JobAnalysis:
    profile_lines = []
    if profile.role:
        profile_lines.append(f"Role: {profile.role}")
    if profile.seniority:
        profile_lines.append(f"Seniority: {profile.seniority}")
    if profile.skills:
        profile_lines.append(f"Key skills: {', '.join(profile.skills)}")

    candidate_block = (
        "CANDIDATE PROFILE:\n" + "\n".join(profile_lines) + "\n\n"
        if profile_lines
        else ""
    )

    user_prompt = (
        f"{candidate_block}"
        f"RESUME (full text for context):\n{profile.raw_text}\n\n"
        f"JOB:\n"
        f"Title: {job.title}\n"
        f"Company: {job.company}\n"
        f"Location: {job.location}\n"
        f"Description: {job.description}"
    )

    raw_response = llm.chat(system=_SYSTEM_PROMPT, user=user_prompt, json_mode=True)

    # Stage 1: direct parse
    data = None
    try:
        data = json.loads(raw_response)
    except json.JSONDecodeError:
        data = None

    # Stage 2: extract JSON object via regex
    if data is None:
        match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
            except json.JSONDecodeError:
                data = None

    # Stage 3: parse failure sentinel
    if data is None:
        return JobAnalysis(score=0, tier="❌ Skip", justification="[parse error]", matching_skills=[], missing_skills=[])

    score = max(0, min(100, int(data.get("score", 0))))
    tier = _derive_tier(score)
    return JobAnalysis(
        score=score,
        tier=tier,
        justification=data.get("justification", ""),
        matching_skills=data.get("matching_skills", []),
        missing_skills=data.get("missing_skills", []),
    )

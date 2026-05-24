from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from llm.base import BaseLLM
from resume.profile import Profile
from scrapers.base import Job

_SYSTEM_PROMPT = (
    "You are an expert technical recruiter. Given a resume and a job description, "
    "evaluate the candidate's fit for the position. "
    "Respond ONLY with a valid JSON object containing these exact fields: "
    '"score" (integer 0-100), '
    '"tier" (string), '
    '"justification" (string in Brazilian Portuguese, 2-3 sentences), '
    '"matching_skills" (array of strings), '
    '"missing_skills" (array of strings). '
    "No markdown, no extra text outside the JSON object."
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
    user_prompt = (
        f"RESUME:\n{profile.raw_text}\n\n"
        f"JOB:\n"
        f"Title: {job.title}\n"
        f"Company: {job.company}\n"
        f"Location: {job.location}\n"
        f"Description: {job.description}"
    )

    raw_response = llm.chat(system=_SYSTEM_PROMPT, user=user_prompt)

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

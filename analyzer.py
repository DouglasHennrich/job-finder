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
    # TODO (T017): implement tier mapping:
    # score >= 80 → "🔥 Must Apply"
    # score >= 60 → "✅ Good Fit"
    # score >= 40 → "🤔 Maybe"
    # score  < 40 → "❌ Skip"
    raise NotImplementedError


def analyze(job: Job, profile: Profile, llm: BaseLLM) -> JobAnalysis:
    # TODO (T017):
    # 1. Build user_prompt with profile.raw_text, job.title, job.company,
    #    job.location, job.description
    # 2. Call llm.chat(system=_SYSTEM_PROMPT, user=user_prompt) → raw_response
    # 3. Stage 1: try json.loads(raw_response); if JSONDecodeError → data = None
    # 4. Stage 2: if data is None, try re.search(r'\{.*\}', raw_response, re.DOTALL);
    #    if match, try json.loads(match.group()); if JSONDecodeError → data = None
    # 5. Stage 3: if data is None, return sentinel JobAnalysis(score=0, tier="❌ Skip",
    #    justification="[parse error]", matching_skills=[], missing_skills=[])
    # 6. Clamp score: max(0, min(100, int(data.get("score", 0))))
    # 7. Derive tier from score via _derive_tier() (authoritative override)
    # 8. Return JobAnalysis(score, tier, justification, matching_skills, missing_skills)
    raise NotImplementedError

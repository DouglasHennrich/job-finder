from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class Config:
    llm_provider: str
    copilot_token: str
    copilot_model: str
    ollama_base_url: str
    ollama_model: str
    serper_api_key: str
    obsidian_vault_path: str
    job_finder_folder: str
    obsidian_job_folder: str
    obsidian_notes_folder: str
    min_score: int
    max_jobs_per_source: int

    @classmethod
    def load(cls) -> "Config":
        load_dotenv()

        llm_provider = os.getenv("LLM_PROVIDER", "copilot")
        copilot_model = os.getenv("COPILOT_MODEL", "claude-sonnet-4.6")
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        ollama_model = os.getenv("OLLAMA_MODEL", "qwen3.6:27b")
        serper_api_key = os.getenv("SERPER_API_KEY", "")
        job_finder_folder = os.getenv("JOB_FINDER_FOLDER", "Job Finder")
        min_score = int(os.getenv("MIN_SCORE", "60"))
        max_jobs_per_source = int(os.getenv("MAX_JOBS_PER_SOURCE", "20"))
        obsidian_vault_path = os.getenv("OBSIDIAN_VAULT_PATH", "")

        copilot_token = os.getenv("COPILOT_TOKEN", "")
        if not copilot_token:
            result = subprocess.run(
                ["gh", "auth", "token"], capture_output=True, text=True
            )
            if result.returncode == 0:
                copilot_token = result.stdout.strip()

        if not os.path.exists(obsidian_vault_path):
            raise ValueError(
                f"[ERROR] Obsidian vault not found: {obsidian_vault_path} — set OBSIDIAN_VAULT_PATH correctly"
            )

        if llm_provider not in ("copilot", "ollama"):
            raise ValueError(
                f'[ERROR] LLM_PROVIDER must be "copilot" or "ollama", got: "{llm_provider}"'
            )

        if llm_provider == "copilot" and not copilot_token:
            raise RuntimeError(
                '[ERROR] Could not resolve COPILOT_TOKEN. Run "gh auth login" or set COPILOT_TOKEN in .env'
            )

        obsidian_job_folder = os.path.join(obsidian_vault_path, job_finder_folder)
        obsidian_notes_folder = os.path.join(obsidian_job_folder, "jobs")

        return cls(
            llm_provider=llm_provider,
            copilot_token=copilot_token,
            copilot_model=copilot_model,
            ollama_base_url=ollama_base_url,
            ollama_model=ollama_model,
            serper_api_key=serper_api_key,
            obsidian_vault_path=obsidian_vault_path,
            job_finder_folder=job_finder_folder,
            obsidian_job_folder=obsidian_job_folder,
            obsidian_notes_folder=obsidian_notes_folder,
            min_score=min_score,
            max_jobs_per_source=max_jobs_per_source,
        )

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
    min_score: int
    max_jobs_per_source: int

    @classmethod
    def load(cls) -> "Config":
        # TODO (T007):
        # 1. Call load_dotenv()
        # 2. Read all env vars with os.getenv(), applying defaults:
        #    LLM_PROVIDER default "copilot", COPILOT_MODEL default "claude-sonnet-4-6",
        #    OLLAMA_BASE_URL default "http://localhost:11434/v1", OLLAMA_MODEL default "llama3",
        #    SERPER_API_KEY default "", JOB_FINDER_FOLDER default "Job Finder",
        #    MIN_SCORE default "60" (cast to int), MAX_JOBS_PER_SOURCE default "20" (cast to int)
        # 3. Auto-detect COPILOT_TOKEN: if os.getenv("COPILOT_TOKEN","") is empty,
        #    run subprocess.run(["gh","auth","token"], capture_output=True, text=True)
        #    and use result.stdout.strip() if returncode == 0
        # 4. Validate OBSIDIAN_VAULT_PATH exists on disk; raise ValueError with
        #    "[ERROR] Obsidian vault not found: {path} — set OBSIDIAN_VAULT_PATH correctly"
        # 5. Validate llm_provider in ("copilot","ollama"); raise ValueError with
        #    '[ERROR] LLM_PROVIDER must be "copilot" or "ollama", got: "{value}"'
        # 6. If llm_provider=="copilot" and token still empty, raise RuntimeError with
        #    '[ERROR] Could not resolve COPILOT_TOKEN. Run "gh auth login" or set COPILOT_TOKEN in .env'
        # 7. Derive obsidian_job_folder = os.path.join(obsidian_vault_path, job_finder_folder)
        # 8. Return cls(...) with all fields
        raise NotImplementedError

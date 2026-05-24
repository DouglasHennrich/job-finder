from __future__ import annotations

import sys
import time
from datetime import datetime

from analyzer import analyze
from config import Config
from llm import build_llm
from obsidian.templates import render_index, render_job_note
from obsidian.writer import (
    load_existing_jobs,
    note_exists,
    save_note,
    slugify_job,
    update_index,
)
from resume.parser import parse_pdf
from scrapers.google_jobs import GoogleJobsScraper
from scrapers.himalayas import HimalayasScraper
from scrapers.indeed import IndeedScraper

_QUERIES = [
    "senior nodejs nestjs typescript remote",
    "desenvolvedor senior nodejs nestjs typescript remoto",
]


def main() -> None:
    # TODO (T035): Implement full pipeline orchestration:
    # 1. Print "[JOB FINDER] Starting run — {timestamp}"
    # 2. Config.load() — sys.exit(1) on ValueError/RuntimeError
    # 3. build_llm(cfg) — sys.exit(1) on RuntimeError
    # 4. Print "[LLM] Provider: {provider} ({model})"
    # 5. parse_pdf("Douglas Hennrich.pdf") — sys.exit(1) on FileNotFoundError/ValueError
    # 6. Print "[RESUME] Loaded profile from: ..."
    # 7. Instantiate HimalayasScraper(), GoogleJobsScraper(api_key=...), IndeedScraper()
    # 8. For each scraper × each query: scraper.fetch(query, max_jobs_per_source)
    #    log [SCRAPER] lines per contracts/cli.md
    # 9. In-memory dedup: seen_slugs set → unique_pairs list; log [DEDUP] line
    # 10. Vault dedup: note_exists() per slug → new_pairs list; log [DEDUP] line
    # 11. For each (slug, job) in new_pairs:
    #     a. analysis = analyze(job, profile, llm); log [SCORE] line
    #     b. If score >= cfg.min_score: render_job_note + save_note; log [SAVED] line
    #     c. Else: increment skipped_score
    # 12. load_existing_jobs + render_index + update_index; log [INDEX] line
    # 13. Print summary: "Done in Xs.\nSaved: N | Skipped (dup): N | Skipped (score): N | Errors: N source(s)"
    # 14. sys.exit(0)
    raise NotImplementedError


if __name__ == "__main__":
    main()

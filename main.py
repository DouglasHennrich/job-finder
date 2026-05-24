from __future__ import annotations

import sys
import time
from datetime import datetime

import openai

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
from resume.parser import load_profile_cache, parse_pdf, save_profile_cache, save_profile_note
from scrapers.base import Job
from scrapers.google_jobs import GoogleJobsScraper
from scrapers.himalayas import HimalayasScraper
from scrapers.indeed import IndeedScraper


def _build_queries() -> list[str]:
    """Fixed query set targeting Backend/FullStack Node.js remote/LATAM roles."""
    return [
        "senior fullstack developer nodejs react remote",
        "desenvolvedor fullstack senior nodejs react remoto",
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
    print(f"[JOB FINDER] Starting run — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    start = time.time()

    try:
        cfg = Config.load()
    except (ValueError, RuntimeError) as e:
        print(e)
        sys.exit(1)

    try:
        llm = build_llm(cfg)
    except RuntimeError as e:
        print(e)
        sys.exit(1)

    print(
        f"[LLM] Provider: {cfg.llm_provider} "
        f"({cfg.copilot_model if cfg.llm_provider == 'copilot' else cfg.ollama_model})"
    )

    try:
        profile = load_profile_cache(cfg.obsidian_job_folder)
        if profile:
            print(f"[RESUME] Loaded profile from cache: {cfg.obsidian_job_folder}")
        else:
            profile = parse_pdf("Douglas Hennrich.pdf")
            save_profile_cache(profile, cfg.obsidian_job_folder)
            print(f"[RESUME] Parsed PDF and cached profile: {profile.pdf_path}")
        save_profile_note(profile, cfg.obsidian_job_folder)
    except (FileNotFoundError, ValueError) as e:
        print(e)
        sys.exit(1)

    queries = _build_queries()
    print(f"[QUERIES] {queries}")

    scrapers = [
        HimalayasScraper(),
        GoogleJobsScraper(api_key=cfg.serper_api_key),
        IndeedScraper(),
    ]

    all_jobs: list[Job] = []
    scraper_errors = 0

    for scraper in scrapers:
        for query in queries:
            try:
                jobs = scraper.fetch(query, cfg.max_jobs_per_source)
            except Exception as e:
                print(f"[ERROR] {scraper.__class__.__name__} | '{query}': {e}")
                scraper_errors += 1
                continue
            print(f"[SCRAPER] {scraper.__class__.__name__} | '{query}' → {len(jobs)} jobs")
            all_jobs.extend(jobs)

    seen_slugs: set[str] = set()
    unique_pairs: list[tuple[str, Job]] = []
    for job in all_jobs:
        slug = slugify_job(job.title, job.company)
        if slug not in seen_slugs:
            seen_slugs.add(slug)
            unique_pairs.append((slug, job))
    skipped_dup = len(all_jobs) - len(unique_pairs)
    print(f"[DEDUP] In-memory: {skipped_dup} duplicates removed, {len(unique_pairs)} unique jobs")

    new_pairs: list[tuple[str, Job]] = []
    for slug, job in unique_pairs:
        if note_exists(slug, cfg.obsidian_job_folder):
            skipped_dup += 1
        else:
            new_pairs.append((slug, job))
    print(
        f"[DEDUP] Vault: {len(unique_pairs) - len(new_pairs)} already saved, "
        f"{len(new_pairs)} new jobs to process"
    )

    saved = 0
    skipped_score = 0
    rate_limited = False
    for slug, job in new_pairs:
        try:
            analysis = analyze(job, profile, llm)
        except openai.RateLimitError as e:
            print(f"[WARN] LLM rate limit reached — stopping scoring early. ({e})")
            rate_limited = True
            break
        except Exception as e:
            print(f"[ERROR] LLM error scoring '{job.title}': {e}")
            skipped_score += 1
            continue
        print(f"[SCORE] {job.title} @ {job.company} → {analysis.score}/100 {analysis.tier}")
        if analysis.score >= cfg.min_score:
            date_str = datetime.now().strftime("%Y-%m-%d")
            content = render_job_note(job, analysis, date_str)
            path = save_note(slug, content, cfg.obsidian_job_folder)
            print(f"[SAVED] {slug}.md → {path}")
            saved += 1
        else:
            skipped_score += 1

    existing = load_existing_jobs(cfg.obsidian_job_folder)
    index_content = render_index(existing)
    update_index(cfg.obsidian_job_folder, index_content)
    print(f"[INDEX] Updated Index.md with {len(existing)} jobs")

    elapsed = time.time() - start
    rate_limit_note = " | WARN: LLM rate limit — scoring incomplete" if rate_limited else ""
    print(
        f"Done in {elapsed:.1f}s.\n"
        f"Saved: {saved} | Skipped (dup): {skipped_dup} | "
        f"Skipped (score): {skipped_score} | Errors: {scraper_errors} source(s)"
        f"{rate_limit_note}"
    )
    sys.exit(0)


if __name__ == "__main__":
    main()

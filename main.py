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
    load_discarded_slugs,
    load_existing_jobs,
    mark_discarded,
    note_exists,
    save_note,
    slugify_job,
    update_index,
)
from resume.parser import load_profile_cache, parse_pdf, save_profile_cache, save_profile_note
from scrapers.base import Job
from scrapers.google_jobs import GoogleJobsScraper
from scrapers.himalayas import HimalayasScraper


def _build_queries() -> list[str]:
    """Generic queries for scrapers that accept free-text search (e.g. Himalayas)."""
    return [
        "senior fullstack developer nodejs react remote",
        "desenvolvedor fullstack senior nodejs react remoto",
    ]


def _build_serper_queries() -> list[str]:
    """Pre-formatted Serper site-search queries for LinkedIn, Inhire and Indeed."""
    sites = "(site:inhire.app OR site:linkedin.com/jobs OR site:indeed.com)"
    return [
        f'{sites} ("full stack") ("node") ("react") remote',
        f'{sites} ("full stack") ("nodejs") ("react") remoto',
    ]


def main() -> None:
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

    model_name = cfg.copilot_model if cfg.llm_provider == "copilot" else cfg.ollama_model
    print(f"[LLM] Provider: {cfg.llm_provider} ({model_name})")

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
    serper_queries = _build_serper_queries()
    print(f"[QUERIES] generic={queries}")
    print(f"[QUERIES] serper={serper_queries}")

    scraper_pairs: list[tuple] = [
        (HimalayasScraper(), queries),
        (GoogleJobsScraper(api_key=cfg.serper_api_key), serper_queries),
    ]

    all_jobs: list[Job] = []
    scraper_errors = 0

    for scraper, scraper_queries in scraper_pairs:
        for query in scraper_queries:
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

    discarded_slugs = load_discarded_slugs(cfg.obsidian_notes_folder)

    new_pairs: list[tuple[str, Job]] = []
    for slug, job in unique_pairs:
        if note_exists(slug, cfg.obsidian_notes_folder):
            skipped_dup += 1
        elif slug in discarded_slugs:
            skipped_dup += 1
        else:
            new_pairs.append((slug, job))
    print(
        f"[DEDUP] Vault: {len(unique_pairs) - len(new_pairs)} already seen "
        f"({len(discarded_slugs)} rejected cache), {len(new_pairs)} new jobs to process"
    )

    saved = 0
    skipped_score = 0
    rate_limited = False
    total = len(new_pairs)
    for i, (slug, job) in enumerate(new_pairs):
        print(f"[SCORE] ({i + 1}/{total}) Analisando: {job.title} @ {job.company} ...")
        job_start = time.time()
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
        job_elapsed = time.time() - job_start
        print(f"[SCORE] ({i + 1}/{total}) {job.title} @ {job.company} → {analysis.score}/100 {analysis.tier} [{job_elapsed:.1f}s]")
        if analysis.score >= cfg.min_score:
            date_str = datetime.now().strftime("%Y-%m-%d")
            content = render_job_note(job, analysis, date_str)
            path = save_note(slug, content, cfg.obsidian_notes_folder)
            print(f"[SAVED] {slug}.md → {path}")
            saved += 1
        else:
            mark_discarded(slug, cfg.obsidian_notes_folder)
            skipped_score += 1

    existing = load_existing_jobs(cfg.obsidian_notes_folder)
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

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
from resume.parser import extract_profile_keywords, load_profile_cache, parse_pdf, save_profile_cache, save_profile_note
from resume.profile import Profile
from scrapers.base import Job
from scrapers.capgemini import CapgeminiScraper
from scrapers.google_jobs import GoogleJobsScraper
from scrapers.himalayas import HimalayasScraper
from scrapers.linkedin import LinkedInScraper
from scrapers.solides import SolidesScraper


_SENIORITY_WORDS = {"junior", "mid", "senior", "lead", "staff", "principal", "pleno"}

_FALLBACK_QUERIES = [
    "fullstack developer nodejs react remote",
    "desenvolvedor fullstack nodejs react remoto",
]
_FALLBACK_SERPER_QUERIES = [
    '(site:inhire.app OR site:linkedin.com/jobs OR site:indeed.com) ("fullstack" OR "full stack developer") ("nodejs") ("react") remote',
    '(site:inhire.app OR site:linkedin.com/jobs OR site:indeed.com) ("fullstack" OR "full stack developer") ("nodejs") ("react") remoto',
]


def _strip_seniority(role: str) -> str:
    """Remove seniority prefix words from a role string (e.g. 'senior fullstack engineer' → 'fullstack engineer')."""
    words = role.lower().split()
    return " ".join(w for w in words if w not in _SENIORITY_WORDS).strip()


def _role_or_term(role: str) -> str:
    """Build a Serper OR term from the role without seniority.

    'senior fullstack engineer' → '("fullstack" OR "fullstack engineer")'
    """
    stripped = _strip_seniority(role)
    words = stripped.split()
    if not stripped:
        return '("fullstack")'
    if len(words) == 1:
        return f'("{stripped}")'
    short = words[0]  # first meaningful word, e.g. "fullstack"
    return f'("{short}" OR "{stripped}")'


def _build_queries(profile: Profile) -> list[str]:
    """Build generic queries from the resume profile (Himalayas, LinkedIn, etc.).

    Seniority is intentionally excluded — it is filtered at scoring time by the LLM.
    Falls back to hardcoded defaults if keywords were not extracted.
    """
    if not profile.role and not profile.skills:
        return _FALLBACK_QUERIES
    role = _strip_seniority(profile.role) if profile.role else "fullstack developer"
    top_skills = " ".join(profile.skills[:3]) if profile.skills else "nodejs react"
    return [
        f"{role} {top_skills} remote",
        f"{role} {top_skills} remoto",
    ]


def _build_serper_queries(profile: Profile) -> list[str]:
    """Build Serper site-search queries from the resume profile.

    Role is expanded as an OR term (short form OR full form) to cast a wider net.
    Seniority is intentionally excluded — filtered at scoring time by the LLM.
    Falls back to hardcoded defaults if keywords were not extracted.
    """
    if not profile.role and not profile.skills:
        return _FALLBACK_SERPER_QUERIES
    sites = "(site:inhire.app OR site:linkedin.com/jobs OR site:indeed.com)"
    role_term = _role_or_term(profile.role) if profile.role else '("fullstack")'
    skill_terms = " ".join(f'("{s}")' for s in profile.skills[:3]) if profile.skills else '("nodejs") ("react")'
    return [
        f"{sites} {role_term} {skill_terms} remote",
        f"{sites} {role_term} {skill_terms} remoto",
    ]


def _build_solides_queries(profile: Profile) -> list[str]:
    """Build title-only queries for Solides.

    The Solides API filters by job title — long free-text queries with skills
    or location keywords return 0 results. We send only the role (stripped of
    seniority) plus a Portuguese variant to maximise coverage.
    """
    stripped = _strip_seniority(profile.role) if profile.role else ""
    if not stripped:
        return ["fullstack developer", "desenvolvedor fullstack"]
    return [stripped, f"desenvolvedor {stripped.split()[0]}"]


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
            if not profile.role and not profile.skills:
                print("[RESUME] Cache missing keywords — extracting via LLM...")
                profile = extract_profile_keywords(profile, llm)
                save_profile_cache(profile, cfg.obsidian_job_folder)
                print(f"[RESUME] Keywords extracted and cached: role={profile.role!r}, seniority={profile.seniority!r}, skills={profile.skills}")
        else:
            profile = parse_pdf("Douglas Hennrich.pdf")
            print(f"[RESUME] Parsed PDF: {profile.pdf_path}")
            print("[RESUME] Extracting keywords via LLM...")
            profile = extract_profile_keywords(profile, llm)
            save_profile_cache(profile, cfg.obsidian_job_folder)
            print(f"[RESUME] Keywords extracted and cached: role={profile.role!r}, seniority={profile.seniority!r}, skills={profile.skills}")
        save_profile_note(profile, cfg.obsidian_job_folder)
    except (FileNotFoundError, ValueError) as e:
        print(e)
        sys.exit(1)

    queries = _build_queries(profile)
    serper_queries = _build_serper_queries(profile)
    solides_queries = _build_solides_queries(profile)
    print(f"[QUERIES] generic={queries}")
    print(f"[QUERIES] serper={serper_queries}")
    print(f"[QUERIES] solides={solides_queries}")

    scraper_pairs: list[tuple] = [
        (HimalayasScraper(), queries),
        (GoogleJobsScraper(api_key=cfg.serper_api_key), serper_queries),
        (LinkedInScraper(), queries),
        (SolidesScraper(), solides_queries),
        (CapgeminiScraper(), queries),
    ]
    print("[SCRAPER] Registered: HimalayasScraper, GoogleJobsScraper, LinkedInScraper, SolidesScraper, CapgeminiScraper")

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

    discarded_slugs = load_discarded_slugs(cfg.obsidian_job_folder)

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
            mark_discarded(
                slug,
                cfg.obsidian_job_folder,
                title=job.title,
                company=job.company,
                score=analysis.score,
                tier=analysis.tier,
                source=job.source,
                url=job.url,
            )
            skipped_score += 1

    active_providers = sorted({scraper.provider_name for scraper, _ in scraper_pairs})
    existing = load_existing_jobs(cfg.obsidian_notes_folder)
    index_content = render_index(existing, discarded_count=len(discarded_slugs), providers=active_providers)
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

from __future__ import annotations

import logging

import requests

from scrapers.base import BaseScraper, Job

logger = logging.getLogger(__name__)

# REST API used by the Capgemini job-search front-end (discovered via HAR capture).
# The page at capgemini.com/careers/.../job-search/ is a React SPA — it calls this
# Azure-hosted endpoint directly; plain requests.get on the WordPress URL returns the
# JS shell only (no job listings).
_API_URL = "https://cg-jobstream-api.azurewebsites.net/api/job-search"


class CapgeminiScraper(BaseScraper):
    """Capgemini public job board scraper using the cg-jobstream REST API."""

    def fetch(self, query: str, max_results: int) -> list[Job]:
        try:
            response = requests.get(
                _API_URL,
                params={"page": 1, "size": max_results, "search": query},
                timeout=15,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            logger.warning("[CapgeminiScraper] fetch failed: %s", exc)
            return []

        jobs: list[Job] = []
        for item in payload.get("data", [])[:max_results]:
            title = item.get("title", "").strip()
            if not title:
                continue
            url = item.get("apply_job_url") or item.get("wp_url") or ""
            location = item.get("location", "") or ""
            description = item.get("description_stripped", "") or ""
            jobs.append(
                Job(
                    title=title,
                    company="Capgemini",
                    location=location,
                    description=description[:2000],
                    url=url,
                    source="capgemini",
                )
            )
        return jobs

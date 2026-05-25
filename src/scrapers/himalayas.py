from __future__ import annotations

import logging

import requests

from scrapers.base import BaseScraper, Job

logger = logging.getLogger(__name__)

_BASE_URL = "https://himalayas.app/jobs/api"


class HimalayasScraper(BaseScraper):
    """Scraper for Himalayas.app public REST API."""

    provider_name = "himalayas"

    def fetch(self, query: str, max_results: int) -> list[Job]:
        try:
            resp = requests.get(
                _BASE_URL,
                params={"q": query, "limit": max_results},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            logger.warning(f"Himalayas request failed: {e}")
            return []

        jobs: list[Job] = []
        for item in data.get("jobs", []):
            # Himalayas is a remote-only platform; the API may not include a `remote`
            # boolean, but guard against any future non-remote entries explicitly.
            if item.get("remote") is False:
                continue
            title = item.get("title", "")
            company = item.get("companyName", "")
            location = ", ".join(item.get("locationRestrictions", [])) or "Remote"
            description = (item.get("description") or "")[:2000]
            url = item.get("applicationLink", "")
            posted_date = str(item.get("pubDate", "")) or None
            jobs.append(
                Job(
                    title=title,
                    company=company,
                    location=location,
                    description=description,
                    url=url,
                    source="himalayas",
                    salary=None,
                    posted_date=posted_date,
                )
            )
        return jobs

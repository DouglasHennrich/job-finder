from __future__ import annotations

import logging
import re

import requests

from scrapers.base import BaseScraper, Job

logger = logging.getLogger(__name__)

_BASE_URL = "https://apigw.solides.com.br/jobs/v3/portal-vacancies-new"
_HEADERS = {
    "Origin": "https://vagas.solides.com.br",
    "Referer": "https://vagas.solides.com.br/",
}


class SolidesScraper(BaseScraper):
    """Scraper for Solides public REST API."""

    provider_name = "solides"

    def fetch(self, query: str, max_results: int) -> list[Job]:
        try:
            resp = requests.get(
                _BASE_URL,
                params={"title": query, "locations": "", "take": max_results, "page": 1},
                headers=_HEADERS,
                timeout=15,
            )
            resp.raise_for_status()
            items = resp.json()["data"]["data"]

            # Remote filter: keep home-office items; fall back to all if none pass
            remote_items = [
                item for item in items
                if item.get("homeOffice") is True or item.get("jobType") == "home-office"
            ]
            if remote_items:
                items = remote_items

            jobs: list[Job] = []
            for item in items:
                title = item.get("title", "")
                if not title:
                    continue
                url = item.get("redirectLink", "")
                if not url:
                    continue

                company = item.get("companyName", "")

                if item.get("homeOffice"):
                    location = "Remote"
                else:
                    city = item.get("city") or {}
                    state = item.get("state") or {}
                    location = f"{city.get('name', '')}, {state.get('code', '')}"

                posted_date = item.get("createdAt")

                raw_desc = item.get("description", "") or ""
                description = re.sub(r"<[^>]+>", "", raw_desc)[:2000]

                jobs.append(
                    Job(
                        title=title,
                        company=company,
                        location=location,
                        description=description,
                        url=url,
                        source="solides",
                        salary=None,
                        posted_date=posted_date,
                    )
                )
            return jobs
        except Exception as e:
            logging.warning(f"[SolidesScraper] {e}")
            return []

from __future__ import annotations

import logging

import requests

from scrapers.base import BaseScraper, Job

logger = logging.getLogger(__name__)

_BASE_URL = "https://himalayas.app/jobs/api"


class HimalayasScraper(BaseScraper):
    """Scraper for Himalayas.app public REST API."""

    def fetch(self, query: str, max_results: int) -> list[Job]:
        # TODO (T021):
        # 1. GET _BASE_URL with params {"q": query, "limit": max_results}, timeout=15
        # 2. Wrap in try/except requests.RequestException → log warning, return []
        # 3. resp.raise_for_status(); data = resp.json()
        # 4. For each item in data.get("jobs", []):
        #    - Skip if not item.get("remote")
        #    - Map: title, company=item["company"]["name"], location from locationRestrictions,
        #      description truncated to 2000 chars, url=item["applicationLink"],
        #      source="himalayas", salary, posted_date
        #    - Append Job(...)
        # 5. Return jobs list
        raise NotImplementedError

from __future__ import annotations

import logging

import requests

from scrapers.base import BaseScraper, Job

logger = logging.getLogger(__name__)

_SERPER_SEARCH_URL = "https://google.serper.dev/search"


class GoogleJobsScraper(BaseScraper):
    """Scraper for job listings via Google site-search (Serper.dev /search endpoint).

    Receives a pre-formatted query (e.g. from _build_serper_queries in main.py) that
    already contains site: operators. Results are parsed with site-specific logic keyed
    by URL domain: inhire.app, linkedin.com, indeed.com.
    """

    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key

    def fetch(self, query: str, max_results: int) -> list[Job]:
        if not self.api_key:
            logger.warning("GoogleJobsScraper: SERPER_API_KEY not set — skipping")
            return []
        try:
            return self._fetch_serper_search(query, max_results)
        except Exception as e:
            logger.warning(f"GoogleJobsScraper Serper search failed: {e}")
            return []

    def _fetch_serper_search(self, query: str, max_results: int) -> list[Job]:
        resp = requests.post(
            _SERPER_SEARCH_URL,
            json={"q": query, "gl": "br", "hl": "pt-br", "num": min(max_results, 10)},
            headers={"X-API-KEY": self.api_key, "Content-Type": "application/json"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        jobs: list[Job] = []
        for item in data.get("organic", [])[:max_results]:
            job = self._parse_organic_result(item)
            if job:
                jobs.append(job)
        return jobs

    def _parse_organic_result(self, item: dict) -> Job | None:
        url = item.get("link", "")
        title_raw = item.get("title", "")
        snippet = (item.get("snippet") or "")[:2000]

        if "inhire.app" in url:
            return self._parse_inhire(url, title_raw, snippet)
        if "linkedin.com" in url:
            return self._parse_linkedin(url, title_raw, snippet)
        if "indeed.com" in url:
            return self._parse_indeed(url, title_raw, snippet)
        return None

    def _parse_inhire(self, url: str, title_raw: str, snippet: str) -> Job:
        # Typical inhire title: "Senior Full Stack Developer - Company Name | inhire.app"
        clean = title_raw.split("|")[0].strip()
        parts = clean.split(" - ", 1)
        title = parts[0].strip()
        company = parts[1].strip() if len(parts) > 1 else ""
        return Job(
            title=title,
            company=company,
            location="Remote",
            description=snippet,
            url=url,
            source="inhire",
        )

    def _parse_linkedin(self, url: str, title_raw: str, snippet: str) -> Job:
        # Typical LinkedIn title: "Company hiring Job Title in Location | LinkedIn"
        # or "Job Title - Company | LinkedIn"
        clean = title_raw.split("|")[0].strip()
        title = clean
        company = ""
        if " hiring " in clean:
            parts = clean.split(" hiring ", 1)
            company = parts[0].strip()
            title = parts[1].split(" in ")[0].strip()
        elif " - " in clean:
            parts = clean.split(" - ", 1)
            title = parts[0].strip()
            company = parts[1].strip()
        return Job(
            title=title,
            company=company,
            location="Remote",
            description=snippet,
            url=url,
            source="linkedin",
        )

    def _parse_indeed(self, url: str, title_raw: str, snippet: str) -> Job:
        # Typical Indeed title: "Job Title - Company Name - Indeed"
        clean = title_raw.replace(" - Indeed", "").replace(" | Indeed", "").strip()
        parts = clean.split(" - ", 1)
        title = parts[0].strip()
        company = parts[1].strip() if len(parts) > 1 else ""
        return Job(
            title=title,
            company=company,
            location="Remote",
            description=snippet,
            url=url,
            source="indeed",
        )


from __future__ import annotations

import asyncio
import logging
import random
import urllib.parse

import requests

from scrapers.base import BaseScraper, Job

logger = logging.getLogger(__name__)

_SERPER_URL = "https://google.serper.dev/jobs"


class GoogleJobsScraper(BaseScraper):
    """Scraper for Google Jobs via Serper.dev (primary) or Playwright (fallback)."""

    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key

    def fetch(self, query: str, max_results: int) -> list[Job]:
        # TODO (T022):
        # 1. If self.api_key is non-empty: try _fetch_serper(); on any Exception,
        #    log warning and fall through to Playwright
        # 2. Call asyncio.get_event_loop().run_until_complete(_fetch_playwright(...))
        raise NotImplementedError

    def _fetch_serper(self, query: str, max_results: int) -> list[Job]:
        # TODO (T022):
        # 1. POST _SERPER_URL with json={"q":query,"gl":"br","hl":"pt-br","num":max_results},
        #    headers={"X-API-KEY": self.api_key}, timeout=15
        # 2. resp.raise_for_status(); data = resp.json()
        # 3. Map data["jobs"] items → Job(title, company, location, description[:2000],
        #    url=item["link"], source="google_jobs", posted_date=item.get("date"))
        # 4. Return jobs list
        raise NotImplementedError

    async def _fetch_playwright(self, query: str, max_results: int) -> list[Job]:
        # TODO (T022):
        # 1. Import async_playwright and stealth_async
        # 2. Launch chromium headless, apply stealth_async
        # 3. Navigate to https://www.google.com/search?q={encoded}&ibp=htl;jobs
        # 4. Sleep random.uniform(2, 4)
        # 5. query_selector_all("div[data-jiz]")
        # 6. For each card up to max_results: extract h2 (title), company el, link href
        # 7. Append Job(..., source="google_jobs"); continue on any Exception
        # 8. Close browser; return jobs
        raise NotImplementedError

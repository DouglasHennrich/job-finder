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
        if self.api_key:
            try:
                return self._fetch_serper(query, max_results)
            except Exception as e:
                logger.warning(f"GoogleJobsScraper Serper failed: {e}")
        # Playwright+stealth fallback (no API key required)
        try:
            return asyncio.run(self._fetch_playwright(query, max_results))
        except Exception as e:
            logger.warning(f"GoogleJobsScraper Playwright fallback failed: {e}")
            return []

    def _fetch_serper(self, query: str, max_results: int) -> list[Job]:
        resp = requests.post(
            _SERPER_URL,
            json={"q": query, "gl": "br", "hl": "pt-br", "num": max_results},
            headers={"X-API-KEY": self.api_key, "Content-Type": "application/json"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        jobs: list[Job] = []
        for item in data.get("jobs", [])[:max_results]:
            jobs.append(
                Job(
                    title=item.get("title", ""),
                    company=item.get("company", ""),
                    location=item.get("location", ""),
                    description=(item.get("description") or "")[:2000],
                    url=item.get("link", ""),
                    source="google_jobs",
                    posted_date=item.get("date"),
                )
            )
        return jobs

    def _fetch_remotive(self, query: str, max_results: int) -> list[Job]:
        import re as _re
        resp = requests.get(
            "https://remotive.com/api/remote-jobs",
            params={"search": query, "limit": max_results},
            timeout=15,
        )
        resp.raise_for_status()
        jobs: list[Job] = []
        for item in resp.json().get("jobs", [])[:max_results]:
            raw_desc = item.get("description", "")
            description = _re.sub(r"<[^>]+>", " ", raw_desc).strip()[:2000]
            jobs.append(
                Job(
                    title=item.get("title", ""),
                    company=item.get("company_name", ""),
                    location=item.get("candidate_required_location", "Remote"),
                    url=item.get("url", ""),
                    description=description,
                    source="remotive",
                )
            )
        return jobs

    async def _fetch_playwright(self, query: str, max_results: int) -> list[Job]:
        from playwright.async_api import async_playwright
        from playwright_stealth import Stealth

        encoded_query = urllib.parse.quote_plus(query)
        jobs: list[Job] = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await Stealth().apply_stealth_async(page)
            await page.goto(
                f"https://www.google.com/search?q={encoded_query}&ibp=htl;jobs"
            )
            await asyncio.sleep(random.uniform(2, 4))
            cards = await page.query_selector_all("div[data-jiz]")
            for card in cards[:max_results]:
                try:
                    h2 = await card.query_selector("h2")
                    title = await h2.inner_text() if h2 else ""
                    company_el = await card.query_selector("[data-company-name]")
                    company = await company_el.inner_text() if company_el else ""
                    link_el = await card.query_selector("a")
                    url = await link_el.get_attribute("href") if link_el else ""
                    jobs.append(
                        Job(
                            title=title,
                            company=company,
                            location="Remote",
                            description="",
                            url=url or "",
                            source="google_jobs",
                        )
                    )
                except Exception as card_err:
                    logger.debug(f"Card extraction error: {card_err}")
                    continue
            await browser.close()
        return jobs

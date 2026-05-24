from __future__ import annotations

import asyncio
import logging
import random
import urllib.parse

from scrapers.base import BaseScraper, Job

logger = logging.getLogger(__name__)

_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


class IndeedScraper(BaseScraper):
    """Indeed scraper using Playwright+stealth with humanised behaviour."""

    def fetch(self, query: str, max_results: int) -> list[Job]:
        try:
            return asyncio.run(self._async_fetch(query, max_results))
        except Exception as e:
            logger.warning(f"IndeedScraper failed: {e}")
            return []

    async def _async_fetch(self, query: str, max_results: int) -> list[Job]:
        from playwright.async_api import async_playwright
        from playwright_stealth import Stealth

        encoded_query = urllib.parse.quote_plus(query)
        target_url = (
            f"https://www.indeed.com/jobs?q={encoded_query}&remotejobs=1&sort=date"
        )
        jobs: list[Job] = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=_USER_AGENT)
            page = await context.new_page()
            await Stealth().apply_stealth_async(page)

            await page.goto(target_url)
            await asyncio.sleep(random.uniform(1.5, 3.5))

            # Humanise: random mouse movement
            await page.mouse.move(
                random.randint(100, 800),
                random.randint(100, 600),
            )

            # Incremental scroll to load cards
            for _ in range(3):
                await page.evaluate("window.scrollBy(0, window.innerHeight * 0.6)")
                await asyncio.sleep(random.uniform(0.5, 1.2))

            # Collect job cards
            cards = await page.query_selector_all(
                "div.job_seen_beacon, .jobTitle, .jcs-JobTitle"
            )
            # Fallback: broader card selector
            if not cards:
                cards = await page.query_selector_all("[data-jk]")

            for card in cards[:max_results]:
                try:
                    title_el = await card.query_selector(".jobTitle a, .jcs-JobTitle")
                    title = (
                        await title_el.inner_text() if title_el else ""
                    ).strip()

                    company_el = await card.query_selector(
                        "[data-testid='company-name'], .companyName"
                    )
                    company = (
                        await company_el.inner_text() if company_el else ""
                    ).strip()

                    location_el = await card.query_selector(
                        "[data-testid='text-location'], .companyLocation"
                    )
                    location = (
                        await location_el.inner_text() if location_el else "Remote"
                    ).strip()

                    link_el = await card.query_selector("a[data-jk], .jobTitle a")
                    href = (
                        await link_el.get_attribute("href") if link_el else ""
                    ) or ""
                    if href and not href.startswith("http"):
                        href = "https://www.indeed.com" + href

                    # Navigate to job detail for description
                    description = ""
                    if href:
                        try:
                            detail_page = await context.new_page()
                            await stealth_async(detail_page)
                            await detail_page.goto(href)
                            await asyncio.sleep(random.uniform(1.5, 3.0))
                            desc_el = await detail_page.query_selector(
                                "#jobDescriptionText, .jobsearch-jobDescriptionText"
                            )
                            if desc_el:
                                description = (
                                    await desc_el.inner_text()
                                )[:2000]
                            await detail_page.close()
                        except Exception as detail_err:
                            logger.debug(f"Indeed detail page error: {detail_err}")

                    if title:
                        jobs.append(
                            Job(
                                title=title,
                                company=company,
                                location=location,
                                url=href,
                                description=description,
                                source="indeed",
                            )
                        )
                except Exception as card_err:
                    logger.debug(f"Indeed card extraction error: {card_err}")
                    continue

            await browser.close()

        return jobs


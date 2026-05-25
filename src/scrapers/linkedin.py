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


class LinkedInScraper(BaseScraper):
    """LinkedIn public job search scraper using Playwright+stealth with humanised behaviour."""

    provider_name = "linkedin"

    def fetch(self, query: str, max_results: int) -> list[Job]:
        try:
            return asyncio.run(self._async_fetch(query, max_results))
        except Exception as e:
            logging.warning(f"[LinkedInScraper] {e}")
            return []

    async def _async_fetch(self, query: str, max_results: int) -> list[Job]:
        from playwright.async_api import async_playwright
        from playwright_stealth import Stealth

        encoded_query = urllib.parse.quote_plus(query)
        target_url = (
            f"https://www.linkedin.com/jobs/search"
            f"?keywords={encoded_query}&location=Brazil&f_WT=2"
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

            cards = await page.query_selector_all(".job-search-card")

            for card in cards[:max_results]:
                try:
                    title_el = await card.query_selector("h3.base-search-card__title")
                    title = (
                        await title_el.inner_text() if title_el else ""
                    ).strip()
                    if not title:
                        continue

                    company_el = await card.query_selector("h4.base-search-card__subtitle")
                    company = (
                        await company_el.inner_text() if company_el else ""
                    ).strip()

                    location_el = await card.query_selector(".job-search-card__location")
                    location = (
                        await location_el.inner_text() if location_el else "Remote"
                    ).strip()

                    link_el = await card.query_selector("a.base-card__full-link[href]")
                    href = (
                        await link_el.get_attribute("href") if link_el else ""
                    ) or ""
                    if href:
                        parsed = urllib.parse.urlparse(href)
                        href = urllib.parse.urlunparse(
                            (parsed.scheme, parsed.netloc, parsed.path, "", "", "")
                        )
                    if not href:
                        continue

                    date_el = await card.query_selector("time[datetime]")
                    posted_date: str | None = None
                    if date_el:
                        posted_date = await date_el.get_attribute("datetime")

                    # Navigate to job detail page to fetch description
                    description = ""
                    try:
                        detail_page = await context.new_page()
                        await Stealth().apply_stealth_async(detail_page)
                        await detail_page.goto(href)
                        await asyncio.sleep(random.uniform(1.5, 3.0))
                        desc_el = await detail_page.query_selector(
                            ".show-more-less-html__markup, "
                            "div#job-details, "
                            "section.description .description__text"
                        )
                        if desc_el:
                            description = (await desc_el.inner_text()).strip()[:2000]
                        await detail_page.close()
                    except Exception as detail_err:
                        logger.debug(f"LinkedIn detail page error: {detail_err}")

                    jobs.append(
                        Job(
                            title=title,
                            company=company,
                            location=location,
                            url=href,
                            description=description,
                            source="linkedin",
                            posted_date=posted_date,
                        )
                    )
                except Exception as card_err:
                    logger.debug(f"LinkedIn card extraction error: {card_err}")
                    continue

            await browser.close()

        return jobs

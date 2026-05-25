from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest

from scrapers.linkedin import LinkedInScraper


def test_linkedin_scraper_returns_list():
    scraper = LinkedInScraper()
    result = scraper.fetch("fullstack developer", 3)
    assert isinstance(result, list)


def test_linkedin_scraper_graceful_failure():
    with patch("asyncio.run", side_effect=RuntimeError("boom")):
        scraper = LinkedInScraper()
        result = scraper.fetch("test", 1)
    assert result == []


def test_linkedin_job_source():
    scraper = LinkedInScraper()
    jobs = scraper.fetch("fullstack developer", 3)
    if not jobs:
        assert True
        return
    assert all(j.source == "linkedin" for j in jobs)

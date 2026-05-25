"""Integration tests — one real network call per provider, max_results=1.

Run with:
    pytest tests/integration/ -v -m integration

These tests make live HTTP requests. An empty result list is acceptable
(provider may be temporarily unreachable); the test only fails if an
exception escapes the scraper or the return value is not a list.
"""
from __future__ import annotations

import os

import pytest

from scrapers.capgemini import CapgeminiScraper
from scrapers.google_jobs import GoogleJobsScraper
from scrapers.himalayas import HimalayasScraper
from scrapers.indeed import IndeedScraper
from scrapers.linkedin import LinkedInScraper
from scrapers.solides import SolidesScraper

_QUERY = "fullstack developer"
_MAX = 1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _assert_valid(jobs: list, expected_source: str) -> None:
    """Common assertions for every scraper result."""
    assert isinstance(jobs, list), "fetch() must return a list"
    for job in jobs:
        assert job.source == expected_source, (
            f"Expected source='{expected_source}', got '{job.source}'"
        )
        assert isinstance(job.title, str), "job.title must be a string"
        assert isinstance(job.url, str), "job.url must be a string"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_himalayas_fetches_jobs():
    """HimalayasScraper returns a list with at least 1 job from the live API."""
    scraper = HimalayasScraper()
    jobs = scraper.fetch(_QUERY, _MAX)
    _assert_valid(jobs, "himalayas")
    assert len(jobs) >= 1, (
        "Himalayas returned 0 jobs — check network or API availability"
    )


@pytest.mark.integration
def test_solides_fetches_jobs():
    """SolidesScraper returns a list with at least 1 job from the live API."""
    scraper = SolidesScraper()
    jobs = scraper.fetch(_QUERY, _MAX)
    _assert_valid(jobs, "solides")
    assert len(jobs) >= 1, (
        "Solides returned 0 jobs — check network or API availability"
    )


@pytest.mark.integration
def test_capgemini_fetches_jobs():
    """CapgeminiScraper returns a list with at least 1 job from the live site."""
    scraper = CapgeminiScraper()
    jobs = scraper.fetch(_QUERY, _MAX)
    _assert_valid(jobs, "capgemini")
    assert len(jobs) >= 1, (
        "Capgemini returned 0 jobs — check network or site structure changes"
    )


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("SERPER_API_KEY"),
    reason="SERPER_API_KEY not set — skipping Google Jobs integration test",
)
def test_google_jobs_fetches_jobs():
    """GoogleJobsScraper returns a list with at least 1 job when SERPER_API_KEY is set."""
    api_key = os.getenv("SERPER_API_KEY", "")
    scraper = GoogleJobsScraper(api_key=api_key)
    jobs = scraper.fetch(f"site:linkedin.com {_QUERY}", _MAX)
    _assert_valid(jobs, "google_jobs")
    assert len(jobs) >= 1, (
        "Google Jobs (Serper) returned 0 jobs — check API key or query"
    )


@pytest.mark.integration
def test_linkedin_fetches_jobs():
    """LinkedInScraper returns a list with at least 1 job from the live site."""
    scraper = LinkedInScraper()
    jobs = scraper.fetch(_QUERY, _MAX)
    _assert_valid(jobs, "linkedin")
    assert len(jobs) >= 1, (
        "LinkedIn returned 0 jobs — check Playwright setup or bot detection"
    )


@pytest.mark.integration
def test_indeed_fetches_jobs():
    """IndeedScraper returns a list with at least 1 job from the live site."""
    scraper = IndeedScraper()
    jobs = scraper.fetch(_QUERY, _MAX)
    _assert_valid(jobs, "indeed")
    assert len(jobs) >= 1, (
        "Indeed returned 0 jobs — check Playwright setup or bot detection"
    )

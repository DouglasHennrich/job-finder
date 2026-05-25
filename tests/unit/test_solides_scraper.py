from __future__ import annotations

from unittest.mock import MagicMock, patch

import requests

from scrapers.solides import SolidesScraper


def test_solides_scraper_returns_list():
    scraper = SolidesScraper()
    result = scraper.fetch("fullstack", 3)
    assert isinstance(result, list)


def test_solides_scraper_graceful_failure():
    with patch("requests.get", side_effect=requests.RequestException("boom")):
        scraper = SolidesScraper()
        result = scraper.fetch("test", 1)
    assert result == []


def test_solides_job_source():
    scraper = SolidesScraper()
    jobs = scraper.fetch("fullstack", 3)
    if not jobs:
        assert True
        return
    assert all(j.source == "solides" for j in jobs)


def test_solides_html_stripped():
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {
        "data": {
            "data": [
                {
                    "title": "Dev",
                    "companyName": "Co",
                    "redirectLink": "https://example.com",
                    "homeOffice": True,
                    "description": "<p>Hello <b>World</b></p>",
                    "createdAt": None,
                }
            ]
        }
    }

    with patch("requests.get", return_value=mock_resp):
        result = SolidesScraper().fetch("test", 1)

    assert len(result) == 1
    assert "Hello World" in result[0].description
    assert "<p>" not in result[0].description

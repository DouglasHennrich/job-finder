from __future__ import annotations

from unittest.mock import MagicMock, patch

from scrapers.capgemini import CapgeminiScraper

_FAKE_PAYLOAD = {
    "count": 2,
    "data": [
        {
            "id": "123-en_US_SAPBTP",
            "title": "Senior Fullstack Developer",
            "location": "Remote",
            "apply_job_url": "https://careers.capgemini.com/job/123",
            "wp_url": None,
            "description_stripped": "Great fullstack role.",
        },
        {
            "id": "456-en_GB_SAPBTP",
            "title": "Backend Node.js Engineer",
            "location": "London",
            "apply_job_url": "https://careers.capgemini.com/job/456",
            "wp_url": None,
            "description_stripped": "Backend role.",
        },
    ],
}


def _mock_response(payload: dict) -> MagicMock:
    resp = MagicMock()
    resp.json.return_value = payload
    resp.raise_for_status = MagicMock()
    return resp


def test_fetch_returns_list():
    """fetch() always returns a list."""
    with patch("scrapers.capgemini.requests.get") as mock_get:
        mock_get.return_value = _mock_response({"count": 0, "data": []})
        result = CapgeminiScraper().fetch("fullstack", 10)
    assert isinstance(result, list)


def test_fetch_graceful_failure_on_runtime_error():
    """fetch() must return [] and not raise when requests.get raises."""
    with patch("scrapers.capgemini.requests.get", side_effect=RuntimeError("network down")):
        result = CapgeminiScraper().fetch("fullstack", 10)
    assert result == []


def test_fetch_jobs_have_capgemini_source():
    """All returned jobs must have source == 'capgemini' and correct fields."""
    with patch("scrapers.capgemini.requests.get") as mock_get:
        mock_get.return_value = _mock_response(_FAKE_PAYLOAD)
        jobs = CapgeminiScraper().fetch("fullstack", 10)

    assert len(jobs) == 2
    for job in jobs:
        assert job.source == "capgemini"
        assert job.company == "Capgemini"
        assert isinstance(job.title, str) and job.title
        assert isinstance(job.url, str)


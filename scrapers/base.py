from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class Job:
    title: str
    company: str
    location: str
    description: str
    url: str
    source: str  # "google_jobs" | "indeed" | "himalayas" | "linkedin" | "solides"
    salary: Optional[str] = None
    posted_date: Optional[str] = None


class BaseScraper(ABC):
    """Base class for all job source scrapers."""

    @abstractmethod
    def fetch(self, query: str, max_results: int) -> list[Job]:
        """Fetch job listings for the given query.

        Must never raise — callers expect an empty list on failure.
        """

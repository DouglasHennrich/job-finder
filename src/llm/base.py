from abc import ABC, abstractmethod


class BaseLLM(ABC):
    """Abstract base class for LLM provider implementations."""

    @abstractmethod
    def chat(self, system: str, user: str) -> str:
        """Send a system+user prompt and return the text response."""

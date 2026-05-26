from abc import ABC, abstractmethod


class BaseLLM(ABC):
    """Abstract base class for LLM provider implementations."""

    @abstractmethod
    def chat(self, system: str, user: str, json_mode: bool = False) -> str:
        """Send a system+user prompt and return the text response.

        When json_mode=True, instructs the provider to return a valid JSON object.
        """

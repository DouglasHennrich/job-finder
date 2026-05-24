import openai

from llm.base import BaseLLM


class OllamaLLM(BaseLLM):
    """LLM provider backed by a local Ollama instance."""

    def __init__(self, base_url: str, model: str) -> None:
        self.model = model
        self.client = openai.OpenAI(base_url=base_url, api_key="ollama")

    def chat(self, system: str, user: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.2,
        )
        return response.choices[0].message.content

import time

import openai

from llm.base import BaseLLM


class OllamaLLM(BaseLLM):
    """LLM provider backed by a local Ollama instance."""

    def __init__(self, base_url: str, model: str) -> None:
        self.model = model
        self.client = openai.OpenAI(base_url=base_url, api_key="ollama")

    def chat(self, system: str, user: str, json_mode: bool = False) -> str:
        print(f"[LLM] Ollama ({self.model}) — enviando prompt...")
        t0 = time.time()
        kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.2,
            **kwargs,
        )
        elapsed = time.time() - t0
        print(f"[LLM] Ollama respondeu em {elapsed:.1f}s")
        return response.choices[0].message.content

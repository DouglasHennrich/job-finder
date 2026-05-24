import openai

from llm.base import BaseLLM


class OllamaLLM(BaseLLM):
    """LLM provider backed by a local Ollama instance."""

    def __init__(self, base_url: str, model: str) -> None:
        # TODO (T015):
        # 1. Store self.model = model
        # 2. Create self.client = openai.OpenAI(base_url=base_url, api_key="ollama")
        raise NotImplementedError

    def chat(self, system: str, user: str) -> str:
        # TODO (T015):
        # 1. Call self.client.chat.completions.create(
        #       model=self.model,
        #       messages=[{"role":"system","content":system},{"role":"user","content":user}],
        #       temperature=0.2)
        # 2. Return response.choices[0].message.content
        raise NotImplementedError

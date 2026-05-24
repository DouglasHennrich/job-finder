import openai

from llm.base import BaseLLM

_GITHUB_MODELS_BASE_URL = "https://models.inference.ai.azure.com"


class CopilotLLM(BaseLLM):
    """LLM provider backed by GitHub Models."""

    def __init__(self, token: str, model: str) -> None:
        # TODO (T016):
        # 1. Store self.model = model
        # 2. Create self.client = openai.OpenAI(base_url=_GITHUB_MODELS_BASE_URL, api_key=token)
        raise NotImplementedError

    def chat(self, system: str, user: str) -> str:
        # TODO (T016):
        # 1. Call self.client.chat.completions.create(
        #       model=self.model,
        #       messages=[{"role":"system","content":system},{"role":"user","content":user}],
        #       temperature=0.2)
        # 2. Return response.choices[0].message.content
        raise NotImplementedError

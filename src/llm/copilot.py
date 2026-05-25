import openai

from llm.base import BaseLLM

_COPILOT_BASE_URL = "https://api.githubcopilot.com"
_COPILOT_INTEGRATION_ID = "vscode-chat"


class CopilotLLM(BaseLLM):
    """LLM provider backed by GitHub Copilot Pro+ API."""

    def __init__(self, token: str, model: str) -> None:
        self.model = model
        self.client = openai.OpenAI(
            base_url=_COPILOT_BASE_URL,
            api_key=token,
            default_headers={"Copilot-Integration-Id": _COPILOT_INTEGRATION_ID},
        )

    def chat(self, system: str, user: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.2,
        )
        return response.choices[0].message.content

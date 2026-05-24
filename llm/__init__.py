from config import Config
from llm.base import BaseLLM
from llm.copilot import CopilotLLM
from llm.ollama import OllamaLLM


def build_llm(config: Config) -> BaseLLM:
    # TODO (T013):
    # 1. If config.llm_provider == "ollama", return OllamaLLM(base_url=..., model=...)
    # 2. If config.copilot_token is empty, raise RuntimeError with
    #    '[ERROR] Could not resolve COPILOT_TOKEN. Run "gh auth login" or set COPILOT_TOKEN in .env'
    # 3. Return CopilotLLM(token=config.copilot_token, model=config.copilot_model)
    raise NotImplementedError

from config import Config
from llm.base import BaseLLM
from llm.copilot import CopilotLLM
from llm.ollama import OllamaLLM


def build_llm(config: Config) -> BaseLLM:
    if config.llm_provider == "ollama":
        return OllamaLLM(base_url=config.ollama_base_url, model=config.ollama_model)
    if not config.copilot_token:
        raise RuntimeError(
            '[ERROR] Could not resolve COPILOT_TOKEN. Run "gh auth login" or set COPILOT_TOKEN in .env'
        )
    return CopilotLLM(token=config.copilot_token, model=config.copilot_model)

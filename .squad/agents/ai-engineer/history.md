# ai-engineer History

## Learnings

### 2026-05-24 — T016 CopilotLLM Fix

**What was fixed:** `llm/copilot.py` was using the wrong `base_url` (`https://api.githubcopilot.com`) and was making raw HTTP calls via `requests.post()` instead of using the OpenAI SDK. Fixed to use `base_url = "https://models.inference.ai.azure.com"` and `openai.OpenAI(base_url=..., api_key=token)` with `client.chat.completions.create(temperature=0.2)`, mirroring OllamaLLM's pattern exactly.

**Why:** The spec (tasks.md T016) explicitly requires the GitHub Models Azure inference endpoint and the OpenAI SDK client — not raw requests — for consistent provider abstraction and SDK-level retry/auth handling.

from __future__ import annotations

from othrys import BaseLLM, LLMConfig, DEFAULT_MODEL, DEFAULT_THINKING_BUDGET, DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE, DEFAULT_TIMEOUT


class DeepLLM(BaseLLM):
    def __init__(self, config: LLMConfig | None = None) -> None:
        cfg = config or LLMConfig(
            model=DEFAULT_MODEL,
            max_tokens=DEFAULT_MAX_TOKENS,
            thinking_budget=DEFAULT_THINKING_BUDGET,
            temperature=DEFAULT_TEMPERATURE,
        )
        super().__init__(cfg, timeout=DEFAULT_TIMEOUT)

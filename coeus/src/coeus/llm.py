from __future__ import annotations

from othrys import BaseLLM, LLMConfig


class CoeusLLM(BaseLLM):
    def __init__(self, config: LLMConfig | None = None) -> None:
        cfg = config or LLMConfig(max_tokens=16000)
        super().__init__(cfg)

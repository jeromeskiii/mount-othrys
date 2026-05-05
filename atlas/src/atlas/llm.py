from __future__ import annotations

from othrys import BaseLLM, LLMConfig, DEFAULT_MODEL


class AtlasLLM(BaseLLM):
    def __init__(self, config: LLMConfig | None = None) -> None:
        cfg = config or LLMConfig(max_tokens=16000)
        super().__init__(cfg)

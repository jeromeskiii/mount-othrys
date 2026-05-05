from __future__ import annotations

from typing import Any

from othrys import BaseLLM, LLMConfig


DEFAULT_MODEL = "claude-sonnet-4-5"


class KronosLLM:
    def __init__(self, model: str = DEFAULT_MODEL, api_key: str | None = None) -> None:
        self.base = BaseLLM(LLMConfig(model=model, api_key=api_key))

    def classify_intent(self, message: str, titan_registry: dict[str, Any]) -> str:
        descriptions = "\n".join([
            f"- {key}: {info.description} (Capabilities: {', '.join(info.capabilities)})"
            for key, info in titan_registry.items()
        ])

        system_prompt = f"""You are the Intent Classifier for Kronos, the supreme orchestrator of Mount Othrys.
Your job is to route user requests to the most appropriate Titan specialist.

AVAILABLE TITANS:
{descriptions}

ROUTING RULES:
1. If the request is about planning, scoping, or thinking through a feature, route to 'coeus'.
2. If the request is an advisory request, architecture review, or complex debugging consultation, route to 'themis'.
3. If the request involves executing a structured plan or managing a complex multi-step workflow, route to 'atlas'.
4. If the request requires deep, multi-file refactoring or heavy implementation, route to 'iapetus'.
5. If the request is a general task or direct instruction, route to 'talos'.
6. If the request is extremely urgent, complex, or requires "relentless" effort, route to 'heracles'.
7. If the request is complex and ambiguous, requires decomposing into subtasks and delegating to specialists, route to 'coordinator'.

Response Format:
Return ONLY the key of the titan (e.g., 'coeus', 'talos', etc.). No preamble, no explanation."""

        response = self.base.call(
            system=system_prompt,
            messages=[{"role": "user", "content": message}],
            max_tokens=10,
        )
        intent = response.strip().lower()

        return intent if intent in titan_registry else "talos"

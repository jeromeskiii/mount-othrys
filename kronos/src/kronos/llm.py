from __future__ import annotations

import os
from typing import Any

import anthropic


class KronosLLM:
    def __init__(self, model: str = "claude-sonnet-4-5", api_key: str | None = None) -> None:
        self.model = model
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set for Kronos semantic routing.")
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def classify_intent(self, message: str, titan_registry: dict[str, Any]) -> str:
        """Classify the user intent into one of the registered Titan modes."""
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

        response = self.client.messages.create(
            model=self.model,
            max_tokens=10,
            system=system_prompt,
            messages=[{"role": "user", "content": message}],
            temperature=0.0,
        )
        parts = [b.text for b in response.content if b.type == "text"]
        intent = "".join(parts).strip().lower()

        # Validation
        if intent in titan_registry:
            return intent

        # Fallback to keyword or default
        return "talos"

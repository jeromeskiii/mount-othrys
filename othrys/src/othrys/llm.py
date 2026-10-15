from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Callable, cast

import anthropic

from .config import DEFAULT_TIMEOUT, load_env
from .context import load_context
from .types import AgentRunResult, LLMConfig, ToolCallRecord

# Adaptive thinking ({"type": "adaptive"}) is only supported on Claude 4.6
# and later. Claude 4.5 and earlier support legacy extended thinking
# ({"type": "enabled", "budget_tokens": N}) only and reject adaptive
# thinking with HTTP 400 "adaptive thinking is not supported on this model".
_ADAPTIVE_MIN_VERSION = (4, 6)
_MIN_THINKING_BUDGET = 1024


def _model_version(model: str) -> tuple[int, int] | None:
    """Extract (major, minor) from a Claude model id.

    "claude-opus-4-5" -> (4, 5); dated ids like "claude-opus-4-5-20251101"
    -> (4, 5); "claude-opus-5" -> (5, 0). Returns None when no version
    numbers are present.
    """
    numbers = re.findall(r"\d+", model)
    if not numbers:
        return None
    major = int(numbers[0])
    minor = int(numbers[1]) if len(numbers) > 1 else 0
    return major, minor


class BaseLLM:
    def __init__(self, config: LLMConfig | None = None, timeout: int = DEFAULT_TIMEOUT) -> None:
        # MF-1: every Python Titan builds its client here, so this is the single
        # place the engine's context envelope is honoured. A Titan invoked
        # directly from a shell receives no envelope, leaving its own defaults
        # and prompts exactly as they were before.
        self.context = load_context()
        self.config = self.context.apply_to(config or LLMConfig())
        api_key = self.config.api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            load_env()
            api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY not set. Export it, pass --api-key, or add it to .env."
            )
        self.client = anthropic.Anthropic(api_key=api_key, timeout=anthropic.Timeout(float(timeout)))

    def _thinking(self, max_tokens: int) -> dict | None:
        if self.config.thinking_budget <= 0:
            return None
        version = _model_version(self.config.model)
        if version is None or version >= _ADAPTIVE_MIN_VERSION:
            return {"type": "adaptive"}
        # Legacy extended thinking: the budget must stay below max_tokens
        # (and at the API minimum of 1024 tokens).
        budget = min(self.config.thinking_budget, max_tokens - _MIN_THINKING_BUDGET)
        return {"type": "enabled", "budget_tokens": max(budget, _MIN_THINKING_BUDGET)}

    def _system_block(self, system: str) -> list[dict]:
        # MF-1: the engine's routed mode identity is prepended to the worker's
        # own system prompt rather than replacing it, so engine metadata is
        # honoured without discarding the Titan personas.
        return [
            {
                "type": "text",
                "text": self.context.compose_system_prompt(system),
                "cache_control": {"type": "ephemeral"},
            }
        ]

    def call(self, system: str, messages: list[dict], max_tokens: int | None = None) -> str:
        effective_max = max_tokens or self.config.max_tokens
        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "max_tokens": effective_max,
            "system": cast(Any, self._system_block(system)),
            "messages": cast(Any, messages),
        }
        thinking = self._thinking(effective_max)
        if thinking is not None:
            kwargs["thinking"] = cast(Any, thinking)
        response = self.client.messages.create(**kwargs)
        parts = [b.text for b in response.content if b.type == "text"]
        return "".join(parts).strip()

    def run_agent(
        self,
        system: str,
        user_prompt: str,
        tools: list[dict],
        tool_dispatch: Callable[[str, dict], tuple[str, bool]],
        max_iterations: int = 25,
        max_tokens: int | None = None,
        on_event: Callable[[str, dict], None] | None = None,
    ) -> AgentRunResult:
        system_blocks = self._system_block(system)
        messages: list[dict] = [{"role": "user", "content": user_prompt}]
        tool_calls: list[ToolCallRecord] = []
        final_text = ""
        stop_reason = ""
        thinking_content: list[str] = []
        iteration = 0
        effective_max = max_tokens or self.config.max_tokens

        for iteration in range(1, max_iterations + 1):
            kwargs: dict[str, Any] = {
                "model": self.config.model,
                "max_tokens": effective_max,
                "system": cast(Any, system_blocks),
                "messages": cast(Any, messages),
                "tools": cast(Any, tools),
            }
            thinking = self._thinking(effective_max)
            if thinking is not None:
                kwargs["thinking"] = cast(Any, thinking)
            response = self.client.messages.create(**kwargs)
            stop_reason = response.stop_reason or ""
            assistant_content: list[dict] = []
            tool_uses: list[Any] = []
            text_chunks: list[str] = []
            for block in response.content:
                if block.type == "text":
                    text_chunks.append(block.text)
                    assistant_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    tool_uses.append(block)
                    assistant_content.append(
                        {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}
                    )
                elif block.type == "thinking":
                    thinking_content.append(block.thinking)
                    assistant_content.append(
                        {"type": "thinking", "thinking": block.thinking, "signature": block.signature}
                    )
                elif block.type == "redacted_thinking":
                    # Must be round-tripped unchanged when thinking is on.
                    assistant_content.append({"type": "redacted_thinking", "data": block.data})
            if text_chunks:
                final_text = "\n".join(text_chunks).strip()
            if on_event:
                on_event(
                    "assistant_turn",
                    {
                        "iteration": iteration,
                        "text": final_text,
                        "tool_uses": len(tool_uses),
                        "thinking_tokens": getattr(response.usage, "thinking_tokens", 0),
                    },
                )

            if not tool_uses:
                break

            messages.append({"role": "assistant", "content": assistant_content})
            tool_results: list[dict] = []
            for tu in tool_uses:
                if on_event:
                    on_event("tool_use", {"name": tu.name, "input": tu.input})
                output, is_error = tool_dispatch(tu.name, dict(tu.input))
                tool_calls.append(
                    ToolCallRecord(name=tu.name, input=dict(tu.input), result=output, is_error=is_error)
                )
                if on_event:
                    on_event(
                        "tool_result",
                        {"name": tu.name, "is_error": is_error, "output_preview": output[:300]},
                    )
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tu.id,
                        "content": output,
                        "is_error": is_error,
                    }
                )
            messages.append({"role": "user", "content": tool_results})

        return AgentRunResult(
            final_text=final_text,
            tool_calls=tool_calls,
            stop_reason=stop_reason,
            iterations=iteration,
            thinking_content=thinking_content,
        )

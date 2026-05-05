from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

import anthropic

from .config import DEFAULT_TIMEOUT, load_env
from .types import AgentRunResult, LLMConfig, ToolCallRecord


class BaseLLM:
    def __init__(self, config: LLMConfig | None = None, timeout: int = DEFAULT_TIMEOUT) -> None:
        self.config = config or LLMConfig()
        api_key = self.config.api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            load_env()
            api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY not set. Export it, pass --api-key, or add it to .env."
            )
        self.client = anthropic.Anthropic(api_key=api_key, timeout=anthropic.Timeout(float(timeout)))

    def _thinking(self) -> dict:
        return {"type": "adaptive"}

    def _system_block(self, system: str) -> list[dict]:
        return [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]

    def call(self, system: str, messages: list[dict], max_tokens: int | None = None) -> str:
        response = self.client.messages.create(
            model=self.config.model,
            max_tokens=max_tokens or self.config.max_tokens,
            system=self._system_block(system),
            messages=messages,
            thinking=self._thinking(),
        )
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

        for iteration in range(1, max_iterations + 1):
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=max_tokens or self.config.max_tokens,
                system=system_blocks,
                messages=messages,
                tools=tools,
                thinking=self._thinking(),
            )
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

            if stop_reason == "end_turn":
                break

        return AgentRunResult(
            final_text=final_text,
            tool_calls=tool_calls,
            stop_reason=stop_reason,
            iterations=iteration,
            thinking_content=thinking_content,
        )

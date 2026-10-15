"""Engine -> worker context envelope (MF-1).

The TypeScript engine routes a request to a Titan and already knows that Titan's
runtime configuration (system prompt, model, budgets, phase). Before MF-1 that
configuration was built by :mod:`engine/src/workflow/runner.ts` and then silently
dropped by the Python bridge, so every worker ran with its own hardcoded model
and budgets and with a second, independently maintained system prompt.

The envelope is passed as a single JSON environment variable rather than as
command-line arguments for two reasons:

* ``--json``, ``--model`` and friends are defined on each Titan's *main*
  argparse parser, and argparse subparsers reject options they do not declare,
  so per-subcommand flags cannot be added without touching every Titan CLI.
* A system prompt can be several kilobytes; keeping it out of ``argv`` avoids
  leaking it into the process table.

The worker honours the envelope in :class:`othrys.llm.BaseLLM`, which is the one
place every Python Titan funnels through. There is therefore a single source of
truth: an engine-routed worker uses the engine's mode configuration, while a
Titan invoked directly from a shell (no envelope) is completely unaffected.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, replace
from typing import Any, Mapping

from .types import LLMConfig

CONTEXT_ENV_VAR = "OTHRYS_CONTEXT"

#: Canonical composition rule, mirrored by the TypeScript engine in
#: ``engine/src/adapters/engineContext.ts``. The engine's short mode identity is
#: prepended to the worker's task-specific prompt instead of replacing it, so
#: engine routing metadata is honoured without discarding the worker personas.
DIRECTIVE_SEPARATOR = "\n\n---\n\n"


def _as_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return None


def _as_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


@dataclass(frozen=True)
class EngineContext:
    """Runtime configuration the engine hands to a routed worker."""

    mode: str = ""
    phase: str = ""
    system_prompt: str = ""
    model: str | None = None
    temperature: float | None = None
    thinking_budget: int | None = None
    max_tokens: int | None = None

    @property
    def is_empty(self) -> bool:
        """True when nothing usable was supplied, so callers can skip work.

        Compares against ``None``/``""`` explicitly rather than using truthiness:
        ``temperature=0.0`` is a meaningful value, not an absent one.
        """
        return all(
            value is None or value == ""
            for value in (
                self.mode,
                self.phase,
                self.system_prompt,
                self.model,
                self.temperature,
                self.thinking_budget,
                self.max_tokens,
            )
        )

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any] | None) -> "EngineContext":
        """Build a context from a decoded envelope, tolerating bad types.

        Unknown keys are ignored and malformed values fall back to ``None``
        rather than raising: a worker must never fail to start because the
        engine sent an unexpected payload.
        """
        if not isinstance(raw, Mapping):
            return cls()
        return cls(
            mode=_as_text(raw.get("mode")),
            phase=_as_text(raw.get("phase")),
            system_prompt=_as_text(raw.get("systemPrompt")),
            model=_as_text(raw.get("model")) or None,
            temperature=_as_float(raw.get("temperature")),
            thinking_budget=_as_int(raw.get("thinkingBudget")),
            max_tokens=_as_int(raw.get("maxTokens")),
        )

    def apply_to(self, config: LLMConfig) -> LLMConfig:
        """Return ``config`` with the engine's overrides applied.

        Only fields the engine actually supplied are overridden; everything else
        keeps whatever the Titan or its command line chose.
        """
        overrides: dict[str, Any] = {}
        if self.model:
            overrides["model"] = self.model
        if self.temperature is not None:
            overrides["temperature"] = self.temperature
        if self.thinking_budget is not None:
            overrides["thinking_budget"] = self.thinking_budget
        if self.max_tokens is not None:
            overrides["max_tokens"] = self.max_tokens
        if not overrides:
            return config
        return replace(config, **overrides)

    def compose_system_prompt(self, worker_prompt: str) -> str:
        """Prepend the engine's mode identity to the worker's own prompt."""
        directive = self.system_prompt.strip()
        if not directive:
            return worker_prompt
        if not worker_prompt.strip():
            return directive
        return f"{directive}{DIRECTIVE_SEPARATOR}{worker_prompt}"


def parse_context(raw: str | None) -> EngineContext:
    """Decode an envelope string. Unset, blank, or invalid input yields an empty context."""
    if not raw or not raw.strip():
        return EngineContext()
    try:
        decoded = json.loads(raw)
    except (ValueError, TypeError):
        return EngineContext()
    return EngineContext.from_mapping(decoded)


def load_context(environ: Mapping[str, str] | None = None) -> EngineContext:
    """Read the engine envelope from the environment."""
    source = os.environ if environ is None else environ
    return parse_context(source.get(CONTEXT_ENV_VAR))
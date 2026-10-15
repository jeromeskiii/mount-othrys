"""Regression coverage for MF-1 — the engine's context envelope reaches the worker.

Before MF-1 the engine built ``{systemPrompt, mode, phase}`` and the Python bridge
dropped it on the floor, so every worker ran with its own prompt and its own
budgets while the routed mode configuration was inert.
"""

from __future__ import annotations

import json

from othrys.context import (
    CONTEXT_ENV_VAR,
    DIRECTIVE_SEPARATOR,
    EngineContext,
    load_context,
    parse_context,
)
from othrys.llm import BaseLLM
from othrys.types import LLMConfig


def test_absent_envelope_is_empty() -> None:
    assert parse_context(None).is_empty
    assert parse_context("").is_empty
    assert parse_context("   ").is_empty
    assert load_context({}).is_empty


def test_malformed_envelope_never_raises() -> None:
    """A worker must never fail to start because the engine sent garbage."""
    assert parse_context("{not json").is_empty
    assert parse_context('"a string"').is_empty
    assert parse_context("[1, 2, 3]").is_empty
    assert parse_context("null").is_empty


def test_wrong_field_types_fall_back_to_none() -> None:
    context = EngineContext.from_mapping(
        {"mode": "talos", "maxTokens": "lots", "temperature": True, "model": 7}
    )

    assert context.mode == "talos"
    assert context.max_tokens is None
    assert context.temperature is None
    assert context.model is None


def test_zero_temperature_is_not_treated_as_absent() -> None:
    """``0.0`` is a meaningful sampling setting, so it must not read as empty."""
    context = parse_context('{"temperature": 0.0}')

    assert not context.is_empty
    assert context.temperature == 0.0


def test_engine_envelope_round_trips() -> None:
    raw = json.dumps(
        {
            "mode": "iapetus",
            "phase": "execute",
            "systemPrompt": "You are Iapetus.",
            "model": "claude-x",
            "maxTokens": 2048,
            "thinkingBudget": 4096,
            "temperature": 0.4,
        }
    )

    context = parse_context(raw)

    assert (context.mode, context.phase, context.system_prompt) == (
        "iapetus",
        "execute",
        "You are Iapetus.",
    )
    assert (
        context.model,
        context.max_tokens,
        context.thinking_budget,
        context.temperature,
    ) == ("claude-x", 2048, 4096, 0.4)


def test_apply_to_only_overrides_supplied_fields() -> None:
    base = LLMConfig(model="claude-opus-4-5", max_tokens=64_000, temperature=0.1)

    assert parse_context(None).apply_to(base) == base

    overridden = parse_context('{"model": "claude-x", "maxTokens": 100}').apply_to(base)
    assert overridden.model == "claude-x"
    assert overridden.max_tokens == 100
    assert overridden.temperature == 0.1, "unsupplied fields keep the Titan's own value"


def test_compose_prepends_without_replacing_the_worker_prompt() -> None:
    context = parse_context('{"systemPrompt": "ENGINE DIRECTIVE"}')

    assert context.compose_system_prompt("WORKER PROMPT") == (
        f"ENGINE DIRECTIVE{DIRECTIVE_SEPARATOR}WORKER PROMPT"
    )
    assert parse_context(None).compose_system_prompt("WORKER PROMPT") == "WORKER PROMPT"
    assert context.compose_system_prompt("   ") == "ENGINE DIRECTIVE"


def test_base_llm_honours_the_envelope(monkeypatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-used")
    monkeypatch.setenv(
        CONTEXT_ENV_VAR,
        '{"mode": "iapetus", "systemPrompt": "ENGINE DIRECTIVE", "maxTokens": 777}',
    )

    llm = BaseLLM(LLMConfig(model="claude-opus-4-5", max_tokens=64_000))

    assert llm.config.max_tokens == 777

    block = llm._system_block("WORKER PROMPT")[0]
    assert block["text"].startswith("ENGINE DIRECTIVE")
    assert "WORKER PROMPT" in block["text"]


def test_base_llm_is_unchanged_without_an_envelope(monkeypatch) -> None:
    """A Titan invoked directly from a shell must behave exactly as before."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-used")
    monkeypatch.delenv(CONTEXT_ENV_VAR, raising=False)

    llm = BaseLLM(LLMConfig(model="claude-opus-4-5", max_tokens=64_000))

    assert llm.config.max_tokens == 64_000
    assert llm._system_block("WORKER PROMPT")[0]["text"] == "WORKER PROMPT"
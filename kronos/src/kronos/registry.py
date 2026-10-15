from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TitanDomain(Enum):
    PLANNING = "planning"
    EXECUTION = "execution"
    DEEP_EXECUTION = "deep_execution"
    ORCHESTRATION = "orchestration"
    ADVISORY = "advisory"
    HIGH_INTENSITY = "high_intensity"
    COORDINATION = "coordination"


class TitanMode(Enum):
    COEUS = "coeus"
    ATLAS = "atlas"
    IAPETUS = "iapetus"
    TALOS = "talos"
    THEMIS = "themis"
    HERACLES = "heracles"
    COORDINATOR = "coordinator"


@dataclass
class TitanInfo:
    name: str
    mode: TitanMode
    domain: TitanDomain
    cli_command: str
    model: str
    description: str
    capabilities: list[str]
    tool_access: list[str]
    tool_blocked: list[str]
    temperature: float
    thinking_budget: int
    max_tokens: int


TITAN_REGISTRY: dict[str, TitanInfo] = {
    "coeus": TitanInfo(
        name="coeus",
        mode=TitanMode.COEUS,
        domain=TitanDomain.PLANNING,
        cli_command="coeus",
        model="claude-opus-4-5",
        description="Strategic planning consultant — interview-first with Metis review",
        capabilities=["planning", "interview", "metis-consultation", "momus-validation"],
        tool_access=["read", "write .sisyphus/*.md"],
        tool_blocked=["write code", "edit code"],
        temperature=0.1,
        thinking_budget=32_000,
        max_tokens=64_000,
    ),
    "atlas": TitanInfo(
        name="atlas",
        mode=TitanMode.ATLAS,
        domain=TitanDomain.EXECUTION,
        cli_command="atlas",
        model="claude-opus-4-5",
        description="Master orchestrator — sequential execution with verification gates",
        capabilities=["delegate", "verify", "boulder-state", "sequential-execution"],
        tool_access=["read", "lsp_diagnostics", "delegate_task"],
        tool_blocked=["write", "edit"],
        temperature=0.1,
        thinking_budget=32_000,
        max_tokens=16_000,
    ),
    "iapetus": TitanInfo(
        name="iapetus",
        mode=TitanMode.IAPETUS,
        domain=TitanDomain.DEEP_EXECUTION,
        cli_command="iapetus",
        model="claude-opus-4-5",
        description="Deep execution — thinking-mode analysis and multi-file implementation",
        capabilities=["deep-analysis", "multi-file-refactor", "architectural-execution"],
        tool_access=["all"],
        tool_blocked=[],
        temperature=0.1,
        thinking_budget=32_000,
        max_tokens=48_000,
    ),
    "talos": TitanInfo(
        name="talos",
        mode=TitanMode.TALOS,
        domain=TitanDomain.ORCHESTRATION,
        cli_command="talos",
        model="claude-opus-4-5",
        description="Primary orchestrator — classifies, routes, delegates to other Titans",
        capabilities=["classify", "route", "delegate", "todo-tracking", "session-persistence"],
        tool_access=["all except task"],
        tool_blocked=["task"],
        temperature=0.1,
        thinking_budget=32_000,
        max_tokens=64_000,
    ),
    "themis": TitanInfo(
        name="themis",
        mode=TitanMode.THEMIS,
        domain=TitanDomain.ADVISORY,
        cli_command="kronos",
        model="gpt-4o",
        description="Strategic technical advisor — read-only architecture and debugging consultation",
        capabilities=["architecture", "debugging", "self-review", "codebase-analysis"],
        tool_access=["read", "question"],
        tool_blocked=["write", "edit", "task", "delegate_task"],
        temperature=0.1,
        thinking_budget=32_000,
        max_tokens=64_000,
    ),
    "heracles": TitanInfo(
        name="heracles",
        mode=TitanMode.HERACLES,
        domain=TitanDomain.HIGH_INTENSITY,
        cli_command="kronos",
        model="inherited",
        description="High-intensity mode — zero-compromise relentless execution",
        capabilities=["ultrawork", "parallel-agents", "verification-guarantee"],
        tool_access=["all"],
        tool_blocked=[],
        temperature=0.0,
        thinking_budget=32_000,
        max_tokens=64_000,
    ),
    "coordinator": TitanInfo(
        name="coordinator",
        mode=TitanMode.COORDINATOR,
        domain=TitanDomain.COORDINATION,
        cli_command="kronos",
        model="claude-opus-4-5",
        description="Strategic coordinator — decomposes vague objectives into executable steps using goal decomposition (e.g. 'analyze data' → load → clean → filter → model → summarize), assigns each step to the right specialist",
        capabilities=["goal-decomposition", "decompose", "delegate", "synthesize", "multi-disciplinary", "plan-tracking"],
        tool_access=["all except write code", "edit code"],
        tool_blocked=["write code", "edit code"],
        temperature=0.1,
        thinking_budget=64_000,
        max_tokens=128_000,
    ),
}

LEGACY_ALIASES: dict[str, str] = {
    "sisyphus": "talos",
    "prometheus": "coeus",
    "oracle": "themis",
    "hephaestus": "iapetus",
    "ultrawork": "heracles",
}


def get_titan(name: str) -> TitanInfo:
    key = name.lower().strip()
    if key in LEGACY_ALIASES:
        key = LEGACY_ALIASES[key]
    if key not in TITAN_REGISTRY:
        raise KeyError(f"Unknown Titan: {name}. Available: {', '.join(TITAN_REGISTRY.keys())}")
    return TITAN_REGISTRY[key]


def list_titans() -> list[TitanInfo]:
    return list(TITAN_REGISTRY.values())

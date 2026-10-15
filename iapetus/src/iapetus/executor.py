from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from othrys import AgentRunResult
from .llm import DeepLLM
from .prompts import (
    DEEP_ANALYSIS_SYSTEM,
    DEEP_EXECUTION_SYSTEM,
    build_analysis_prompt,
    build_execution_prompt,
)
from .tools import make_dispatcher, tool_specs


def _classify(text: str) -> tuple[bool, bool, str]:
    stripped = text.strip()
    for line in reversed(stripped.splitlines()):
        ls = line.strip()
        if ls.upper().startswith("DONE:"):
            return True, False, ls[5:].strip()
        if ls.upper().startswith("BLOCKED:"):
            return False, True, ls[8:].strip()
    return False, False, stripped[-500:]


@dataclass
class DeepResult:
    success: bool
    blocked: bool
    summary: str
    analysis: str
    iterations: int
    raw: AgentRunResult


class DeepExecutor:
    def __init__(
        self,
        *,
        llm: DeepLLM,
        workdir: Path,
        on_event: Callable[[str, dict], None] | None = None,
    ) -> None:
        self.llm = llm
        self.workdir = workdir
        self.on_event = on_event

    def run_analysis(
        self,
        objective: str,
        findings: list[str],
        decisions: list[str],
    ) -> str:
        user = build_analysis_prompt(
            objective=objective,
            workdir=str(self.workdir),
            findings=findings,
            decisions=decisions,
        )
        return self.llm.call(
            system=DEEP_ANALYSIS_SYSTEM,
            messages=[{"role": "user", "content": user}],
        )

    def run(
        self,
        *,
        objective: str,
        findings: list[str] | None = None,
        decisions: list[str] | None = None,
        analysis: str | None = None,
        max_iterations: int = 50,
        max_tokens: int | None = None,
    ) -> DeepResult:
        if findings is None:
            findings = []
        if decisions is None:
            decisions = []
        if analysis is None:
            analysis = self.run_analysis(
                objective=objective,
                findings=findings,
                decisions=decisions,
            )

        dispatch = make_dispatcher(workdir=self.workdir)
        user = build_execution_prompt(
            objective=objective,
            workdir=str(self.workdir),
            analysis=analysis,
            findings=findings,
            decisions=decisions,
        )

        raw = self.llm.run_agent(
            system=DEEP_EXECUTION_SYSTEM,
            user_prompt=user,
            tools=tool_specs(),
            tool_dispatch=dispatch,
            max_iterations=max_iterations,
            max_tokens=max_tokens,
            on_event=self.on_event,
        )

        success, blocked, summary = _classify(raw.final_text)
        return DeepResult(
            success=success,
            blocked=blocked,
            summary=summary,
            analysis=analysis,
            iterations=raw.iterations,
            raw=raw,
        )

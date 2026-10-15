from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from othrys import AgentRunResult
from .boulder import Task, Boulder
from .llm import AtlasLLM
from .prompts import SUBAGENT_SYSTEM, build_subagent_prompt
from .tools import ToolContext, make_dispatcher, tool_specs


@dataclass
class ExecutionResult:
    success: bool
    summary: str
    blocked: bool
    raw: AgentRunResult


def _classify_summary(text: str) -> tuple[bool, bool, str]:
    stripped = text.strip()
    for line in reversed(stripped.splitlines()):
        ls = line.strip()
        if ls.upper().startswith("DONE:"):
            return True, False, ls[5:].strip()
        if ls.upper().startswith("BLOCKED:"):
            return False, True, ls[8:].strip()
    return False, False, stripped[-500:]


def execute_task(
    *,
    llm: AtlasLLM,
    boulder: Boulder,
    task: Task,
    workdir: Path,
    log_path: Path,
    on_event: Callable[[str, dict], None] | None = None,
) -> ExecutionResult:
    ctx = ToolContext(workdir=workdir)
    dispatch = make_dispatcher(ctx)
    prompt = build_subagent_prompt(
        objective=boulder.objective,
        phase=task.phase,
        title=task.title,
        description=task.description,
        deliverable=task.deliverable,
        steps=task.steps,
        workdir=str(workdir),
        findings=boulder.findings,
        decisions=boulder.decisions,
        previous_attempt_notes=task.notes if task.attempts > 0 else None,
    )

    log_lines: list[str] = [
        f"=== Task: {task.id} ({task.title}) ===",
        f"Attempt: {task.attempts + 1}",
        f"Workdir: {workdir}",
        "",
        "--- Prompt ---",
        prompt,
        "",
        "--- Run ---",
    ]

    def _log(event: str, payload: dict) -> None:
        if event == "tool_use":
            log_lines.append(f"[tool_use] {payload['name']} {payload['input']}")
        elif event == "tool_result":
            preview = payload["output_preview"].replace("\n", " ⏎ ")
            err = " ERROR" if payload["is_error"] else ""
            log_lines.append(f"[tool_result{err}] {payload['name']}: {preview}")
        elif event == "assistant_turn":
            log_lines.append(f"[assistant iter={payload['iteration']} tool_uses={payload['tool_uses']}]")
            if payload["text"]:
                log_lines.append(f"  text: {payload['text'][:400]}")
        if on_event:
            on_event(event, payload)

    result = llm.run_agent(
        system=SUBAGENT_SYSTEM,
        user_prompt=prompt,
        tools=tool_specs(),
        tool_dispatch=dispatch,
        on_event=_log,
    )

    success, blocked, summary = _classify_summary(result.final_text)
    log_lines.extend(["", f"--- Final ({result.stop_reason}) ---", result.final_text])
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("\n".join(log_lines))

    return ExecutionResult(success=success, summary=summary, blocked=blocked, raw=result)

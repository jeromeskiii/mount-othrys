from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .boulder import Boulder, BoulderStatus, BoulderStore, Task, TaskStatus
from .executor import execute_task
from .llm import AtlasLLM
from .verifier import run_verifications, adjudicate


def get_max_attempts(task: Task) -> int:
    """Dynamic cognitive budget based on task priority."""
    if task.priority <= 1:
        return 3
    if task.priority >= 5:
        return 12
    return (task.priority * 2) + 1


@dataclass
class StepOutcome:
    task_id: str
    title: str
    success: bool
    blocked: bool
    summary: str
    verdict: str
    reason: str


class Orchestrator:
    def __init__(
        self,
        store: BoulderStore,
        llm: AtlasLLM,
        workdir: Path,
        on_event: Callable[[str, dict], None] | None = None,
    ) -> None:
        self.store = store
        self.llm = llm
        self.workdir = workdir
        self.on_event = on_event

    def _emit(self, event: str, payload: dict) -> None:
        if self.on_event:
            self.on_event(event, payload)

    def step(self, boulder: Boulder) -> StepOutcome | None:
        task = boulder.next_pending()
        if task is None:
            boulder.status = BoulderStatus.DONE if boulder.is_done() else BoulderStatus.BLOCKED
            self.store.save(boulder)
            return None

        boulder.status = BoulderStatus.RUNNING
        task.status = TaskStatus.RUNNING
        task.attempts += 1
        if task.started_at is None:
            from datetime import datetime, timezone

            task.started_at = datetime.now(timezone.utc).isoformat()
        self.store.save(boulder)
        self._emit("task_start", {"id": task.id, "title": task.title, "attempt": task.attempts})

        log_path = self.store.run_log_path(boulder.name, f"{task.id}-attempt-{task.attempts}")
        exec_result = execute_task(
            llm=self.llm,
            boulder=boulder,
            task=task,
            workdir=self.workdir,
            log_path=log_path,
            on_event=self.on_event,
        )

        if exec_result.blocked:
            task.status = TaskStatus.BLOCKED
            task.notes.append(f"Subagent blocked: {exec_result.summary}")
            boulder.status = BoulderStatus.BLOCKED
            self.store.save(boulder)
            return StepOutcome(task.id, task.title, False, True, exec_result.summary, "BLOCKED", exec_result.summary)

        results = run_verifications(task, self.workdir)
        task.verifications = results
        verdict = adjudicate(self.llm, task, results)
        task.notes.append(f"Attempt {task.attempts}: {verdict.verdict} — {verdict.reason}")

        if verdict.all_passed:
            task.status = TaskStatus.DONE
            from datetime import datetime, timezone

            task.finished_at = datetime.now(timezone.utc).isoformat()
            if exec_result.summary:
                boulder.findings.append(f"[{task.id}] {exec_result.summary}")
            boulder.status = BoulderStatus.RUNNING if boulder.next_pending() else BoulderStatus.DONE
            self.store.save(boulder)
            return StepOutcome(task.id, task.title, True, False, exec_result.summary, verdict.verdict, verdict.reason)

        max_attempts = get_max_attempts(task)
        if task.attempts >= max_attempts:
            task.status = TaskStatus.FAILED
            task.notes.append(f"Exhausted cognitive budget of {max_attempts} attempts.")
            boulder.status = BoulderStatus.BLOCKED
            self.store.save(boulder)
            return StepOutcome(task.id, task.title, False, False, exec_result.summary, verdict.verdict, verdict.reason)

        task.status = TaskStatus.PENDING
        task.notes.append(f"Reattempt hint: {verdict.next_step}")
        self.store.save(boulder)
        return StepOutcome(task.id, task.title, False, False, exec_result.summary, verdict.verdict, verdict.reason)

    def run_to_completion(self, boulder: Boulder, max_steps: int = 50) -> list[StepOutcome]:
        outcomes: list[StepOutcome] = []
        for _ in range(max_steps):
            outcome = self.step(boulder)
            if outcome is None:
                break
            outcomes.append(outcome)
            if outcome.blocked:
                break
            if not outcome.success and boulder.status == BoulderStatus.BLOCKED:
                break
        return outcomes

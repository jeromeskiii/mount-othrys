from __future__ import annotations

from pathlib import Path
from typing import Any

from atlas.boulder import BoulderStore, Boulder, Task, BoulderStatus, TaskStatus


def load_boulder_from_atlas(*, root: Path, name: str) -> Boulder:
    store = BoulderStore(root)
    return store.load(name)


def find_blocked_tasks(boulder: Boulder) -> list[Task]:
    return [t for t in boulder.tasks if t.status in (TaskStatus.BLOCKED, TaskStatus.FAILED)]


def find_next_pending(boulder: Boulder) -> Task | None:
    return next(
        (t for t in boulder.tasks if t.status == TaskStatus.PENDING),
        None,
    )


def to_objective(*, boulder: Boulder, task: Task) -> str:
    parts = [
        f"Boulder objective: {boulder.objective}",
        f"\nTask: {task.phase} — {task.title}",
        f"\nDescription: {task.description}",
        f"\nDeliverable: {task.deliverable}",
    ]
    if task.steps:
        parts.append("\nSteps:")
        parts.extend(f"{i}. {s}" for i, s in enumerate(task.steps, 1))
    if task.verifications:
        parts.append("\nVerification commands:")
        parts.extend(f"- `{v.command}` ({v.description})" for v in task.verifications if v.command)
    if boulder.findings:
        parts.append("\nCumulative findings:")
        parts.extend(f"- {f}" for f in boulder.findings)
    if boulder.decisions:
        parts.append("\nCumulative decisions:")
        parts.extend(f"- {d}" for d in boulder.decisions)
    return "\n".join(parts)

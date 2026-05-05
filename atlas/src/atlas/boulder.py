from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
import yaml


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    VERIFYING = "verifying"
    BLOCKED = "blocked"
    DONE = "done"
    FAILED = "failed"


class BoulderStatus(str, Enum):
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    DONE = "done"
    ABORTED = "aborted"


@dataclass
class Verification:
    command: str
    description: str = ""
    passed: bool | None = None
    output: str = ""


@dataclass
class Task:
    id: str
    phase: str
    title: str
    description: str
    deliverable: str = ""
    steps: list[str] = field(default_factory=list)
    verifications: list[Verification] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 1
    attempts: int = 0
    notes: list[str] = field(default_factory=list)
    started_at: str | None = None
    finished_at: str | None = None


@dataclass
class Boulder:
    name: str
    plan_path: str
    objective: str = ""
    status: BoulderStatus = BoulderStatus.READY
    tasks: list[Task] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    def touch(self) -> None:
        self.updated_at = _now()

    def next_pending(self) -> Task | None:
        for t in self.tasks:
            if t.status in (TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.VERIFYING):
                return t
        return None

    def is_done(self) -> bool:
        return all(t.status == TaskStatus.DONE for t in self.tasks) and bool(self.tasks)

    def has_failures(self) -> bool:
        return any(t.status == TaskStatus.FAILED for t in self.tasks)


def _serialize(boulder: Boulder) -> dict:
    data = asdict(boulder)
    data["status"] = boulder.status.value
    for t, raw in zip(boulder.tasks, data["tasks"]):
        raw["status"] = t.status.value
    return data


def _deserialize(data: dict) -> Boulder:
    raw_tasks = data.pop("tasks", [])
    tasks = []
    for t in raw_tasks:
        verifs = [Verification(**v) for v in t.pop("verifications", [])]
        status = TaskStatus(t.pop("status", "pending"))
        tasks.append(Task(verifications=verifs, status=status, **t))
    status = BoulderStatus(data.pop("status", "ready"))
    return Boulder(tasks=tasks, status=status, **data)


class BoulderStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.boulders_dir = root / ".sisyphus" / "boulders"
        self.boulders_dir.mkdir(parents=True, exist_ok=True)

    def boulder_dir(self, name: str) -> Path:
        return self.boulders_dir / name

    def state_path(self, name: str) -> Path:
        return self.boulder_dir(name) / "boulder.yaml"

    def notepad_path(self, name: str) -> Path:
        return self.boulder_dir(name) / "notepad.md"

    def task_list_path(self, name: str) -> Path:
        return self.boulder_dir(name) / "task-list.md"

    def runs_dir(self, name: str) -> Path:
        d = self.boulder_dir(name) / "runs"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def run_log_path(self, name: str, task_id: str) -> Path:
        return self.runs_dir(name) / f"{task_id}.log"

    def exists(self, name: str) -> bool:
        return self.state_path(name).exists()

    def load(self, name: str) -> Boulder:
        path = self.state_path(name)
        if not path.exists():
            raise FileNotFoundError(f"No boulder named '{name}'. Run: atlas start {name}")
        return _deserialize(yaml.safe_load(path.read_text()))

    def save(self, boulder: Boulder) -> None:
        boulder.touch()
        self.boulder_dir(boulder.name).mkdir(parents=True, exist_ok=True)
        self.state_path(boulder.name).write_text(
            yaml.safe_dump(_serialize(boulder), sort_keys=False)
        )
        self._render_task_list(boulder)
        self._render_notepad(boulder)

    def list_all(self) -> list[Boulder]:
        out = []
        for d in sorted(self.boulders_dir.iterdir()) if self.boulders_dir.exists() else []:
            sp = d / "boulder.yaml"
            if sp.exists():
                try:
                    out.append(_deserialize(yaml.safe_load(sp.read_text())))
                except Exception:
                    continue
        return out

    def _render_task_list(self, boulder: Boulder) -> None:
        lines = [
            f"# Boulder: {boulder.name}",
            "",
            f"**Status:** `{boulder.status.value}`  ",
            f"**Plan:** `{boulder.plan_path}`  ",
            f"**Updated:** {boulder.updated_at}",
            "",
            "## Objective",
            "",
            boulder.objective or "_(none)_",
            "",
            "## Tasks",
            "",
        ]
        for t in boulder.tasks:
            mark = {
                TaskStatus.DONE: "[x]",
                TaskStatus.FAILED: "[!]",
                TaskStatus.RUNNING: "[~]",
                TaskStatus.VERIFYING: "[?]",
                TaskStatus.BLOCKED: "[-]",
            }.get(t.status, "[ ]")
            lines.append(f"- {mark} **{t.id}** — {t.title} _(status: {t.status.value}, attempts: {t.attempts})_")
        self.task_list_path(boulder.name).write_text("\n".join(lines))

    def _render_notepad(self, boulder: Boulder) -> None:
        lines = [
            f"# Notepad: {boulder.name}",
            "",
            "## Findings",
            "",
        ]
        lines.extend(f"- {f}" for f in boulder.findings) if boulder.findings else lines.append("_(none yet)_")
        lines.extend(["", "## Decisions", ""])
        lines.extend(f"- {d}" for d in boulder.decisions) if boulder.decisions else lines.append("_(none yet)_")
        lines.extend(["", "## Task Notes", ""])
        for t in boulder.tasks:
            if t.notes:
                lines.append(f"### {t.id} — {t.title}")
                lines.extend(f"- {n}" for n in t.notes)
                lines.append("")
        self.notepad_path(boulder.name).write_text("\n".join(lines))

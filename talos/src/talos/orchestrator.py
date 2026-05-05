from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path


class TodoStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


@dataclass
class Todo:
    id: str
    content: str
    status: TodoStatus = TodoStatus.PENDING
    titan: str = ""
    priority: str = "high"
    notes: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_todo(id: str, content: str, titan: str = "", priority: str = "high") -> Todo:
    now = _now()
    return Todo(
        id=id,
        content=content,
        titan=titan,
        priority=priority,
        created_at=now,
        updated_at=now,
    )


class TalosOrchestrator:
    def __init__(self, workdir: Path) -> None:
        self.workdir = workdir
        self.todos: list[Todo] = []
        self._counter = 0

    def add(self, content: str, titan: str = "", priority: str = "high") -> Todo:
        self._counter += 1
        tid = f"todo-{self._counter:03d}"
        todo = make_todo(tid, content, titan, priority)
        self.todos.append(todo)
        return todo

    def complete(self, todo_id: str, notes: list[str] | None = None) -> None:
        t = next((t for t in self.todos if t.id == todo_id), None)
        if t:
            t.status = TodoStatus.DONE
            t.updated_at = _now()
            if notes:
                t.notes.extend(notes)

    def in_progress(self, todo_id: str) -> None:
        t = next((t for t in self.todos if t.id == todo_id), None)
        if t:
            t.status = TodoStatus.IN_PROGRESS
            t.updated_at = _now()

    def cancel(self, todo_id: str) -> None:
        t = next((t for t in self.todos if t.id == todo_id), None)
        if t:
            t.status = TodoStatus.CANCELLED
            t.updated_at = _now()

    def pending_todos(self) -> list[Todo]:
        return [t for t in self.todos if t.status == TodoStatus.PENDING]

    def active_todos(self) -> list[Todo]:
        return [t for t in self.todos if t.status in (TodoStatus.IN_PROGRESS, TodoStatus.PENDING)]

    def done_todos(self) -> list[Todo]:
        return [t for t in self.todos if t.status == TodoStatus.DONE]

    def is_done(self) -> bool:
        return all(t.status in (TodoStatus.DONE, TodoStatus.CANCELLED) for t in self.todos)

    def spawn_titan(
        self,
        titan: str,
        subcommand: str,
        args: list[str],
        binary_path: str | None = None,
    ) -> tuple[int, str]:
        bin_map = {
            "coeus": binary_path or "coeus",
            "atlas": binary_path or "atlas",
            "iapetus": binary_path or "iapetus",
        }
        cmd = [bin_map.get(titan, titan), subcommand] + args
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(self.workdir),
                env={k: v for k, v in os.environ.items() if not k.endswith(("API_KEY", "SECRET", "TOKEN", "PASSWORD"))},
                capture_output=True,
                text=True,
                timeout=600,
            )
            output = (proc.stdout or "") + (proc.stderr or "")
            return proc.returncode, output
        except subprocess.TimeoutExpired as e:
            return 124, f"[TIMEOUT] {e}"
        except FileNotFoundError:
            return 127, f"[NOT FOUND] '{cmd[0]}' not in PATH"

    def dispatch_sequential(
        self,
        tasks: list[tuple[str, str, list[str]]],
        binary_map: dict[str, str] | None = None,
    ) -> dict[str, tuple[int, str]]:
        results: dict[str, tuple[int, str]] = {}
        for titan, subcommand, args in tasks:
            bin_path = (binary_map or {}).get(titan, "")
            code, out = self.spawn_titan(titan, subcommand, args, bin_path or None)
            results[f"{titan}:{subcommand}"] = (code, out)
        return results
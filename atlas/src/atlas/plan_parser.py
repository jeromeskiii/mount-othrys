from __future__ import annotations

import re
from pathlib import Path

from .boulder import Task, Verification, TaskStatus


_PHASE_RE = re.compile(r"^###\s+Phase\s+(\d+)\s*[—\-:]\s*(.+?)\s*$", re.MULTILINE)
_OBJECTIVE_RE = re.compile(r"^##\s+Objective\s*\n+([\s\S]*?)(?=\n##\s|\Z)", re.MULTILINE)
_DELIVERABLE_RE = re.compile(r"^\*\*Deliverable:\*\*\s*(.+?)\s*$", re.MULTILINE)
_STEPS_BLOCK_RE = re.compile(r"^\*\*Steps:\*\*\s*\n([\s\S]*?)(?=\n\*\*\w|\Z)", re.MULTILINE)
_VERIF_BLOCK_RE = re.compile(r"^\*\*Verification:\*\*\s*\n([\s\S]*?)(?=\n###\s|\Z)", re.MULTILINE)
_BULLET_RE = re.compile(r"^\s*[-*]\s+(.+?)\s*$", re.MULTILINE)
_NUMBERED_RE = re.compile(r"^\s*\d+\.\s+(.+?)\s*$", re.MULTILINE)
_BACKTICK_CMD_RE = re.compile(r"`([^`]+)`")


def _slug(s: str, max_len: int = 40) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:max_len].rstrip("-") or "task"


def _extract_objective(text: str) -> str:
    m = _OBJECTIVE_RE.search(text)
    return m.group(1).strip() if m else ""


def _split_phases(text: str) -> list[tuple[int, str, str]]:
    matches = list(_PHASE_RE.finditer(text))
    out = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out.append((int(m.group(1)), m.group(2).strip(), text[start:end]))
    return out


def _extract_steps(body: str) -> list[str]:
    block_match = _STEPS_BLOCK_RE.search(body)
    if not block_match:
        return []
    block = block_match.group(1)
    cleaned = re.sub(r"```[\s\S]*?```", "", block)
    nums = [m.group(1).strip() for m in _NUMBERED_RE.finditer(cleaned)]
    if nums:
        return nums
    return [m.group(1).strip() for m in _BULLET_RE.finditer(cleaned)]


def _extract_verifications(body: str) -> list[Verification]:
    block_match = _VERIF_BLOCK_RE.search(body)
    if not block_match:
        return []
    block = block_match.group(1)
    out: list[Verification] = []
    for line in block.splitlines():
        bullet = re.match(r"^\s*[-*]\s+(.+?)\s*$", line)
        if not bullet:
            continue
        desc = bullet.group(1).strip()
        cmds = _BACKTICK_CMD_RE.findall(desc)
        runnable = [c for c in cmds if _looks_runnable(c)]
        if runnable:
            for cmd in runnable:
                out.append(Verification(command=cmd, description=desc))
        else:
            out.append(Verification(command="", description=desc))
    return out


def _looks_runnable(cmd: str) -> bool:
    cmd = cmd.strip()
    if not cmd or "\n" in cmd:
        return False
    runners = (
        "pytest", "python", "uv ", "npm ", "pnpm ", "yarn ", "node ",
        "ruff", "mypy", "cargo ", "go ", "make ", "bash ", "sh ",
        "git ", "ls ", "cat ", "grep ", "rg ", "test ", "curl ",
        "cd ", "echo ", "mkdir ", "rm ", "cp ", "mv ", "touch ",
        "docker ", "kubectl ", "tsc", "eslint", "prettier", "jest",
        "vitest", "playwright", "deno ", "bun ", "tox", "poetry ",
        "pip ", "pipx ", "rustc ", "rustfmt", "clippy",
    )
    if cmd.startswith(runners):
        return True
    if cmd.startswith(("./", "../", "/")):
        return True
    if re.match(r"^[A-Z_][A-Z0-9_]*=", cmd):
        return True
    return False


def _extract_deliverable(body: str) -> str:
    m = _DELIVERABLE_RE.search(body)
    return m.group(1).strip() if m else ""


def _extract_description(body: str) -> str:
    deliverable_idx = body.find("**Deliverable:**")
    steps_idx = body.find("**Steps:**")
    if deliverable_idx == -1 and steps_idx == -1:
        return body.strip()[:500]
    cutoff = min([i for i in (deliverable_idx, steps_idx) if i != -1])
    return body[:cutoff].strip()


def parse_plan(plan_path: Path) -> tuple[str, list[Task]]:
    text = plan_path.read_text()
    objective = _extract_objective(text)
    tasks: list[Task] = []
    for phase_num, phase_title, body in _split_phases(text):
        tid = f"phase-{phase_num}-{_slug(phase_title, 30)}"
        tasks.append(
            Task(
                id=tid,
                phase=f"Phase {phase_num}",
                title=phase_title,
                description=_extract_description(body),
                deliverable=_extract_deliverable(body),
                steps=_extract_steps(body),
                verifications=_extract_verifications(body),
                status=TaskStatus.PENDING,
            )
        )
    return objective, tasks

from __future__ import annotations

import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path


MAX_OUTPUT_CHARS = 16_000
DEFAULT_TIMEOUT = 120

_ALLOWED_ENV_VARS = frozenset({
    "PATH", "HOME", "LANG", "LC_ALL", "SHELL", "USER", "LOGNAME",
    "TMPDIR", "TERM", "PWD",
})


@dataclass
class ToolContext:
    workdir: Path
    timeout: int = DEFAULT_TIMEOUT


def _truncate(s: str, limit: int = MAX_OUTPUT_CHARS) -> str:
    if len(s) <= limit:
        return s
    head = s[: limit // 2]
    tail = s[-limit // 2 :]
    omitted = len(s) - len(head) - len(tail)
    return f"{head}\n\n[... {omitted} chars truncated ...]\n\n{tail}"


def _resolve(ctx: ToolContext, raw: str) -> Path:
    p = Path(raw)
    if not p.is_absolute():
        p = (ctx.workdir / p).resolve()
    return p


def _under_workdir(ctx: ToolContext, p: Path) -> bool:
    try:
        p.resolve().relative_to(ctx.workdir.resolve())
        return True
    except ValueError:
        return False


def _safe_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k in _ALLOWED_ENV_VARS}


def tool_specs() -> list[dict]:
    return [
        {
            "name": "bash",
            "description": (
                "Run a shell command in the project working directory. "
                "Returns combined stdout/stderr (truncated if huge). Use for builds, tests, lint, "
                "git operations, file searches (rg/grep). Has a 120s timeout."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute"},
                    "timeout": {"type": "integer", "description": "Optional timeout seconds (default 120, max 600)"},
                },
                "required": ["command"],
            },
        },
        {
            "name": "read",
            "description": "Read a file from disk. Returns contents (truncated if huge). Path can be absolute or relative to workdir.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                },
                "required": ["path"],
            },
        },
        {
            "name": "write",
            "description": "Write a file. Creates parent directories. Overwrites existing content. Path must be inside the project workdir.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
        {
            "name": "edit",
            "description": (
                "Replace exact text in a file. old_string must occur exactly once unless replace_all=true. "
                "Path must be inside the project workdir."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "old_string": {"type": "string"},
                    "new_string": {"type": "string"},
                    "replace_all": {"type": "boolean"},
                },
                "required": ["path", "old_string", "new_string"],
            },
        },
        {
            "name": "list_dir",
            "description": "List entries in a directory (one per line, dirs suffixed with '/').",
            "input_schema": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    ]


def make_dispatcher(ctx: ToolContext):
    def dispatch(name: str, args: dict) -> tuple[str, bool]:
        try:
            if name == "bash":
                return _run_bash(ctx, args)
            if name == "read":
                return _do_read(ctx, args)
            if name == "write":
                return _do_write(ctx, args)
            if name == "edit":
                return _do_edit(ctx, args)
            if name == "list_dir":
                return _do_list(ctx, args)
            return f"Unknown tool: {name}", True
        except Exception as e:
            return f"{type(e).__name__}: {e}", True

    return dispatch


def _run_bash(ctx: ToolContext, args: dict) -> tuple[str, bool]:
    raw_cmd = args.get("command", "").strip()
    if not raw_cmd:
        return "Empty command", True
    timeout = min(int(args.get("timeout", ctx.timeout)), 600)
    try:
        parsed = shlex.split(raw_cmd)
    except ValueError as e:
        return f"Invalid command syntax: {e}", True
    if not parsed:
        return "Empty command", True
    try:
        proc = subprocess.run(
            parsed,
            shell=False,
            capture_output=True,
            text=True,
            cwd=str(ctx.workdir),
            timeout=timeout,
            env=_safe_env(),
        )
    except FileNotFoundError:
        return f"Command not found: {parsed[0]}", True
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or "") + (e.stderr or "")
        return f"[TIMEOUT after {timeout}s]\n{_truncate(out)}", True
    body = f"[exit {proc.returncode}]\n"
    if proc.stdout:
        body += f"--- stdout ---\n{proc.stdout}"
    if proc.stderr:
        body += f"\n--- stderr ---\n{proc.stderr}"
    return _truncate(body), proc.returncode != 0


def _do_read(ctx: ToolContext, args: dict) -> tuple[str, bool]:
    p = _resolve(ctx, args["path"])
    if not _under_workdir(ctx, p):
        return f"Refused: {p} is outside workdir {ctx.workdir}", True
    if not p.exists():
        return f"Not found: {p}", True
    if p.is_dir():
        return f"Is a directory: {p}", True
    return _truncate(p.read_text(errors="replace")), False


def _do_write(ctx: ToolContext, args: dict) -> tuple[str, bool]:
    p = _resolve(ctx, args["path"])
    if not _under_workdir(ctx, p):
        return f"Refused: {p} is outside workdir {ctx.workdir}", True
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(args["content"])
    return f"Wrote {len(args['content'])} chars to {p}", False


def _do_edit(ctx: ToolContext, args: dict) -> tuple[str, bool]:
    p = _resolve(ctx, args["path"])
    if not _under_workdir(ctx, p):
        return f"Refused: {p} is outside workdir {ctx.workdir}", True
    if not p.exists():
        return f"Not found: {p}", True
    text = p.read_text()
    old = args["old_string"]
    new = args["new_string"]
    replace_all = bool(args.get("replace_all", False))
    if old not in text:
        return f"old_string not found in {p}", True
    if not replace_all and text.count(old) > 1:
        return f"old_string occurs {text.count(old)} times in {p}; pass replace_all=true or expand context", True
    updated = text.replace(old, new) if replace_all else text.replace(old, new, 1)
    p.write_text(updated)
    return f"Edited {p}", False


def _do_list(ctx: ToolContext, args: dict) -> tuple[str, bool]:
    p = _resolve(ctx, args["path"])
    if not p.exists():
        return f"Not found: {p}", True
    if not p.is_dir():
        return f"Not a directory: {p}", True
    entries = []
    for child in sorted(p.iterdir()):
        entries.append(child.name + ("/" if child.is_dir() else ""))
    return "\n".join(entries) or "(empty)", False

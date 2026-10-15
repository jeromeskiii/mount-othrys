from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from othrys import LLMConfig

from . import __version__
from .classifier import classify, RequestType
from .delegation import build_delegation_prompt
from .llm import TalosLLM
from .orchestrator import TalosOrchestrator, Todo, TodoStatus
from .prompts import (
    TALOS_IDENTITY,
    TRIVIAL_HANDLER_SYSTEM,
    EXPLICIT_HANDLER_SYSTEM,
    EXPLORATORY_HANDLER_SYSTEM,
    OPEN_ENDED_HANDLER_SYSTEM,
    AMBIGUOUS_HANDLER_SYSTEM,
)
from .session import create_session, load_session, save_session, append_message, update_todos, list_sessions
from .titan_router import (
    route_request,
    resolve_titan_command,
    TITAN_COEUS,
    TITAN_ATLAS,
    TITAN_IAPETUS,
    TITAN_DIRECT,
)
from .tools import make_dispatcher, tool_specs


def _print(obj: object, *, as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(obj, indent=2, default=str))
    else:
        print(obj)


def _session_todos_to_runtime(todos: list[dict[str, Any]]) -> list[Todo]:
    runtime: list[Todo] = []
    for raw in todos:
        runtime.append(
            Todo(
                id=str(raw.get("id", "")),
                content=str(raw.get("content", "")),
                status=TodoStatus(str(raw.get("status", TodoStatus.PENDING.value))),
                titan=str(raw.get("titan", "")),
                priority=str(raw.get("priority", "high")),
                notes=[str(n) for n in raw.get("notes", [])],
                created_at=str(raw.get("created_at", "")),
                updated_at=str(raw.get("updated_at", "")),
            )
        )
    return runtime


def _llm(args: argparse.Namespace) -> TalosLLM:
    return TalosLLM(
        LLMConfig(
            model=args.model,
            api_key=args.api_key,
            thinking_budget=args.thinking_budget,
            max_tokens=args.max_tokens,
        )
    )


def _workdir(args: argparse.Namespace) -> Path:
    return Path(args.workdir or args.root or ".").resolve()


def _emit(event: str, payload: dict[str, Any]) -> None:
    if event == "classify":
        print(f"  [{payload['type'].value}] {payload['reason']}", flush=True)
    elif event == "titan_route":
        print(f"  → {payload['titan']}/{payload['action']}: {payload['reason']}", flush=True)
    elif event == "todo_add":
        print(f"  + todo: {payload['content'][:60]}", flush=True)
    elif event == "todo_done":
        print(f"  ✓ {payload['id']}: {payload['content'][:60]}", flush=True)


def cmd_session(args: argparse.Namespace) -> None:
    if args.sub == "new":
        s = create_session()
        _print({"session": s.session_id, "created": s.created_at}, as_json=args.json)
        return
    if args.sub == "list":
        sessions = list_sessions()
        _print(
            [{"id": s.session_id, "titan": s.titan, "status": s.status, "updated": s.updated_at} for s in sessions],
            as_json=args.json,
        )
        return
    if args.sub == "show":
        session_obj = load_session(args.session_id)
        if not session_obj:
            _print({"error": f"Session {args.session_id} not found"}, as_json=args.json)
            sys.exit(1)
        _print(
            {
                "session_id": session_obj.session_id,
                "titan": session_obj.titan,
                "objective": session_obj.objective,
                "status": session_obj.status,
                "messages": len(session_obj.messages),
                "todos": session_obj.todos,
            },
            as_json=args.json,
        )


def cmd_ask(args: argparse.Namespace) -> None:
    workdir = _workdir(args)
    session = None
    if args.session:
        if not args.session_id:
            _print({"error": "--session requires --session-id"}, as_json=args.json)
            sys.exit(1)
        session = load_session(args.session_id or "")
        if not session:
            _print({"error": f"Session {args.session_id} not found"}, as_json=args.json)
            sys.exit(1)

    message = args.message or (sys.stdin.read() if args.stdin else "")
    if not message.strip():
        _print({"error": "No message provided"}, as_json=args.json)
        sys.exit(1)

    req_type, reason = classify(message)
    if not args.json:
        print(f"  Classification: {req_type.value} — {reason}")

    if session:
        append_message(session, "user", message)

    if req_type == RequestType.AMBIGUOUS:
        system = AMBIGUOUS_HANDLER_SYSTEM
        prompt = f"\n# User Request\n\n{message}\n\nAsk ONE clarifying question."
        llm = _llm(args)
        ambiguous_response = llm.call(system=system, messages=[{"role": "user", "content": prompt}])
        print(f"\n{ambiguous_response}")
        if session:
            append_message(session, "assistant", ambiguous_response)
        return

    if args.session and session:
        orch = TalosOrchestrator(workdir)
        orch.todos = _session_todos_to_runtime(session.todos)

    route = route_request(message, session.session_id if session else None)
    if not args.json:
        print(f"  Route: {route.titan} → {route.action}")
        if route.subcommand:
            print(f"  Subcommand: {route.subcommand}")

    if route.titan in (TITAN_COEUS, TITAN_ATLAS, TITAN_IAPETUS):
        subcmd: str | None
        if route.titan == TITAN_COEUS:
            subcmd = route.subcommand or "interview"
            t_args = list(args.titan_args) if args.titan_args else [message]
        elif route.titan == TITAN_ATLAS:
            subcmd = route.subcommand or "run"
            t_args = list(args.titan_args)
        elif route.titan == TITAN_IAPETUS:
            subcmd = route.subcommand or "execute"
            t_args = list(args.titan_args) if args.titan_args else [message]
        else:
            subcmd = route.subcommand
            t_args = list(args.titan_args)

        cmd, env_extra = resolve_titan_command(route.titan, subcmd, t_args)
        if not args.json:
            print(f"\n  Spawning: {' '.join(cmd)}")
        env = {**os.environ, **env_extra, "TALOS_SESSION": session.session_id if session else ""}
        proc = subprocess.run(
            cmd, cwd=str(workdir), env=env, capture_output=True, text=True, timeout=600
        )
        print(proc.stdout or "")
        if proc.stderr:
            print(proc.stderr, file=sys.stderr)
        sys.exit(proc.returncode)

    if req_type == RequestType.TRIVIAL:
        system = TRIVIAL_HANDLER_SYSTEM
        tools = tool_specs()
    elif req_type == RequestType.EXPLICIT:
        system = EXPLICIT_HANDLER_SYSTEM
        tools = tool_specs()
    elif req_type == RequestType.EXPLORATORY:
        system = EXPLORATORY_HANDLER_SYSTEM
        tools = tool_specs()
    else:
        system = OPEN_ENDED_HANDLER_SYSTEM
        tools = tool_specs()

    dispatch = make_dispatcher(workdir=workdir)

    def on_event(event: str, payload: dict[str, Any]) -> None:
        if args.json:
            return
        if event == "assistant_turn":
            print(f"  iter={payload['iteration']} tools={payload['tool_uses']}", flush=True)
        elif event == "tool_use":
            print(f"  · {payload['name']}", flush=True)

    llm = _llm(args)
    user_prompt = f"\n# Request\n\n{message}\n\nWorkdir: {workdir}"
    result = llm.run_agent(
        system=system,
        user_prompt=user_prompt,
        tools=tools,
        tool_dispatch=dispatch,
        max_iterations=50,
        on_event=on_event if not args.json else None,
    )

    if session:
        append_message(session, "assistant", result.final_text)

    if not args.json:
        print(f"\n{result.final_text}")
    else:
        _print(
            {
                "type": req_type.value,
                "route": route.titan,
                "summary": result.final_text[:500],
                "iterations": result.iterations,
            },
            as_json=True,
        )


def cmd_todos(args: argparse.Namespace) -> None:
    workdir = _workdir(args)
    orch = TalosOrchestrator(workdir)
    session = None

    if args.session_id:
        session = load_session(args.session_id)
        if session:
            orch.todos = _session_todos_to_runtime(session.todos)

    if args.add:
        for item in args.add:
            t = orch.add(item, titan=args.titan or "")
            if not args.json:
                print(f"Added: {t.id} — {t.content}")
            if args.session_id and session:
                update_todos(session, [t.__dict__ for t in orch.todos])

    elif args.done:
        orch.complete(args.done)
        if args.session_id and session:
            update_todos(session, [t.__dict__ for t in orch.todos])

    elif args.cancel:
        orch.cancel(args.cancel)
        if args.session_id and session:
            update_todos(session, [t.__dict__ for t in orch.todos])

    else:
        todos = orch.todos
        if args.filter:
            if args.filter == "pending":
                todos = orch.pending_todos()
            elif args.filter == "active":
                todos = orch.active_todos()
            elif args.filter == "done":
                todos = orch.done_todos()
        _print(
            [{"id": t.id, "content": t.content, "status": t.status.value, "titan": t.titan} for t in todos],
            as_json=args.json,
        )


def main() -> None:
    p = argparse.ArgumentParser(prog="talos", description="Talos — primary orchestrator for the Kronos Titan system")
    p.add_argument("--version", action="version", version=f"talos {__version__}")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("--root", default=".", help="project root")
    p.add_argument("--workdir", default=None, help="working directory")
    p.add_argument("--model", default="claude-opus-4-5")
    p.add_argument("--api-key", default=None, help="ANTHROPIC_API_KEY override")
    p.add_argument("--thinking-budget", type=int, default=32_000)
    p.add_argument("--max-tokens", type=int, default=64_000)

    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("ask", help="process a natural-language request")
    s.add_argument("message", nargs="?", help="request text")
    s.add_argument("--stdin", action="store_true")
    s.add_argument("--session", action="store_true", help="use session")
    s.add_argument("--session-id", default=None)
    s.add_argument("--titan-args", nargs="*", default=[], help="args forwarded to Titan")
    s.set_defaults(func=cmd_ask)

    s = sub.add_parser("session", help="manage sessions")
    s.add_argument("sub", choices=["new", "list", "show"])
    s.add_argument("--session-id", default=None)
    s.set_defaults(func=cmd_session)

    s = sub.add_parser("todos", help="manage todo list")
    s.add_argument("--add", action="append", default=[], help="add todo")
    s.add_argument("--done", default=None, help="complete a todo by id")
    s.add_argument("--cancel", default=None, help="cancel a todo by id")
    s.add_argument("--filter", choices=["pending", "active", "done", "all"], default="all")
    s.add_argument("--session-id", default=None)
    s.add_argument("--titan", default="")
    s.set_defaults(func=cmd_todos)

    s = sub.add_parser("route", help="classify and route a request without executing")
    s.add_argument("message", help="request text")
    s.set_defaults(func=lambda args: _print(route_request(args.message).__dict__, as_json=args.json))

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

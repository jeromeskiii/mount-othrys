from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .boulder import Boulder, BoulderStatus, BoulderStore, TaskStatus
from .llm import AtlasLLM, LLMConfig
from .orchestrator import Orchestrator
from .plan_parser import parse_plan


def _print(obj, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(obj, indent=2, default=str))
    else:
        print(obj)


def _store(args) -> BoulderStore:
    return BoulderStore(Path(args.root).resolve())


def _llm(args) -> AtlasLLM:
    return AtlasLLM(LLMConfig(model=args.model, api_key=args.api_key))


def _resolve_plan_path(args, name: str) -> tuple[Path, bool]:
    """Resolve plan path. Returns (Path, is_manifest)."""
    if args.plan:
        p = Path(args.plan).resolve()
        return p, p.suffix == ".json"
    
    # Check for manifest first
    manifest = Path(args.root).resolve() / ".sisyphus" / "plans" / f"{name}.manifest.json"
    if manifest.exists():
        return manifest, True
        
    candidate = Path(args.root).resolve() / ".sisyphus" / "plans" / f"{name}.md"
    if candidate.exists():
        return candidate, False
    raise FileNotFoundError(
        f"Plan not found. Looked at: {candidate}. Pass --plan <path> or run `coeus plan {name}` first."
    )


def cmd_start(args) -> None:
    store = _store(args)
    name = args.name
    if store.exists(name) and not args.force:
        _print({"error": f"Boulder '{name}' already exists. Use --force to overwrite."}, as_json=args.json)
        sys.exit(1)
    
    plan_path, is_manifest = _resolve_plan_path(args, name)
    
    if is_manifest:
        # Phase 3: Formal Handshake Protocol
        # Load from JSON manifest
        data = json.loads(plan_path.read_text())
        objective = data.get("objective", f"Campaign from {plan_path.name}")
        tasks = []
        from .boulder import Task
        for t in data.get("tasks", []):
            tasks.append(Task(
                id=t.get("id", "T1"),
                phase=t.get("phase", "General"),
                title=t.get("title", "Task"),
                description=t.get("description", ""),
                deliverable=t.get("deliverable", ""),
                priority=int(t.get("priority", 1))
            ))
    else:
        objective, tasks = parse_plan(plan_path)

    if not tasks:
        _print({"error": f"No tasks found in plan {plan_path}"}, as_json=args.json)
        sys.exit(1)
        
    boulder = Boulder(name=name, plan_path=str(plan_path), objective=objective, tasks=tasks)
    store.save(boulder)
    payload = {
        "boulder": name,
        "plan": str(plan_path),
        "tasks": len(tasks),
        "task_ids": [t.id for t in tasks],
        "state_file": str(store.state_path(name)),
    }
    if args.json:
        _print(payload, as_json=True)
    else:
        print(f"Boulder created: {name}")
        print(f"  Plan: {plan_path}")
        print(f"  Tasks: {len(tasks)}")
        for t in tasks:
            print(f"    - {t.id}: {t.title}")
        print(f"\nRun: atlas run {name}    (sequential)  or  atlas step {name}    (one task)")


def _emit_event(event: str, payload: dict) -> None:
    if event == "task_start":
        print(f"\n▶ Task {payload['id']} (attempt {payload['attempt']}): {payload['title']}", flush=True)
    elif event == "task_verify":
        print(f"  ↳ verifying…", flush=True)
    elif event == "tool_use":
        print(f"  · {payload['name']}", flush=True)


def cmd_step(args) -> None:
    store = _store(args)
    boulder = store.load(args.name)
    if boulder.status == BoulderStatus.DONE:
        _print({"status": "done", "message": "Boulder already complete."}, as_json=args.json)
        return
    llm = _llm(args)
    orch = Orchestrator(store, llm, Path(args.workdir or args.root).resolve(), on_event=None if args.json else _emit_event)
    outcome = orch.step(boulder)
    if outcome is None:
        _print({"status": boulder.status.value, "message": "No pending tasks."}, as_json=args.json)
        return
    payload = {
        "task_id": outcome.task_id,
        "title": outcome.title,
        "success": outcome.success,
        "blocked": outcome.blocked,
        "verdict": outcome.verdict,
        "reason": outcome.reason,
        "summary": outcome.summary,
        "boulder_status": boulder.status.value,
    }
    if args.json:
        _print(payload, as_json=True)
    else:
        mark = "✓" if outcome.success else ("⛔" if outcome.blocked else "✗")
        print(f"\n{mark} {outcome.task_id} → {outcome.verdict}: {outcome.reason}")
        if outcome.summary:
            print(f"  summary: {outcome.summary[:200]}")
        print(f"  boulder: {boulder.status.value}")


def cmd_run(args) -> None:
    store = _store(args)
    boulder = store.load(args.name)
    llm = _llm(args)
    orch = Orchestrator(store, llm, Path(args.workdir or args.root).resolve(), on_event=None if args.json else _emit_event)
    outcomes = orch.run_to_completion(boulder, max_steps=args.max_steps)
    payload = {
        "boulder": args.name,
        "status": boulder.status.value,
        "steps": len(outcomes),
        "results": [
            {"task_id": o.task_id, "success": o.success, "blocked": o.blocked, "verdict": o.verdict}
            for o in outcomes
        ],
    }
    if args.json:
        _print(payload, as_json=True)
    else:
        print(f"\n=== Boulder {args.name}: {boulder.status.value} ===")
        for o in outcomes:
            mark = "✓" if o.success else ("⛔" if o.blocked else "✗")
            print(f"  {mark} {o.task_id}: {o.verdict}")


def cmd_status(args) -> None:
    store = _store(args)
    boulder = store.load(args.name)
    payload = {
        "boulder": boulder.name,
        "status": boulder.status.value,
        "plan": boulder.plan_path,
        "objective": boulder.objective,
        "tasks": [
            {"id": t.id, "title": t.title, "status": t.status.value, "attempts": t.attempts}
            for t in boulder.tasks
        ],
        "task_list": str(store.task_list_path(args.name)),
        "notepad": str(store.notepad_path(args.name)),
    }
    if args.json:
        _print(payload, as_json=True)
    else:
        print(f"Boulder: {boulder.name}")
        print(f"Status:  {boulder.status.value}")
        print(f"Plan:    {boulder.plan_path}")
        print("Tasks:")
        for t in boulder.tasks:
            mark = {
                TaskStatus.DONE: "✓",
                TaskStatus.FAILED: "✗",
                TaskStatus.BLOCKED: "⛔",
                TaskStatus.RUNNING: "▶",
                TaskStatus.VERIFYING: "?",
            }.get(t.status, "·")
            print(f"  {mark} {t.id} [{t.status.value}, attempts={t.attempts}] — {t.title}")


def cmd_list(args) -> None:
    store = _store(args)
    boulders = store.list_all()
    if args.json:
        _print(
            [
                {"name": b.name, "status": b.status.value, "tasks": len(b.tasks), "updated": b.updated_at}
                for b in boulders
            ],
            as_json=True,
        )
        return
    if not boulders:
        print("No boulders.")
        return
    for b in boulders:
        done = sum(1 for t in b.tasks if t.status == TaskStatus.DONE)
        print(f"  {b.name}  [{b.status.value}]  {done}/{len(b.tasks)} tasks  (updated {b.updated_at})")


def cmd_show(args) -> None:
    store = _store(args)
    if args.what == "tasks":
        path = store.task_list_path(args.name)
    elif args.what == "notepad":
        path = store.notepad_path(args.name)
    elif args.what == "log":
        if not args.task:
            print("--task <task-id> required for log", file=sys.stderr)
            sys.exit(1)
        runs = sorted(store.runs_dir(args.name).glob(f"{args.task}-attempt-*.log"))
        if not runs:
            print(f"No logs for task {args.task}", file=sys.stderr)
            sys.exit(1)
        path = runs[-1]
    else:
        print(f"Unknown view: {args.what}", file=sys.stderr)
        sys.exit(1)
    if not path.exists():
        print(f"Not found: {path}", file=sys.stderr)
        sys.exit(1)
    print(path.read_text())


def cmd_abort(args) -> None:
    store = _store(args)
    boulder = store.load(args.name)
    boulder.status = BoulderStatus.ABORTED
    store.save(boulder)
    _print({"boulder": args.name, "status": "aborted"}, as_json=args.json)


def cmd_design(args) -> None:
    """Initialize or preview a design boulder from a natural language objective."""
    import re
    store = _store(args)
    raw_name = getattr(args, "name", None) or "design"
    slug = re.sub(r"[^a-z0-9-]+", "-", raw_name.lower()).strip("-")[:40] or "design"
    prompt = raw_name

    plan_file = Path(args.root).resolve() / ".sisyphus" / "plans" / f"{slug}.md"
    if not plan_file.exists():
        plan_file.parent.mkdir(parents=True, exist_ok=True)
        plan_file.write_text(f"# Plan: {slug}\n\nObjective: {prompt}\n\n## Tasks\n- [ ] Task 1: Analyze and design architecture for {prompt}\n")

    from .boulder import Boulder, Task
    task = Task(id="T1", phase="Design", title=f"Design {slug}", description=prompt, priority=1)
    boulder = Boulder(name=slug, plan_path=str(plan_file), objective=prompt, tasks=[task])
    store.save(boulder)
    payload = {
        "boulder": slug,
        "objective": prompt,
        "plan": str(plan_file),
        "tasks": len(boulder.tasks),
        "state_file": str(store.state_path(slug)),
    }
    if args.json:
        _print(payload, as_json=True)
    else:
        print(f"Atlas Design Boulder created: {slug}")
        print(f"  Plan: {plan_file}")
        print(f"  Objective: {prompt}")


def main() -> None:
    p = argparse.ArgumentParser(prog="atlas", description="Atlas — sequential orchestrator for Coeus plans")
    p.add_argument("--version", action="version", version=f"atlas {__version__}")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("--root", default=".", help="project root containing .sisyphus/ (default: cwd)")
    p.add_argument("--workdir", default=None, help="working directory subagents operate in (default: --root)")
    p.add_argument("--model", default="claude-opus-4-5", help="Anthropic model")
    p.add_argument("--api-key", default=None, help="ANTHROPIC_API_KEY override")

    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("start", help="initialize a boulder from a Coeus plan")
    s.add_argument("name")
    s.add_argument("--plan", default=None, help="explicit plan path (defaults to .sisyphus/plans/<name>.md)")
    s.add_argument("--force", action="store_true")
    s.set_defaults(func=cmd_start)

    s = sub.add_parser("step", help="run the next pending task")
    s.add_argument("name")
    s.set_defaults(func=cmd_step)

    s = sub.add_parser("run", help="run all tasks sequentially until done or blocked")
    s.add_argument("name")
    s.add_argument("--max-steps", type=int, default=50)
    s.set_defaults(func=cmd_run)

    s = sub.add_parser("status", help="show boulder status")
    s.add_argument("name")
    s.set_defaults(func=cmd_status)

    s = sub.add_parser("list", help="list all boulders")
    s.set_defaults(func=cmd_list)

    s = sub.add_parser("show", help="show task list, notepad, or run log")
    s.add_argument("name")
    s.add_argument("what", choices=["tasks", "notepad", "log"])
    s.add_argument("--task", default=None)
    s.set_defaults(func=cmd_show)

    s = sub.add_parser("abort", help="mark boulder aborted")
    s.add_argument("name")
    s.set_defaults(func=cmd_abort)

    s = sub.add_parser("design", help="design architecture and initialize boulder")
    s.add_argument("name", nargs="?", default="design", help="boulder name or design objective")
    s.set_defaults(func=cmd_design)

    args = p.parse_args()
    try:
        args.func(args)
    except FileNotFoundError as e:
        _print({"error": str(e)}, as_json=args.json)
        sys.exit(1)
    except RuntimeError as e:
        _print({"error": str(e)}, as_json=args.json)
        sys.exit(2)


if __name__ == "__main__":
    main()

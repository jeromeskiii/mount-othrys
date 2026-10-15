from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

from . import __version__
from .config import DEFAULT_CONFIG_PATH, KronosConfig, load_config, save_config
from .dispatch import build_dispatch_plan
from .llm import KronosLLM
from .registry import get_titan, list_titans
from .router import route, route_explicit
from .storage import FortressStore


def _get_store() -> FortressStore:
    db_path = Path.home() / ".sisyphus" / "fortress.db"
    return FortressStore(db_path)


def _get_llm(config: KronosConfig) -> KronosLLM | None:
    try:
        return KronosLLM(api_key=config.api_key)
    except Exception:
        return None


def _print(obj, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(obj, indent=2, default=str))
    else:
        print(obj)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _resolve_invocation(command: str) -> tuple[list[str], dict[str, str]]:
    repo_root = _repo_root()
    module_invocations: dict[str, tuple[Path, str, list[Path]]] = {
        "coeus": (
            repo_root / "coeus" / ".venv" / "bin" / "python",
            "coeus",
            [repo_root / "coeus" / "src", repo_root / "othrys" / "src"],
        ),
        "atlas": (
            repo_root / "atlas" / ".venv" / "bin" / "python",
            "atlas",
            [repo_root / "atlas" / "src", repo_root / "othrys" / "src"],
        ),
        "iapetus": (
            repo_root / "iapetus" / ".venv" / "bin" / "python",
            "iapetus",
            [repo_root / "iapetus" / "src", repo_root / "atlas" / "src", repo_root / "othrys" / "src"],
        ),
        "talos": (
            repo_root / "talos" / ".venv" / "bin" / "python",
            "talos",
            [repo_root / "talos" / "src", repo_root / "iapetus" / "src", repo_root / "atlas" / "src", repo_root / "othrys" / "src"],
        ),
    }
    candidate = module_invocations.get(command)
    if candidate and candidate[0].exists():
        python_bin, module_name, source_paths = candidate
        env = {**os.environ}
        py_path_parts = [str(path) for path in source_paths]
        if env.get("PYTHONPATH"):
            py_path_parts.append(env["PYTHONPATH"])
        env["PYTHONPATH"] = os.pathsep.join(py_path_parts)
        return [str(python_bin), "-m", module_name], env
    return [command], {**os.environ}


def _run_command(command: str, args: list[str], workdir: str = ".") -> int:
    resolved, env = _resolve_invocation(command)
    cmd = resolved + args
    try:
        proc = subprocess.run(cmd, cwd=workdir, timeout=600, env=env)
        return proc.returncode
    except FileNotFoundError as e:
        print(f"Error: failed to execute '{' '.join(resolved)}': {e}", file=sys.stderr)
        return 127
    except subprocess.TimeoutExpired:
        print(f"Error: {command} timed out after 600s", file=sys.stderr)
        return 124


def cmd_route(args) -> None:
    config = load_config(Path(args.config_file) if hasattr(args, "config_file") and args.config_file else None)
    llm = _get_llm(config)
    message = args.message
    titan, reason = route(message, llm=llm)
    result = {
        "message": message[:200],
        "titan": titan.name.lower(),
        "titan_key": titan.mode.value,
        "domain": titan.domain.value,
        "reason": reason,
        "cli_command": titan.cli_command,
    }
    if args.json:
        _print(result, as_json=True)
    else:
        print(f"  → {titan.name} ({titan.domain.value})")
        print(f"    Reason: {reason}")
        print(f"    Command: {titan.cli_command}")
    if args.execute:
        try:
            plan = build_dispatch_plan(titan.mode.value, message, args.titan_args)
        except ValueError as e:
            print(str(e), file=sys.stderr)
            sys.exit(2)
        if not args.json:
            print(f"    Dispatch: {plan.command} {' '.join(plan.args)}")
            print(f"    Wiring: {plan.explanation}")
        code = _run_command(plan.command, plan.args, workdir=args.workdir or ".")
        sys.exit(code)


def cmd_titan(args) -> None:
    if args.list:
        titans = list_titans()
        if args.json:
            _print([
                {
                    "name": t.name.lower(),
                    "domain": t.domain.value,
                    "model": t.model,
                    "description": t.description,
                    "capabilities": t.capabilities,
                    "cli": t.cli_command,
                }
                for t in titans
            ], as_json=True)
        else:
            print("Available Titans:\n")
            for t in titans:
                print(f"  {t.name:<10} ({t.domain.value})")
                print(f"             {t.description}")
                print(f"             model: {t.model}, cli: {t.cli_command}")
                print()
        return

    titan = get_titan(args.name)
    if args.json:
        _print({
            "name": titan.name.lower(),
            "domain": titan.domain.value,
            "model": titan.model,
            "description": titan.description,
            "capabilities": titan.capabilities,
            "tool_access": titan.tool_access,
            "tool_blocked": titan.tool_blocked,
            "cli": titan.cli_command,
            "thinking_budget": titan.thinking_budget,
            "max_tokens": titan.max_tokens,
        }, as_json=True)
    else:
        print(f"Titan: {titan.name}")
        print(f"Domain: {titan.domain.value}")
        print(f"Model: {titan.model}")
        print(f"Description: {titan.description}")
        print(f"Capabilities: {', '.join(titan.capabilities)}")
        print(f"Tool access: {', '.join(titan.tool_access)}")
        print(f"Tool blocked: {', '.join(titan.tool_blocked) or '(none)'}")
        print(f"CLI: {titan.cli_command}")
        print(f"Thinking budget: {titan.thinking_budget}")
        print(f"Max tokens: {titan.max_tokens}")


def cmd_ask(args) -> None:
    config = load_config(Path(args.config_file) if hasattr(args, "config_file") and args.config_file else None)
    llm = _get_llm(config)
    titan, reason = route(args.message, llm=llm)
    if not args.json:
        print(f"  Classification: {titan.name} ({titan.domain.value})")
        print(f"  Reason: {reason}")

    titan_args = args.titan_args or []
    if args.titan:
        explicit = route_explicit(args.titan)
        titan = explicit
        if not args.json:
            print(f"  Override: → {explicit.name}")

    # Phase 1: Shared Blackboard Integration
    store = _get_store()
    campaign_id = store.create_campaign(args.message, lead_titan=titan.mode.value)
    if not args.json:
        print(f"  Campaign: {campaign_id[:8]}… (stored in Fortress)")

    try:
        plan = build_dispatch_plan(titan.mode.value, args.message, titan_args)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(2)
    if not args.json:
        print(f"  Dispatch: {plan.command} {' '.join(plan.args)}")
        print(f"  Wiring: {plan.explanation}")
    code = _run_command(plan.command, plan.args, workdir=args.workdir or ".")
    sys.exit(code)


def cmd_config(args) -> None:
    config_path = Path(args.config_file) if hasattr(args, "config_file") and args.config_file else None
    config = load_config(config_path)

    changed = False
    if args.set_model:
        config.default_model = args.set_model
        changed = True
    if args.set_api_key:
        config.api_key = args.set_api_key
        changed = True
    if args.set_thinking:
        config.thinking_budget = int(args.set_thinking)
        changed = True
    if args.set_max_tokens:
        config.max_tokens = int(args.set_max_tokens)
        changed = True

    if changed:
        save_config(config, config_path)
        if not args.json:
            print(f"Configuration saved to {config_path or DEFAULT_CONFIG_PATH}")

    if args.json:
        _print({
            "default_model": config.default_model,
            "api_key": "***" if config.api_key else None,
            "thinking_budget": config.thinking_budget,
            "max_tokens": config.max_tokens,
            "timeout": config.timeout,
            "workdir": config.workdir,
            "titan_overrides": config.titan_overrides,
        }, as_json=True)
    else:
        print(f"  Model:           {config.default_model}")
        print(f"  API Key:         {'***' if config.api_key else '(not set)'}")
        print(f"  Thinking Budget: {config.thinking_budget}")
        print(f"  Max Tokens:      {config.max_tokens}")
        print(f"  Timeout:         {config.timeout}")
        print(f"  Workdir:         {config.workdir}")
        if config.titan_overrides:
            print(f"  Titan Overrides: {config.titan_overrides}")


def cmd_campaigns(args) -> None:
    store = _get_store()
    if args.id:
        ctx = store.get_campaign_context(args.id)
        if args.json:
            _print(ctx, as_json=True)
        else:
            print(f"Campaign Context: {args.id}")
            print("-" * 40)
            print("Findings:")
            for f in ctx["findings"]:
                print(f"  [{f['titan']}] {f['key']}: {f['value']}")
            print("\nLatest Context Payload:")
            print(json.dumps(ctx["latest_context"], indent=2))
        return

    with sqlite3.connect(store.db_path) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT id, objective, lead_titan, created_at FROM campaigns ORDER BY created_at DESC")
        rows = cur.fetchall()
        if args.json:
            _print([dict(r) for r in rows], as_json=True)
        else:
            print(f"{'ID':<10} {'Lead':<10} {'Objective'}")
            print("-" * 60)
            for r in rows:
                print(f"{r['id'][:8]:<10} {r['lead_titan']:<10} {r['objective'][:40]}")


def main() -> None:
    p = argparse.ArgumentParser(prog="kronos", description="Kronos — unified Titan intelligence")
    p.add_argument("--version", action="version", version=f"kronos {__version__}")
    p.add_argument("--json", action="store_true")
    p.add_argument("--workdir", default=".", help="working directory")

    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("route", help="classify and route a request to the appropriate Titan")
    s.add_argument("message", help="natural-language request")
    s.add_argument("--execute", action="store_true", help="also execute the routed command")
    s.add_argument("--titan-args", nargs="*", default=[], help="args to forward to Titan")
    s.set_defaults(func=cmd_route)

    s = sub.add_parser("titan", help="show Titan info or list all Titans")
    s.add_argument("name", nargs="?", default=None, help="Titan name (coeus, atlas, iapetus, talos, themis, heracles, coordinator)")
    s.add_argument("--list", action="store_true", help="list all Titans")
    s.set_defaults(func=cmd_titan)

    s = sub.add_parser("ask", help="route and execute a natural-language request")
    s.add_argument("message", help="natural-language request")
    s.add_argument("--titan", default=None, help="override: force specific Titan")
    s.add_argument("--titan-args", nargs="*", default=[], help="args forwarded to Titan")
    s.set_defaults(func=cmd_ask)

    s = sub.add_parser("config", help="view or edit Kronos configuration")
    s.add_argument("--config-file", default=None, help="path to kronos.yaml")
    s.add_argument("--set-model", default=None)
    s.add_argument("--set-api-key", default=None)
    s.add_argument("--set-thinking", default=None)
    s.add_argument("--set-max-tokens", default=None)
    s.set_defaults(func=cmd_config)

    c = sub.add_parser("campaigns", help="view campaigns and shared Blackboard context")
    c.add_argument("id", nargs="?", default=None, help="Campaign ID to view details")
    c.set_defaults(func=cmd_campaigns)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

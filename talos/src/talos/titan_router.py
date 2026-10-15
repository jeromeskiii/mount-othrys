from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

TITAN_COEUS = "coeus"
TITAN_ATLAS = "atlas"
TITAN_IAPETUS = "iapetus"
TITAN_DIRECT = "direct"


@dataclass
class RouteResult:
    titan: str
    action: str
    reason: str
    subcommand: str | None = None
    extra_args: list[str] = field(default_factory=list)


def route_request(message: str, session_id: str | None = None) -> RouteResult:
    msg_lower = message.lower()
    words = message.split()

    if any(kw in msg_lower for kw in ["plan this", "create a plan", "make a plan", "build a plan",
                                        "help me think", "what should we", "scope this",
                                        "spec for", "define the approach"]):
        return RouteResult(
            titan=TITAN_COEUS,
            action="spawn_coeus",
            reason="Planning request detected",
            subcommand="interview",
        )

    if any(kw in msg_lower for kw in ["run the plan", "execute the plan", "atlas", "run atlas",
                                        "start the boulder", "continue the boulder",
                                        "boulder", "sequential execution", "plan-driven"]):
        return RouteResult(
            titan=TITAN_ATLAS,
            action="spawn_atlas",
            reason="Atlas execution request detected",
            subcommand="run",
        )

    if any(kw in msg_lower for kw in ["deep ", "iapetus", "deeply analyze", "complex refactor",
                                        "multi-file", "architectural", "deep execution",
                                        "think deeply", "thorough analysis"]):
        return RouteResult(
            titan=TITAN_IAPETUS,
            action="spawn_iapetus",
            reason="Deep execution request detected",
            subcommand="execute",
        )

    if any(kw in msg_lower for kw in ["implement", "add the", "build the", "create the",
                                        "fix the", "change the", "edit the", "write the"]):
        first_word = words[0].lower() if words else ""
        if first_word in ("implement", "add", "build", "create", "fix", "change", "edit", "write"):
            return RouteResult(
                titan=TITAN_DIRECT,
                action="execute_direct",
                reason="Implementation request — direct execution",
            )

    return RouteResult(
        titan=TITAN_DIRECT,
        action="execute_direct",
        reason="Default to direct execution",
    )


import shutil
import sys

def resolve_titan_command(
    titan: str, subcommand: str | None = None, args: list[str] | None = None
) -> tuple[list[str], dict[str, str]]:
    repo_root = Path(__file__).resolve().parents[3]
    venv_python = repo_root / titan / ".venv" / "bin" / "python"
    env_extra: dict[str, str] = {}

    titan_src = str(repo_root / titan / "src")
    othrys_src = str(repo_root / "othrys" / "src")
    existing_pp = os.environ.get("PYTHONPATH", "")
    env_extra["PYTHONPATH"] = f"{titan_src}:{othrys_src}" + (f":{existing_pp}" if existing_pp else "")

    if venv_python.exists():
        cmd = [str(venv_python), "-m", titan]
    elif shutil.which(titan):
        cmd = [titan]
    else:
        cmd = [sys.executable, "-m", titan]

    if subcommand:
        cmd.append(subcommand)
    if args:
        cmd.extend(args)

    return cmd, env_extra


def forward_to_titan(result: RouteResult, args: list[str], *, workdir: Path | None = None) -> int:
    if result.titan not in (TITAN_COEUS, TITAN_ATLAS, TITAN_IAPETUS):
        return 1
    subcmd = result.subcommand or ("interview" if result.titan == TITAN_COEUS else "run" if result.titan == TITAN_ATLAS else "execute")
    cmd, env_extra = resolve_titan_command(result.titan, subcmd, args)
    env = {**os.environ, **env_extra}
    proc = subprocess.run(cmd, cwd=str(workdir or Path.cwd()), env=env)
    return proc.returncode


def forward_to_titan_binary(result: RouteResult, args: list[str], binary_path: str, *, workdir: Path | None = None) -> int:
    cmd = [binary_path] + args
    proc = subprocess.run(cmd, cwd=str(workdir or Path.cwd()))
    return proc.returncode

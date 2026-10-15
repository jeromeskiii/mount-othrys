from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from othrys import match_rule

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


#: Canonical table Titan -> (worker, action, reason) Talos delegates to.
DELEGATIONS: dict[str, tuple[str, str, str]] = {
    TITAN_COEUS: (TITAN_COEUS, "spawn_coeus", "Planning request detected"),
    TITAN_ATLAS: (TITAN_ATLAS, "spawn_atlas", "Atlas execution request detected"),
    TITAN_IAPETUS: (TITAN_IAPETUS, "spawn_iapetus", "Deep execution request detected"),
}

#: Default subcommand per delegated worker.
DELEGATION_SUBCOMMANDS: dict[str, str] = {
    TITAN_COEUS: "interview",
    TITAN_ATLAS: "run",
    TITAN_IAPETUS: "execute",
}


def route_request(message: str, session_id: str | None = None) -> RouteResult:
    """Decide whether Talos handles a request itself or delegates it.

    MF-2: the keyword lists that used to live here were a third routing table,
    disagreeing with both the engine's triggers and Kronos's ``ROUTING_RULES``.
    This now reads the canonical table via ``othrys.routing`` and maps the
    resolved Titan into Talos's own actions.
    """
    found = match_rule(message)

    if found is not None and found.titan in DELEGATIONS:
        worker, action, reason = DELEGATIONS[found.titan]
        return RouteResult(
            titan=worker,
            action=action,
            reason=reason,
            subcommand=DELEGATION_SUBCOMMANDS[found.titan],
        )

    if found is not None and found.titan == "talos":
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

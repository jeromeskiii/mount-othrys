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


def forward_to_titan(result: RouteResult, args: list[str], *, workdir: Path | None = None) -> int:
    cmd: list[str]
    env_extra = {}

    if result.titan == TITAN_COEUS:
        cmd = ["coeus", result.subcommand or "interview"] + (args or [])
    elif result.titan == TITAN_ATLAS:
        cmd = ["atlas", result.subcommand or "run"] + args
    elif result.titan == TITAN_IAPETUS:
        cmd = ["iapetus", result.subcommand or "execute"] + args
    else:
        return 1

    env = {**os.environ, **env_extra}
    proc = subprocess.run(cmd, cwd=str(workdir or Path.cwd()), env=env)
    return proc.returncode


def forward_to_titan_binary(result: RouteResult, args: list[str], binary_path: str, *, workdir: Path | None = None) -> int:
    cmd = [binary_path] + args
    proc = subprocess.run(cmd, cwd=str(workdir or Path.cwd()))
    return proc.returncode

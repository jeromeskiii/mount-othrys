from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DispatchPlan:
    command: str
    args: list[str]
    explanation: str


def build_dispatch_plan(titan_key: str, message: str, titan_args: list[str] | None = None) -> DispatchPlan:
    extra = titan_args or []

    if titan_key == "coeus":
        if extra:
            return DispatchPlan(command="coeus", args=extra, explanation="User-supplied Coeus args")
        return DispatchPlan(
            command="coeus",
            args=["interview", message],
            explanation="Natural-language planning request → `coeus interview <message>`",
        )

    if titan_key == "atlas":
        if extra:
            return DispatchPlan(command="atlas", args=extra, explanation="User-supplied Atlas args")
        raise ValueError("Atlas execution requires explicit titan args, e.g. `--titan-args run <boulder-name>`.")

    if titan_key == "iapetus":
        if extra:
            return DispatchPlan(command="iapetus", args=extra, explanation="User-supplied Iapetus args")
        return DispatchPlan(
            command="iapetus",
            args=["execute", "--objective", message],
            explanation="Deep execution request → `iapetus execute --objective <message>`",
        )

    if titan_key == "talos":
        if extra:
            return DispatchPlan(command="talos", args=extra, explanation="User-supplied Talos args")
        return DispatchPlan(
            command="talos",
            args=["ask", message],
            explanation="General task request → `talos ask <message>`",
        )

    if titan_key == "themis":
        if extra:
            return DispatchPlan(
                command="iapetus",
                args=extra,
                explanation="Explicit advisory override using supplied args",
            )
        return DispatchPlan(
            command="iapetus",
            args=["analyze", "--objective", message],
            explanation="Themis is wired via read-only deep analysis",
        )

    if titan_key == "heracles":
        if extra:
            return DispatchPlan(
                command="iapetus",
                args=extra,
                explanation="Explicit Heracles override using supplied args",
            )
        return DispatchPlan(
            command="iapetus",
            args=[
                "execute",
                "--objective",
                f"HERACLES MODE ENABLED! {message}",
                "--max-iterations",
                "80",
            ],
            explanation="Heracles is wired via high-intensity deep execution",
        )

    if titan_key == "coordinator":
        if extra:
            return DispatchPlan(command="kronos", args=extra, explanation="User-supplied Coordinator args")
        return DispatchPlan(
            command="kronos",
            args=["ask", message],
            explanation="Strategic coordination request → `kronos ask <message>`",
        )

    raise KeyError(f"Unknown titan key: {titan_key}")

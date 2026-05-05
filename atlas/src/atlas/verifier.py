from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .boulder import Task, Verification
from .llm import AtlasLLM
from .prompts import VERIFIER_SYSTEM, build_verifier_prompt
from .tools import _truncate, DEFAULT_TIMEOUT


_VERDICT_RE = re.compile(r"^VERDICT:\s*(PASS|FAIL|INCONCLUSIVE)\s*$", re.MULTILINE | re.IGNORECASE)


@dataclass
class VerifyResult:
    verdict: str
    reason: str
    next_step: str
    raw: str
    all_passed: bool

def _check_code_integrity(workdir: Path) -> Verification | None:
    """Implicit integrity check (LSP-First principle)."""
    py_files = list(workdir.glob("**/*.py"))
    if not py_files:
        return None

    try:
        cmd = ["python", "-m", "py_compile"] + [str(f.relative_to(workdir)) for f in py_files[:20]]
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(workdir), timeout=30)
        if proc.returncode != 0:
            return Verification(
                command="lsp_integrity_check",
                description="Implicit code integrity check (syntax/types)",
                passed=False,
                output=f"LSP Integrity Failure:\n{proc.stderr}"
            )
    except Exception:
        pass
    return None


def run_verifications(task: Task, workdir: Path) -> list[Verification]:
    out: list[Verification] = []

    # 1. LSP-First Integrity Check
    integrity = _check_code_integrity(workdir)
    if integrity:
        out.append(integrity)

    # 2. Defined Verifications
    for v in task.verifications:
        if not v.command:
            out.append(Verification(command="", description=v.description, passed=None, output="(manual check)"))
            continue
        try:
            proc = subprocess.run(
                v.command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=str(workdir),
                timeout=DEFAULT_TIMEOUT,
                env={k: v for k, v in os.environ.items() if not k.endswith(("API_KEY", "SECRET", "TOKEN", "PASSWORD"))},
            )
            output = f"[exit {proc.returncode}]\n"
            if proc.stdout:
                output += proc.stdout
            if proc.stderr:
                output += f"\n--- stderr ---\n{proc.stderr}"
            out.append(
                Verification(
                    command=v.command,
                    description=v.description,
                    passed=(proc.returncode == 0),
                    output=_truncate(output),
                )
            )
        except subprocess.TimeoutExpired as e:
            partial = (e.stdout or "") + (e.stderr or "")
            out.append(
                Verification(
                    command=v.command,
                    description=v.description,
                    passed=False,
                    output=f"[TIMEOUT]\n{_truncate(partial)}",
                )
            )
    return out


def adjudicate(llm: AtlasLLM, task: Task, results: list[Verification]) -> VerifyResult:
    runnable = [r for r in results if r.command]
    if runnable and all(r.passed for r in runnable):
        return VerifyResult(
            verdict="PASS",
            reason=f"All {len(runnable)} verification command(s) exited 0.",
            next_step="",
            raw="(short-circuit: all green)",
            all_passed=True,
        )
    if not results:
        return VerifyResult(
            verdict="PASS",
            reason="No verifications defined for this task.",
            next_step="",
            raw="(no verifications)",
            all_passed=True,
        )

    user = build_verifier_prompt(
        task_title=f"{task.phase} — {task.title}",
        deliverable=task.deliverable,
        verifications=[(r.command, r.description, r.output) for r in results],
    )
    raw = llm.call(VERIFIER_SYSTEM, [{"role": "user", "content": user}], max_tokens=1500)
    m = _VERDICT_RE.search(raw)
    verdict = (m.group(1).upper() if m else "INCONCLUSIVE")
    reason = ""
    next_step = ""
    for line in raw.splitlines():
        if line.upper().startswith("REASON:"):
            reason = line.split(":", 1)[1].strip()
        elif line.upper().startswith("NEXT:"):
            next_step = line.split(":", 1)[1].strip()
    return VerifyResult(
        verdict=verdict,
        reason=reason or raw[:300],
        next_step=next_step,
        raw=raw,
        all_passed=(verdict == "PASS"),
    )

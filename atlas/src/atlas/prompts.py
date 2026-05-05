from __future__ import annotations


ATLAS_IDENTITY = """You are Atlas — the Master Orchestrator from the Kronos Titan system.

In Greek mythology, Atlas holds up the celestial heavens. You hold up the entire workflow:
coordinating every subagent, every task, every verification gate until the plan is done.

You are a conductor, not a musician. A general, not a soldier.
You DELEGATE atomic tasks to focused subagents. You VERIFY their work via plan-defined gates.
You NEVER write code yourself. You NEVER touch the user's repo with your own hands.

When you spawn a subagent, you give it: the task, the deliverable, the steps, and the verification.
When the subagent finishes, you run the verification commands. Green → next task. Red → reattempt or block.
"""


SUBAGENT_SYSTEM = """You are an Atlas subagent — a focused executor for a single task in a larger plan.

You have direct tool access: bash, read, write, edit, list_dir.

YOUR JOB:
- Execute exactly ONE task from the plan: the one described in the user message below.
- Follow the steps. Produce the deliverable. Nothing more, nothing less.
- Match the existing codebase style. Read neighboring files before writing new ones.
- When done, briefly summarize what you changed (file paths + 1-line per change).

HARD RULES:
- Stay strictly within the task's scope. Do NOT fix unrelated issues, refactor extras, or add tests not requested.
- Do NOT run destructive commands (rm -rf, git reset --hard, force push). If you think you need one, STOP and report.
- Do NOT modify files outside the project workdir.
- Do NOT mark the task complete with broken code. If a step fails, report the failure honestly.
- Use real tools. Do not simulate, hallucinate file contents, or pretend a command ran.

When the task is genuinely done, end your turn with a final summary message starting with "DONE:".
If you hit a blocker you cannot resolve, end with "BLOCKED: <reason>".
"""


VERIFIER_SYSTEM = """You are an Atlas verification agent.

Your only job: given a task's verification commands and their outputs, produce a verdict.

Format your response as:
VERDICT: PASS | FAIL | INCONCLUSIVE
REASON: <one or two sentences>
NEXT: <if FAIL, the single most likely root cause and a one-line fix suggestion>

Do not run new tools. Do not speculate beyond the evidence. If outputs are missing, say INCONCLUSIVE.
"""


def build_subagent_prompt(
    *,
    objective: str,
    phase: str,
    title: str,
    description: str,
    deliverable: str,
    steps: list[str],
    workdir: str,
    findings: list[str],
    decisions: list[str],
    previous_attempt_notes: list[str] | None = None,
) -> str:
    parts = [
        f"# Plan Objective\n\n{objective or '(none stated)'}",
        f"\n# Working Directory\n\n`{workdir}`",
        f"\n# Your Task: {phase} — {title}\n",
    ]
    if description:
        parts.append(f"## Context\n\n{description}\n")
    if deliverable:
        parts.append(f"## Deliverable\n\n{deliverable}\n")
    if steps:
        parts.append("## Steps\n")
        parts.extend(f"{i}. {s}" for i, s in enumerate(steps, 1))
        parts.append("")
    if findings:
        parts.append("## Cumulative Findings (from prior tasks)\n")
        parts.extend(f"- {f}" for f in findings)
        parts.append("")
    if decisions:
        parts.append("## Cumulative Decisions (from prior tasks)\n")
        parts.extend(f"- {d}" for d in decisions)
        parts.append("")
    if previous_attempt_notes:
        parts.append("## Previous Attempt Failed — Notes\n")
        parts.extend(f"- {n}" for n in previous_attempt_notes)
        parts.append("\nFix the failure described above. Do not repeat the same approach blindly.")
    parts.append("\nExecute now. End with `DONE: <summary>` or `BLOCKED: <reason>`.")
    return "\n".join(parts)


def build_verifier_prompt(
    *,
    task_title: str,
    deliverable: str,
    verifications: list[tuple[str, str, str]],
) -> str:
    """verifications: list of (command, description, output)."""
    lines = [
        f"# Task: {task_title}",
        f"\n## Deliverable\n{deliverable or '(none stated)'}",
        "\n## Verification Results\n",
    ]
    for i, (cmd, desc, out) in enumerate(verifications, 1):
        lines.append(f"### Check {i}: {desc or cmd}")
        if cmd:
            lines.append(f"\n**Command:** `{cmd}`")
        lines.append(f"\n**Output:**\n```\n{out}\n```\n")
    lines.append("Render your verdict now.")
    return "\n".join(lines)

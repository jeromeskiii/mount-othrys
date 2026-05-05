from __future__ import annotations


SECTION_ORDER = ["TASK", "EXPECTED OUTCOME", "REQUIRED TOOLS", "MUST DO", "MUST NOT DO", "CONTEXT"]


def build_delegation_prompt(
    *,
    task: str,
    outcome: str,
    tools: list[str],
    must_do: list[str],
    must_not: list[str],
    context: str,
) -> str:
    sections = [
        f"1. TASK: {task}",
        f"2. EXPECTED OUTCOME: {outcome}",
        f"3. REQUIRED TOOLS: {', '.join(tools)}",
        f"4. MUST DO:\n" + "\n".join(f"- {m}" for m in must_do),
        f"5. MUST NOT DO:\n" + "\n".join(f"- {m}" for m in must_not),
        f"6. CONTEXT:\n{context}",
    ]
    return "\n\n".join(sections)
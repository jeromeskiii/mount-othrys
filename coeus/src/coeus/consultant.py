from __future__ import annotations

import json
from dataclasses import dataclass
from json import JSONDecoder

from coeus.llm import CoeusLLM
from coeus.prompts import (
    PHASE1_INQUIRY_SYSTEM,
    METIS_SYSTEM,
    PLAN_GENERATION_SYSTEM,
    MOMUS_SYSTEM,
)
from coeus.state import Draft, Phase, QA


def _extract_json(text: str) -> dict:
    decoder = JSONDecoder()
    idx = 0
    while idx < len(text):
        if text[idx] == "{":
            try:
                obj, end = decoder.raw_decode(text, idx)
                if isinstance(obj, dict):
                    return obj
                idx = end
            except json.JSONDecodeError:
                idx += 1
        else:
            idx += 1
    raise ValueError(f"Coeus did not return JSON. Raw output:\n{text}")


def _build_inquiry_user_message(draft: Draft) -> str:
    lines = [
        f"## Original Request\n{draft.request}",
        "",
        "## Clearance Gate State",
    ]
    for gate, ok in draft.clearance.items():
        lines.append(f"- {gate}: {'CLEARED' if ok else 'OPEN'}")
    lines.append("")
    lines.append("## Conversation So Far")
    if not draft.qa_log:
        lines.append("_(no questions asked yet)_")
    for i, qa in enumerate(draft.qa_log, 1):
        lines.append(f"\nQ{i}: {qa.question}")
        lines.append(f"A{i}: {qa.answer if qa.answer else '(unanswered)'}")
    if draft.findings:
        lines.append("\n## Findings So Far")
        lines.extend(f"- {f}" for f in draft.findings)
    return "\n".join(lines)


@dataclass
class InquiryStep:
    action: str
    gate: str | None = None
    question: str | None = None
    finding: str | None = None
    summary: str | None = None


class Consultant:
    def __init__(self, llm: CoeusLLM) -> None:
        self.llm = llm

    def next_inquiry_step(self, draft: Draft) -> InquiryStep:
        user = _build_inquiry_user_message(draft)
        raw = self.llm.call(
            system=PHASE1_INQUIRY_SYSTEM,
            messages=[{"role": "user", "content": user}],
            max_tokens=2000,
        )
        data = _extract_json(raw)
        return InquiryStep(
            action=data.get("action", ""),
            gate=data.get("gate"),
            question=data.get("question"),
            finding=data.get("finding"),
            summary=data.get("summary"),
        )

    def metis_review(self, draft: Draft) -> tuple[str, bool]:
        user = _build_inquiry_user_message(draft)
        raw = self.llm.call(
            system=METIS_SYSTEM,
            messages=[{"role": "user", "content": user}],
            max_tokens=4000,
        )
        proceed = "METIS_VERDICT: PROCEED" in raw.upper()
        return raw, proceed

    def generate_plan(self, draft: Draft) -> str:
        user = _build_inquiry_user_message(draft)
        if draft.metis_notes:
            user += f"\n\n## Metis Pre-Plan Critique\n{draft.metis_notes}"
        return self.llm.call(
            system=PLAN_GENERATION_SYSTEM,
            messages=[{"role": "user", "content": user}],
            max_tokens=8000,
        )

    def momus_review(self, plan_markdown: str) -> tuple[str, bool]:
        raw = self.llm.call(
            system=MOMUS_SYSTEM,
            messages=[{"role": "user", "content": f"## Plan to Review\n\n{plan_markdown}"}],
            max_tokens=4000,
        )
        approved = "MOMUS_VERDICT: APPROVED" in raw.upper()
        return raw, approved


def apply_inquiry_step(draft: Draft, step: InquiryStep, answer: str | None = None) -> None:
    if step.action == "ask" and step.question:
        draft.qa_log.append(QA(question=step.question, answer=answer))
    elif step.action == "clear" and step.gate:
        draft.clearance[step.gate] = True
        if step.finding:
            draft.findings.append(f"[{step.gate}] {step.finding}")
    elif step.action == "ready_for_plan":
        if step.summary:
            draft.findings.append(f"[summary] {step.summary}")
        for g in draft.clearance:
            draft.clearance[g] = True
        draft.phase = Phase.METIS_REVIEW

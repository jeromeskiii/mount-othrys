from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
import yaml


class Phase(str, Enum):
    INQUIRY = "inquiry"
    METIS_REVIEW = "metis_review"
    PLAN_GENERATION = "plan_generation"
    MOMUS_REVIEW = "momus_review"
    COMPLETE = "complete"


class ClearanceGate(str, Enum):
    INTENT_CLEAR = "intent_clear"
    SCOPE_DEFINED = "scope_defined"
    CONSTRAINTS_KNOWN = "constraints_known"
    SUCCESS_CRITERIA = "success_criteria"
    CONTEXT_GATHERED = "context_gathered"


@dataclass
class QA:
    question: str
    answer: str | None = None
    asked_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    answered_at: str | None = None


@dataclass
class Draft:
    name: str
    request: str
    phase: Phase = Phase.INQUIRY
    clearance: dict[str, bool] = field(default_factory=dict)
    qa_log: list[QA] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    plan_path: str | None = None
    metis_notes: str | None = None
    momus_notes: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self) -> None:
        if not self.clearance:
            self.clearance = {gate.value: False for gate in ClearanceGate}

    def is_cleared(self) -> bool:
        return all(self.clearance.get(gate.value, False) for gate in ClearanceGate)

    def pending_gates(self) -> list[str]:
        return [g for g in self.clearance if not self.clearance[g]]

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()


def _serialize(draft: Draft) -> dict:
    data = asdict(draft)
    data["phase"] = draft.phase.value
    return data


def _deserialize(data: dict) -> Draft:
    qa_log = [QA(**q) for q in data.pop("qa_log", [])]
    phase = Phase(data.pop("phase", "inquiry"))
    return Draft(qa_log=qa_log, phase=phase, **data)


class DraftStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.drafts_dir = root / ".sisyphus" / "drafts"
        self.plans_dir = root / ".sisyphus" / "plans"
        self.state_dir = root / ".sisyphus" / "state"
        for d in (self.drafts_dir, self.plans_dir, self.state_dir):
            d.mkdir(parents=True, exist_ok=True)

    def state_path(self, name: str) -> Path:
        return self.state_dir / f"{name}.yaml"

    def draft_path(self, name: str) -> Path:
        return self.drafts_dir / f"{name}.md"

    def plan_path(self, name: str) -> Path:
        return self.plans_dir / f"{name}.md"

    def exists(self, name: str) -> bool:
        return self.state_path(name).exists()

    def load(self, name: str) -> Draft:
        path = self.state_path(name)
        if not path.exists():
            raise FileNotFoundError(f"No draft named '{name}'. Run: coeus interview <request> --name {name}")
        data = yaml.safe_load(path.read_text())
        return _deserialize(data)

    def save(self, draft: Draft) -> None:
        draft.touch()
        self.state_path(draft.name).write_text(yaml.safe_dump(_serialize(draft), sort_keys=False))
        self._render_draft_md(draft)

    def list_all(self) -> list[Draft]:
        out = []
        for path in sorted(self.state_dir.glob("*.yaml")):
            try:
                out.append(_deserialize(yaml.safe_load(path.read_text())))
            except Exception:
                continue
        return out

    def _render_draft_md(self, draft: Draft) -> None:
        lines = [
            f"# Draft: {draft.name}",
            "",
            f"**Phase:** `{draft.phase.value}`  ",
            f"**Created:** {draft.created_at}  ",
            f"**Updated:** {draft.updated_at}",
            "",
            "## Original Request",
            "",
            draft.request,
            "",
            "## Clearance Gates",
            "",
        ]
        for gate, ok in draft.clearance.items():
            mark = "[x]" if ok else "[ ]"
            lines.append(f"- {mark} {gate}")
        lines.extend(["", "## Q&A Log", ""])
        if not draft.qa_log:
            lines.append("_(none yet)_")
        for i, qa in enumerate(draft.qa_log, 1):
            lines.append(f"### Q{i}. {qa.question}")
            lines.append("")
            lines.append(qa.answer if qa.answer else "_(unanswered)_")
            lines.append("")
        if draft.findings:
            lines.extend(["## Findings", ""])
            lines.extend(f"- {f}" for f in draft.findings)
            lines.append("")
        if draft.decisions:
            lines.extend(["## Decisions", ""])
            lines.extend(f"- {d}" for d in draft.decisions)
            lines.append("")
        if draft.metis_notes:
            lines.extend(["## Metis Review", "", draft.metis_notes, ""])
        if draft.momus_notes:
            lines.extend(["## Momus Review", "", draft.momus_notes, ""])
        if draft.plan_path:
            lines.extend(["## Generated Plan", "", f"See: `{draft.plan_path}`", ""])
        self.draft_path(draft.name).write_text("\n".join(lines))

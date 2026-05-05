from __future__ import annotations

from pathlib import Path

import pytest

from coeus.consultant import InquiryStep, apply_inquiry_step
from coeus.state import ClearanceGate, Draft, DraftStore, Phase, QA


def test_draft_starts_with_all_gates_open() -> None:
    d = Draft(name="x", request="r")
    assert not d.is_cleared()
    assert set(d.pending_gates()) == {g.value for g in ClearanceGate}


def test_draft_cleared_when_all_gates_true() -> None:
    d = Draft(name="x", request="r")
    for g in ClearanceGate:
        d.clearance[g.value] = True
    assert d.is_cleared()
    assert d.pending_gates() == []


def test_store_roundtrip(tmp_path: Path) -> None:
    store = DraftStore(tmp_path)
    d = Draft(name="auth", request="Add JWT auth")
    d.qa_log.append(QA(question="Algorithm?", answer="HS256"))
    d.findings.append("[intent_clear] HS256 chosen")
    store.save(d)

    loaded = store.load("auth")
    assert loaded.name == "auth"
    assert loaded.request == "Add JWT auth"
    assert len(loaded.qa_log) == 1
    assert loaded.qa_log[0].answer == "HS256"
    assert loaded.findings == ["[intent_clear] HS256 chosen"]
    assert loaded.phase == Phase.INQUIRY


def test_store_renders_markdown(tmp_path: Path) -> None:
    store = DraftStore(tmp_path)
    d = Draft(name="x", request="Build a thing")
    store.save(d)
    md = store.draft_path("x").read_text()
    assert "# Draft: x" in md
    assert "Build a thing" in md
    assert "[ ] intent_clear" in md


def test_apply_ask_appends_qa() -> None:
    d = Draft(name="x", request="r")
    step = InquiryStep(action="ask", gate="intent_clear", question="Why?")
    apply_inquiry_step(d, step)
    assert len(d.qa_log) == 1
    assert d.qa_log[0].question == "Why?"
    assert d.qa_log[0].answer is None


def test_apply_clear_sets_gate_and_records_finding() -> None:
    d = Draft(name="x", request="r")
    step = InquiryStep(action="clear", gate="intent_clear", finding="user wants X")
    apply_inquiry_step(d, step)
    assert d.clearance["intent_clear"] is True
    assert d.findings == ["[intent_clear] user wants X"]


def test_apply_ready_for_plan_clears_all_and_advances_phase() -> None:
    d = Draft(name="x", request="r")
    step = InquiryStep(action="ready_for_plan", summary="all set")
    apply_inquiry_step(d, step)
    assert d.is_cleared()
    assert d.phase == Phase.METIS_REVIEW
    assert any("[summary] all set" in f for f in d.findings)


def test_load_missing_raises(tmp_path: Path) -> None:
    store = DraftStore(tmp_path)
    with pytest.raises(FileNotFoundError):
        store.load("nope")


def test_list_all_returns_drafts(tmp_path: Path) -> None:
    store = DraftStore(tmp_path)
    store.save(Draft(name="a", request="r1"))
    store.save(Draft(name="b", request="r2"))
    names = sorted(d.name for d in store.list_all())
    assert names == ["a", "b"]

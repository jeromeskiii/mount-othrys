"""Regression coverage for MF-2 — one canonical routing table.

The golden corpus lives inside the table itself, so both languages are held to
the identical expectations: this module asserts the Python matcher, and
``engine/tests/routingTable.test.ts`` asserts the TypeScript router against the
same ``examples`` array. A drift in either implementation fails its own suite.
"""

from __future__ import annotations

import pytest

from othrys.routing import DEFAULT_TITAN, canonical_titan, load_examples, load_table, match_rule


def test_table_has_one_weighted_entry_per_titan():
    entries = load_table()
    assert entries

    titans = [entry.titan for entry in entries]
    assert len(titans) == len(set(titans)), "each Titan owns exactly one entry"
    assert all(entry.patterns for entry in entries), "no entry may be trigger-less"
    assert DEFAULT_TITAN in titans


@pytest.mark.parametrize("message,expected", load_examples())
def test_golden_corpus_matches_the_canonical_table(message: str, expected: str) -> None:
    assert canonical_titan(message)[0] == expected


def test_specific_intent_outranks_the_generic_talos_rule() -> None:
    """Regression: MF-2's shadowing defect.

    Talos's generic ``/implement/`` trigger used to win against Iapetus because
    routing was first-match over declaration order.
    """
    matched = match_rule("Implement this complex work")
    assert matched is not None
    assert matched.titan == "iapetus"

    talos = next(entry for entry in load_table() if entry.titan == "talos")
    assert matched.weight > talos.weight


def test_ties_resolve_to_the_earlier_entry() -> None:
    order = [entry.titan for entry in load_table()]
    weights = {entry.titan: entry.weight for entry in load_table()}
    assert weights["coeus"] == weights["themis"], "this test needs an equal-weight pair"

    # Both entries match at the same weight, so the earlier one must win.
    matched = match_rule("plan this with themis")
    assert matched is not None
    assert matched.titan == "coeus"
    assert order.index("coeus") < order.index("themis")


def test_falls_through_when_no_rule_matches() -> None:
    assert match_rule("zzzz no intent here") is None

    titan, reason = canonical_titan("zzzz no intent here")
    assert titan == DEFAULT_TITAN
    assert "Default to" in reason


def test_routing_is_deterministic_across_calls() -> None:
    results = {canonical_titan("Implement this complex work")[0] for _ in range(10)}
    assert results == {"iapetus"}
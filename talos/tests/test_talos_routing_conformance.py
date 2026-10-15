"""MF-2 conformance: Talos routing must agree with the canonical table.

Talos used to carry its own keyword lists — a third routing table that disagreed
with both the engine's and Kronos's. These tests fail if a private table returns.
"""

from __future__ import annotations

from othrys.routing import load_examples, load_table

from talos.titan_router import (
    DELEGATION_SUBCOMMANDS,
    DELEGATIONS,
    TITAN_DIRECT,
    route_request,
)


def test_delegations_only_reference_canonical_titans() -> None:
    canonical = {entry.titan for entry in load_table()}

    assert set(DELEGATIONS) <= canonical
    assert set(DELEGATION_SUBCOMMANDS) == set(DELEGATIONS)


def test_delegates_exactly_the_workers_talos_can_reach() -> None:
    assert set(DELEGATIONS) == {"coeus", "atlas", "iapetus"}


def test_route_request_agrees_with_the_canonical_table() -> None:
    mismatches = []
    for message, expected in load_examples():
        # Talos delegates the three workers it can spawn and handles its own
        # intent directly; anything else it does not own falls to direct.
        wanted = expected if expected in DELEGATIONS else TITAN_DIRECT
        result = route_request(message)
        if result.titan != wanted:
            mismatches.append((message, expected, result.titan))

    assert mismatches == []


def test_delegation_subcommands_are_stable() -> None:
    assert DELEGATION_SUBCOMMANDS == {
        "coeus": "interview",
        "atlas": "run",
        "iapetus": "execute",
    }
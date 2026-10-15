"""MF-2 conformance: Kronos routing must agree with the canonical table.

Kronos used to carry its own ``ROUTING_RULES`` list, which had drifted from the
engine's triggers. These tests fail if a private table is ever reintroduced.
"""

from __future__ import annotations

from othrys.routing import load_examples, load_table

from kronos.registry import TITAN_REGISTRY
from kronos.router import CANONICAL_TO_REGISTRY, route

EXPECTED_MAPPING = {
    "coeus": "coeus",
    "atlas": "atlas",
    "iapetus": "iapetus",
    "talos": "talos",
    "themis": "themis",
    "heracles": "heracles",
    "kronos": "coordinator",
}


def test_mapping_covers_every_canonical_titan() -> None:
    assert set(CANONICAL_TO_REGISTRY) == {entry.titan for entry in load_table()}
    assert CANONICAL_TO_REGISTRY == EXPECTED_MAPPING


def test_every_mapped_key_exists_in_the_kronos_registry() -> None:
    for registry_key in CANONICAL_TO_REGISTRY.values():
        assert registry_key in TITAN_REGISTRY


def test_route_agrees_with_the_canonical_table() -> None:
    mismatches = []
    for message, expected in load_examples():
        # Without an LLM client, route() is the deterministic table-only path;
        # the semantic classifier only runs when no canonical rule matches.
        titan, _ = route(message)
        wanted = CANONICAL_TO_REGISTRY.get(expected, expected)
        if titan.name.lower() != wanted:
            mismatches.append((message, expected, titan.name))

    assert mismatches == []


def test_table_decides_when_no_llm_client_is_available() -> None:
    titan, reason = route("plan this feature for me")

    assert titan.name == "coeus"
    assert "canonical" in reason.lower()
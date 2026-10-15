"""Canonical intent -> Titan routing (MF-2).

Before MF-2 three independent, disagreeing routing tables existed:

* ``engine/src/router.ts`` (the TypeScript engine, the actual request boundary)
* ``kronos/src/kronos/router.py`` (``ROUTING_RULES``)
* ``talos/src/talos/titan_router.py`` (its own keyword lists)

They disagreed on real inputs and the engine's first-match-wins scan made the
result order dependent, so a generic ``/implement/`` trigger on Talos permanently
shadowed Iapetus's specific intent. This module is now the single authority: the
table lives in ``routing.table.json`` next to this file, is shipped inside the
``othrys`` wheel, and is read by the TypeScript engine through
``engine/src/routing/table.ts``.

Scoring is deliberately simple and language-neutral so both implementations can
be held to the identical golden corpus stored in the table's ``examples`` key:
every matching entry scores its own ``weight``; the highest weight wins; ties
resolve to the earliest entry. Nothing matched means the caller's default
applies.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from typing import Any

TABLE_RESOURCE = "routing.table.json"

#: Titan every consumer falls back to when nothing matches.
DEFAULT_TITAN = "talos"


@dataclass(frozen=True)
class RoutingPattern:
    """One compiled trigger, kept with its source text for reason reporting."""

    source: str
    flags: str
    regex: re.Pattern[str]

    def matches(self, message: str) -> bool:
        return self.regex.search(message) is not None


@dataclass(frozen=True)
class RoutingEntry:
    """One weighted intent group owned by a single Titan."""

    id: str
    titan: str
    weight: int
    description: str
    patterns: tuple[RoutingPattern, ...]


@dataclass(frozen=True)
class RouteMatch:
    """The winning entry for a message."""

    titan: str
    entry_id: str
    weight: int
    pattern: str
    reason: str


def _compile(source: str, flags: str) -> RoutingPattern:
    regex_flags = re.IGNORECASE if "i" in flags else 0
    return RoutingPattern(source=source, flags=flags, regex=re.compile(source, regex_flags))


def _read_table_text() -> str:
    return resources.files("othrys").joinpath(TABLE_RESOURCE).read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def _parsed_table() -> dict[str, Any]:
    data = json.loads(_read_table_text())
    if not isinstance(data, dict) or not isinstance(data.get("entries"), list):
        raise RuntimeError(f"{TABLE_RESOURCE} is malformed: expected an 'entries' list")
    return data


@lru_cache(maxsize=1)
def load_table() -> tuple[RoutingEntry, ...]:
    """Return the canonical routing entries in precedence order."""
    entries: list[RoutingEntry] = []
    for raw in _parsed_table()["entries"]:
        patterns = tuple(
            _compile(str(p["pattern"]), str(p.get("flags", ""))) for p in raw.get("patterns", [])
        )
        entries.append(
            RoutingEntry(
                id=str(raw["id"]),
                titan=str(raw["titan"]),
                weight=int(raw["weight"]),
                description=str(raw.get("description", "")),
                patterns=patterns,
            )
        )
    return tuple(entries)


@lru_cache(maxsize=1)
def load_examples() -> tuple[tuple[str, str], ...]:
    """Return the golden (message, titan) corpus shared with the TypeScript tests."""
    examples = _parsed_table().get("examples", [])
    return tuple((str(item["message"]), str(item["titan"])) for item in examples)


def match_rule(message: str) -> RouteMatch | None:
    """Return the highest-weighted matching entry, or ``None`` when nothing matches."""
    best_entry: RoutingEntry | None = None
    best_pattern: RoutingPattern | None = None

    for entry in load_table():
        if best_entry is not None and entry.weight <= best_entry.weight:
            # Cannot win, and equal weights defer to the earlier entry.
            continue
        for pattern in entry.patterns:
            if pattern.matches(message):
                best_entry, best_pattern = entry, pattern
                break

    if best_entry is None or best_pattern is None:
        return None

    return RouteMatch(
        titan=best_entry.titan,
        entry_id=best_entry.id,
        weight=best_entry.weight,
        pattern=best_pattern.source,
        reason=f"Canonical rule '{best_entry.id}' matched /{best_pattern.source}/ → {best_entry.titan}",
    )


def canonical_titan(message: str, default: str = DEFAULT_TITAN) -> tuple[str, str]:
    """Resolve a message to ``(titan, reason)``, falling back to ``default``."""
    found = match_rule(message)
    if found is not None:
        return found.titan, found.reason
    return default, f"Default to {default} (no canonical rule matched)"
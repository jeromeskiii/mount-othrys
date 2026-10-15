#!/usr/bin/env python3
"""Pass-2 independent verification, method 2: cross-language routing agreement.

Pass 1 compared the TypeScript router against the Python matcher over the table's
curated 23-example corpus. This pass generates a much broader message set derived
from every pattern in the table plus decoys, and diffs the two implementations
decision-for-decision, to catch divergence the curated corpus could miss.
"""
from __future__ import annotations

import json
import re
import string
import subprocess
import sys
from pathlib import Path

REPO = Path("/Users/ohmskiii/mount-othrys")
sys.path.insert(0, str(REPO / "othrys" / "src"))

from othrys.routing import DEFAULT_TITAN, canonical_titan, load_table  # noqa: E402

TAG = string.ascii_lowercase
SPECIAL = set("\\^$.|?*+()[]{}")


def literal(pattern: str) -> str:
    """Best-effort literal form of a pattern, for use as a test message."""
    stripped = "".join(ch for ch in pattern if ch not in SPECIAL)
    return stripped.strip() or pattern


def build_messages() -> list[str]:
    messages: list[str] = []
    for entry in load_table():
        for pattern in entry.patterns:
            lit = literal(pattern.source)
            # bare, capitalised, and embedded in surrounding prose
            messages.append(lit)
            messages.append(lit.capitalize())
            messages.append(f"please {lit} for me")
            messages.append(f"could you {lit} this thing today")
    # decoys: must fall through to the default
    messages += [
        "hello there",
        "good morning",
        "zzzz nothing to see",
        "what time is it",
        "12345",
        "",
        "   ",
        "just chatting about the weather",
    ]
    return messages


def ts_decisions(messages: list[str]) -> list[str]:
    script = (
        "import { matchRoutingRule } from "
        f"'{REPO}/engine/dist/index.js';\n"
        "const msgs = JSON.parse(process.argv[1]);\n"
        "console.log(JSON.stringify(msgs.map(m => (matchRoutingRule(m)?.titan) ?? null)));"
    )
    out = subprocess.run(
        ["node", "--input-type=module", "-e", script, json.dumps(messages)],
        capture_output=True, text=True, check=True,
    )
    return out.stdout.strip().splitlines()[-1] and json.loads(out.stdout.strip().splitlines()[-1])


def main() -> int:
    messages = build_messages()
    ts = ts_decisions(messages)
    py = [(canonical_titan(m)[0] if canonical_titan(m)[1].startswith("Canonical") else None) for m in messages]

    assert len(ts) == len(py) == len(messages), (len(ts), len(py), len(messages))

    mismatches = [(m, t, p) for m, t, p in zip(messages, ts, py) if t != p]
    print(f"messages compared : {len(messages)}")
    print(f"mismatches        : {len(mismatches)}")
    for m, t, p in mismatches[:15]:
        print(f"  MISMATCH ts={t!r} py={p!r} msg={m!r}")

    decided = sum(1 for d in ts if d is not None)
    print(f"decided by table  : {decided} / {len(messages)} (rest fall through to {DEFAULT_TITAN})")

    # Every message must reach *some* Titan in the engine, even with no match.
    fallbacks = [m for m, d in zip(messages, ts) if d is None]
    print(f"fall-throughs     : {len(fallbacks)}")

    return 1 if mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())
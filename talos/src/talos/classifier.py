from __future__ import annotations

from enum import Enum


class RequestType(Enum):
    TRIVIAL = "trivial"
    EXPLICIT = "explicit"
    EXPLORATORY = "exploratory"
    OPEN_ENDED = "open-ended"
    AMBIGUOUS = "ambiguous"


TRIVIAL_SIGNALS = [
    "typo", "single file", "simple modification", "one line", "single function",
    "one file", "straightforward", "trivial",
]

EXPLICIT_SIGNALS = [
    "specific file", "exact line", "edit the", "change the", "add to the",
    "remove from", "replace in", "line ", "function ", "at line",
]

EXPLORATORY_SIGNALS = [
    "how does", "how do", "explain", "what does", "what is the", "why does",
    "understand", "figure out", "find where", "which file",
]

OPEN_ENDED_SIGNALS = [
    "improve", "refactor", "clean up", "optimize", "better", "restructure",
    "reorganize", "modernize", "upgrade",
]

AMBIGUOUS_SIGNALS = [
    "maybe", "not sure", "either", "could be", "unsure", "confused",
    "what do you think", "i'm not certain", "might need",
]


def classify(message: str) -> tuple[RequestType, str]:
    msg = message.lower()

    trivial_count = sum(1 for s in TRIVIAL_SIGNALS if s in msg)
    explicit_count = sum(1 for s in EXPLICIT_SIGNALS if s in msg)
    exploratory_count = sum(1 for s in EXPLORATORY_SIGNALS if s in msg)
    open_ended_count = sum(1 for s in OPEN_ENDED_SIGNALS if s in msg)
    ambiguous_count = sum(1 for s in AMBIGUOUS_SIGNALS if s in msg)

    counts = {
        RequestType.TRIVIAL: trivial_count,
        RequestType.EXPLICIT: explicit_count,
        RequestType.EXPLORATORY: exploratory_count,
        RequestType.OPEN_ENDED: open_ended_count,
        RequestType.AMBIGUOUS: ambiguous_count,
    }

    if all(c == 0 for c in counts.values()):
        return RequestType.OPEN_ENDED, "No specific signals — defaulting to open-ended"

    best = max(counts, key=counts.get)

    if explicit_count >= 2 and best not in (RequestType.EXPLICIT, RequestType.TRIVIAL):
        return RequestType.EXPLICIT, "Multiple specific file/line references detected"
    if exploratory_count >= 2 and best == RequestType.AMBIGUOUS:
        return RequestType.EXPLORATORY, "Multiple how/why questions detected"
    if open_ended_count >= 1 and open_ended_count == max(trivial_count, explicit_count):
        return RequestType.OPEN_ENDED, "Refactor/improve language detected"

    reasons = {
        RequestType.TRIVIAL: "Single-file, simple change",
        RequestType.EXPLICIT: "Specific file/line/function specified",
        RequestType.EXPLORATORY: "How/why/explain question",
        RequestType.OPEN_ENDED: "Improve/refactor language",
        RequestType.AMBIGUOUS: "Unclear scope or multiple interpretations",
    }
    return best, reasons[best]
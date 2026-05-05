from __future__ import annotations

from .llm import KronosLLM
from .registry import TITAN_REGISTRY, TitanInfo, get_titan

ROUTING_RULES: list[tuple[list[str], str]] = [
    (["plan this", "create a plan", "make a plan", "build a plan",
      "help me think", "what should we", "scope this",
      "spec for", "define the approach"], "coeus"),
    (["run the plan", "execute the plan", "atlas", "start the boulder",
      "continue the boulder", "boulder", "sequential execution", "plan-driven"], "atlas"),
    (["iapetus", "deeply analyze", "deep analyze", "complex refactor",
      "multi-file", "architectural", "deep execution", "think deeply"], "iapetus"),
    (["consult on", "themis", "architecture decision", "review this",
      "debug this", "what do you think about", "is this a good approach"], "themis"),
    (["ultrawork", "ulw", "heracles", "finish this now", "just do it",
      "no excuses", "relentless"], "heracles"),
    (["coordinator", "orchestrate", "coordinate this", "complex problem",
      "multi-disciplinary", "break this down", "delegation", "delegate"], "coordinator"),
]


def route(message: str, llm: KronosLLM | None = None) -> tuple[TitanInfo, str]:
    msg = message.lower()

    # 1. Fast Path: Keyword matching
    for keywords, titan_key in ROUTING_RULES:
        for kw in keywords:
            if kw in msg:
                info = TITAN_REGISTRY[titan_key]
                return info, f"Keyword match: '{kw}' → {titan_key}"

    # 2. Semantic Path: LLM classification
    if llm:
        try:
            titan_key = llm.classify_intent(message, TITAN_REGISTRY)
            return TITAN_REGISTRY[titan_key], f"Semantic classification → {titan_key}"
        except Exception:
            # Fallback to defaults on LLM failure
            pass

    # 3. Heuristic Fallback
    if any(kw in msg for kw in ["implement", "add the", "build the", "create the",
                                  "fix the", "change the", "edit the"]):
        return TITAN_REGISTRY["talos"], "Implementation request → direct execution"

    return TITAN_REGISTRY["talos"], "Default to Talos (primary orchestrator)"


def route_explicit(titan_name: str) -> TitanInfo:
    return get_titan(titan_name)

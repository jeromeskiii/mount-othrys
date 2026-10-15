from __future__ import annotations

from othrys import match_rule

from .llm import KronosLLM
from .registry import TITAN_REGISTRY, TitanInfo, get_titan

#: Canonical table Titan -> this registry's key.
#:
#: The canonical table uses the engine's vocabulary, which has a `kronos` Titan;
#: Kronos's own registry names that role `coordinator`. Everything else maps
#: one-to-one.
CANONICAL_TO_REGISTRY: dict[str, str] = {
    "coeus": "coeus",
    "atlas": "atlas",
    "iapetus": "iapetus",
    "talos": "talos",
    "themis": "themis",
    "heracles": "heracles",
    "kronos": "coordinator",
}


def route(message: str, llm: KronosLLM | None = None) -> tuple[TitanInfo, str]:
    """Resolve a request to a Titan.

    MF-2: this module used to carry its own ``ROUTING_RULES`` keyword list, which
    had drifted from the engine's triggers and from Talos's. Routing now defers
    to the single canonical table via ``othrys.routing``; only the optional
    semantic-classification step remains local.
    """
    found = match_rule(message)
    if found is not None:
        registry_key = CANONICAL_TO_REGISTRY.get(found.titan)
        if registry_key is not None:
            return TITAN_REGISTRY[registry_key], found.reason

    # Semantic path: reached only when no canonical rule matched.
    if llm is not None:
        try:
            titan_key = llm.classify_intent(message, TITAN_REGISTRY)
            return TITAN_REGISTRY[titan_key], f"Semantic classification → {titan_key}"
        except Exception:
            # Fallback to defaults on LLM failure
            pass

    return TITAN_REGISTRY["talos"], "Default to Talos (primary orchestrator)"


def route_explicit(titan_name: str) -> TitanInfo:
    return get_titan(titan_name)

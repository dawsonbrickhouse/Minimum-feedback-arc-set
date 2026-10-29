"""Registry of candidate reduction rules (see docs/candidate_rules.md).

To add a rule: implement ``CandidateRule`` in a new module and append an
instance to ``_RULES`` below (docs/adding_a_candidate.md walks through it).
"""

from __future__ import annotations

from .base import Application, CandidateRule, Match, Oracle, Status
from .false_generalizations import ArcDisjointCycleBound, GreedyMaxDeltaFirst, InDegreeOneContraction
from .structural import (
    ArcDomination,
    InDegreeOneExchange,
    ModuleContraction,
    NeighborhoodDominance,
    ThreeTerminalGadget,
    TwoTerminalSeparator,
)
from .two_cycle_cancellation import TwoCycleCancellation
from .two_cycle_local_bound import TwoCycleLocalBound

_RULES: list[CandidateRule] = [
    TwoCycleLocalBound(),
    TwoCycleCancellation(),
    ModuleContraction(),
    TwoTerminalSeparator(),
    ThreeTerminalGadget(),
    NeighborhoodDominance(),
    InDegreeOneExchange(),
    ArcDomination(),
    ArcDisjointCycleBound(),
    InDegreeOneContraction(),
    GreedyMaxDeltaFirst(),
]

REGISTRY: dict[str, CandidateRule] = {r.name: r for r in _RULES}
if len(REGISTRY) != len(_RULES):
    raise RuntimeError("duplicate candidate rule names")


def get_rule(name: str) -> CandidateRule:
    try:
        return REGISTRY[name]
    except KeyError:
        raise KeyError(f"unknown candidate {name!r}; known: {sorted(REGISTRY)}") from None


__all__ = ["Application", "CandidateRule", "Match", "Oracle", "REGISTRY", "Status", "get_rule"]

"""Interface every candidate (unproven or under-test) reduction rule implements.

A candidate claims an exact identity

    OPT(G) = OPT(G') + correction

for every graph ``G`` and *match* (a concrete occurrence of the rule's pattern)
satisfying its preconditions, where ``G'`` is produced by ``apply``. A candidate
may also provide ``lift``: a map from an optimal FAS of ``G'`` to a claimed
optimal FAS of ``G``. The harness (``fas.harness``) checks both claims.

Candidates are deliberately isolated from the core solver: nothing in
``fas.exact_solver`` or ``fas.reductions`` imports this package.
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar

from ..exact_solver import FASResult
from ..graph import Arc, Graph

Match = dict[str, Any]
"""A JSON-serialisable description of one occurrence of a rule's pattern."""

Lift = Callable[[frozenset[Arc]], frozenset[Arc]]


class Status(str, Enum):
    """Research-notebook statuses (see docs/research_notebook.md)."""

    IDEA = "IDEA"
    CONJECTURE = "CONJECTURE"
    TESTED_ON_FINITE_INSTANCES = "TESTED_ON_FINITE_INSTANCES"
    COUNTEREXAMPLE_FOUND = "COUNTEREXAMPLE_FOUND"
    PROOF_ATTEMPT = "PROOF_ATTEMPT"
    PROVED_WITHIN_STATED_ASSUMPTIONS = "PROVED_WITHIN_STATED_ASSUMPTIONS"
    NOVELTY_UNVERIFIED = "NOVELTY_UNVERIFIED"
    PRIOR_ART_FOUND = "PRIOR_ART_FOUND"


class Oracle:
    """Exact OPT oracle shared by the harness and by rules that need sub-solutions.

    Raises ``fas.exact_solver.SolverLimitError`` when a strongly connected
    component exceeds ``max_component_size``; the harness reports that as
    INCONCLUSIVE, never as a pass.
    """

    def __init__(self, max_component_size: int = 14, cache_size: int = 200_000):
        self.max_component_size = max_component_size
        self._cache: dict[Graph, FASResult] = {}
        self._cache_size = cache_size
        self.calls = 0

    def solve(self, g: Graph) -> FASResult:
        from ..exact_solver import solve_exact

        hit = self._cache.get(g)
        if hit is not None:
            return hit
        self.calls += 1
        res = solve_exact(g, method="dp", decompose_sccs=True, max_component_size=self.max_component_size)
        if len(self._cache) < self._cache_size:
            self._cache[g] = res
        return res

    def opt(self, g: Graph) -> int:
        return self.solve(g).cost


@dataclass(frozen=True)
class Application:
    """Result of applying a candidate at one match."""

    reduced: Graph
    correction: int
    lift: Lift | None = None
    note: str = ""


class CandidateRule(ABC):
    """Subclass this to add a rule; see docs/adding_a_candidate.md."""

    name: ClassVar[str]
    title: ClassVar[str]
    statuses: ClassVar[tuple[Status, ...]]
    pattern: ClassVar[str]
    preconditions: ClassVar[str]
    transformation: ClassVar[str]
    claimed_identity: ClassVar[str]
    proof_sketch: ClassVar[str] = "none yet"
    open_questions: ClassVar[str] = ""
    expected: ClassVar[str] = "unknown"  # "true", "false" or "unknown": the author's prior, for reporting only
    exhaustive_kinds: ClassVar[tuple[str, ...]] = ("digraph",)

    @abstractmethod
    def find_matches(self, g: Graph) -> list[Match]:
        """All occurrences of the pattern in ``g`` that satisfy the preconditions."""

    @abstractmethod
    def check_preconditions(self, g: Graph, match: Match) -> str | None:
        """Independently re-check a match: return None if valid, else the reason it fails."""

    @abstractmethod
    def apply(self, g: Graph, match: Match, oracle: Oracle) -> Application:
        """Build ``G'`` and the claimed correction for one valid match."""

    def explain_preconditions(self, g: Graph, match: Match) -> str:
        """Human-readable evidence that the preconditions hold at ``match``."""
        return f"match {match} satisfies: {self.preconditions}"

    def generate(self, rng: random.Random, n: int) -> Graph | None:
        """Optionally build a random graph on about ``n`` vertices that contains a match.
        Returning None means 'no targeted generator'."""
        return None

    def card(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "title": self.title,
            "statuses": [s.value for s in self.statuses],
            "pattern": self.pattern,
            "preconditions": self.preconditions,
            "transformation": self.transformation,
            "claimed_identity": self.claimed_identity,
            "proof_sketch": self.proof_sketch,
            "open_questions": self.open_questions,
            "expected": self.expected,
        }

"""Independent checks for claimed feedback arc set solutions."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from .exact_solver import FASResult, backward_arcs
from .graph import Arc, Graph, find_cycle, is_acyclic


@dataclass
class VerificationReport:
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems

    def require(self, condition: bool, message: str) -> None:
        if not condition:
            self.problems.append(message)


def is_feedback_arc_set(g: Graph, removed: Iterable[Arc]) -> bool:
    removed = frozenset(removed)
    return removed <= frozenset(g.arc_pairs()) and is_acyclic(g.remove_arc_pairs(removed))


def verify_removed_set(g: Graph, removed: Iterable[Arc], expected_cost: int | None = None) -> VerificationReport:
    """Check that ``removed`` is a FAS of ``g`` (and optimal if ``expected_cost`` is given)."""
    removed = frozenset(removed)
    report = VerificationReport()
    unknown = removed - frozenset(g.arc_pairs())
    report.require(not unknown, f"removed arcs not in graph: {sorted(unknown)}")
    if unknown:
        return report
    remaining = g.remove_arc_pairs(removed)
    cycle = find_cycle(remaining)
    report.require(cycle is None, f"graph minus removed arcs still has cycle {cycle}")
    if expected_cost is not None:
        cost = g.arc_weight(removed)
        report.require(cost == expected_cost, f"removed weight {cost} != expected optimum {expected_cost}")
    return report


def verify_result(g: Graph, result: FASResult, expected_cost: int | None = None) -> VerificationReport:
    """Check internal consistency of a solver result and, optionally, its optimality."""
    report = VerificationReport()
    report.require(
        sorted(result.ordering) == list(g.vertices),
        "ordering is not a permutation of the vertices",
    )
    if not report.ok:
        return report
    report.require(
        result.removed_arcs == backward_arcs(g, result.ordering),
        "removed arcs differ from the backward arcs of the ordering",
    )
    report.require(
        result.cost == g.arc_weight(result.removed_arcs),
        f"reported cost {result.cost} != weight of removed arcs",
    )
    report.problems.extend(verify_removed_set(g, result.removed_arcs, expected_cost).problems)
    return report

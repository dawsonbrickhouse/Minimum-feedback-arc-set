"""Baseline (proven, literature-standard) reduction rules with solution lifting.

Every rule here satisfies an exact identity ``OPT(G) = OPT(G') + offset`` and
provides a ``lift`` that maps an optimal FAS of the reduced graph ``G'`` to an
optimal FAS of ``G``. Proofs, preconditions, runtimes and sources are in
``docs/baseline_reductions.md``. Experimental rules do *not* belong here; they
live in ``fas.candidates`` until proven.

Rules (applied to a fixpoint, in this order):

* ``self_loop``         remove all self-loops; offset = their total multiplicity.
* ``source_sink``       delete a vertex with no in-arcs or no out-arcs.
* ``inter_scc_arcs``    delete every arc whose ends lie in different SCCs.
* ``degree_two_bypass`` a vertex ``v`` whose only in-neighbour is ``u`` (weight a)
                        and only out-neighbour is ``w`` (weight b), ``u, w != v``,
                        is replaced by ``min(a, b)`` extra copies of ``(u, w)``.

After the fixpoint the kernel is split into its strongly connected components,
which are solved independently (OPT is additive over SCCs).
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field

from .exact_solver import FASResult, Method, solve_exact
from .graph import Arc, Graph, strongly_connected_components, topological_order

SELF_LOOP = "self_loop"
SOURCE_SINK = "source_sink"
INTER_SCC = "inter_scc_arcs"
BYPASS = "degree_two_bypass"
BASELINE_RULES: tuple[str, ...] = (SELF_LOOP, SOURCE_SINK, INTER_SCC, BYPASS)

RemovedSet = frozenset[Arc]


# ---------------------------------------------------------------------- steps


@dataclass(frozen=True)
class ReductionStep:
    """One applied rule. ``offset`` is the weight it commits to the solution."""

    rule: str
    offset: int

    def lift(self, removed: RemovedSet) -> RemovedSet:
        return removed

    def describe(self) -> str:
        return self.rule


@dataclass(frozen=True)
class SelfLoopStep(ReductionStep):
    loops: tuple[int, ...] = ()

    def lift(self, removed: RemovedSet) -> RemovedSet:
        return removed | {(v, v) for v in self.loops}

    def describe(self) -> str:
        return f"removed self-loops at {list(self.loops)} (weight {self.offset})"


@dataclass(frozen=True)
class VertexRemovalStep(ReductionStep):
    vertex: int = -1
    reason: str = ""

    def describe(self) -> str:
        return f"deleted {self.reason} vertex {self.vertex}"


@dataclass(frozen=True)
class InterSccStep(ReductionStep):
    arcs: tuple[Arc, ...] = ()

    def describe(self) -> str:
        return f"deleted {len(self.arcs)} arcs between different SCCs"


@dataclass(frozen=True)
class BypassStep(ReductionStep):
    u: int = -1
    v: int = -1
    w: int = -1
    a: int = 0  # multiplicity of (u, v)
    b: int = 0  # multiplicity of (v, w)
    c: int = 0  # multiplicity of (u, w) before the step

    def lift(self, removed: RemovedSet) -> RemovedSet:
        if (self.u, self.w) not in removed:
            return removed
        lifted = set(removed)
        lifted.discard((self.u, self.w))
        if self.c > 0:
            lifted.add((self.u, self.w))
        lifted.add((self.u, self.v) if self.a <= self.b else (self.v, self.w))
        return frozenset(lifted)

    def describe(self) -> str:
        return (f"bypassed {self.v}: {self.u}->{self.v} (x{self.a}), {self.v}->{self.w} (x{self.b}) "
                f"replaced by {min(self.a, self.b)} extra copies of {self.u}->{self.w}")


# ---------------------------------------------------------------------- mutable work graph


class _WorkGraph:
    def __init__(self, g: Graph):
        self.out: dict[int, dict[int, int]] = {v: dict(g.out_arcs(v)) for v in g.vertices}
        self.inn: dict[int, dict[int, int]] = {v: dict(g.in_arcs(v)) for v in g.vertices}

    def remove_vertex(self, v: int) -> None:
        for w in self.out.pop(v):
            if w != v:
                del self.inn[w][v]
        for u in self.inn.pop(v):
            if u != v:
                del self.out[u][v]

    def remove_arc(self, u: int, v: int) -> None:
        del self.out[u][v]
        del self.inn[v][u]

    def add_arc(self, u: int, v: int, k: int) -> None:
        self.out[u][v] = self.out[u].get(v, 0) + k
        self.inn[v][u] = self.inn[v].get(u, 0) + k

    def to_graph(self) -> Graph:
        return Graph(self.out, {(u, v): k for u, nbrs in self.out.items() for v, k in nbrs.items()})


def _remove_self_loops(wg: _WorkGraph) -> list[ReductionStep]:
    loops = sorted(v for v in wg.out if v in wg.out[v])
    if not loops:
        return []
    weight = sum(wg.out[v][v] for v in loops)
    for v in loops:
        wg.remove_arc(v, v)
    return [SelfLoopStep(SELF_LOOP, weight, tuple(loops))]


def _remove_sources_sinks(wg: _WorkGraph) -> list[ReductionStep]:
    steps: list[ReductionStep] = []
    pending = sorted(wg.out)
    while pending:
        next_round: set[int] = set()
        for v in pending:
            if v not in wg.out:
                continue
            reason = "source" if not wg.inn[v] else "sink" if not wg.out[v] else ""
            if reason:
                next_round.update(w for w in (*wg.out[v], *wg.inn[v]) if w != v)
                wg.remove_vertex(v)
                steps.append(VertexRemovalStep(SOURCE_SINK, 0, v, reason))
        pending = sorted(next_round)
    return steps


def _remove_inter_scc_arcs(wg: _WorkGraph) -> list[ReductionStep]:
    comp_of = {v: i for i, comp in enumerate(strongly_connected_components(wg.to_graph())) for v in comp}
    arcs = [(u, v) for u, nbrs in wg.out.items() for v in nbrs if comp_of[u] != comp_of[v]]
    if not arcs:
        return []
    for u, v in arcs:
        wg.remove_arc(u, v)
    return [InterSccStep(INTER_SCC, 0, tuple(sorted(arcs)))]


def _bypass_degree_two(wg: _WorkGraph) -> list[ReductionStep]:
    steps: list[ReductionStep] = []
    for v in sorted(wg.out):
        if v not in wg.out or len(wg.inn[v]) != 1 or len(wg.out[v]) != 1:
            continue
        (u, a), = wg.inn[v].items()
        (w, b), = wg.out[v].items()
        if u == v or w == v:
            continue
        c = wg.out[u].get(w, 0)
        wg.remove_vertex(v)
        wg.add_arc(u, w, min(a, b))
        steps.append(BypassStep(BYPASS, 0, u, v, w, a, b, c))
    return steps


_RULE_FUNCS = {
    SELF_LOOP: _remove_self_loops,
    SOURCE_SINK: _remove_sources_sinks,
    INTER_SCC: _remove_inter_scc_arcs,
    BYPASS: _bypass_degree_two,
}


# ---------------------------------------------------------------------- driver


@dataclass
class ReductionResult:
    original: Graph
    kernel: Graph
    steps: list[ReductionStep] = field(default_factory=list)

    @property
    def offset(self) -> int:
        return sum(s.offset for s in self.steps)

    def components(self) -> list[Graph]:
        """Kernel SCCs with at least one arc (every other vertex is trivially solved)."""
        comps = []
        for comp in strongly_connected_components(self.kernel):
            sub = self.kernel.induced_subgraph(comp)
            if sub.num_arc_pairs:
                comps.append(sub)
        return comps

    def rule_counts(self) -> dict[str, int]:
        return dict(Counter(s.rule for s in self.steps))

    def lift(self, kernel_removed: Iterable[Arc]) -> RemovedSet:
        removed = frozenset(kernel_removed)
        for step in reversed(self.steps):
            removed = step.lift(removed)
        return removed

    def summary(self) -> dict:
        return {
            "n_before": self.original.n,
            "m_before": self.original.m,
            "n_after": self.kernel.n,
            "m_after": self.kernel.m,
            "offset": self.offset,
            "rule_counts": self.rule_counts(),
            "component_sizes": sorted((c.n for c in self.components()), reverse=True),
        }


def reduce_graph(g: Graph, rules: Iterable[str] = BASELINE_RULES) -> ReductionResult:
    """Apply the selected baseline rules until none changes the graph."""
    selected = [r for r in BASELINE_RULES if r in set(rules)]
    unknown = set(rules) - set(BASELINE_RULES)
    if unknown:
        raise ValueError(f"unknown baseline rules {sorted(unknown)}")
    wg = _WorkGraph(g)
    steps: list[ReductionStep] = []
    while True:
        round_steps: list[ReductionStep] = []
        for rule in selected:
            round_steps.extend(_RULE_FUNCS[rule](wg))
        if not round_steps:
            break
        steps.extend(round_steps)
    return ReductionResult(g, wg.to_graph(), steps)


def ordering_from_removed(g: Graph, removed: Iterable[Arc]) -> tuple[int, ...]:
    order = topological_order(g.remove_arc_pairs(removed))
    if order is None:
        raise ValueError("removed arcs do not form a feedback arc set")
    return order


def solve_with_reductions(
    g: Graph,
    rules: Iterable[str] = BASELINE_RULES,
    method: Method = "dp",
    max_component_size: int | None = None,
) -> tuple[FASResult, ReductionResult]:
    """Reduce, solve each kernel SCC exactly, and lift back to an optimal FAS of ``g``."""
    red = reduce_graph(g, rules)
    kernel_removed: set[Arc] = set()
    for comp in red.components():
        kernel_removed |= solve_exact(comp, method=method, max_component_size=max_component_size).removed_arcs
    removed = red.lift(kernel_removed)
    ordering = ordering_from_removed(g, removed)
    cost = g.arc_weight(removed)
    expected = red.offset + red.kernel.arc_weight(kernel_removed)
    if cost != expected:
        raise AssertionError(f"lifted cost {cost} != offset + kernel cost {expected}")
    return FASResult(cost, ordering, removed, f"{method}+baseline"), red

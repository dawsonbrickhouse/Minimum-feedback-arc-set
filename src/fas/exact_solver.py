"""Exact minimum feedback arc set solvers.

Both solvers use the *linear ordering* formulation: for an ordering ``pi`` of
the vertices, an arc ``(u, v)`` is *backward* when ``pos(u) >= pos(v)`` (so
self-loops are always backward). The backward arcs of any ordering form a
feedback arc set, and every minimal FAS is the backward set of some ordering,
hence ``OPT(G) = min_pi  sum of multiplicities of backward arcs``
(proof in ``docs/problem_definition.md``).

Determinism / tie-breaking:

* ``solve_brute_force`` returns the lexicographically first optimal ordering
  of the sorted vertex list.
* ``solve_dp`` reconstructs from the full set downwards, choosing as the last
  vertex of each prefix the *smallest* vertex id achieving the optimum.
* ``solve_exact`` with SCC decomposition concatenates per-component orderings
  in the condensation's topological order (Tarjan order, see ``graph.py``).

Different solvers may therefore return different optimal orderings; the cost
is always the same.
"""

from __future__ import annotations

import itertools
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from .graph import Arc, Graph, strongly_connected_components

DEFAULT_BRUTE_FORCE_LIMIT = 9
DEFAULT_DP_LIMIT = 20

Method = Literal["dp", "brute"]


class SolverLimitError(RuntimeError):
    """Raised when an instance exceeds a configured exact-solver size limit."""


@dataclass(frozen=True)
class FASResult:
    """An optimal solution: ``removed_arcs`` are arc pairs (all copies removed)."""

    cost: int
    ordering: tuple[int, ...]
    removed_arcs: frozenset[Arc]
    method: str

    def to_dict(self) -> dict:
        return {
            "cost": self.cost,
            "ordering": list(self.ordering),
            "removed_arcs": sorted([list(a) for a in self.removed_arcs]),
            "method": self.method,
        }


def backward_arcs(g: Graph, ordering: Sequence[int]) -> frozenset[Arc]:
    pos = {v: i for i, v in enumerate(ordering)}
    if len(pos) != g.n or set(pos) != set(g.vertices):
        raise ValueError("ordering must be a permutation of the graph's vertices")
    return frozenset((u, v) for (u, v), _ in g.arcs() if pos[u] >= pos[v])


def ordering_cost(g: Graph, ordering: Sequence[int]) -> int:
    return g.arc_weight(backward_arcs(g, ordering))


def _result(g: Graph, ordering: Sequence[int], method: str) -> FASResult:
    removed = backward_arcs(g, ordering)
    return FASResult(g.arc_weight(removed), tuple(ordering), removed, method)


def _check_limit(n: int, limit: int, what: str) -> None:
    if n > limit:
        raise SolverLimitError(f"{what}: {n} vertices exceeds limit {limit}")


def solve_brute_force(g: Graph, max_vertices: int = DEFAULT_BRUTE_FORCE_LIMIT) -> FASResult:
    """Try all ``n!`` orderings. Intended only as an independent oracle."""
    _check_limit(g.n, max_vertices, "brute force")
    arcs = list(g.arcs())
    best_cost: int | None = None
    best_order: tuple[int, ...] = g.vertices
    for perm in itertools.permutations(g.vertices):
        pos = {v: i for i, v in enumerate(perm)}
        cost = sum(k for (u, v), k in arcs if pos[u] >= pos[v])
        if best_cost is None or cost < best_cost:
            best_cost, best_order = cost, perm
            if cost == 0:
                break
    return _result(g, best_order, "brute")


def solve_dp(g: Graph, max_vertices: int = DEFAULT_DP_LIMIT) -> FASResult:
    """Subset dynamic programme, ``O(2^n * n)`` time and ``O(2^n)`` memory.

    ``DP[S]`` is the minimum backward weight of an ordering of ``S`` placed as a
    prefix; with ``v`` last in ``S`` the new backward arcs are ``v -> S\\{v}``:
    ``DP[S] = min_v DP[S \\ v] + w(v -> S \\ v)``. Self-loops are added separately.
    """
    _check_limit(g.n, max_vertices, "subset DP")
    verts = g.vertices
    n = len(verts)
    idx = {v: i for i, v in enumerate(verts)}
    out_mask = [0] * n
    extra: list[list[tuple[int, int]]] = [[] for _ in range(n)]
    loop_weight = 0
    for (u, v), k in g.arcs():
        if u == v:
            loop_weight += k
            continue
        i, bit = idx[u], 1 << idx[v]
        out_mask[i] |= bit
        if k > 1:
            extra[i].append((bit, k - 1))

    def step_cost(i: int, rest: int) -> int:
        c = (out_mask[i] & rest).bit_count()
        for bit, k in extra[i]:
            if rest & bit:
                c += k
        return c

    full = (1 << n) - 1
    dp = [0] * (full + 1)
    for s in range(1, full + 1):
        best = -1
        t = s
        while t:
            low = t & -t
            i = low.bit_length() - 1
            rest = s ^ low
            c = dp[rest] + step_cost(i, rest)
            if best < 0 or c < best:
                best = c
            t ^= low
        dp[s] = best

    order_rev: list[int] = []
    s = full
    while s:
        for i in range(n):
            low = 1 << i
            if s & low and dp[s ^ low] + step_cost(i, s ^ low) == dp[s]:
                order_rev.append(verts[i])
                s ^= low
                break
    ordering = tuple(reversed(order_rev))
    result = _result(g, ordering, "dp")
    if result.cost != dp[full] + loop_weight:
        raise AssertionError("internal error: DP reconstruction cost mismatch")
    return result


def solve_exact(
    g: Graph,
    method: Method = "dp",
    decompose_sccs: bool = True,
    max_component_size: int | None = None,
) -> FASResult:
    """Exact solver. With ``decompose_sccs`` each strongly connected component is
    solved separately (OPT is additive over SCCs; see docs/baseline_reductions.md).
    ``max_component_size`` overrides the per-method default size limit."""
    if method == "dp":
        limit = DEFAULT_DP_LIMIT if max_component_size is None else max_component_size
        solver = lambda h: solve_dp(h, max_vertices=limit)  # noqa: E731
    elif method == "brute":
        limit = DEFAULT_BRUTE_FORCE_LIMIT if max_component_size is None else max_component_size
        solver = lambda h: solve_brute_force(h, max_vertices=limit)  # noqa: E731
    else:
        raise ValueError(f"unknown method {method!r}")
    if not decompose_sccs:
        return solver(g)
    ordering: list[int] = []
    for comp in strongly_connected_components(g):
        if len(comp) == 1:
            ordering.extend(comp)
        else:
            ordering.extend(solver(g.induced_subgraph(comp)).ordering)
    return _result(g, ordering, f"{method}+scc")


def opt_value(g: Graph, **kwargs) -> int:
    return solve_exact(g, **kwargs).cost

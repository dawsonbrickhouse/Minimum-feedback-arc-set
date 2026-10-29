"""Small helpers shared by candidate rules."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable

from ..graph import Arc, Graph


def heavy_weight(g: Graph) -> int:
    """A multiplicity larger than any feedback arc set of ``g`` can cost."""
    return g.m + 1


def make_undeletable(g: Graph, arcs: Iterable[Arc]) -> Graph:
    """Add ``heavy_weight(g)`` copies to each arc so no optimal FAS removes it.
    Arcs that do not exist yet are created (used to force an order)."""
    big = heavy_weight(g)
    return g.with_arcs({a: big for a in set(arcs)})


def two_cycle_bound(g: Graph, v: int) -> int:
    """L(v): total of min(w(u,v), w(v,u)) over 2-cycles at v. The 2-cycles at v are
    arc-disjoint, so every FAS contains at least L(v) weight of arcs incident to v."""
    return sum(min(g.multiplicity(u, v), k) for u, k in g.out_arcs(v).items() if u != v and g.has_arc(u, v))


def max_arc_disjoint_cycles_through(g: Graph, v: int) -> int:
    """nu(v): maximum number of arc-disjoint cycles through ``v`` (multiplicities are
    capacities), computed as a max-flow from v's out-side to v's in-side.
    Self-loops at ``v`` are ignored."""
    source, sink = ("out", v), ("in", v)

    def node(x: int, as_tail: bool):
        if x != v:
            return x
        return source if as_tail else sink

    cap: dict[object, dict[object, int]] = {}
    for (a, b), k in g.arcs():
        if a == b:
            continue
        ta, hb = node(a, True), node(b, False)
        cap.setdefault(ta, {}).setdefault(hb, 0)
        cap[ta][hb] += k
        cap.setdefault(hb, {}).setdefault(ta, 0)
    flow = 0
    while True:
        parent: dict[object, object] = {source: None}
        queue = deque([source])
        while queue and sink not in parent:
            x = queue.popleft()
            for y, c in cap.get(x, {}).items():
                if c > 0 and y not in parent:
                    parent[y] = x
                    queue.append(y)
        if sink not in parent:
            return flow
        path = []
        y = sink
        while parent[y] is not None:
            path.append((parent[y], y))
            y = parent[y]
        push = min(cap[a][b] for a, b in path)
        for a, b in path:
            cap[a][b] -= push
            cap[b][a] += push
        flow += push


def in_arc_pairs(g: Graph, v: int) -> set[Arc]:
    return {(u, v) for u in g.in_neighbors(v)}


def out_arc_pairs(g: Graph, v: int) -> set[Arc]:
    return {(v, w) for w in g.out_neighbors(v)}

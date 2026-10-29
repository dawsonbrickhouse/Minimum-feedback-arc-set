"""Exploratory mining of exhaustive small-graph data.

These tools *suggest* hypotheses; they never prove anything. Every pattern they
report is "true on the enumerated finite instances" only.

Analyses
--------
``vertex``    For each vertex v: is deleting v and paying all its in-arcs (or all
              its out-arcs) optimal? Grouped by a local signature, with the first
              failing example per signature and whether a proved rule explains it.
``arc``       For each arc pair e: is e in every / some / no optimal FAS? Grouped
              by a local signature.
``boundary``  For small "sides" H attached to 3 terminals, the boundary cost
              function f_H(sigma) = min cost of H over orders inducing the terminal
              order sigma; checks whether f_H is pairwise (representable by arcs
              among the terminals plus a constant).

Isomorphic copies are enumerated once, but symmetric vertices/arcs inside one
graph are each counted; counts are therefore "vertex (arc) occurrences in
isomorphism-class representatives".
"""

from __future__ import annotations

import itertools
import time
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from .boundary import boundary_function, pairwise_decomposition
from .candidates.base import Oracle
from .candidates.common import heavy_weight, max_arc_disjoint_cycles_through, two_cycle_bound
from .generators import isomorphism_classes
from .graph import Graph, reachable

# ---------------------------------------------------------------------- generic aggregation


@dataclass
class SignatureStats:
    count: int = 0
    labels: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    examples: dict[str, dict[str, Any]] = field(default_factory=dict)

    def add(self, label: str, example: dict[str, Any]) -> None:
        self.count += 1
        self.labels[label] += 1
        if label not in self.examples:
            self.examples[label] = example

    def to_dict(self) -> dict[str, Any]:
        return {"count": self.count, "labels": dict(self.labels), "examples": self.examples}


def _graphs(kind: str, n_values: Iterable[int]) -> Iterable[Graph]:
    for n in n_values:
        yield from isomorphism_classes(n, kind)  # type: ignore[arg-type]


# ---------------------------------------------------------------------- vertex forcing


def vertex_signature(g: Graph, v: int) -> tuple[int, int, int, int]:
    return (g.in_weight(v), g.out_weight(v), two_cycle_bound(g, v), max_arc_disjoint_cycles_through(g, v))


def mine_vertex_forcing(kind: str = "digraph", n_values: Iterable[int] = (3, 4, 5),
                        oracle: Oracle | None = None) -> dict[str, Any]:
    """Label each vertex occurrence by which 'delete v and pay one side' moves are optimal."""
    oracle = oracle or Oracle()
    stats: dict[tuple[int, ...], SignatureStats] = defaultdict(SignatureStats)
    start = time.monotonic()
    graphs = 0
    for g in _graphs(kind, n_values):
        graphs += 1
        opt = oracle.opt(g)
        for v in g.vertices:
            d_in, d_out, bound, nu = sig = vertex_signature(g, v)
            if d_in == 0 or d_out == 0:
                continue  # sources/sinks are a baseline rule
            delta = opt - oracle.opt(g.remove_vertices([v]))
            label = ("in+out" if delta == d_in == d_out else "in" if delta == d_in
                     else "out" if delta == d_out else "neither")
            stats[sig].add(label, {"graph": g.to_dict(), "vertex": v, "opt": opt, "delta": delta})
    rows = []
    for sig, st in sorted(stats.items()):
        d_in, d_out, bound, nu = sig
        forced_in = st.labels.get("in", 0) + st.labels.get("in+out", 0)
        forced_out = st.labels.get("out", 0) + st.labels.get("in+out", 0)
        explained_in = d_in <= bound
        explained_out = d_out <= bound
        rows.append({
            "signature": {"w_in": d_in, "w_out": d_out, "L_two_cycle": bound, "nu_cycles": nu},
            "occurrences": st.count,
            "forced_in_fraction": round(forced_in / st.count, 4),
            "forced_out_fraction": round(forced_out / st.count, 4),
            "always_forced_in": forced_in == st.count,
            "always_forced_out": forced_out == st.count,
            "explained_by_two_cycle_bound": {"in": explained_in, "out": explained_out},
            "unexplained_always_forced": (forced_in == st.count and not explained_in)
            or (forced_out == st.count and not explained_out),
            "first_neither_example": st.examples.get("neither"),
            "labels": dict(st.labels),
        })
    return {"analysis": "vertex", "kind": kind, "n_values": list(n_values), "graphs": graphs,
            "elapsed_seconds": round(time.monotonic() - start, 2), "rows": rows}


# ---------------------------------------------------------------------- arc status


def arc_signature(g: Graph, a: int, b: int) -> tuple[int, ...]:
    return (
        int(g.has_arc(b, a)),
        g.out_weight(a), g.in_weight(a), g.out_weight(b), g.in_weight(b),
    )


def mine_arc_status(kind: str = "digraph", n_values: Iterable[int] = (3, 4, 5),
                    oracle: Oracle | None = None) -> dict[str, Any]:
    """Classify each arc on a cycle as in 'all', 'some' or 'no' optimal FAS."""
    oracle = oracle or Oracle()
    stats: dict[tuple[int, ...], SignatureStats] = defaultdict(SignatureStats)
    start = time.monotonic()
    graphs = 0
    for g in _graphs(kind, n_values):
        graphs += 1
        opt = oracle.opt(g)
        big = heavy_weight(g)
        for (a, b), k in g.arcs():
            if a == b or a not in reachable(g, b):
                continue  # loops are always removed; arcs on no cycle never
            in_some = oracle.opt(g.remove_arc_pairs([(a, b)])) + k == opt
            in_all = oracle.opt(g.with_arcs({(a, b): big})) > opt
            label = "all" if in_all else "some" if in_some else "none"
            stats[arc_signature(g, a, b)].add(label, {"graph": g.to_dict(), "arc": [a, b], "opt": opt})
    rows = []
    for sig, st in sorted(stats.items()):
        rows.append({
            "signature": dict(zip(("antiparallel", "tail_out", "tail_in", "head_out", "head_in"), sig)),
            "occurrences": st.count,
            "labels": dict(st.labels),
            "uniform": len(st.labels) == 1,
            "examples": st.examples,
        })
    return {"analysis": "arc", "kind": kind, "n_values": list(n_values), "graphs": graphs,
            "elapsed_seconds": round(time.monotonic() - start, 2), "rows": rows}


def _arc_label(g: Graph, a: int, b: int, k: int, opt: int, oracle: Oracle) -> str:
    in_some = oracle.opt(g.remove_arc_pairs([(a, b)])) + k == opt
    in_all = oracle.opt(g.with_arcs({(a, b): heavy_weight(g)})) > opt
    return "all" if in_all else "some" if in_some else "none"


def falsify_arc_signatures(result: dict[str, Any], graphs: Iterable[Graph],
                           oracle: Oracle | None = None, min_occurrences: int = 10) -> list[dict[str, Any]]:
    """Re-test every uniform 'all'/'none' arc signature from ``mine_arc_status`` on
    further graphs (e.g. larger random ones). Returns one row per hypothesis with
    its confirmations and the first refuting example, if any."""
    oracle = oracle or Oracle()
    hyps = {}
    for row in result["rows"]:
        if row["uniform"] and row["occurrences"] >= min_occurrences:
            (label,) = row["labels"]
            if label in ("all", "none"):
                hyps[tuple(row["signature"].values())] = {"signature": row["signature"], "claim": label,
                                                          "seen_exhaustive": row["occurrences"],
                                                          "confirmed": 0, "refuted": 0, "first_refutation": None}
    for g in graphs:
        opt = None
        for (a, b), k in g.arcs():
            h = hyps.get(arc_signature(g, a, b))
            if h is None or a == b or a not in reachable(g, b):
                continue
            opt = oracle.opt(g) if opt is None else opt
            label = _arc_label(g, a, b, k, opt, oracle)
            if label == h["claim"]:
                h["confirmed"] += 1
            else:
                h["refuted"] += 1
                if h["first_refutation"] is None:
                    h["first_refutation"] = {"graph": g.to_dict(), "arc": [a, b], "label": label}
    return sorted(hyps.values(), key=lambda h: (h["refuted"] > 0, -h["confirmed"]))


def falsify_vertex_signatures(result: dict[str, Any], graphs: Iterable[Graph],
                              oracle: Oracle | None = None) -> list[dict[str, Any]]:
    """Re-test 'always forced' vertex signatures from ``mine_vertex_forcing``."""
    oracle = oracle or Oracle()
    hyps = {}
    for row in result["rows"]:
        for side in ("in", "out"):
            if row[f"always_forced_{side}"]:
                sig = tuple(row["signature"].values())
                hyps[(sig, side)] = {"signature": row["signature"], "side": side,
                                     "explained_by_two_cycle_bound": row["explained_by_two_cycle_bound"][side],
                                     "confirmed": 0, "refuted": 0, "first_refutation": None}
    for g in graphs:
        opt = None
        for v in g.vertices:
            sig = vertex_signature(g, v)
            for side in ("in", "out"):
                h = hyps.get((sig, side))
                if h is None:
                    continue
                opt = oracle.opt(g) if opt is None else opt
                paid = sig[0] if side == "in" else sig[1]
                if opt == oracle.opt(g.remove_vertices([v])) + paid:
                    h["confirmed"] += 1
                else:
                    h["refuted"] += 1
                    if h["first_refutation"] is None:
                        h["first_refutation"] = {"graph": g.to_dict(), "vertex": v}
    return sorted(hyps.values(), key=lambda h: (h["refuted"] > 0, -h["confirmed"]))


# ---------------------------------------------------------------------- 3-terminal boundary functions

TERMINALS = (0, 1, 2)


def enumerate_sides(internal: int) -> Iterable[Graph]:
    """All sides with terminals 0,1,2 and ``internal`` extra vertices: every arc pair
    touching an internal vertex is chosen freely (none / -> / <- / both); arcs among
    terminals are excluded (they are pairwise by definition)."""
    verts = list(range(3 + internal))
    pairs = [(u, v) for u, v in itertools.combinations(verts, 2) if v >= 3]
    for choice in itertools.product(range(4), repeat=len(pairs)):
        mult = {}
        for (u, v), c in zip(pairs, choice):
            if c & 1:
                mult[(u, v)] = 1
            if c & 2:
                mult[(v, u)] = 1
        yield Graph(verts, mult)


def mine_boundary(max_internal: int = 2, oracle: Oracle | None = None) -> dict[str, Any]:
    """Which 3-terminal sides have a non-pairwise boundary function?"""
    oracle = oracle or Oracle()
    start = time.monotonic()
    rows = []
    for k in range(1, max_internal + 1):
        total = pairwise = 0
        residual_shapes: dict[tuple[int, int], dict[str, Any]] = {}
        smallest: dict[str, Any] | None = None
        for side in enumerate_sides(k):
            total += 1
            f = boundary_function(side, TERMINALS, oracle)
            coeffs, res = pairwise_decomposition(f, TERMINALS)
            if res == [0, 0]:
                pairwise += 1
                continue
            key = tuple(res)
            entry = residual_shapes.setdefault(key, {"count": 0, "example": None})
            entry["count"] += 1
            example = {"side": side.to_dict(), "m": side.m,
                       "f": {"".join(map(str, s)): v for s, v in f.items()}, "residual": res}
            if entry["example"] is None or side.m < entry["example"]["m"]:
                entry["example"] = example
            if smallest is None or side.m < smallest["m"]:
                smallest = example
        rows.append({
            "internal_vertices": k, "sides": total, "pairwise": pairwise,
            "non_pairwise": total - pairwise,
            "residual_shapes": {str(list(key)): v for key, v in sorted(residual_shapes.items())},
            "smallest_non_pairwise": smallest,
        })
    return {"analysis": "boundary", "terminals": list(TERMINALS), "rows": rows,
            "elapsed_seconds": round(time.monotonic() - start, 2)}

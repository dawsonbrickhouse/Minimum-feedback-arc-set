"""Plausible-looking rules that the harness is expected to refute.

They are kept in the registry on purpose: they document which natural
generalisations fail, and they keep the harness honest (a harness that cannot
find these counterexamples is broken).
"""

from __future__ import annotations

import random

from ..generators import random_digraph
from ..graph import Graph
from .base import Application, CandidateRule, Match, Oracle, Status
from .common import in_arc_pairs, max_arc_disjoint_cycles_through, out_arc_pairs


class ArcDisjointCycleBound(CandidateRule):
    name = "arc_disjoint_cycle_bound"
    title = "Delete v when its in-weight is at most the number of arc-disjoint cycles through v"
    statuses = (Status.COUNTEREXAMPLE_FOUND,)
    expected = "false"
    pattern = "vertex v with nu(v) = max number of arc-disjoint cycles through v"
    preconditions = "no self-loop at v and w_in(v) <= nu(v) (side 'in') or w_out(v) <= nu(v) (side 'out')"
    transformation = "G' = G - v"
    claimed_identity = "OPT(G) = OPT(G - v) + w_in(v)   (resp. w_out(v))"
    proof_sketch = (
        "Attempted generalisation of two_cycle_local_bound. The step that breaks: arcs of an "
        "optimal F that cut cycles through v need not be incident to v, and such arcs can also "
        "cut cycles avoiding v, so F minus the arcs at v is not cheap enough."
    )

    def find_matches(self, g: Graph) -> list[Match]:
        matches: list[Match] = []
        for v in g.vertices:
            if g.has_arc(v, v):
                continue
            nu = max_arc_disjoint_cycles_through(g, v)
            if nu == 0:
                continue
            if g.in_weight(v) <= nu:
                matches.append({"vertex": v, "side": "in"})
            if g.out_weight(v) <= nu:
                matches.append({"vertex": v, "side": "out"})
        return matches

    def check_preconditions(self, g: Graph, match: Match) -> str | None:
        v, side = match.get("vertex"), match.get("side")
        if not g.has_vertex(v) or side not in ("in", "out"):
            return f"malformed match {match}"
        if g.has_arc(v, v):
            return f"self-loop at {v}"
        weight = g.in_weight(v) if side == "in" else g.out_weight(v)
        nu = max_arc_disjoint_cycles_through(g, v)
        return None if weight <= nu else f"w_{side}({v}) = {weight} > nu({v}) = {nu}"

    def apply(self, g: Graph, match: Match, oracle: Oracle) -> Application:
        v = match["vertex"]
        paid = in_arc_pairs(g, v) if match["side"] == "in" else out_arc_pairs(g, v)
        return Application(g.remove_vertices([v]), g.arc_weight(paid), lambda r: r | paid)

    def explain_preconditions(self, g: Graph, match: Match) -> str:
        v, side = match["vertex"], match["side"]
        weight = g.in_weight(v) if side == "in" else g.out_weight(v)
        return f"w_{side}({v}) = {weight} <= nu({v}) = {max_arc_disjoint_cycles_through(g, v)}"

    def generate(self, rng: random.Random, n: int) -> Graph | None:
        g = random_digraph(n, rng.uniform(0.15, 0.4), rng)
        cyc = rng.sample(range(n), 3)
        return g.with_arcs({(a, b): 1 for a, b in zip(cyc, cyc[1:] + cyc[:1]) if not g.has_arc(a, b)})


class InDegreeOneContraction(CandidateRule):
    name = "in_degree_one_contraction"
    title = "Contract the unique in-arc of a vertex (naive FAS analogue of DFVS IN1)"
    statuses = (Status.COUNTEREXAMPLE_FOUND, Status.PRIOR_ART_FOUND)
    expected = "false"
    pattern = "vertex v whose only in-arc is (u, v), multiplicity 1, u != v"
    preconditions = "no self-loop at v; in-arc pair set of v is exactly {(u, v)} with w = 1"
    transformation = "merge v into u: every arc (v, x) becomes (u, x) (a loop if x = u)"
    claimed_identity = "OPT(G) = OPT(G / uv)"
    proof_sketch = (
        "Fails: in G one may pay 1 for (u,v) to cut all cycles through v, while in G/uv those "
        "cycles only can be cut at the former out-arcs of v. The literature review (§3.4) "
        "already reports a 4-arc counterexample."
    )

    def find_matches(self, g: Graph) -> list[Match]:
        out: list[Match] = []
        for v in g.vertices:
            ins = g.in_arcs(v)
            if len(ins) == 1 and not g.has_arc(v, v):
                (u, k), = ins.items()
                if k == 1 and u != v:
                    out.append({"u": u, "v": v})
        return out

    def check_preconditions(self, g: Graph, match: Match) -> str | None:
        u, v = match.get("u"), match.get("v")
        if not (g.has_vertex(u) and g.has_vertex(v)) or u == v:
            return f"malformed match {match}"
        if dict(g.in_arcs(v)) != {u: 1}:
            return f"in-arcs of {v} are {dict(g.in_arcs(v))}, expected only ({u},{v}) x1"
        return None

    def apply(self, g: Graph, match: Match, oracle: Oracle) -> Application:
        u, v = match["u"], match["v"]
        mult = {a: k for a, k in g.arcs() if v not in a}
        for x, k in g.out_arcs(v).items():
            mult[(u, x)] = mult.get((u, x), 0) + k
        return Application(Graph([x for x in g.vertices if x != v], mult), 0)

    def generate(self, rng: random.Random, n: int) -> Graph | None:
        g = random_digraph(n, rng.uniform(0.2, 0.5), rng)
        v = rng.randrange(n)
        g = g.remove_arc_pairs(in_arc_pairs(g, v))
        u = rng.choice([x for x in range(n) if x != v])
        return g.with_arcs({(u, v): 1})


class GreedyMaxDeltaFirst(CandidateRule):
    name = "greedy_max_delta_first"
    title = "A vertex maximising w_out - w_in can be placed first (Eades-Lin-Smyth greedy step)"
    statuses = (Status.COUNTEREXAMPLE_FOUND,)
    expected = "false"
    pattern = "the smallest-id vertex v maximising delta(v) = w_out(v) - w_in(v) (loops ignored)"
    preconditions = "G has at least one arc"
    transformation = "G' = G - v"
    claimed_identity = "OPT(G) = OPT(G - v) + w_in(v)"
    proof_sketch = (
        "Not expected to hold: Eades, Lin and Smyth (1993) use this choice inside a heuristic "
        "with an approximation bound, not an exactness guarantee."
    )

    @staticmethod
    def _delta(g: Graph, v: int) -> int:
        loop = g.multiplicity(v, v)
        return (g.out_weight(v) - loop) - (g.in_weight(v) - loop)

    def find_matches(self, g: Graph) -> list[Match]:
        if g.num_arc_pairs == 0 or g.self_loops():
            return []
        best = max(g.vertices, key=lambda v: (self._delta(g, v), -v))
        return [{"vertex": best}]

    def check_preconditions(self, g: Graph, match: Match) -> str | None:
        v = match.get("vertex")
        if not g.has_vertex(v):
            return f"malformed match {match}"
        best = max(g.vertices, key=lambda x: (self._delta(g, x), -x))
        return None if best == v else f"{v} is not the greedy choice ({best} is)"

    def apply(self, g: Graph, match: Match, oracle: Oracle) -> Application:
        v = match["vertex"]
        paid = in_arc_pairs(g, v)
        return Application(g.remove_vertices([v]), g.arc_weight(paid), lambda r: r | paid)

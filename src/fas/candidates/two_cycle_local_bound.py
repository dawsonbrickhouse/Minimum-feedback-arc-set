"""Worked example used in docs/adding_a_candidate.md.

Plain English: if every arc entering ``v`` can be "paid for" by the 2-cycles at
``v`` (which any solution must break anyway), delete ``v`` and pay for all of its
in-arcs.
"""

from __future__ import annotations

import random

from ..generators import random_digraph
from ..graph import Graph
from .base import Application, CandidateRule, Match, Oracle, Status
from .common import in_arc_pairs, out_arc_pairs, two_cycle_bound


class TwoCycleLocalBound(CandidateRule):
    name = "two_cycle_local_bound"
    title = "Delete a vertex whose in- (or out-) weight is covered by its 2-cycles"
    statuses = (Status.PROVED_WITHIN_STATED_ASSUMPTIONS, Status.NOVELTY_UNVERIFIED)
    expected = "true"
    pattern = "vertex v with L(v) = sum over 2-cycles u<->v of min(w(u,v), w(v,u))"
    preconditions = "no self-loop at v, and w_in(v) <= L(v) (side 'in') or w_out(v) <= L(v) (side 'out')"
    transformation = "G' = G - v"
    claimed_identity = "OPT(G) = OPT(G - v) + w_in(v)   (resp. + w_out(v))"
    proof_sketch = (
        "<=: any FAS of G-v plus all in-arcs of v is a FAS of G (v becomes a source). "
        ">=: an optimal F must break each 2-cycle at v; these are arc-disjoint, so "
        "w(F ∩ arcs at v) >= L(v) >= w_in(v); F minus the arcs at v is a FAS of G-v. "
        "Also a corollary of 2-cycle cancellation (R4) followed by source deletion."
    )
    open_questions = "Implied by two_cycle_cancellation + source/sink deletion; kept as a teaching example."

    def find_matches(self, g: Graph) -> list[Match]:
        matches: list[Match] = []
        for v in g.vertices:
            if g.has_arc(v, v):
                continue
            bound = two_cycle_bound(g, v)
            if bound == 0:
                continue  # plain source/sink: already a baseline rule
            if g.in_weight(v) <= bound:
                matches.append({"vertex": v, "side": "in"})
            if g.out_weight(v) <= bound:
                matches.append({"vertex": v, "side": "out"})
        return matches

    def check_preconditions(self, g: Graph, match: Match) -> str | None:
        v, side = match.get("vertex"), match.get("side")
        if not g.has_vertex(v) or side not in ("in", "out"):
            return f"malformed match {match}"
        if g.has_arc(v, v):
            return f"vertex {v} has a self-loop"
        weight = g.in_weight(v) if side == "in" else g.out_weight(v)
        bound = two_cycle_bound(g, v)
        if weight > bound:
            return f"w_{side}({v}) = {weight} > L({v}) = {bound}"
        return None

    def apply(self, g: Graph, match: Match, oracle: Oracle) -> Application:
        v, side = match["vertex"], match["side"]
        paid = in_arc_pairs(g, v) if side == "in" else out_arc_pairs(g, v)
        correction = g.arc_weight(paid)

        def lift(removed: frozenset) -> frozenset:
            return removed | paid

        return Application(g.remove_vertices([v]), correction, lift)

    def explain_preconditions(self, g: Graph, match: Match) -> str:
        v, side = match["vertex"], match["side"]
        weight = g.in_weight(v) if side == "in" else g.out_weight(v)
        return f"w_{side}({v}) = {weight} <= L({v}) = {two_cycle_bound(g, v)}; no self-loop at {v}"

    def generate(self, rng: random.Random, n: int) -> Graph | None:
        base = random_digraph(n - 1, rng.uniform(0.1, 0.5), rng)
        v = n - 1
        partners = rng.sample(range(n - 1), k=rng.randint(1, max(1, min(3, n - 1))))
        arcs = {(u, v): 1 for u in partners} | {(v, u): 1 for u in partners}
        for w in range(n - 1):
            if w not in partners and rng.random() < 0.3:
                arcs[(v, w)] = 1
        return base.with_arcs(arcs)

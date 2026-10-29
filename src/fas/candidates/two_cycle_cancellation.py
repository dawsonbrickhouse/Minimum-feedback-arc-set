"""2-cycle cancellation (literature review R4, tagged [OWN] there, i.e. not a cited result)."""

from __future__ import annotations

import random

from ..generators import random_multigraph
from ..graph import Graph
from .base import Application, CandidateRule, Match, Oracle, Status


class TwoCycleCancellation(CandidateRule):
    name = "two_cycle_cancellation"
    title = "Cancel the common weight of a 2-cycle"
    statuses = (Status.PROVED_WITHIN_STATED_ASSUMPTIONS, Status.PRIOR_ART_FOUND)
    expected = "true"
    pattern = "2-cycle u <-> v with a = w(u,v), b = w(v,u), u != v"
    preconditions = "both arcs present"
    transformation = "subtract min(a, b) from both multiplicities, deleting arcs that reach 0"
    claimed_identity = "OPT(G) = OPT(G') + min(a, b)"
    proof_sketch = (
        "In every linear order exactly one of (u,v), (v,u) is backward, so for every order "
        "cost_G(order) = cost_G'(order) + min(a, b); minimising over orders gives the identity. "
        "An optimal order of G' is optimal for G, so the backward arcs of that order lift the solution."
    )
    open_questions = (
        "Prior art: Brandenburg & Hanauer, Univ. Passau tech. report MIP-1104 (2011), Sec. 2.1, erase both "
        "arcs of a 2-cycle and add the one conforming to the order (unweighted case, read directly)."
    )

    def find_matches(self, g: Graph) -> list[Match]:
        return [{"u": u, "v": v} for (u, v), _ in g.arcs() if u < v and g.has_arc(v, u)]

    def check_preconditions(self, g: Graph, match: Match) -> str | None:
        u, v = match.get("u"), match.get("v")
        if u == v or not (g.has_vertex(u) and g.has_vertex(v)):
            return f"malformed match {match}"
        if not (g.has_arc(u, v) and g.has_arc(v, u)):
            return f"{u}<->{v} is not a 2-cycle"
        return None

    def apply(self, g: Graph, match: Match, oracle: Oracle) -> Application:
        u, v = match["u"], match["v"]
        a, b = g.multiplicity(u, v), g.multiplicity(v, u)
        c = min(a, b)
        reduced = g.with_multiplicity(u, v, a - c).with_multiplicity(v, u, b - c)

        def lift(removed: frozenset) -> frozenset:
            # The surviving arc of the pair (if any) tells which side is backward;
            # otherwise orient by an order of G' - removed.
            from ..reductions import ordering_from_removed

            order = ordering_from_removed(reduced, removed)
            pos = {x: i for i, x in enumerate(order)}
            back = (u, v) if pos[u] > pos[v] else (v, u)
            return frozenset(removed) | {back}

        return Application(reduced, c, lift)

    def generate(self, rng: random.Random, n: int) -> Graph | None:
        g = random_multigraph(n, rng.uniform(0.15, 0.5), 3, rng)
        u, v = rng.sample(range(n), 2)
        return g.with_arcs({(u, v): rng.randint(1, 3), (v, u): rng.randint(1, 3)})

"""Structural candidates: modules, two-terminal separators and dominance-type exchanges."""

from __future__ import annotations

import itertools
import random

from ..generators import random_digraph
from ..boundary import boundary_function, three_terminal_gadget
from ..graph import Arc, Graph, reachable, topological_order, weakly_connected_components
from .base import Application, CandidateRule, Match, Oracle, Status
from .common import heavy_weight, make_undeletable

MODULE_SUBSET_LIMIT = 8  # enumerate all vertex subsets as module candidates only for n <= this


# ---------------------------------------------------------------------- modules


def _module_violation(g: Graph, members: frozenset[int]) -> str | None:
    first = min(members)
    for x in g.vertices:
        if x in members:
            continue
        w_in, w_out = g.multiplicity(x, first), g.multiplicity(first, x)
        for m in members:
            if g.multiplicity(x, m) != w_in or g.multiplicity(m, x) != w_out:
                return f"vertex {x} distinguishes {first} and {m}"
    return None


class ModuleContraction(CandidateRule):
    name = "module_contraction"
    title = "Solve a module separately and contract it to one weighted vertex"
    statuses = (Status.PROVED_WITHIN_STATED_ASSUMPTIONS, Status.NOVELTY_UNVERIFIED)
    expected = "true"
    pattern = "module M (2 <= |M| < n): every outside x has equal multiplicity to / from all of M"
    preconditions = "M is a module (multiplicities, not just adjacency, agree)"
    transformation = (
        "G' = G[M] disjoint-union G/M, where G/M replaces M by a new vertex q with "
        "w(x,q) = |M| w(x,m) and w(q,x) = |M| w(m,x)"
    )
    claimed_identity = "OPT(G) = OPT(G[M]) + OPT(G/M) = OPT(G')"
    proof_sketch = (
        "Each m in M pays the same position-dependent external cost c(slot). Moving all of M to "
        "the slot of the cheapest member, keeping M's internal order, does not increase the cost, "
        "so some optimal order has M contiguous; for such orders the cost splits exactly into the "
        "G[M] part and the G/M part. Literature review R13 ([OWN]) states the same identity."
    )

    def find_matches(self, g: Graph) -> list[Match]:
        vs = g.vertices
        if len(vs) <= MODULE_SUBSET_LIMIT:
            subsets = (frozenset(c) for k in range(2, len(vs)) for c in itertools.combinations(vs, k))
        else:
            subsets = (frozenset(c) for c in itertools.combinations(vs, 2))
        return [{"module": sorted(m)} for m in subsets if _module_violation(g, m) is None]

    def check_preconditions(self, g: Graph, match: Match) -> str | None:
        members = frozenset(match.get("module", ()))
        if len(members) < 2 or len(members) >= g.n or not all(g.has_vertex(m) for m in members):
            return f"malformed module {match}"
        return _module_violation(g, members)

    def apply(self, g: Graph, match: Match, oracle: Oracle) -> Application:
        members = frozenset(match["module"])
        rep = min(members)
        q = max(g.vertices) + 1
        size = len(members)
        mult = {(a, b): k for (a, b), k in g.arcs() if (a in members) == (b in members)}
        for x in g.vertices:
            if x in members:
                continue
            if g.multiplicity(x, rep):
                mult[(x, q)] = size * g.multiplicity(x, rep)
            if g.multiplicity(rep, x):
                mult[(q, x)] = size * g.multiplicity(rep, x)
        reduced = Graph([*g.vertices, q], mult)

        def lift(removed: frozenset[Arc]) -> frozenset[Arc]:
            out: set[Arc] = set()
            for a, b in removed:
                if a == q:
                    out.update((m, b) for m in members)
                elif b == q:
                    out.update((a, m) for m in members)
                else:
                    out.add((a, b))
            return frozenset(out)

        return Application(reduced, 0, lift)

    def generate(self, rng: random.Random, n: int) -> Graph | None:
        k = rng.randint(2, max(2, n // 3))
        outside = n - k
        g = random_digraph(outside, rng.uniform(0.2, 0.5), rng)
        members = list(range(outside, n))
        inner = random_digraph(k, rng.uniform(0.2, 0.7), rng).relabeled({i: outside + i for i in range(k)})
        mult = dict(g.arcs()) | dict(inner.arcs())
        for x in range(outside):
            to_m, from_m = rng.random() < 0.4, rng.random() < 0.4
            for m in members:
                if to_m:
                    mult[(x, m)] = 1
                if from_m:
                    mult[(m, x)] = 1
        return Graph(range(n), mult)


# ---------------------------------------------------------------------- two-terminal separators


class TwoTerminalSeparator(CandidateRule):
    name = "two_terminal_separator"
    title = "Replace the far side of a 2-vertex separator by parallel arcs between the terminals"
    statuses = (Status.PROVED_WITHIN_STATED_ASSUMPTIONS, Status.NOVELTY_UNVERIFIED)
    expected = "true"
    pattern = (
        "terminals x != y and a weakly connected component C of G - {x, y}; "
        "G2 = G[C + {x,y}] without arcs between x and y and without loops at x, y; G1 = G - C"
    )
    preconditions = "C is a union of weak components of G - {x, y} (no arcs between C and the rest)"
    transformation = (
        "f_xy = OPT(G2 + H*(x,y)), f_yx = OPT(G2 + H*(y,x)) with H heavy; "
        "G' = G1 + |f_xy - f_yx| copies of (x,y) if f_xy <= f_yx, else of (y,x)"
    )
    claimed_identity = "OPT(G) = OPT(G') + min(f_xy, f_yx)"
    proof_sketch = (
        "A simple cycle meeting both C and V(G1)-{x,y} passes x and y once each, so it is an x~>y "
        "path in one side plus a y~>x path in the other. Hence G-F is acyclic iff both sides are "
        "acyclic and not both directions are realised across sides, so "
        "OPT(G) = min(f1_xy + f2_xy, f1_yx + f2_yx) where f_xy = min cost leaving the side acyclic "
        "with no y~>x path (= OPT(side + heavy (x,y))). Applying the same formula to G' (the gadget "
        "has f_xy = 0, f_yx = d) gives the identity. Full proof: docs/proof_obligations.md."
    )
    open_questions = (
        "3-terminal analogue: is the boundary cost function of a 3-terminal side always "
        "representable by arcs among the terminals plus a constant? (see mining 'boundary')"
    )

    def find_matches(self, g: Graph) -> list[Match]:
        matches: list[Match] = []
        for x, y in itertools.combinations(g.vertices, 2):
            rest = g.remove_vertices([x, y])
            for comp in weakly_connected_components(rest):
                side = g.induced_subgraph([*comp, x, y])
                if any(a in comp or b in comp for (a, b), _ in side.arcs()):
                    matches.append({"x": x, "y": y, "component": list(comp)})
        return matches

    def check_preconditions(self, g: Graph, match: Match) -> str | None:
        x, y, comp = match.get("x"), match.get("y"), frozenset(match.get("component", ()))
        if x == y or not comp or x in comp or y in comp or not all(g.has_vertex(v) for v in (x, y, *comp)):
            return f"malformed match {match}"
        for (a, b), _ in g.arcs():
            if (a in comp) != (b in comp) and not ({a, b} - comp) <= {x, y}:
                return f"arc ({a},{b}) joins C to a vertex outside C + {{x, y}}"
        return None

    @staticmethod
    def _sides(g: Graph, x: int, y: int, comp: frozenset[int]) -> tuple[Graph, Graph]:
        g2_vertices = [*comp, x, y]
        g2_arcs = {(a, b): k for (a, b), k in g.arcs() if (a in comp or b in comp)}
        return g.remove_vertices(comp), Graph(g2_vertices, g2_arcs)

    def apply(self, g: Graph, match: Match, oracle: Oracle) -> Application:
        x, y, comp = match["x"], match["y"], frozenset(match["component"])
        g1, g2 = self._sides(g, x, y, comp)
        big = heavy_weight(g2)
        sol_xy = oracle.solve(g2.with_arcs({(x, y): big}))
        sol_yx = oracle.solve(g2.with_arcs({(y, x): big}))
        f_xy, f_yx = sol_xy.cost, sol_yx.cost
        gadget = (x, y) if f_xy <= f_yx else (y, x)
        d = abs(f_xy - f_yx)
        reduced = g1.with_arcs({gadget: d}) if d else g1
        g1_pairs = frozenset(g1.arc_pairs())

        def lift(removed: frozenset[Arc]) -> frozenset[Arc]:
            r1 = frozenset(a for a in removed if a in g1_pairs)
            rest = g1.remove_arc_pairs(r1)
            allows_xy = x not in reachable(rest, y)  # side-1 has no y~>x path
            allows_yx = y not in reachable(rest, x)
            options = []
            if allows_xy:
                options.append((f_xy, sol_xy.removed_arcs))
            if allows_yx:
                options.append((f_yx, sol_yx.removed_arcs))
            if not options:
                raise ValueError("side 1 is cyclic after removal; reduced solution is not a FAS")
            _, side2 = min(options, key=lambda t: t[0])
            return r1 | side2

        return Application(reduced, min(f_xy, f_yx), lift, note=f"f_xy={f_xy}, f_yx={f_yx}")

    def explain_preconditions(self, g: Graph, match: Match) -> str:
        return (f"terminals x={match['x']}, y={match['y']}; component C={match['component']} of G - {{x,y}} "
                "has no arcs to vertices outside C + {x, y} (checked arc by arc)")

    def generate(self, rng: random.Random, n: int) -> Graph | None:
        k1 = rng.randint(1, max(1, n - 4))
        k2 = max(1, n - 2 - k1)
        x, y = 0, 1
        a = list(range(2, 2 + k1))
        b = list(range(2 + k1, 2 + k1 + k2))
        mult: dict[Arc, int] = {}
        for part in (a, b):
            vs = [x, y, *part]
            for u, v in itertools.permutations(vs, 2):
                if {u, v} == {x, y}:
                    continue
                if rng.random() < 0.35:
                    mult[(u, v)] = 1
        if rng.random() < 0.5:
            mult[(x, y) if rng.random() < 0.5 else (y, x)] = 1
        return Graph(range(2 + k1 + k2), mult)


class ThreeTerminalGadget(CandidateRule):
    name = "three_terminal_gadget"
    title = "Replace the far side of a 3-vertex separator by a gadget with <= 2 internal vertices"
    statuses = (Status.PROVED_WITHIN_STATED_ASSUMPTIONS, Status.NOVELTY_UNVERIFIED)
    expected = "true"
    pattern = "terminals T = {x, y, z} and a weak component C of G - T; G2 = arcs touching C, G1 = G - C"
    preconditions = "no arc joins C to a vertex outside C + T"
    transformation = (
        "compute f_G2 on the 6 orders of T; G' = G1 + weighted gadget H (stars on <= 2 new vertices "
        "plus arcs among T) with f_H = f_G2 - c"
    )
    claimed_identity = "OPT(G) = OPT(G') + c"
    proof_sketch = (
        "OPT(G) = min_sigma f_G1(sigma) + f_G2(sigma) (boundary functions add under gluing). Functions "
        "on the 6 orders split into a pairwise part (constant + 3 pair indicators, realisable by arcs "
        "among T) and a 2-dimensional residual; the three one-vertex stars have residuals [1,0], [0,1], "
        "[-1,-1], which generate all integer residuals with non-negative coefficients using at most two "
        "of them. Full proof: docs/proof_obligations.md (PO-5)."
    )
    open_questions = (
        "Gadgets are weighted. Smallest unweighted gadgets? Does a bounded-size gadget family exist "
        "for 4 terminals (24 orders, residual dimension 17)?"
    )

    def find_matches(self, g: Graph) -> list[Match]:
        matches: list[Match] = []
        for terms in itertools.combinations(g.vertices, 3):
            rest = g.remove_vertices(terms)
            for comp in weakly_connected_components(rest):
                comp_set = set(comp)
                if any(a in comp_set or b in comp_set for (a, b), _ in g.induced_subgraph([*comp, *terms]).arcs()):
                    matches.append({"terminals": list(terms), "component": list(comp)})
        return matches

    def check_preconditions(self, g: Graph, match: Match) -> str | None:
        terms = tuple(match.get("terminals", ()))
        comp = frozenset(match.get("component", ()))
        if len(set(terms)) != 3 or not comp or comp & set(terms) or not all(g.has_vertex(v) for v in (*terms, *comp)):
            return f"malformed match {match}"
        for (a, b), _ in g.arcs():
            if (a in comp) != (b in comp) and not ({a, b} - comp) <= set(terms):
                return f"arc ({a},{b}) joins C to a vertex outside C + T"
        return None

    def apply(self, g: Graph, match: Match, oracle: Oracle) -> Application:
        terms: tuple[int, int, int] = tuple(match["terminals"])  # type: ignore[assignment]
        comp = frozenset(match["component"])
        g1 = g.remove_vertices(comp)
        g2 = Graph([*comp, *terms], {(a, b): k for (a, b), k in g.arcs() if a in comp or b in comp})
        f2 = boundary_function(g2, terms, oracle)
        gadget, const = three_terminal_gadget(f2, terms, max(g.vertices) + 1, oracle)
        reduced = g1.with_arcs(dict(gadget.arcs())) if gadget.num_arc_pairs else g1
        reduced = Graph(sorted(set(reduced.vertices) | set(gadget.vertices)), dict(reduced.arcs()))
        g1_pairs = frozenset(g1.arc_pairs())
        big = g2.m + 1

        def lift(removed: frozenset[Arc]) -> frozenset[Arc]:
            order = topological_order(reduced.remove_arc_pairs(removed))
            if order is None:
                raise ValueError("reduced solution is not a FAS")
            sigma = tuple(v for v in order if v in terms)
            forced = g2.with_arcs({(sigma[i], sigma[i + 1]): big for i in range(2)})
            side2 = oracle.solve(forced).removed_arcs
            return frozenset(a for a in removed if a in g1_pairs) | side2

        return Application(reduced, const, lift, note=f"boundary function {f2}")

    def explain_preconditions(self, g: Graph, match: Match) -> str:
        return (f"terminals {match['terminals']}; component C={match['component']} of G - T has no arcs "
                "to vertices outside C + T (checked arc by arc)")

    def generate(self, rng: random.Random, n: int) -> Graph | None:
        terms = [0, 1, 2]
        k1 = rng.randint(1, max(1, (n - 3) // 2))
        side_a = list(range(3, 3 + k1))
        side_b = list(range(3 + k1, max(n, 5 + k1)))
        mult: dict[Arc, int] = {}
        for part in (side_a, side_b):
            for u, v in itertools.permutations([*terms, *part], 2):
                if (u in part or v in part) and rng.random() < 0.35:
                    mult[(u, v)] = 1
        for u, v in itertools.permutations(terms, 2):
            if rng.random() < 0.2:
                mult[(u, v)] = 1
        return Graph(range(max(n, 5 + k1)), mult)


# ---------------------------------------------------------------------- exchange / dominance rules


class NeighborhoodDominance(CandidateRule):
    name = "neighborhood_dominance"
    title = "If v dominates u (in-weights to v <= to u, out-weights of u <= of v), some optimum puts v before u"
    statuses = (Status.PROVED_WITHIN_STATED_ASSUMPTIONS, Status.NOVELTY_UNVERIFIED)
    expected = "true"
    pattern = "ordered pair (u, v), u != v"
    preconditions = (
        "no arc (u, v); no loops at u, v; for all x not in {u, v}: w(x,v) <= w(x,u) and w(u,x) <= w(v,x)"
    )
    transformation = "G' = G + H copies of (v, u) with H = m(G) + 1 (forces v before u)"
    claimed_identity = "OPT(G) = OPT(G')"
    proof_sketch = (
        "Swap u and v when u precedes v. Only vertices strictly between them change status: the "
        "change is I_v - O_v - I_u + O_u with I/O the in/out-weight from the vertices between; "
        "the dominance inequalities make it <= 0, and the arc (v,u) (if any) becomes forward."
    )
    open_questions = "Related to arc domination (review R16) and DFVS DOME; not a size reduction on its own."

    @staticmethod
    def _violation(g: Graph, u: int, v: int) -> str | None:
        if u == v:
            return "u = v"
        if g.has_arc(u, v):
            return f"arc ({u},{v}) present"
        if g.has_arc(u, u) or g.has_arc(v, v):
            return "self-loop at u or v"
        for x in g.vertices:
            if x in (u, v):
                continue
            if g.multiplicity(x, v) > g.multiplicity(x, u):
                return f"w({x},{v}) > w({x},{u})"
            if g.multiplicity(u, x) > g.multiplicity(v, x):
                return f"w({u},{x}) > w({v},{x})"
        return None

    def find_matches(self, g: Graph) -> list[Match]:
        return [{"u": u, "v": v} for u, v in itertools.permutations(g.vertices, 2)
                if self._violation(g, u, v) is None]

    def check_preconditions(self, g: Graph, match: Match) -> str | None:
        u, v = match.get("u"), match.get("v")
        if not (g.has_vertex(u) and g.has_vertex(v)):
            return f"malformed match {match}"
        return self._violation(g, u, v)

    def apply(self, g: Graph, match: Match, oracle: Oracle) -> Application:
        return Application(make_undeletable(g, [(match["v"], match["u"])]), 0, lambda r: r)


class InDegreeOneExchange(CandidateRule):
    name = "in_degree_one_exchange"
    title = "A vertex with one cheap in-arc: some optimum removes none of its out-arcs"
    statuses = (Status.PROVED_WITHIN_STATED_ASSUMPTIONS, Status.NOVELTY_UNVERIFIED)
    expected = "true"
    pattern = "vertex v whose only in-arc pair is (t, v) (side 'in'), or only out-arc pair is (v, t) (side 'out')"
    preconditions = "t != v, no loop at v, and w of that unique arc <= w of every arc on the other side"
    transformation = "make every out-arc (resp. in-arc) of v undeletable (add H = m(G)+1 copies)"
    claimed_identity = "OPT(G) = OPT(G')"
    proof_sketch = (
        "Replace the out-arcs of v in an optimal F by (t, v): every cycle through an out-arc of v "
        "enters v through (t, v), so the result is a FAS, and it is no heavier. Literature review "
        "R9 ([OWN])."
    )

    def find_matches(self, g: Graph) -> list[Match]:
        out: list[Match] = []
        for v in g.vertices:
            for side in ("in", "out"):
                if self._violation(g, v, side) is None:
                    out.append({"vertex": v, "side": side})
        return out

    @staticmethod
    def _violation(g: Graph, v: int, side: str) -> str | None:
        if g.has_arc(v, v):
            return f"self-loop at {v}"
        one, other = (g.in_arcs(v), g.out_arcs(v)) if side == "in" else (g.out_arcs(v), g.in_arcs(v))
        if len(one) != 1 or not other:
            return f"{v} does not have exactly one {side}-arc pair and a nonempty other side"
        (t, k), = one.items()
        if t == v:
            return "unique arc is a loop"
        if any(k > w for w in other.values()):
            return f"unique {side}-arc weight {k} exceeds an arc on the other side"
        return None

    def check_preconditions(self, g: Graph, match: Match) -> str | None:
        v, side = match.get("vertex"), match.get("side")
        if not g.has_vertex(v) or side not in ("in", "out"):
            return f"malformed match {match}"
        return self._violation(g, v, side)

    def apply(self, g: Graph, match: Match, oracle: Oracle) -> Application:
        v = match["vertex"]
        arcs = [(v, w) for w in g.out_neighbors(v)] if match["side"] == "in" else [(u, v) for u in g.in_neighbors(v)]
        return Application(make_undeletable(g, arcs), 0, lambda r: r)


class ArcDomination(CandidateRule):
    name = "arc_domination"
    title = "If every cycle through e uses a no-heavier arc f, some optimum keeps e"
    statuses = (Status.PROVED_WITHIN_STATED_ASSUMPTIONS, Status.NOVELTY_UNVERIFIED)
    expected = "true"
    pattern = "arc pairs e = (a, b) and f != e"
    preconditions = "a != b, w(f) <= w(e), e lies on a cycle, and G - f has no path b ~> a"
    transformation = "make e undeletable (add H = m(G)+1 copies)"
    claimed_identity = "OPT(G) = OPT(G')"
    proof_sketch = (
        "If an optimal F contains e, F - e + f is no heavier and still a FAS: every cycle through e "
        "is e plus a b~>a path, which must use f. Literature review R16 ([OWN])."
    )

    @staticmethod
    def _violation(g: Graph, e: Arc, f: Arc) -> str | None:
        a, b = e
        if a == b or e == f or not g.has_arc(*e) or not g.has_arc(*f):
            return "e must be a non-loop arc, f a different arc"
        if g.multiplicity(*f) > g.multiplicity(*e):
            return f"w(f)={g.multiplicity(*f)} > w(e)={g.multiplicity(*e)}"
        if a not in reachable(g, b):
            return "e lies on no cycle"
        if a in reachable(g.remove_arc_pairs([f]), b):
            return f"G - f still has a path {b} ~> {a}"
        return None

    def find_matches(self, g: Graph) -> list[Match]:
        pairs = g.arc_pairs()
        return [{"e": list(e), "f": list(f)} for e in pairs for f in pairs if self._violation(g, e, f) is None]

    def check_preconditions(self, g: Graph, match: Match) -> str | None:
        try:
            e, f = tuple(match["e"]), tuple(match["f"])
        except (KeyError, TypeError):
            return f"malformed match {match}"
        return self._violation(g, e, f)  # type: ignore[arg-type]

    def apply(self, g: Graph, match: Match, oracle: Oracle) -> Application:
        return Application(make_undeletable(g, [tuple(match["e"])]), 0, lambda r: r)


__all__ = [
    "ArcDomination",
    "ThreeTerminalGadget",
    "InDegreeOneExchange",
    "ModuleContraction",
    "NeighborhoodDominance",
    "TwoTerminalSeparator",
]

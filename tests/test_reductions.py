"""Every baseline rule must satisfy OPT(G) = offset + OPT(kernel) and lift an optimal
kernel solution to an optimal solution of G -- checked individually and combined."""

import random

import pytest

from fas.exact_solver import solve_dp, solve_exact
from fas.generators import all_labeled_graphs, isomorphism_classes, random_family, random_multigraph
from fas.graph import Graph
from fas.reductions import (
    BASELINE_RULES,
    BYPASS,
    SELF_LOOP,
    reduce_graph,
    solve_with_reductions,
)
from fas.verify import verify_removed_set, verify_result

RULE_SETS = [(r,) for r in BASELINE_RULES] + [BASELINE_RULES]


def _check(g: Graph, rules) -> None:
    opt = solve_dp(g).cost
    red = reduce_graph(g, rules)
    kernel_opt = solve_exact(red.kernel)
    assert red.offset + kernel_opt.cost == opt, (rules, g, red.kernel)
    lifted = red.lift(kernel_opt.removed_arcs)
    assert verify_removed_set(g, lifted, expected_cost=opt).ok, (rules, g)
    assert red.kernel.n <= g.n


@pytest.mark.parametrize("rules", RULE_SETS, ids=lambda r: "+".join(r))
def test_rules_exhaustive_labeled_n4(rules):
    for g in all_labeled_graphs(4):
        _check(g, rules)


@pytest.mark.parametrize("rules", RULE_SETS, ids=lambda r: "+".join(r))
def test_rules_exhaustive_classes_n5(rules):
    for g in isomorphism_classes(5, "digraph"):
        _check(g, rules)


@pytest.mark.parametrize("rules", RULE_SETS, ids=lambda r: "+".join(r))
def test_rules_random_multigraphs_with_loops(rules):
    rng = random.Random(2024)
    for _ in range(250):
        n = rng.randint(1, 9)
        g = random_multigraph(n, rng.uniform(0.05, 0.5), 3, rng)
        for _ in range(rng.randint(0, 2)):
            v = rng.randrange(n)
            g = g.with_arcs({(v, v): rng.randint(1, 2)})
        _check(g, rules)


@pytest.mark.parametrize("family", ["sparse", "planted", "scc_dag", "repeated_triangle", "overlapping_cycles"])
def test_solve_with_reductions_families(family):
    for g in random_family(family, 14, 5, seed=5):
        res, red = solve_with_reductions(g)
        expected = solve_exact(g).cost
        assert res.cost == expected
        assert verify_result(g, res, expected_cost=expected).ok
        assert red.offset + sum(solve_exact(c).cost for c in red.components()) == expected


def test_bypass_of_two_cycle_becomes_self_loop():
    # 0 <-> 1 with weights 2 and 3, plus a triangle through 0 to keep 0 alive.
    g = Graph.from_arcs([(0, 1, 2), (1, 0, 3), (0, 2), (2, 3), (3, 0)])
    red = reduce_graph(g, (BYPASS, SELF_LOOP))
    assert red.offset == 2 + 1  # 2-cycle contributes min(2, 3); the triangle collapses to a loop
    assert red.kernel.num_arc_pairs == 0


def test_bypass_merges_with_existing_arc():
    # path 0->1->2 parallel to arc 0->2, closed by 2->0 (x5)
    g = Graph.from_arcs([(0, 1), (1, 2), (0, 2), (2, 0, 5)])
    red = reduce_graph(g, (BYPASS,))
    # bypassing 1 gives 0->2 x2; then 2 (only in 0, only out 0) collapses to loop 0->0 x min(2,5)
    first = red.steps[0]
    assert (first.v, first.c) == (1, 1)
    assert red.kernel == Graph.from_arcs([(0, 0, 2)])
    _check(g, (BYPASS,))


def test_pure_dag_reduces_to_nothing():
    g = Graph.from_arcs([(0, 1), (1, 2), (0, 2), (2, 3)])
    red = reduce_graph(g)
    assert red.kernel.n == 0 and red.offset == 0


def test_unknown_rule_rejected():
    with pytest.raises(ValueError):
        reduce_graph(Graph.empty(1), ["nope"])


def test_summary_fields():
    g = Graph.from_arcs([(0, 1), (1, 2), (2, 0), (2, 3), (3, 3)])
    s = reduce_graph(g).summary()
    assert s["n_before"] == 4 and s["offset"] == 2 and s["n_after"] == 0

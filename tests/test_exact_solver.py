"""Correctness of the exact solvers: hand-checked cases, exhaustive comparison of
brute force against the subset DP, and randomized differential tests."""

import itertools
import random

import pytest

from fas.exact_solver import (
    SolverLimitError,
    backward_arcs,
    ordering_cost,
    solve_brute_force,
    solve_dp,
    solve_exact,
)
from fas.generators import all_labeled_graphs, isomorphism_classes, random_family, random_multigraph
from fas.graph import Graph, is_acyclic
from fas.verify import verify_result

HAND_CHECKED = [
    # (description, arcs, OPT) -- each value justified in the comment.
    ("empty graph", [], 0),
    ("single self-loop: the loop is in every FAS", [(0, 0)], 1),
    ("self-loop with multiplicity 3", [(0, 0, 3)], 3),
    ("2-cycle", [(0, 1), (1, 0)], 1),
    ("2-cycle with weights 2 and 5: drop the cheaper side", [(0, 1, 2), (1, 0, 5)], 2),
    ("directed triangle", [(0, 1), (1, 2), (2, 0)], 1),
    ("DAG", [(0, 1), (1, 2), (0, 2)], 0),
    # Two triangles sharing arc 2->0: removing it breaks both.
    ("two triangles sharing an arc", [(0, 1), (1, 2), (2, 0), (0, 3), (3, 2)], 1),
    # Two arc-disjoint triangles sharing only vertex 0: need 2.
    ("bowtie", [(0, 1), (1, 2), (2, 0), (0, 3), (3, 4), (4, 0)], 2),
    # Complete digraph on 3 vertices: three disjoint 2-cycles, so >= 3; any order gives 3.
    ("complete digraph K3", [(u, v) for u, v in itertools.permutations(range(3), 2)], 3),
    # Complete digraph K4: 6 disjoint 2-cycles, any order gives exactly 6.
    ("complete digraph K4", [(u, v) for u, v in itertools.permutations(range(4), 2)], 6),
    # Rotational tournament on 5 vertices (i -> i+1, i+2): it has 5 directed triangles;
    # an arc i->i+1 lies on 1 of them and an arc i->i+2 on 2, so 2 arcs cover at most 4
    # triangles and OPT >= 3; the identity order has 3 backward arcs.
    ("rotational tournament T5", [(i, (i + d) % 5) for i in range(5) for d in (1, 2)], 3),
    # Two disjoint SCCs plus a connecting arc: 1 + 1.
    ("two triangles joined by one arc", [(0, 1), (1, 2), (2, 0), (2, 3), (3, 4), (4, 5), (5, 3)], 2),
    ("isolated vertices only", [], 0),
]


@pytest.mark.parametrize("desc, arcs, opt", HAND_CHECKED, ids=[h[0] for h in HAND_CHECKED])
def test_hand_checked(desc, arcs, opt):
    g = Graph.from_arcs(arcs, vertices=range(3))
    for res in (solve_brute_force(g), solve_dp(g), solve_exact(g), solve_exact(g, method="brute")):
        assert res.cost == opt, desc
        assert verify_result(g, res, expected_cost=opt).ok


def test_backward_arcs_definition():
    g = Graph.from_arcs([(0, 1), (1, 0), (2, 2)])
    assert backward_arcs(g, (0, 1, 2)) == {(1, 0), (2, 2)}
    assert ordering_cost(g, (1, 0, 2)) == 2
    with pytest.raises(ValueError):
        backward_arcs(g, (0, 1))


def test_limits():
    g = Graph.empty(10)
    with pytest.raises(SolverLimitError):
        solve_brute_force(g)
    with pytest.raises(SolverLimitError):
        solve_dp(g, max_vertices=9)
    assert solve_exact(g, max_component_size=1).cost == 0  # all SCCs are singletons


def test_deterministic_tie_breaking():
    g = Graph.from_arcs([(0, 1), (1, 0)])
    assert solve_brute_force(g).ordering == (0, 1)
    assert solve_dp(g).ordering == solve_dp(g).ordering


@pytest.mark.parametrize("n", [0, 1, 2, 3, 4])
def test_exhaustive_labeled_brute_vs_dp(n):
    """Every labeled loopless digraph (antiparallel pairs allowed) on n <= 4 vertices."""
    count = 0
    for g in all_labeled_graphs(n):
        b, d = solve_brute_force(g), solve_dp(g)
        assert b.cost == d.cost, g
        assert verify_result(g, d, expected_cost=b.cost).ok
        assert is_acyclic(g.remove_arc_pairs(d.removed_arcs))
        count += 1
    assert count == 4 ** (n * (n - 1) // 2)


def test_exhaustive_n5_classes_brute_vs_dp():
    """All 9608 isomorphism classes of digraphs on 5 vertices."""
    for g in isomorphism_classes(5, "digraph"):
        b, d, e = solve_brute_force(g), solve_dp(g), solve_exact(g)
        assert b.cost == d.cost == e.cost, g
        assert verify_result(g, d, expected_cost=b.cost).ok
        assert verify_result(g, e, expected_cost=b.cost).ok


def test_tournament_classes_n6_brute_vs_dp():
    for g in isomorphism_classes(6, "tournament"):
        assert solve_brute_force(g).cost == solve_dp(g).cost


def test_random_differential_with_loops_and_multiplicities():
    rng = random.Random(12345)
    for _ in range(150):
        n = rng.randint(1, 7)
        g = random_multigraph(n, rng.uniform(0.1, 0.7), 3, rng)
        if rng.random() < 0.3:
            g = g.with_arcs({(rng.randrange(n), rng.randrange(n)): rng.randint(1, 2)})
        b = solve_brute_force(g)
        for res in (solve_dp(g), solve_exact(g), solve_exact(g, decompose_sccs=False)):
            assert res.cost == b.cost, g
            assert verify_result(g, res, expected_cost=b.cost).ok


@pytest.mark.parametrize("family", ["sparse", "dense", "tournament", "planted", "scc_dag", "overlapping_cycles"])
def test_random_families_scc_vs_plain_dp(family):
    for g in random_family(family, 11, 4, seed=99):
        a = solve_exact(g)
        b = solve_dp(g)
        assert a.cost == b.cost
        assert verify_result(g, a, expected_cost=b.cost).ok


def test_non_contiguous_vertex_ids():
    g = Graph.from_arcs([(10, 30), (30, 20), (20, 10), (30, 10)])
    assert solve_dp(g).cost == solve_brute_force(g).cost == 1

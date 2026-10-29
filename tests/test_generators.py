import pytest

from fas.generators import (
    FAMILIES,
    GenerationLimitError,
    GenerationLimits,
    all_labeled_graphs,
    canonical_code,
    isomorphism_classes,
    planted_cycles,
    random_family,
    scc_dag,
)
from fas.graph import Graph, strongly_connected_components

# OEIS A000273 (digraphs), A001174 (oriented graphs), A000568 (tournaments).
OEIS_COUNTS = {
    "digraph": {1: 1, 2: 3, 3: 16, 4: 218, 5: 9608},
    "oriented": {1: 1, 2: 2, 3: 7, 4: 42, 5: 582, 6: 21480},
    "tournament": {1: 1, 2: 1, 3: 2, 4: 4, 5: 12, 6: 56, 7: 456},
}


@pytest.mark.parametrize("kind", sorted(OEIS_COUNTS))
def test_class_counts_match_oeis(kind):
    for n, expected in OEIS_COUNTS[kind].items():
        assert len(isomorphism_classes(n, kind)) == expected, (kind, n)


def test_labeled_counts():
    assert sum(1 for _ in all_labeled_graphs(3)) == 4**3
    assert sum(1 for _ in all_labeled_graphs(4, "oriented")) == 3**6
    assert sum(1 for _ in all_labeled_graphs(4, "tournament")) == 2**6


def test_labeled_graphs_collapse_to_classes():
    codes = {canonical_code(g) for g in all_labeled_graphs(4)}
    assert len(codes) == 218


def test_canonical_code_is_relabeling_invariant():
    g = Graph.from_arcs([(0, 1), (1, 2), (2, 0), (2, 3), (3, 2)])
    h = g.relabeled({0: 3, 1: 0, 2: 1, 3: 2})
    assert canonical_code(g) == canonical_code(h)


def test_limits_enforced():
    with pytest.raises(GenerationLimitError):
        list(all_labeled_graphs(6))
    with pytest.raises(GenerationLimitError):
        isomorphism_classes(6, "digraph")
    with pytest.raises(GenerationLimitError):
        list(random_family("dense", 10, 5, seed=0, limits=GenerationLimits(max_n=5)))


@pytest.mark.parametrize("family", sorted(FAMILIES))
def test_families_are_deterministic(family):
    a = list(random_family(family, 9, 3, seed=7))
    b = list(random_family(family, 9, 3, seed=7))
    assert a == b
    assert all(g.n >= 9 or family == "repeated_triangle" for g in a)


def test_scc_dag_blocks_are_sccs():
    g = scc_dag([3, 1, 4, 2], 0.3, 0.5, seed=3)
    assert sorted(strongly_connected_components(g)) == [(0, 1, 2), (3,), (4, 5, 6, 7), (8, 9)]


def test_planted_cycles_contains_cycle():
    g = planted_cycles(8, 2, 3, 0.2, seed=1)
    assert any(len(c) > 1 for c in strongly_connected_components(g))

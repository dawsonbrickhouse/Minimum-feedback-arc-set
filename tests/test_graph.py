import random

import pytest

from fas.generators import random_digraph, random_multigraph
from fas.graph import (
    Graph,
    GraphError,
    find_cycle,
    is_acyclic,
    strongly_connected_components,
    topological_order,
    weakly_connected_components,
)


def test_duplicate_policy():
    with pytest.raises(GraphError):
        Graph.from_arcs([(0, 1), (0, 1)])
    assert Graph.from_arcs([(0, 1), (0, 1)], duplicates="count").multiplicity(0, 1) == 2
    assert Graph.from_arcs([(0, 1), (0, 1)], duplicates="merge").multiplicity(0, 1) == 1


def test_rejects_bad_input():
    with pytest.raises(GraphError):
        Graph([0, 1], {(0, 2): 1})
    with pytest.raises(GraphError):
        Graph([0, 1], {(0, 1): 0})
    with pytest.raises(GraphError):
        Graph.from_edge_list("0 x")


def test_basic_queries_and_isolated_vertices():
    g = Graph.from_arcs([(0, 1), (1, 0, 2), (2, 2)], vertices=[5])
    assert g.vertices == (0, 1, 2, 5)
    assert g.m == 4 and g.num_arc_pairs == 3
    assert g.self_loops() == {2: 1}
    assert g.in_weight(0) == 2 and g.out_weight(1) == 2
    assert not g.is_simple()


def test_serialization_roundtrip():
    g = Graph.from_arcs([(3, 1), (1, 3, 4), (7, 7)], vertices=[9])
    assert Graph.from_json(g.to_json()) == g
    text = "# comment\n3 1\n1 3 4\n7 7\n9\n"
    assert Graph.from_edge_list(text) == g


def test_equality_and_hash():
    a = Graph.from_arcs([(0, 1), (1, 2)])
    b = Graph.from_arcs([(1, 2), (0, 1)])
    assert a == b and hash(a) == hash(b)
    assert a != Graph.from_arcs([(0, 1), (1, 2)], vertices=[3])


def test_acyclicity_and_cycles():
    dag = Graph.from_arcs([(0, 1), (1, 2), (0, 2)])
    assert is_acyclic(dag) and topological_order(dag) == (0, 1, 2) and find_cycle(dag) is None
    loop = Graph.from_arcs([(0, 0)])
    assert not is_acyclic(loop) and find_cycle(loop) == [0]
    cyc = Graph.from_arcs([(0, 1), (1, 2), (2, 0), (2, 3)])
    c = find_cycle(cyc)
    assert c is not None and sorted(c) == [0, 1, 2]


def test_empty_graph():
    g = Graph.empty(0)
    assert is_acyclic(g) and strongly_connected_components(g) == []


def _check_cycle_is_real(g: Graph, cycle: list[int]) -> None:
    for a, b in zip(cycle, cycle[1:] + cycle[:1]):
        assert g.has_arc(a, b)


def test_scc_against_networkx_random():
    nx = pytest.importorskip("networkx")
    rng = random.Random(1)
    for _ in range(300):
        n = rng.randint(0, 12)
        g = random_digraph(n, rng.random() * 0.4, rng)
        h = nx.DiGraph()
        h.add_nodes_from(g.vertices)
        h.add_edges_from(g.arc_pairs())
        ours = sorted(strongly_connected_components(g))
        theirs = sorted(tuple(sorted(c)) for c in nx.strongly_connected_components(h))
        assert ours == theirs
        assert is_acyclic(g) == nx.is_directed_acyclic_graph(h)
        cyc = find_cycle(g)
        assert (cyc is None) == is_acyclic(g)
        if cyc:
            _check_cycle_is_real(g, cyc)
        assert len(weakly_connected_components(g)) == nx.number_weakly_connected_components(h)


def test_scc_order_is_topological():
    rng = random.Random(2)
    for _ in range(200):
        g = random_multigraph(rng.randint(1, 10), 0.25, 2, rng)
        comps = strongly_connected_components(g)
        where = {v: i for i, c in enumerate(comps) for v in c}
        for (u, v), _ in g.arcs():
            assert where[u] <= where[v]

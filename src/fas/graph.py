"""Immutable directed multigraph model and basic graph algorithms.

Conventions (full discussion in ``docs/problem_definition.md``):

* Vertices are Python ``int`` identifiers; they need not be contiguous.
* An *arc pair* ``(u, v)`` carries a positive integer *multiplicity*. The
  unweighted FAS of a multigraph counts every copy, i.e. multiplicity acts as
  an integer weight. Removing an arc pair always removes all of its copies
  (keeping only some copies of a pair can never help acyclicity).
* Self-loops ``(v, v)`` are allowed. Every copy of a self-loop lies in every
  feedback arc set.
* Antiparallel pairs ``(u, v)`` and ``(v, u)`` are allowed (2-cycles).
* Duplicate arcs in input are rejected by default; see ``Graph.from_arcs``.
"""

from __future__ import annotations

import heapq
import json
from collections.abc import Iterable, Iterator, Mapping
from typing import Literal

Arc = tuple[int, int]
DuplicatePolicy = Literal["error", "count", "merge"]


class GraphError(ValueError):
    """Raised for malformed graph input."""


class Graph:
    """An immutable directed multigraph with integer vertex ids."""

    __slots__ = ("_vertices", "_vertex_set", "_mult", "_out", "_in", "_hash")

    def __init__(self, vertices: Iterable[int], multiplicities: Mapping[Arc, int]):
        vertex_list = sorted(set(vertices))
        for v in vertex_list:
            if not isinstance(v, int) or isinstance(v, bool):
                raise GraphError(f"vertex ids must be int, got {v!r}")
        vertex_set = frozenset(vertex_list)
        mult: dict[Arc, int] = {}
        out_adj: dict[int, dict[int, int]] = {v: {} for v in vertex_list}
        in_adj: dict[int, dict[int, int]] = {v: {} for v in vertex_list}
        for (u, v), k in sorted(multiplicities.items()):
            if u not in vertex_set or v not in vertex_set:
                raise GraphError(f"arc ({u}, {v}) uses an unknown vertex")
            if not isinstance(k, int) or isinstance(k, bool) or k < 1:
                raise GraphError(f"multiplicity of ({u}, {v}) must be a positive int, got {k!r}")
            mult[(u, v)] = k
            out_adj[u][v] = k
            in_adj[v][u] = k
        self._vertices: tuple[int, ...] = tuple(vertex_list)
        self._vertex_set = vertex_set
        self._mult = mult
        self._out = out_adj
        self._in = in_adj
        self._hash: int | None = None

    # ------------------------------------------------------------------ construction
    @classmethod
    def from_arcs(
        cls,
        arcs: Iterable[Arc | tuple[int, int, int]],
        vertices: Iterable[int] | None = None,
        duplicates: DuplicatePolicy = "error",
    ) -> Graph:
        """Build a graph from ``(u, v)`` or ``(u, v, multiplicity)`` tuples.

        ``duplicates`` controls repeated arc pairs in the input:
        ``"error"`` (default) rejects them, ``"count"`` adds multiplicities and
        ``"merge"`` keeps a single copy (multiplicity 1, or the maximum given).
        Vertices mentioned only in ``vertices`` become isolated vertices.
        """
        mult: dict[Arc, int] = {}
        vs: set[int] = set(vertices) if vertices is not None else set()
        for arc in arcs:
            if len(arc) == 2:
                u, v = arc  # type: ignore[misc]
                k = 1
            elif len(arc) == 3:
                u, v, k = arc  # type: ignore[misc]
            else:
                raise GraphError(f"arc must have 2 or 3 entries, got {arc!r}")
            if (u, v) in mult:
                if duplicates == "error":
                    raise GraphError(f"duplicate arc ({u}, {v}); pass duplicates='count' or 'merge'")
                if duplicates == "count":
                    mult[(u, v)] += k
                elif duplicates == "merge":
                    mult[(u, v)] = max(mult[(u, v)], k)
                else:
                    raise GraphError(f"unknown duplicate policy {duplicates!r}")
            else:
                mult[(u, v)] = k
            vs.add(u)
            vs.add(v)
        return cls(vs, mult)

    @classmethod
    def empty(cls, n: int = 0) -> Graph:
        return cls(range(n), {})

    # ------------------------------------------------------------------ basic queries
    @property
    def vertices(self) -> tuple[int, ...]:
        return self._vertices

    @property
    def n(self) -> int:
        return len(self._vertices)

    @property
    def m(self) -> int:
        """Total number of arcs counted with multiplicity."""
        return sum(self._mult.values())

    @property
    def num_arc_pairs(self) -> int:
        return len(self._mult)

    def has_vertex(self, v: int) -> bool:
        return v in self._vertex_set

    def arcs(self) -> Iterator[tuple[Arc, int]]:
        """Iterate ``((u, v), multiplicity)`` in sorted order."""
        return iter(self._mult.items())

    def arc_pairs(self) -> tuple[Arc, ...]:
        return tuple(self._mult)

    def multiplicity(self, u: int, v: int) -> int:
        return self._mult.get((u, v), 0)

    def has_arc(self, u: int, v: int) -> bool:
        return (u, v) in self._mult

    def out_neighbors(self, v: int) -> tuple[int, ...]:
        return tuple(self._out[v])

    def in_neighbors(self, v: int) -> tuple[int, ...]:
        return tuple(self._in[v])

    def out_arcs(self, v: int) -> Mapping[int, int]:
        return dict(self._out[v])

    def in_arcs(self, v: int) -> Mapping[int, int]:
        return dict(self._in[v])

    def out_weight(self, v: int) -> int:
        """Out-degree counted with multiplicity (self-loops included)."""
        return sum(self._out[v].values())

    def in_weight(self, v: int) -> int:
        """In-degree counted with multiplicity (self-loops included)."""
        return sum(self._in[v].values())

    def self_loops(self) -> dict[int, int]:
        return {u: k for (u, v), k in self._mult.items() if u == v}

    def is_simple(self) -> bool:
        """True when there are no self-loops and every multiplicity is 1."""
        return all(k == 1 and u != v for (u, v), k in self._mult.items())

    def arc_weight(self, arcs: Iterable[Arc]) -> int:
        """Total multiplicity of the given arc pairs (each pair counted once)."""
        return sum(self._mult[a] for a in set(arcs))

    # ------------------------------------------------------------------ derived graphs
    def induced_subgraph(self, vertices: Iterable[int]) -> Graph:
        keep = frozenset(vertices)
        missing = keep - self._vertex_set
        if missing:
            raise GraphError(f"unknown vertices {sorted(missing)}")
        return Graph(keep, {(u, v): k for (u, v), k in self._mult.items() if u in keep and v in keep})

    def remove_vertices(self, vertices: Iterable[int]) -> Graph:
        drop = frozenset(vertices)
        return self.induced_subgraph(v for v in self._vertices if v not in drop)

    def remove_arc_pairs(self, arcs: Iterable[Arc]) -> Graph:
        drop = frozenset(arcs)
        return Graph(self._vertices, {a: k for a, k in self._mult.items() if a not in drop})

    def with_arcs(self, arcs: Mapping[Arc, int]) -> Graph:
        """Return a copy where multiplicities in ``arcs`` are *added* (new vertices allowed)."""
        mult = dict(self._mult)
        vs = set(self._vertices)
        for (u, v), k in arcs.items():
            mult[(u, v)] = mult.get((u, v), 0) + k
            vs.update((u, v))
        return Graph(vs, mult)

    def with_multiplicity(self, u: int, v: int, k: int) -> Graph:
        """Return a copy where pair ``(u, v)`` has multiplicity ``k`` (0 deletes it)."""
        mult = dict(self._mult)
        if k == 0:
            mult.pop((u, v), None)
        else:
            mult[(u, v)] = k
        return Graph(self._vertices, mult)

    def relabeled(self, mapping: Mapping[int, int]) -> Graph:
        """Rename vertices with an injective mapping (unmapped ids are kept)."""
        new_ids = [mapping.get(v, v) for v in self._vertices]
        if len(set(new_ids)) != len(new_ids):
            raise GraphError("relabeling is not injective")
        return Graph(new_ids, {(mapping.get(u, u), mapping.get(v, v)): k for (u, v), k in self._mult.items()})

    def compact(self) -> tuple[Graph, dict[int, int]]:
        """Relabel vertices to ``0..n-1`` preserving order; returns (graph, old->new)."""
        mapping = {v: i for i, v in enumerate(self._vertices)}
        return self.relabeled(mapping), mapping

    # ------------------------------------------------------------------ serialization
    def to_dict(self) -> dict:
        return {
            "vertices": list(self._vertices),
            "arcs": [[u, v] if k == 1 else [u, v, k] for (u, v), k in self._mult.items()],
        }

    @classmethod
    def from_dict(cls, data: Mapping) -> Graph:
        if "arcs" not in data:
            raise GraphError("graph JSON needs an 'arcs' list")
        return cls.from_arcs((tuple(a) for a in data["arcs"]), vertices=data.get("vertices"))

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> Graph:
        return cls.from_dict(json.loads(text))

    @classmethod
    def from_edge_list(cls, text: str, duplicates: DuplicatePolicy = "error") -> Graph:
        """Parse lines ``u v [multiplicity]``; ``#`` starts a comment; a lone ``u`` adds a vertex."""
        arcs: list[tuple[int, ...]] = []
        vertices: list[int] = []
        for lineno, raw in enumerate(text.splitlines(), start=1):
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            try:
                fields = [int(x) for x in line.split()]
            except ValueError as exc:
                raise GraphError(f"line {lineno}: expected integers, got {raw!r}") from exc
            if len(fields) == 1:
                vertices.append(fields[0])
            elif len(fields) in (2, 3):
                arcs.append(tuple(fields))
            else:
                raise GraphError(f"line {lineno}: expected 'u v [multiplicity]', got {raw!r}")
        return cls.from_arcs(arcs, vertices=vertices, duplicates=duplicates)  # type: ignore[arg-type]

    # ------------------------------------------------------------------ dunder
    def _key(self) -> tuple:
        return (self._vertices, tuple(self._mult.items()))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Graph) and self._key() == other._key()

    def __hash__(self) -> int:
        if self._hash is None:
            self._hash = hash(self._key())
        return self._hash

    def __repr__(self) -> str:
        arcs = ", ".join(f"{u}->{v}" + (f"x{k}" if k > 1 else "") for (u, v), k in self._mult.items())
        return f"Graph(n={self.n}, arcs=[{arcs}])"


# ====================================================================== algorithms


def strongly_connected_components(g: Graph) -> list[tuple[int, ...]]:
    """Tarjan's algorithm (iterative). Returns SCCs in a topological order of the
    condensation (sources first); vertices inside each SCC are sorted."""
    index: dict[int, int] = {}
    low: dict[int, int] = {}
    on_stack: set[int] = set()
    stack: list[int] = []
    sccs: list[tuple[int, ...]] = []
    counter = 0
    for root in g.vertices:
        if root in index:
            continue
        work: list[tuple[int, Iterator[int]]] = [(root, iter(g.out_neighbors(root)))]
        index[root] = low[root] = counter
        counter += 1
        stack.append(root)
        on_stack.add(root)
        while work:
            v, it = work[-1]
            advanced = False
            for w in it:
                if w not in index:
                    index[w] = low[w] = counter
                    counter += 1
                    stack.append(w)
                    on_stack.add(w)
                    work.append((w, iter(g.out_neighbors(w))))
                    advanced = True
                    break
                if w in on_stack:
                    low[v] = min(low[v], index[w])
            if advanced:
                continue
            work.pop()
            if work:
                parent = work[-1][0]
                low[parent] = min(low[parent], low[v])
            if low[v] == index[v]:
                comp = []
                while True:
                    w = stack.pop()
                    on_stack.discard(w)
                    comp.append(w)
                    if w == v:
                        break
                sccs.append(tuple(sorted(comp)))
    sccs.reverse()  # Tarjan emits sinks first
    return sccs


def topological_order(g: Graph) -> tuple[int, ...] | None:
    """Lexicographically smallest topological order (Kahn + min-heap), or None if cyclic.
    Self-loops make a graph cyclic."""
    indeg = {v: 0 for v in g.vertices}
    for (u, v), _ in g.arcs():
        if u == v:
            return None
        indeg[v] += 1
    heap = [v for v, d in indeg.items() if d == 0]
    heapq.heapify(heap)
    order: list[int] = []
    while heap:
        v = heapq.heappop(heap)
        order.append(v)
        for w in g.out_neighbors(v):
            indeg[w] -= 1
            if indeg[w] == 0:
                heapq.heappush(heap, w)
    return tuple(order) if len(order) == g.n else None


def is_acyclic(g: Graph) -> bool:
    return topological_order(g) is not None


def find_cycle(g: Graph) -> list[int] | None:
    """Return the vertex sequence of some directed cycle, or None if acyclic."""
    for v, k in g.self_loops().items():
        if k:
            return [v]
    color: dict[int, int] = {v: 0 for v in g.vertices}  # 0 white, 1 grey, 2 black
    parent: dict[int, int] = {}
    for root in g.vertices:
        if color[root]:
            continue
        color[root] = 1
        work: list[tuple[int, Iterator[int]]] = [(root, iter(g.out_neighbors(root)))]
        while work:
            v, it = work[-1]
            for w in it:
                if color[w] == 0:
                    color[w] = 1
                    parent[w] = v
                    work.append((w, iter(g.out_neighbors(w))))
                    break
                if color[w] == 1:
                    cycle = [v]
                    while cycle[-1] != w:
                        cycle.append(parent[cycle[-1]])
                    cycle.reverse()
                    return cycle
            else:
                color[v] = 2
                work.pop()
    return None


def weakly_connected_components(g: Graph) -> list[tuple[int, ...]]:
    seen: set[int] = set()
    comps: list[tuple[int, ...]] = []
    for root in g.vertices:
        if root in seen:
            continue
        seen.add(root)
        comp = [root]
        frontier = [root]
        while frontier:
            v = frontier.pop()
            for w in (*g.out_neighbors(v), *g.in_neighbors(v)):
                if w not in seen:
                    seen.add(w)
                    comp.append(w)
                    frontier.append(w)
        comps.append(tuple(sorted(comp)))
    return comps


def reachable(g: Graph, source: int, avoid: frozenset[int] = frozenset()) -> set[int]:
    """Vertices reachable from ``source`` by paths whose internal vertices avoid ``avoid``."""
    seen = {source}
    frontier = [source]
    while frontier:
        v = frontier.pop()
        if v != source and v in avoid:
            continue
        for w in g.out_neighbors(v):
            if w not in seen:
                seen.add(w)
                frontier.append(w)
    return seen

"""Graph generators: exhaustive enumeration, isomorphism classes and random families.

All generators are deterministic given their arguments (random ones take an
explicit ``seed`` or ``random.Random``) and enforce explicit size limits so no
search is unbounded. Generated graphs use vertices ``0..n-1``.

Isomorphism classes are produced by vertex extension plus a brute-force
canonical form (minimum adjacency code over all ``n!`` relabelings). The class
counts are checked in the test-suite against OEIS A000273 (digraphs), A001174
(oriented graphs) and A000568 (tournaments) for every ``n`` we support.
"""

from __future__ import annotations

import functools
import itertools
import random
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Literal

from .graph import Graph

Kind = Literal["digraph", "oriented", "tournament"]

MAX_LABELED_N = 5
MAX_CANONICAL_N = 7
MAX_CLASSES_N: dict[str, int] = {"digraph": 5, "oriented": 6, "tournament": 7}


class GenerationLimitError(ValueError):
    """Raised when a request exceeds a generator's configured limit."""


@dataclass(frozen=True)
class GenerationLimits:
    max_n: int = 60
    max_count: int = 100_000


def _pair_states(kind: Kind) -> tuple[tuple[bool, bool], ...]:
    """Allowed (u->v, v->u) states for an unordered pair u < v."""
    if kind == "digraph":
        return ((False, False), (True, False), (False, True), (True, True))
    if kind == "oriented":
        return ((False, False), (True, False), (False, True))
    if kind == "tournament":
        return ((True, False), (False, True))
    raise ValueError(f"unknown kind {kind!r}")


def all_labeled_graphs(n: int, kind: Kind = "digraph") -> Iterator[Graph]:
    """Every loopless simple graph of the given kind on vertices ``0..n-1``."""
    if n > MAX_LABELED_N:
        raise GenerationLimitError(f"labeled enumeration limited to n <= {MAX_LABELED_N}")
    pairs = list(itertools.combinations(range(n), 2))
    states = _pair_states(kind)
    for choice in itertools.product(states, repeat=len(pairs)):
        arcs: list[tuple[int, int]] = []
        for (u, v), (fwd, bwd) in zip(pairs, choice):
            if fwd:
                arcs.append((u, v))
            if bwd:
                arcs.append((v, u))
        yield Graph.from_arcs(arcs, vertices=range(n))


def canonical_code(g: Graph) -> tuple[int, ...]:
    """Isomorphism-invariant code of a graph on ``0..n-1`` (brute force over n!)."""
    if g.n > MAX_CANONICAL_N:
        raise GenerationLimitError(f"canonical form limited to n <= {MAX_CANONICAL_N}")
    if g.vertices != tuple(range(g.n)):
        g, _ = g.compact()
    n = g.n
    arcs = list(g.arcs())
    # Vertices are first sorted by an isomorphism-invariant signature; only
    # relabelings that respect this sorted order are tried. Isomorphic graphs
    # get the same candidate set (up to isomorphism), so the minimum is canonical.
    signature = {
        v: (g.out_weight(v), g.in_weight(v), sum(1 for w in g.out_neighbors(v) if g.has_arc(w, v)))
        for v in range(n)
    }
    groups: list[list[int]] = []
    for sig in sorted(set(signature.values())):
        groups.append([v for v in range(n) if signature[v] == sig])
    best: tuple[int, ...] | None = None
    for parts in itertools.product(*(itertools.permutations(grp) for grp in groups)):
        perm = [0] * n
        pos = 0
        for part in parts:
            for v in part:
                perm[v] = pos
                pos += 1
        code = [0] * (n * n)
        for (u, v), k in arcs:
            code[perm[u] * n + perm[v]] = k
        t = tuple(code)
        if best is None or t < best:
            best = t
    return (n, *best) if best is not None else (n,)


def graph_from_code(code: tuple[int, ...]) -> Graph:
    n = code[0]
    mult = {(i // n, i % n): k for i, k in enumerate(code[1:]) if k}
    return Graph(range(n), mult)


@functools.lru_cache(maxsize=None)
def isomorphism_classes(n: int, kind: Kind = "digraph") -> tuple[Graph, ...]:
    """One canonical representative per isomorphism class of loopless simple graphs.

    Built by extending every class on ``n-1`` vertices by a new vertex in all
    possible ways: deleting any vertex of an ``n``-vertex graph yields some
    ``(n-1)``-vertex class, so every class is reached.
    """
    if n > MAX_CLASSES_N[kind]:
        raise GenerationLimitError(f"{kind} class enumeration limited to n <= {MAX_CLASSES_N[kind]}")
    if n == 0:
        return (Graph.empty(0),)
    classes = {canonical_code(Graph.empty(1))}
    states = _pair_states(kind)
    for size in range(2, n + 1):
        new_classes: set[tuple[int, ...]] = set()
        new_v = size - 1
        for code in classes:
            base = graph_from_code(code)
            for choice in itertools.product(states, repeat=size - 1):
                mult = {a: k for a, k in base.arcs()}
                for u, (fwd, bwd) in enumerate(choice):
                    if fwd:
                        mult[(u, new_v)] = 1
                    if bwd:
                        mult[(new_v, u)] = 1
                new_classes.add(canonical_code(Graph(range(size), mult)))
        classes = new_classes
    return tuple(graph_from_code(c) for c in sorted(classes))


# ---------------------------------------------------------------------- random families


def _rng(seed: int | random.Random) -> random.Random:
    return seed if isinstance(seed, random.Random) else random.Random(seed)


def _check_n(n: int, limits: GenerationLimits) -> None:
    if n < 0 or n > limits.max_n:
        raise GenerationLimitError(f"n={n} outside [0, {limits.max_n}]")


def random_digraph(
    n: int, p: float, seed: int | random.Random, antiparallel: bool = True,
    limits: GenerationLimits = GenerationLimits(),
) -> Graph:
    """G(n, p) on ordered pairs; with ``antiparallel=False`` each unordered pair
    gets at most one arc (an oriented graph)."""
    _check_n(n, limits)
    rng = _rng(seed)
    arcs = []
    for u, v in itertools.combinations(range(n), 2):
        if antiparallel:
            if rng.random() < p:
                arcs.append((u, v))
            if rng.random() < p:
                arcs.append((v, u))
        elif rng.random() < p:
            arcs.append((u, v) if rng.random() < 0.5 else (v, u))
    return Graph.from_arcs(arcs, vertices=range(n))


def random_tournament(n: int, seed: int | random.Random, limits: GenerationLimits = GenerationLimits()) -> Graph:
    _check_n(n, limits)
    rng = _rng(seed)
    arcs = [(u, v) if rng.random() < 0.5 else (v, u) for u, v in itertools.combinations(range(n), 2)]
    return Graph.from_arcs(arcs, vertices=range(n))


def random_multigraph(
    n: int, p: float, max_multiplicity: int, seed: int | random.Random,
    limits: GenerationLimits = GenerationLimits(),
) -> Graph:
    """Random loopless multigraph: each ordered pair present w.p. ``p`` with
    multiplicity uniform in ``1..max_multiplicity``."""
    _check_n(n, limits)
    rng = _rng(seed)
    arcs = []
    for u, v in itertools.permutations(range(n), 2):
        if rng.random() < p:
            arcs.append((u, v, rng.randint(1, max_multiplicity)))
    return Graph.from_arcs(arcs, vertices=range(n))


def planted_cycles(
    n: int, num_cycles: int, cycle_length: int, noise_p: float, seed: int | random.Random,
    limits: GenerationLimits = GenerationLimits(),
) -> Graph:
    """A random DAG (forward arcs w.p. ``noise_p`` w.r.t. a hidden order) plus
    ``num_cycles`` planted directed cycles of the given length on random vertices."""
    _check_n(n, limits)
    if cycle_length < 2 or cycle_length > n:
        raise GenerationLimitError("cycle_length must lie in [2, n]")
    rng = _rng(seed)
    order = list(range(n))
    rng.shuffle(order)
    arcs: set[tuple[int, int]] = set()
    for i, j in itertools.combinations(range(n), 2):
        if rng.random() < noise_p:
            arcs.add((order[i], order[j]))
    for _ in range(num_cycles):
        cyc = rng.sample(range(n), cycle_length)
        for a, b in zip(cyc, cyc[1:] + cyc[:1]):
            arcs.add((a, b))
    return Graph.from_arcs(sorted(arcs), vertices=range(n))


def scc_dag(
    sizes: list[int], p_inside: float, p_between: float, seed: int | random.Random,
    limits: GenerationLimits = GenerationLimits(),
) -> Graph:
    """Blocks of the given sizes, each made strongly connected by a Hamiltonian
    cycle plus random arcs (prob ``p_inside``); arcs between blocks only go from
    earlier to later blocks (prob ``p_between``), so the blocks are the SCCs."""
    n = sum(sizes)
    _check_n(n, limits)
    rng = _rng(seed)
    arcs: set[tuple[int, int]] = set()
    blocks: list[list[int]] = []
    start = 0
    for s in sizes:
        block = list(range(start, start + s))
        blocks.append(block)
        start += s
        if s >= 2:
            for a, b in zip(block, block[1:] + block[:1]):
                arcs.add((a, b))
        for u, v in itertools.permutations(block, 2):
            if rng.random() < p_inside:
                arcs.add((u, v))
    for bi, bj in itertools.combinations(range(len(blocks)), 2):
        for u in blocks[bi]:
            for v in blocks[bj]:
                if rng.random() < p_between:
                    arcs.add((u, v))
    return Graph.from_arcs(sorted(arcs), vertices=range(n))


def repeated_pattern(
    pattern: Graph, copies: int, link_p: float, seed: int | random.Random,
    limits: GenerationLimits = GenerationLimits(),
) -> Graph:
    """Disjoint copies of ``pattern`` (on ``0..k-1``) joined by random arcs
    between consecutive copies in both directions (prob ``link_p`` per pair)."""
    k = pattern.n
    n = k * copies
    _check_n(n, limits)
    rng = _rng(seed)
    mult: dict[tuple[int, int], int] = {}
    for c in range(copies):
        for (u, v), m in pattern.arcs():
            mult[(c * k + u, c * k + v)] = m
    for c in range(copies):
        nxt = (c + 1) % copies
        if nxt == c:
            continue
        for u in range(k):
            for v in range(k):
                a, b = c * k + u, nxt * k + v
                if rng.random() < link_p:
                    mult.setdefault((a, b), 1)
                if rng.random() < link_p:
                    mult.setdefault((b, a), 1)
    return Graph(range(n), mult)


def overlapping_short_cycles(n: int, seed: int | random.Random, limits: GenerationLimits = GenerationLimits()) -> Graph:
    """Adversarial family: every vertex lies on several 2- and 3-cycles that share
    arcs, which defeats purely local degree rules and SCC splitting."""
    _check_n(n, limits)
    rng = _rng(seed)
    arcs: set[tuple[int, int]] = set()
    for v in range(n):
        arcs.add((v, (v + 1) % n))
        arcs.add(((v + 2) % n, v))
        if rng.random() < 0.5:
            arcs.add(((v + 1) % n, v))
    return Graph.from_arcs(sorted(a for a in arcs if a[0] != a[1]), vertices=range(n))


FAMILIES: dict[str, Callable[[int, random.Random], Graph]] = {
    "sparse": lambda n, rng: random_digraph(n, 1.5 / max(n - 1, 1), rng),
    "dense": lambda n, rng: random_digraph(n, 0.5, rng),
    "oriented_dense": lambda n, rng: random_digraph(n, 0.8, rng, antiparallel=False),
    "tournament": lambda n, rng: random_tournament(n, rng),
    "multigraph": lambda n, rng: random_multigraph(n, 0.3, 3, rng),
    "planted": lambda n, rng: planted_cycles(n, max(1, n // 3), min(n, 4), 0.3, rng),
    "scc_dag": lambda n, rng: scc_dag(_split(n, rng), 0.3, 0.2, rng),
    "repeated_triangle": lambda n, rng: repeated_pattern(
        Graph.from_arcs([(0, 1), (1, 2), (2, 0)]), max(1, n // 3), 0.15, rng),
    "overlapping_cycles": lambda n, rng: overlapping_short_cycles(max(n, 3), rng),
}


def _split(n: int, rng: random.Random) -> list[int]:
    sizes: list[int] = []
    remaining = n
    while remaining > 0:
        s = min(remaining, rng.randint(1, 6))
        sizes.append(s)
        remaining -= s
    return sizes


def random_family(
    family: str, n: int, count: int, seed: int,
    limits: GenerationLimits = GenerationLimits(),
) -> Iterator[Graph]:
    """``count`` graphs from a named family, reproducible from ``seed``."""
    if family not in FAMILIES:
        raise ValueError(f"unknown family {family!r}; choose from {sorted(FAMILIES)}")
    if count > limits.max_count:
        raise GenerationLimitError(f"count={count} exceeds limit {limits.max_count}")
    _check_n(n, limits)
    rng = random.Random(f"{family}:{n}:{seed}")
    for _ in range(count):
        yield FAMILIES[family](n, rng)

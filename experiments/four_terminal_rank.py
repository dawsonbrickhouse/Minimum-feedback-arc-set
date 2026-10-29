"""Exploratory: how much of the 24-dimensional space of functions on the orders of
4 terminals is spanned by boundary functions of small sides?

The pairwise functions (constant + 6 pair indicators) span rank 7. For k = 3 the
1-vertex stars already span the remaining rank (6 - 4 = 2). This script reports the
rank of the span of the pairwise basis together with the boundary functions of
(a) all 1-internal-vertex sides and (b) a seeded sample of 2-internal-vertex sides.
Rank of the *span* is a necessary condition only; realisability needs the
non-negative integer cone, which is not computed here.

Usage: python experiments/four_terminal_rank.py [--samples 2000] [--seed 0] [--out results/mining/four_terminal_rank.json]
"""

from __future__ import annotations

import argparse
import itertools
import json
import random
from fractions import Fraction
from pathlib import Path

from fas.boundary import boundary_function
from fas.candidates import Oracle
from fas.graph import Graph

TERMS = (0, 1, 2, 3)
ORDERS = list(itertools.permutations(TERMS))
LINKS = ("none", "in", "out", "both")  # arcs between an internal vertex and a terminal


def _rank(rows: list[list[int]]) -> int:
    basis: list[list[Fraction]] = []
    pivots: list[int] = []
    for row in rows:
        vec = [Fraction(x) for x in row]
        for b, p in zip(basis, pivots):
            if vec[p]:
                factor = vec[p] / b[p]
                vec = [x - factor * y for x, y in zip(vec, b)]
        pivot = next((i for i, x in enumerate(vec) if x), None)
        if pivot is not None:
            basis.append(vec)
            pivots.append(pivot)
    return len(basis)


def _pairwise_basis() -> list[list[int]]:
    rows = [[1] * len(ORDERS)]
    for s, t in itertools.combinations(TERMS, 2):
        rows.append([1 if o.index(t) < o.index(s) else 0 for o in ORDERS])
    return rows


def _side(links: dict[tuple[int, int], str], internal_arcs: dict[tuple[int, int], int], internals: list[int]) -> Graph:
    mult: dict[tuple[int, int], int] = dict(internal_arcs)
    for (w, t), kind in links.items():
        if kind in ("in", "both"):
            mult[(t, w)] = 1
        if kind in ("out", "both"):
            mult[(w, t)] = 1
    return Graph([*TERMS, *internals], mult)


def _vector(g: Graph, oracle: Oracle) -> list[int]:
    f = boundary_function(g, TERMS, oracle)
    return [f[o] for o in ORDERS]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="results/mining/four_terminal_rank.json")
    args = ap.parse_args()
    oracle = Oracle()
    pair = _pairwise_basis()
    base_rank = _rank(pair)

    one = [_vector(_side({(4, t): k for t, k in zip(TERMS, combo)}, {}, [4]), oracle)
           for combo in itertools.product(LINKS, repeat=4)]
    rank_one = _rank(pair + one)

    rng = random.Random(args.seed)
    two: list[list[int]] = []
    rank_trace = []
    for i in range(args.samples):
        links = {(w, t): rng.choice(LINKS) for w in (4, 5) for t in TERMS}
        inner = rng.choice([{}, {(4, 5): 1}, {(5, 4): 1}, {(4, 5): 1, (5, 4): 1}])
        two.append(_vector(_side(links, inner, [4, 5]), oracle))
        if (i + 1) % 500 == 0 or i + 1 == args.samples:
            rank_trace.append({"samples": i + 1, "rank": _rank(pair + one + two)})

    record = {
        "orders": len(ORDERS), "pairwise_rank": base_rank,
        "one_internal_sides": len(one), "rank_with_one_internal": rank_one,
        "two_internal_samples": args.samples, "seed": args.seed, "rank_trace_with_two_internal": rank_trace,
        "full_rank": len(ORDERS),
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(record, indent=1))
    print(json.dumps(record, indent=1))


if __name__ == "__main__":
    main()

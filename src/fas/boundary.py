"""Boundary (interface) cost functions of graph pieces glued at terminal vertices.

If ``G = G1 ∪ G2`` with ``V(G1) ∩ V(G2) = T`` and the arcs partitioned, then

    OPT(G) = min over orders sigma of T of  f_G1(sigma) + f_G2(sigma),

where ``f_H(sigma)`` is the minimum backward weight of an order of ``H`` whose
restriction to ``T`` is ``sigma`` (two orders agreeing on ``T`` can always be
merged). Boundary functions therefore add under gluing at ``T``, and replacing
``G2`` by any ``H`` with ``f_H = f_G2 - c`` changes OPT by exactly ``c``.
Proof: docs/proof_obligations.md (PO-5).
"""

from __future__ import annotations

import itertools
from typing import Protocol

from .graph import Arc, Graph


class _Solver(Protocol):
    def opt(self, g: Graph) -> int: ...


Order = tuple[int, ...]


def boundary_function(side: Graph, terminals: tuple[int, ...], oracle: _Solver) -> dict[Order, int]:
    """``f(sigma)`` for every order ``sigma`` of ``terminals``, forcing sigma with a
    heavy path ``sigma[0] -> sigma[1] -> ...`` (heavier than any FAS of ``side``)."""
    big = side.m + 1
    return {
        sigma: oracle.opt(side.with_arcs({(sigma[i], sigma[i + 1]): big for i in range(len(sigma) - 1)}))
        for sigma in itertools.permutations(terminals)
    }


def pairwise_decomposition(f: dict[Order, int], terminals: tuple[int, int, int]) -> tuple[dict[str, int], list[int]]:
    """Fit ``f(sigma) = c + p[y<x] + q[z<y] + r[z<x]`` on four orders and return the
    coefficients plus residuals on the other two orders. Residuals are ``[0, 0]``
    iff ``f`` is *pairwise*, i.e. realisable by arcs among the terminals plus a
    constant."""
    x, y, z = terminals
    c = f[(x, y, z)]
    p = f[(y, x, z)] - c
    q = f[(x, z, y)] - c
    r = f[(z, x, y)] - c - q
    residual = [f[(y, z, x)] - (c + p + r), f[(z, y, x)] - (c + p + q + r)]
    return {"c": c, "p_yx": p, "q_zy": q, "r_zx": r}, residual


def pairwise_gadget(coeffs: dict[str, int], terminals: tuple[int, int, int]) -> tuple[dict[Arc, int], int]:
    """Arcs among terminals and a constant realising a pairwise function.
    Coefficient ``k`` on ``[t<s]`` is arc ``s -> t`` of weight ``k`` (backward exactly
    when ``t`` precedes ``s``); negative ``k`` becomes ``t -> s`` of weight ``-k``
    with ``k`` added to the constant."""
    x, y, z = terminals
    arcs: dict[Arc, int] = {}
    const = coeffs["c"]
    for (s, t), k in (((x, y), coeffs["p_yx"]), ((y, z), coeffs["q_zy"]), ((x, z), coeffs["r_zx"])):
        if k > 0:
            arcs[(s, t)] = k
        elif k < 0:
            arcs[(t, s)] = -k
            const += k
    return arcs, const


def star_templates(terminals: tuple[int, int, int], w: int) -> dict[str, Graph]:
    """Single-internal-vertex gadgets whose residuals are [1,0], [0,1], [-1,-1]
    (verified at run time by ``three_terminal_gadget``)."""
    x, y, z = terminals
    verts = [x, y, z, w]
    return {
        "A": Graph(verts, {(x, w): 1, (y, w): 1, (w, z): 1}),
        "B": Graph(verts, {(x, w): 1, (z, w): 1, (w, y): 1}),
        "C": Graph(verts, {(x, w): 1, (w, y): 1, (w, z): 1}),
    }


EXPECTED_STAR_RESIDUALS = {"A": [1, 0], "B": [0, 1], "C": [-1, -1]}


def three_terminal_gadget(
    f: dict[Order, int], terminals: tuple[int, int, int], first_new_id: int, oracle: _Solver,
) -> tuple[Graph, int]:
    """A weighted gadget ``H`` on the terminals plus at most two new vertices, and a
    constant ``c``, with ``f_H(sigma) + c = f(sigma)`` for all six orders."""
    x, y, z = terminals
    (a, b) = pairwise_decomposition(f, terminals)[1]
    if a >= 0 and b >= 0:
        mult = {"A": a, "B": b, "C": 0}
    else:
        t = max(-a, -b)
        mult = {"A": a + t, "B": b + t, "C": t}
    gadget_arcs: dict[Arc, int] = {}
    vertices = [x, y, z]
    remainder = dict(f)
    next_id = first_new_id
    for key in ("A", "B", "C"):
        k = mult[key]
        if k == 0:
            continue
        star = star_templates(terminals, next_id)[key]
        f_star = boundary_function(star, terminals, oracle)
        if pairwise_decomposition(f_star, terminals)[1] != EXPECTED_STAR_RESIDUALS[key]:
            raise AssertionError(f"star {key} residual differs from the expected value")
        for sigma in remainder:
            remainder[sigma] -= k * f_star[sigma]
        for arc, w in star.arcs():
            gadget_arcs[arc] = gadget_arcs.get(arc, 0) + k * w
        vertices.append(next_id)
        next_id += 1
    coeffs, residual = pairwise_decomposition(remainder, terminals)
    if residual != [0, 0]:
        raise AssertionError("remainder is not pairwise; decomposition bug")
    arcs, const = pairwise_gadget(coeffs, terminals)
    for arc, w in arcs.items():
        gadget_arcs[arc] = gadget_arcs.get(arc, 0) + w
    return Graph(vertices, gadget_arcs), const

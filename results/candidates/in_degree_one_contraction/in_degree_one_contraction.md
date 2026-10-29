# Counterexample: `in_degree_one_contraction`

**Claim:** OPT(G) = OPT(G / uv)

**Minimised graph G** (n=3, m=4): 0->1, 1->2, 2->0, 2->1

**Match:** `{"u": 1, "v": 2}`

**Why the preconditions hold:** match {'u': 1, 'v': 2} satisfies: no self-loop at v; in-arc pair set of v is exactly {(u, v)} with w = 1

**Reduced graph G'** (n=2, m=3): 0->1, 1->0, 1->1

| quantity | value |
|---|---|
| OPT(G) | 1 (optimal FAS: [(1, 2)]) |
| OPT(G') | 2 (optimal FAS: [(0, 1), (1, 1)]) |
| claimed correction | 0 |
| OPT(G') + correction | 2 |
| discrepancy OPT(G) - (OPT(G') + c) | -1 |
| failure kind | identity |

Replaying the match on the saved graph gives outcome **counterexample**.
Original (unminimised) graph: 0->1, 1->2, 2->0, 2->1.
Minimisation: 7 attempts; accepted moves: relabel {0: 0, 1: 1, 2: 2}.

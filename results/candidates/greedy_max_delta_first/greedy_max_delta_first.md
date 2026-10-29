# Counterexample: `greedy_max_delta_first`

**Claim:** OPT(G) = OPT(G - v) + w_in(v)

**Minimised graph G** (n=4, m=5): 1->3, 2->0, 2->1, 3->1, 3->2

**Match:** `{"vertex": 2}`

**Why the preconditions hold:** match {'vertex': 2} satisfies: G has at least one arc

**Reduced graph G'** (n=3, m=2): 1->3, 3->1

| quantity | value |
|---|---|
| OPT(G) | 1 (optimal FAS: [(1, 3)]) |
| OPT(G') | 1 (optimal FAS: [(1, 3)]) |
| claimed correction | 1 |
| OPT(G') + correction | 2 |
| discrepancy OPT(G) - (OPT(G') + c) | -1 |
| failure kind | identity |

Replaying the match on the saved graph gives outcome **counterexample**.
Original (unminimised) graph: 1->3, 2->0, 2->1, 3->1, 3->2.
Minimisation: 9 attempts; accepted moves: relabel {0: 0, 1: 1, 2: 2, 3: 3}.

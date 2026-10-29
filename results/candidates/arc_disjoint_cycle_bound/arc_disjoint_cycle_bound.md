# Counterexample: `arc_disjoint_cycle_bound`

**Claim:** OPT(G) = OPT(G - v) + w_in(v)   (resp. w_out(v))

**Minimised graph G** (n=3, m=4): 0->1, 1->2, 2->0, 2->1

**Match:** `{"vertex": 0, "side": "in"}`

**Why the preconditions hold:** w_in(0) = 1 <= nu(0) = 1

**Reduced graph G'** (n=2, m=2): 1->2, 2->1

| quantity | value |
|---|---|
| OPT(G) | 1 (optimal FAS: [(1, 2)]) |
| OPT(G') | 1 (optimal FAS: [(1, 2)]) |
| claimed correction | 1 |
| OPT(G') + correction | 2 |
| discrepancy OPT(G) - (OPT(G') + c) | -1 |
| failure kind | identity |

Replaying the match on the saved graph gives outcome **counterexample**.
Original (unminimised) graph: 0->1, 1->2, 2->0, 2->1.
Minimisation: 7 attempts; accepted moves: relabel {0: 0, 1: 1, 2: 2}.

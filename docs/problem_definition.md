# Problem definition and conventions

## The problem

A **feedback arc set (FAS)** of a directed graph `G = (V, A)` is a set of arcs `F ⊆ A` such that `G − F` has no directed cycle. The **minimum feedback arc set problem** asks for a FAS of minimum size; we write `OPT(G)` for that size. The problem is NP-hard (it is on Karp's 1972 list; see `literature_review.md`).

## Conventions used by this code base

| Situation | Convention | Where enforced |
|---|---|---|
| Vertex ids | Any Python `int`; not necessarily `0..n-1`. | `fas.graph.Graph` |
| Duplicate arcs in input | Rejected by default (`duplicates="error"`). `"count"` treats them as parallel copies (multiplicity), `"merge"` keeps one copy. | `Graph.from_arcs`, `Graph.from_edge_list` |
| Parallel arcs / weights | An arc pair `(u, v)` has a positive integer multiplicity `w(u, v)`. OPT counts every copy, so multiplicity acts as an integer arc weight. Unweighted inputs stay unweighted, but several reductions create multiplicities. | `Graph` |
| Removing an arc | A solution removes arc *pairs*: all copies of `(u, v)` together. Keeping some copies of a pair never helps, since one remaining copy keeps every cycle through it. | `FASResult.removed_arcs` |
| Self-loops | Allowed. A loop is a cycle of length 1, so every copy of every loop lies in every FAS. In the ordering view a loop always points backward. | solvers, `self_loop` rule |
| 2-cycles (antiparallel arcs) | Allowed. | everywhere |
| Empty graph, isolated vertices | `OPT = 0`. | solvers |
| Disconnected graphs | Handled naturally; OPT is additive over weak components (a special case of the SCC rule). | solvers |
| Tie-breaking | Deterministic. Brute force returns the lexicographically first optimal ordering of the sorted vertex list. The DP picks, as the last vertex of each prefix, the smallest vertex id achieving the optimum. With SCC splitting, components are concatenated in Tarjan's topological order. Different solvers may return different optimal solutions of equal cost. | `fas.exact_solver` |
| Size limits | Brute force: at most 9 vertices by default. Subset DP: at most 20 vertices per component by default. Exceeding a limit raises `SolverLimitError`, which the candidate harness reports as `inconclusive`. | `fas.exact_solver` |

## The ordering formulation (and why the solvers are correct)

For a linear order `π` of `V`, call an arc `(u, v)` **backward** when `pos(u) ≥ pos(v)`. Self-loops are always backward.

**Lemma 1.** `OPT(G) = min over π of w(backward arcs of π)`.

*Proof.*
- (≤) For any order `π`, the forward arcs all go from earlier to later positions, so they form an acyclic graph. Hence the backward arcs of `π` form a FAS.
- (≥) Let `F` be any FAS. Take a topological order `π` of the acyclic graph `G − F`. Every arc outside `F` is forward in `π`, so the backward arcs of `π` are a subset of `F`, and their weight is at most `w(F)`. ∎

**Brute force** (`solve_brute_force`) evaluates all `n!` orders. By Lemma 1 it is correct. It is used only as an independent oracle.

**Subset DP** (`solve_dp`). Let `DP[S]` be the minimum backward weight of an order of `S` placed as a prefix. Arcs inside `S` are the only ones whose status is decided by the order of `S`. If `v` is the last vertex of `S`, the arcs that become backward are `v → S∖{v}`. Arcs from `S∖{v}` to `v` are forward. Arcs between `S` and `V∖S` do not depend on the order inside `S`. Hence

`DP[∅] = 0`, `DP[S] = min_{v∈S} DP[S∖{v}] + w(v → S∖{v})`,

and `OPT = DP[V] + w(self-loops)`. This runs in `O(2^n · n)` time and `O(2^n)` memory. The recurrence is the one stated in the specification. The literature review attributes the classical `O*(2^n)` DP to Lawler 1964 (attribution tagged UNVERIFIED there).

**Verification.** Every reported solution can be re-checked with `fas.verify.verify_result`. The checks are:
1. the ordering is a permutation of `V`;
2. the removed set equals the backward arcs of the ordering;
3. the cost equals the removed weight;
4. `G − removed` is acyclic, checked by an independent cycle finder;
5. optionally, the cost equals a known optimum.

## Test evidence for the solvers

These are in `tests/test_exact_solver.py`; actual results are in `docs/final_report.md`.

- Hand-checked instances, each OPT justified in a comment. Examples: the 5-vertex rotational tournament has OPT 3 (5 triangles, each arc on at most 2 of them); K3 and K4 complete digraphs have OPT 3 and 6.
- Brute force equals the DP on **every** labeled loopless digraph with `n ≤ 4` (`4^{n(n−1)/2}` graphs, 4,096 for `n = 4`).
- Brute force equals the DP on **all 9,608** isomorphism classes of digraphs with 5 vertices, and on all 56 tournaments with 6 vertices.
- The class counts match OEIS A000273 (digraphs, `n ≤ 5`), A001174 (oriented graphs, `n ≤ 6`) and A000568 (tournaments, `n ≤ 7`). This checks the generator, so it checks that "all graphs" really means all of them.
- Randomized differential tests on multigraphs with loops (`n ≤ 7`) and on random families (`n = 11`): every solved instance is re-verified.
- SCC, cycle-finding and biconnected-block routines are cross-checked against NetworkX on random graphs.

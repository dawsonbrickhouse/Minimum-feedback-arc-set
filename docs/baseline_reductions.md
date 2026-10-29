# Baseline reductions

These rules are implemented in `src/fas/reductions.py`. Each one is a known rule from the literature, with a complete proof given here. Each satisfies an exact identity `OPT(G) = OPT(G') + offset`, and each provides a *lift* that turns an optimal FAS of `G'` into an optimal FAS of `G`. None of them is a discovery of this project. Experimental rules live in `src/fas/candidates/` instead (see `candidate_rules.md`).

Notation: `w(u, v)` is the multiplicity of arc `(u, v)`, which is 0 if the arc is absent. `w_in(v)` and `w_out(v)` are the weighted in- and out-degrees. "Lit. review" refers to `literature_review.md`, with its verification tags.

The rules are applied to a fixpoint in this order: `self_loop`, `source_sink`, `inter_scc_arcs`, `degree_two_bypass`, `pendant_two_cycle`. The kernel is then split into SCCs and biconnected blocks, and each piece is solved by the subset DP.

Every rule (individually, and all combined) is tested for the identity and for lift optimality:
- on all 4,096 labeled digraphs with `n = 4`;
- on all 9,608 digraph classes with `n = 5`;
- on 250 random multigraphs with self-loops (`n ≤ 9`).

The full pipeline is additionally checked on random families with `n = 14` (`tests/test_reductions.py`).

---

## B1. Self-loop removal

- **Precondition:** a loop of multiplicity `k` at `v`.
- **Transformation:** delete the loop.
- **Identity:** `OPT(G) = OPT(G − loop) + k`.
- **Proof:** a loop is a cycle by itself, so every FAS contains it. Removing it creates no cycle and destroys no other cycle.
- **Lift:** add `(v, v)`.
- **Runtime:** `O(n)` per pass.
- **Limitations:** none.
- **Source:** Baharev et al. 2021, Fig. 4(1) (lit. review R3, [V-src]).

## B2. Source / sink deletion

- **Precondition:** `v` has no in-arcs or no out-arcs.
- **Transformation:** delete `v`.
- **Identity:** `OPT(G) = OPT(G − v)`.
- **Proof:** no cycle passes through `v`, so `G` and `G − v` have the same cycles.
- **Lift:** identity.
- **Runtime:** `O(n + m)` with a work queue.
- **Limitations:** subsumed by B3 together with SCC splitting, but cheap. It is iterated because deleting `v` can create new sources and sinks.
- **Source:** standard. Eades, Lin and Smyth 1993 exploit the same fact (lit. review 1.6, [V-abs]/[V-sec]).

## B3. Inter-SCC arc deletion and SCC decomposition

- **Precondition:** none.
- **Transformation:** delete every arc whose endpoints lie in different strongly connected components (SCCs), then solve each SCC separately.
- **Identity:** `OPT(G) = Σ_C OPT(G[C])`.
- **Proof:** a directed cycle lies inside one SCC. Hence an arc between SCCs lies on no cycle and never needs to be removed. A set `F` is a FAS of `G` iff `F ∩ A(G[C])` is a FAS of each `G[C]`. The arc sets of the `G[C]` are disjoint, so the minima add.
- **Lift:** union of the per-component solutions.
- **Runtime:** `O(n + m)` (Tarjan).
- **Limitations:** does nothing on strongly connected inputs.
- **Source:** standard; stated in Baharev et al. 2021 §2 and the PACE 2022 report (lit. review R1, [V-src]).

## B4. Degree-two bypass (chain contraction)

- **Precondition:** `v` has no loop. Its only in-neighbour is `u` (weight `a`) and its only out-neighbour is `w` (weight `b`), with `u ≠ v ≠ w`. The case `u = w` is allowed.
- **Transformation:** delete `v` and add `min(a, b)` copies of `(u, w)`. They merge with any existing `(u, w)` copies (`c ≥ 0` of them). If `u = w`, the result is a loop, which B1 then removes.
- **Identity:** `OPT(G) = OPT(G')`.
- **Proof:** every cycle through `v` contains the path `u → v → w`. Write `m = min(a, b)`.

  *(OPT(G) ≤ OPT(G'))* Let `F'` be a FAS of `G'`.
  - If `F'` removes the pair `(u, w)` (cost `c + m`), let `F` consist of `F' ∖ {(u, w)}`, plus the original `(u, w)` if `c > 0`, plus the cheaper of `(u, v)` and `(v, w)`. Then `w(F) = w(F')`. A cycle of `G − F` cannot use `v` (one of its two arcs is gone) and cannot use `(u, w)`. Hence it is a cycle of `G' − F'`, which is impossible.
  - Otherwise let `F = F'`. A cycle of `G − F` that passes through `v` maps to a closed walk in `G' − F'` by replacing `u → v → w` with the kept arc `u → w`. Any other cycle is already in `G' − F'`. A closed walk contains a cycle, so `G − F` is acyclic.

  *(OPT(G') ≤ OPT(G))* Let `F` be a minimal optimal FAS of `G`. It contains at most one of `(u, v)` and `(v, w)`: every cycle through one passes through the other, so keeping both would contradict minimality.
  - If it contains neither, then `G − F` has no `w ⇝ u` path. Such a path together with `u → v → w` would form a cycle. Therefore `F` with the merged arc kept is a FAS of `G'`.
  - If it contains one of them (weight at least `m`), let `F' = F` minus that arc. If `G − F` has a `w ⇝ u` path, also add the merged pair `(u, w)`. Its extra cost is at most `m` beyond the original copies, and those originals must already lie in `F` (otherwise `u → w` plus the `w ⇝ u` path would be a cycle in `G − F`). In both cases `w(F') ≤ w(F)`, and `G' − F'` is acyclic.
- **Lift:** if `(u, w)` is in the reduced solution, replace it by the original `(u, w)` (when `c > 0`) plus the cheaper of `(u, v)` and `(v, w)`. Otherwise keep the solution unchanged.
- **Runtime:** `O(1)` per application after an `O(n)` scan.
- **Limitations:** creates multiplicities, so unweighted inputs become weighted.
- **Source:** Baharev et al. 2021 Fig. 4(4)–(6) ("runs", "3-arc bypass", "3-cycle"); Hecht 2018 Def. 4 / Prop. 2 (essential minor). Lit. review R6, [V-src].

## B5. Pendant 2-cycle (Baharev patterns 2 and 3)

- **Precondition:** `b` has no loop and lies on a 2-cycle `a ⇄ b`. Either (i) `b`'s only out-arc pair is `(b, a)` and `w(b, a) ≤ w(a, b)`, or (ii) `b`'s only in-arc pair is `(a, b)` and `w(a, b) ≤ w(b, a)`.
- **Transformation:** delete `b`. The offset is `w(b, a)` in case (i) and `w(a, b)` in case (ii).
- **Identity:** `OPT(G) = OPT(G − b) + offset`.
- **Proof (case i; case ii is symmetric):**
  - (≤) Removing `(b, a)` makes `b` a sink, so a FAS of `G − b` plus `(b, a)` is a FAS of `G`.
  - (≥) Any FAS `F` of `G` breaks the 2-cycle, so it contains arcs at `b` of total weight at least `min(w(a, b), w(b, a)) = w(b, a)`. `F` minus the arcs at `b` is a FAS of `G − b`.
- **Lift:** add the paid arc.
- **Runtime:** `O(deg)` per vertex.
- **Limitations:** local; a special case of the candidate `two_cycle_local_bound`.
- **Source:** Baharev et al. 2021 Fig. 4(2,3) and §A.1 (lit. review R5, [V-src]).

## B6. Biconnected-block split (applied at solve time)

- **Precondition:** none.
- **Transformation:** split each kernel SCC into the blocks of its underlying undirected simple graph, ignoring direction and loops, and solve each block separately.
- **Identity:** `OPT(G) = Σ_B OPT(G[B])`.
- **Proof:**
  - A directed cycle of length at least 3 is a cycle of the underlying graph. That cycle is 2-connected, so it lies in one block.
  - A 2-cycle uses one underlying edge, which lies in exactly one block.
  - Two blocks share at most one vertex, so the arc sets of the `G[B]` partition the arcs.
  - The same argument as for SCCs then applies.
- **Lift:** union.
- **Runtime:** `O(n + m)` (Hopcroft–Tarjan, iterative).
- **Source:** Park–Akers 1992, as cited by Baharev et al. §2 and Pustoslemšek et al. 2024 (lit. review R2, [V-sec]; primary text unverified).

---

## Considered but not included

- **Baharev et al. general safe-arc rule (R8).** Correct, but it needs exact sub-solutions on chosen induced subgraphs, and the authors themselves found it too expensive for presolve.
- **Hecht's isolated-cycle rule (R17).** Not implemented; the exact preconditions need care.
- **Bessy et al. safe partitions (R10).** General, but finding a safe partition needs a good order plus a certificate packing; this is listed as future work.
- **Tournament kernel rules (R11, R12) and Kemeny rules (R15).** Class-specific or parameter-dependent; not OPT identities on general digraphs.
- **2-cycle cancellation (R4), modules (R13), in-degree-1 exchange (R9), arc domination (R16).** The literature review tags these [OWN], meaning they are the reviewer's own derivations, not cited results. They are therefore treated as **candidates** here, with proofs in `proof_obligations.md`, and are not counted as literature baseline.

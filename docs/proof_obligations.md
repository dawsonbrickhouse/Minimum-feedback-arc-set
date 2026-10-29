# Proof obligations

This file holds the full proofs behind every status `PROVED_WITHIN_STATED_ASSUMPTIONS` in
`src/fas/candidates/`. Each proof has three parts:

- a **statement** with its exact preconditions;
- the **proof** of the OPT identity and of the solution lift (`lift` in the code);
- a **critical review** listing what the proof relies on and where it could go wrong.

The code's statuses must agree with this file. A rule loses `PROVED_WITHIN_STATED_ASSUMPTIONS`
if a proof here is found to be wrong.

Finite search results are listed as *evidence only*. They never stand in for a proof.

Proofs written: 2026-10-29. Review: the author re-read each proof against the code on the same
day. No independent human review has been done yet. That is the first item in
"Remaining obligations" at the end.

## Conventions (from `problem_definition.md`)

- `G = (V, w)` is a directed multigraph. `w(a, b) ∈ Z≥0` is the multiplicity of arc `(a, b)`,
  loops included. `m(G) = Σ w`.
- An *arc pair* `(a, b)` is all copies together. A feedback arc set (FAS) removes arc pairs.
  Its weight is the sum of the multiplicities removed.
- For a linear order π of `V`, `cost_G(π) = Σ { w(a, b) : pos(a) ≥ pos(b) }`. Loops are always
  backward.
- **Lemma 1** (`problem_definition.md`): `OPT(G) = min_π cost_G(π)`, the minimum FAS weight. The
  backward arc pairs of an optimal order form an optimal FAS. If `F` is a FAS, any topological
  order of `G − F` has all its backward arcs in `F`.
- *Heavy forcing.* `H = m(G) + 1` copies of `(a, b)` can never be backward in an optimal order of
  the augmented graph, because putting `a` first in any order costs at most `m(G)`. So
  `OPT(G + H·(a, b))` equals the minimum of `cost_G(π)` over orders with `a` before `b`.
  The code uses this in `make_undeletable` and `boundary_function`.

Several rules below have the form "make some arcs undeletable". For these, the identity
`OPT(G') = OPT(G)` follows from two facts:

- adding arcs never decreases OPT;
- some optimal FAS `F` of `G` contains none of the boosted arcs, so `F` is also a FAS of `G'` of
  the same weight.

The lift is then the identity map. Any optimal FAS of `G'` avoids the boosted arcs. Removing
it from `G` leaves a subgraph of `G' − F'`, which is acyclic, and its weight is `OPT(G') = OPT(G)`.

---

## PO-1 `two_cycle_local_bound`

**Statement.** Let `v` have no loop. Let `L(v) = Σ_u min(w(u, v), w(v, u))` over the 2-cycles at
`v`. If `w_in(v) ≤ L(v)`, then `OPT(G) = OPT(G − v) + w_in(v)`. The `out` side is symmetric.

**Proof.**

- (≤) Let `F` be an optimal FAS of `G − v`. Then `F` together with all in-arcs of `v` is a FAS of
  `G`: `v` becomes a source, so no cycle passes through it.
- (≥) Let `F` be an optimal FAS of `G`. For each `u` with a 2-cycle `u ↔ v`, `F` must contain
  `(u, v)` or `(v, u)`. These pairs are arc-disjoint for different `u`, so the arcs of `F`
  incident to `v` weigh at least `L(v) ≥ w_in(v)`. `F` minus the arcs at `v` is a FAS of `G − v`.
  So `OPT(G) ≥ OPT(G − v) + w_in(v)`.

**Lift.** Add the in-arc pairs of `v`; the (≤) argument shows this is optimal.

**Critical review.**

- A loop at `v` would belong to every FAS but is not counted in `L(v)`. That is why it is excluded.
- Parallel arcs are fine because removal is by pair and weight is multiplicity.
- This rule is implied by PO-2 (cancel every 2-cycle at `v`) followed by source/sink deletion.
  It is kept as a teaching example.

**Evidence.**

- Searches: no counterexample in the standard or deep profile; counts are in
  `candidate_rules.md`.
- Mining (`results/mining/summary.md`): on all 9,842 digraph classes with n = 3–5, every
  vertex-signature where "delete v and pay one side" is always optimal is explained by this
  bound.

## PO-2 `two_cycle_cancellation`

**Statement.** For `u ≠ v` with `a = w(u, v) > 0` and `b = w(v, u) > 0`, let `c = min(a, b)` and
let `G'` subtract `c` from both multiplicities. Then `OPT(G) = OPT(G') + c`.

**Proof.** In every linear order exactly one of `(u, v)` and `(v, u)` is backward. So for every π,
`cost_G(π) = cost_G'(π) + c`: if `(u, v)` is backward, we compare `a` with `a − c` and the other
arc contributes 0 in both graphs; the other case is symmetric. Minimising over π gives the
identity, and the minimisers coincide.

**Lift.** Take a topological order of `G' − F'` (`ordering_from_removed`). It is optimal for `G'`,
hence optimal for `G`. Its backward arcs in `G` are those of `F'` plus whichever of `(u, v)` and
`(v, u)` it makes backward. That is what `lift` returns.

**Critical review.** The identity holds order by order, so nothing is lost. The only subtlety is
the lift. When both arcs cancel completely, `F'` says nothing about `u` and `v`, so the lift must
orient the pair from an order. The code does this.

**Prior art.** Brandenburg & Hanauer, Univ. Passau tech. report MIP-1104 (2011), §2.1. Read
directly. They describe the unweighted operation of erasing both arcs of a 2-cycle and adding
one back by the order. The weighted cancellation is a direct restatement of it.

## PO-3 `module_contraction`

**Statement.** Let `M ⊆ V` with `2 ≤ |M| < |V|` be a module: for every `x ∉ M`,
`w(x, m)` and `w(m, x)` do not depend on `m ∈ M`. Let `G/M` replace `M` by a new vertex `q`
with `w(x, q) = |M|·w(x, m)` and `w(q, x) = |M|·w(m, x)`. Then
`OPT(G) = OPT(G[M]) + OPT(G/M)`. The code solves `G' = G[M] ⊔ G/M`. Its OPT is the sum because
`G[M]` and `G/M` are vertex-disjoint pieces with no arcs between them.

**Proof.**

1. *Some optimum has `M` contiguous.* Fix an optimal order π and write `C = V ∖ M`. For `m ∈ M`,
   the cost of arcs between `m` and `C` depends only on the *slot* of `m` relative to the order
   of `C`. Because `M` is a module, this is the same function `e(slot)` for every member. Let
   `m*` be a member whose slot minimises `e`. Build π′ by moving all of `M`, in its π-internal
   order, into the slot of `m*`. Arcs inside `M` keep their status. Arcs inside `C` keep their
   status. Each member's external cost becomes `e(slot(m*)) ≤` its old cost. So π′ is optimal
   too.
2. *Cost split for contiguous orders.* If `M` is contiguous in π, then
   `cost_G(π) = cost_{G[M]}(π|M) + cost_{G/M}(π/M)`. Here `π/M` replaces the block by `q`.
   Each `x ∈ C` contributes `|M|·w(x, m)` or `|M|·w(m, x)` exactly when every member does.
3. Minimising the two terms independently gives the identity, and every pair of orders can be
   realised: put any order of `G[M]` into `q`'s slot of any order of `G/M`.

**Lift.** Given FASs `F_M` of `G[M]` and `F_q` of `G/M`, the lift expands each `(x, q)` or
`(q, x)` in `F_q` to all `|M|` arc pairs between `x` and `M`.

- Weight: `w(F_M) + w(F_q)`, the same as in `G'`.
- FAS: suppose a cycle in `G` minus the lifted set uses a vertex of `C`. Map every member of `M`
  to `q`. The non-removed arcs between `M` and `C` map to non-removed arcs at `q`, because
  removal was expanded for all members. The result is a closed walk in `G/M − F_q` through a
  vertex of `C`. Such a walk contains a cycle, which is a contradiction. Cycles inside `M` are
  broken by `F_M`. Cycles inside `C` are broken by `F_q`.

**Critical review.**

- The module condition must hold for *multiplicities*, not just adjacency. The code checks
  multiplicities.
- Loops at members belong to `G[M]`. Loops at `C`-vertices belong to `G/M`.
- *Matcher.* `find_matches` enumerates all subsets when `n ≤ 8`. For larger `n` it uses the
  module closures of vertex pairs. The smallest module containing a set is obtained by
  repeatedly adding vertices that distinguish two members, since every module containing the
  set must contain such a vertex. So for `n > 8` the matcher finds every minimal module of size
  at least 2, but not necessarily every module.
- An earlier pairs-only matcher made the harness report `RULE_BUG`: its targeted generator
  planted 3-vertex modules that were not found. That incompleteness is fixed and covered by a
  regression test. It never affected soundness.

**Prior art.** None found for FAS (review R13 is tagged [OWN]). The analogous "clones" idea for
Kemeny rankings is mentioned on Wikipedia without a located primary source. Bessy et al. use
modules for tournaments. **NOVELTY_UNVERIFIED**; this identity is very plausibly folklore.

## PO-4 `two_terminal_separator`

**Statement.**

- *Setting.* Let `x ≠ y` and let `C` be a union of weak components of `G − {x, y}`. Split `G`
  into two sides:
  - `G2`: the arcs with an endpoint in `C`, on vertex set `C ∪ {x, y}`;
  - `G1 = G − C`, which keeps all arcs among `{x, y}`, including loops.
- *Definition.* For a side `S`, let `f_S^{xy} = OPT(S + H·(x, y))` and
  `f_S^{yx} = OPT(S + H·(y, x))`.
- *Transformation.* Let `d = |f_2^{xy} − f_2^{yx}|`. Let `G'` be `G1` plus `d` copies of
  `(x, y)` if `f_2^{xy} ≤ f_2^{yx}`, else `d` copies of `(y, x)`.
- *Identity.* `OPT(G) = OPT(G') + min(f_2^{xy}, f_2^{yx})`.

**Proof.** This is the `k = 2` case of the gluing lemma in PO-5. By heavy forcing, `f_S^{xy}` is
the minimum cost of an order of `S` with `x` before `y`, so it is the boundary function value on
the order `(x, y)`. By the gluing lemma,

`OPT(G) = min(f_1^{xy} + f_2^{xy}, f_1^{yx} + f_2^{yx})`.

The gadget adds `d` to exactly the orders where its arc is backward. Suppose
`f_2^{xy} ≤ f_2^{yx}`; the other case is symmetric. Then

`OPT(G') = min(f_1^{xy}, f_1^{yx} + d) = OPT(G) − f_2^{xy}`.

This holds even when `G1` already has arcs between `x` and `y`, because order cost is linear in
multiplicities.

A direct cycle-based proof is also available. A simple cycle meeting both `C` and
`V(G1) ∖ {x, y}` passes through `x` and `y` once each. It therefore splits into an `x ⇝ y` path
on one side and a `y ⇝ x` path on the other. This gives the same formula.

**Lift.**

1. Take an optimal FAS `F'` of `G'` and let `r1 = F' ∩ arcs(G1)`.
2. `G1 − r1` is acyclic, since it is a subgraph of `G' − F'` up to merged copies. So at least one
   of "no `y ⇝ x` path" and "no `x ⇝ y` path" holds in it.
3. Choose the cheaper side-2 solution among the allowed directions. Merging the two acyclic
   sides with the same relative order of `x` and `y` gives an order of `G` whose backward arcs
   lie in the lifted set, so the lifted set is a FAS.
4. Weight check. If `F'` keeps the gadget arc, then direction `x → y` is allowed and the lifted
   weight is `w(r1) + f_2^{xy} = OPT(G') + c`. If `F'` removes the gadget pair, it paid `d` for
   that, and the lifted weight is at most `w_G(r1) + f_2^{yx} = w(F') + c`.

**Critical review.**

- *Arc assignment.* Arcs between `x` and `y` and loops at `x`, `y` are put in `G1`. Each arc must
  be counted on exactly one side; the code assigns arcs to `G2` iff they touch `C`.
- *Precondition.* `C` must not touch any vertex outside `C ∪ {x, y}`. `check_preconditions`
  verifies this arc by arc.

**Prior art.** Nutov & Penn (J. Comb. Optim. 4(2):235–251, 2000, doi:10.1023/A:1009802905533)
compose minimum dicycle covers across 2-vertex cuts. Only the abstract was checked; the exact
form of their gadget is unverified. Park–Akers (1992) handle 1-vertex cuts (blocks), cited via
secondary sources. **PRIOR_ART_FOUND** at abstract level.

## PO-5 Gluing lemma and `three_terminal_gadget`

**Gluing lemma.**

- *Setting.* Let `G = G1 ∪ G2` with `V(G1) ∩ V(G2) = T`, and partition the arcs between the two
  sides. Each arc lies in exactly one side. Arcs among `T` may go on either side but are counted
  once.
- *Definition.* For an order σ of `T`, let `f_i(σ)` be the minimum of `cost_{G_i}(π)` over orders
  π of `V(G_i)` whose restriction to `T` is σ.
- *Claim.* `OPT(G) = min_σ f_1(σ) + f_2(σ)`.

*Proof.*

- (≥) Restrict an optimal order of `G` to each side. Both restrictions induce the same σ, and
  every arc's status depends only on its endpoints' relative order. So `cost_G = cost_1 + cost_2`.
- (≤) Take optimal orders `π_1` and `π_2` for a fixed σ. They agree on `T`, so they can be merged
  into one order of `V(G)`. Place the non-terminal vertices of each side between the same
  consecutive terminals, in their own relative order. Restricting the merged order to each side
  gives `π_1` and `π_2` back, so its cost is `f_1(σ) + f_2(σ)`. ∎

The same argument gives **additivity**. If `H` and `H'` are glued only at `T`, then
`f_{H ∪ H'} = f_H + f_{H'}`. This also covers arcs among `T` (a side with no internal vertex)
and new arcs merged with existing arcs.

**Replacement corollary.** If `f_H(σ) + c = f_2(σ)` for all σ, then replacing `G2` by `H` gives
`OPT(G) = OPT(G1 ∪ H) + c`.

**Realisation theorem (k = 3).** For every integer function `f` on the 6 orders of `T = (x, y, z)`
there are a constant `c` and a gadget `H` with `f_H + c = f`. `H` consists of non-negative
integer-weighted arcs among `T` plus at most two new vertices, each carrying a weighted star.

*Proof.*

1. **Pairwise part.** Arcs among `T` realise the functions
   `c + p·[y<x] + q·[z<y] + r·[z<x]` for any integers `p, q, r`. A negative coefficient on
   `[t<s]` is realised by the reverse arc, using `[t<s] = 1 − [s<t]` and adjusting `c`. These
   functions form a 4-dimensional lattice. `pairwise_decomposition` fits `c, p, q, r` on four
   orders and returns the *residual*: the misfit on the other two orders `(y, z, x)` and
   `(z, y, x)`. The residual is a linear map with integer coefficients, from `Z^6` onto `Z^2`,
   that vanishes exactly on pairwise functions. (The fitted model matches the four fitting
   orders by construction; checked by hand in `boundary.py`.)
2. **Stars.** The one-vertex gadgets have the following residuals, computed by the exact solver
   and re-asserted every time a gadget is built:
   - A = {x→w, y→w, w→z}: residual `[1, 0]`;
   - B = {x→w, z→w, w→y}: residual `[0, 1]`;
   - C = {x→w, w→y, w→z}: residual `[−1, −1]`.

   Scaling a star's arc weights by `k` scales its boundary function by `k`.
3. **Combining.** Let `[a, b]` be the residual of `f`.
   - If `a, b ≥ 0`, use `a·A + b·B`.
   - Otherwise let `t = max(−a, −b) > 0` and use `(a+t)·A + (b+t)·B + t·C`. One of the first two
     coefficients is 0, so at most two stars are used, and all coefficients are ≥ 0.

   By additivity, `f` minus the stars' functions has residual 0, so it is pairwise and realised
   by step 1. ∎

**Rule.**

- *Setting.* Let `C` be a weak component of `G − T` with no arcs leaving `C ∪ T`. Let `G2` be the
  arcs touching `C` and `G1 = G − C`.
- *Transformation.* Compute `f_2` with 6 exact solves using heavy forcing paths
  `σ_0 → σ_1 → σ_2`, then build `H` and `c` as above.
- *Identity.* `OPT(G) = OPT(G1 ∪ H) + c` by the corollary.

**Lift.**

1. Take an order of `G' − F'` and let σ be its restriction to `T`.
2. Solve `G2` with σ forced, at cost `f_2(σ)`.
3. Return `(F' ∩ arcs(G1)) ∪` that side-2 solution.

It is a FAS because the two sides are acyclic and consistent with σ (merge as in the gluing
lemma). For the weight: `OPT(G') = w(F') ≥ w(F' ∩ G1) + f_H(σ)`, so the lifted weight is
`≤ OPT(G') + c = OPT(G)`.

**Critical review.**

- **Gadgets are weighted.** The rule leaves the unweighted class even when `G` is unweighted.
  This is the main limitation (see `open_questions.md`, Q1–Q2).
- **Size reduction is not guaranteed.** `H` can have up to 2 internal vertices plus large weights.
  The rule shrinks the instance only when `|C| > 2`. The benchmark applies proved rules only when
  they shrink the largest piece.
- **Cost.** `f_2` needs 6 exact solves of `C ∪ T`, so it is only practical for small `C`.
- **Dependence on computed residuals.** Steps 1–3 rely on the star residuals. These are checked
  computationally rather than derived by hand. A hand derivation is straightforward but not
  written here, and is listed as a remaining obligation.

**Prior art.**

- The gluing lemma is the standard separator/dynamic-programming argument for ordering problems,
  and is almost certainly folklore. It is not claimed as new.
- Crowston–Gutin–Jones (FSTTCS 2012, Rule 2) is one specific small-interface replacement.
- The review frames general small-interface replacement as "protrusion replacement" (§7 item 2).
- A web search (2026-10-29) found protrusion machinery (Garnero–Paul–Sau–Thilikos) but no FAS
  statement of the k = 3 realisation theorem.

**NOVELTY_UNVERIFIED.** The search was shallow, and the result may well be known in
treewidth-DP or linear-ordering-polytope language.

## PO-6 `neighborhood_dominance`

**Statement.** Let `u ≠ v` with no loops at `u` or `v`, `w(u, v) = 0`, and for every
`x ∉ {u, v}`: `w(x, v) ≤ w(x, u)` and `w(u, x) ≤ w(v, x)`. Then some optimal order puts `v`
before `u`. Hence `OPT(G) = OPT(G + H·(v, u))`.

**Proof.**

1. Take an optimal π with `u` before `v` and swap the positions of `u` and `v`.
2. Arcs between `{u, v}` and vertices outside the segment between them keep their status.
3. For the set `B` of vertices strictly between, the cost changes by
   `Σ_B w(x, v) + Σ_B w(u, x) − Σ_B w(x, u) − Σ_B w(v, x) ≤ 0`, by the two inequalities.
4. The arcs `(v, u)` become forward, and there is no `(u, v)` arc to become backward.

So the swapped order is no worse. The rest is the "make undeletable" pattern from the
conventions above, with "forced order" in place of "avoids the arcs". `OPT(G + H·(v, u))` is the
minimum over orders with `v` before `u`, and one of those is optimal for `G`.

**Lift.** Identity map, valid because an optimal order of `G'` has `v` before `u`.

**Critical review.** Equal neighbourhoods are allowed: twins dominate each other both ways. The
rule may then be applied to `(u, v)` and `(v, u)` at once only if the code applies one match at
a time. The harness and the benchmark do apply one match at a time. Applying two conflicting
forced orders simultaneously would be unsound; this is documented in the guide.

## PO-7 `in_degree_one_exchange`

**Statement.** Let `v` have no loop and a unique in-arc pair `(t, v)` with `t ≠ v`. Suppose
`w(t, v) ≤ w(v, x)` for every out-arc `(v, x)` of `v`. Then some optimal FAS contains no out-arc
of `v`, and making all out-arcs of `v` undeletable preserves OPT. The `out` side is symmetric.

**Proof.**

1. Let `F` be optimal and contain some out-arcs of `v`.
2. Let `F' = F ∖ out(v) ∪ {(t, v)}`.
3. *Weight.* `F'` removes at least one arc of weight `≥ w(t, v)` and adds at most `w(t, v)`, so it
   is no heavier.
4. *FAS.* Every cycle through `v` enters through `(t, v)`, which `F'` removes. Cycles avoiding `v`
   use no arcs at `v`, so `F` and `F'` hit them in the same arcs.

**Critical review.** The rule differs from naive contraction of `(t, v)`, which is refuted (see
`candidate_rules.md`). The exchange keeps the graph and only fixes which side pays. It does not
shrink the graph on its own; it enables later rules.

**Prior art.** The review's R9 is tagged [OWN]. The DFVS IN1 analogue is classical, but its FAS
translation is not cited. **NOVELTY_UNVERIFIED.**

## PO-8 `arc_domination`

**Statement.** Let `e = (a, b)` with `a ≠ b` and `f ≠ e` be arc pairs with `w(f) ≤ w(e)`, and
suppose `G − f` has no path `b ⇝ a`. Then some optimal FAS avoids `e`, and making `e`
undeletable preserves OPT.

**Proof.**

1. Let `F` be optimal with `e ∈ F` and let `F' = F ∖ {e} ∪ {f}`. Its weight is
   `≤ w(F) − w(e) + w(f) ≤ w(F)`.
2. A simple cycle through `e` is `e` plus a `b ⇝ a` path. Every such path uses `f`, which `F'`
   removes.
3. Cycles avoiding `e` are hit by some arc of `F ∖ {e} ⊆ F'`.

**Critical review.** The precondition "e lies on a cycle" only removes trivial matches. If `f` is
`(b, a)`, then `e` and `f` form a 2-cycle and the rule reduces to "remove the lighter arc of a
2-cycle whose other cycles all pass through it". That is consistent.

**Prior art.** The review's R16 is tagged [OWN]; the DFVS analogue is vertex domination
(Meiburg 2022). **NOVELTY_UNVERIFIED.**

---

## Refuted candidates (no proof obligation; see `candidate_rules.md`)

| Rule | Where the attempted proof breaks |
|---|---|
| `arc_disjoint_cycle_bound` | The cuts that break the ν(v) cycles through `v` need not be incident to `v`, and can also break other cycles. "F minus the arcs at v" is then not a cheap FAS of `G − v`. |
| `in_degree_one_contraction` | In `G`, one unit on `(u, v)` breaks every cycle through `v`. After contraction, those cycles go through `u`'s merged out-arcs, and a 2-cycle can become a loop. |
| `greedy_max_delta_first` | The Eades–Lin–Smyth choice is a heuristic step with an approximation guarantee, not an exactness guarantee. |

## Remaining obligations

1. **Independent review** of PO-3, PO-4 and PO-5 by a second person. These are the proofs with
   the most moving parts.
2. **PO-5 star residuals by hand.** For each star, write the 6 boundary values with the optimal
   position of `w`, instead of relying on the solver assertion.
3. **PO-5 for k = 4** is open: 24 orders, a pairwise lattice of rank 7 (1 + 6 pairs), and
   residual rank 17. See `open_questions.md`.

## Prior-art checks still needed

- PO-3 (module contraction): search linear-ordering-problem and Kemeny "clone" literature for the
  weighted quotient identity.
- PO-4: read Nutov & Penn (2000) in full to confirm that their composition gives this gadget.
- PO-5: search treewidth/pathwidth DP for linear-arrangement and FAS problems, and
  linear-ordering-polytope facet literature, for 3-terminal realisability.
- PO-7 and PO-8: search FAS kernelization and preprocessing papers (Baharev et al. 2021;
  Hecht 2018 in full) for arc-level exchange rules.

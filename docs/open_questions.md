# Open questions, ranked

Ranked on 2026-10-29 by **promise** and **tractability**.

- *Promise*: could this give a new, useful exact reduction?
- *Tractability*: can a student make real progress with this tool in a few weeks?

Both ratings are judgement calls; the reasoning is given for each question. Nothing here is
claimed to be new. Every question still needs a literature check before any claim is made
(`literature_review.md`, section 7).

| Rank | Question | Promise | Tractability |
|---|---|---|---|
| 1 | Smallest *unweighted* gadgets for 2- and 3-terminal sides | high | high |
| 2 | Do 4-terminal sides always have bounded-size weighted gadgets? | high | medium |
| 3 | Which mined arc signatures survive richer features and larger falsification? | medium | high |
| 4 | A cheap certificate that generalises `L(v)` for "delete v, pay one side" | medium | medium |
| 5 | Near-modules with a bounded correction | medium | medium |
| 6 | Safe partitions in sparse digraphs (review R10, §7 item 3) | medium | low–medium |

## Q1. Smallest unweighted gadgets for small interfaces

**Background.** `two_terminal_separator` and `three_terminal_gadget` are proved, but their
gadgets are *weighted*, so they leave the class of unweighted simple digraphs. The literature
review (§7 item 2) names unweighted-closed replacement as a target.

**An elementary observation (this project, not claimed new).** Constant-size unweighted gadgets
cannot exist, even with 2 terminals.

- Let `S_k` be the side `x → c_i → y` for `i = 1..k`. Then `f(x before y) = 0` and
  `f(y before x) = k`.
- Glue `S_k` to the context `T_j` made of `y → d_i → x` for `i = 1..j`. The result has
  `OPT = min(k, j)`.
- For `k ≠ k'`, the difference `min(k, j) − min(k', j)` is not constant in `j`. So `S_k` and
  `S_k'` are not equivalent in the protrusion sense (`literature_review.md` §7), and there are
  infinitely many classes.

**The right question.** Given the boundary function `f` of an unweighted side (up to a
constant), what is the smallest unweighted simple gadget realising it? Is that size bounded by
a function of `max f − min f`? When is it smaller than the side it replaces? A "yes" with a
small bound gives a size-reducing rule that stays unweighted.

**First step.**

1. Extend `fas.mining.mine_boundary` to record, for each boundary function seen, the smallest
   side that realises it. The current data covers sides with ≤ 2 internal vertices
   (`results/mining/boundary_3terminal.json`: 16,384 sides, 2,922 non-pairwise).
2. Tabulate the minimum size as a function of `f`.
3. Try to prove the pattern for 2 terminals first, where `f` is just the pair
   `(f_xy, f_yx)`.

## Q2. Bounded gadgets for 4 terminals

**Background.** For 3 terminals, every integer function on the 6 orders is realisable, up to a
constant, by ≤ 2 weighted stars plus arcs (PO-5). Four terminals have 24 orders and a pairwise
part of rank 7.

**Data (this session, `experiments/four_terminal_rank.py`, seed 0,
`results/mining/four_terminal_rank.json`).**

- The pairwise basis plus the boundary functions of all 256 one-internal-vertex sides span
  **rank 20 of 24**. So one-vertex stars cannot be enough.
- Adding sampled two-internal-vertex sides reaches **rank 24** after 1,000 samples. The rank was
  23 after the first 500.
- The method reproduces the known 3-terminal answer: rank 4 rising to 6.

**Caveat.** Spanning rank is necessary, not sufficient. Realisability needs every integer
function to be a *non-negative integer* combination (up to the pairwise part), and the cone was
not computed.

**Open.** Do 2-internal-vertex gadgets positively span the residual space? If so, what is the
largest number of gadgets a function needs? A "yes" gives a 4-terminal rule like PO-5.

**First step.**

1. Compute the residuals of all two-internal-vertex sides; there are 4 × 4⁸ = 262,144. This
   needs a checkpointed run, about 6 M tiny solves.
2. Solve a small LP to test whether the cone is the whole space. This needs an LP solver, which
   would be a new dependency (for example `scipy`).

## Q3. Arc signatures that survive

**Background.** Mining over all 9,842 digraph classes with n = 3–5 gave 400 local arc
signatures `(antiparallel, tail out/in, head out/in)`. The labels are "in all / some / no
optimal FAS".

- 103 uniform signatures had ≥ 10 occurrences.
- Falsification on 600 random larger graphs refuted 36 of them, and 56 survived with at least
  one confirmation.
- A hand-built 7-vertex graph refutes one survivor
  (`tests/test_tools.py::test_mined_hypothesis_refuted_by_hand_example`).

So degree-level signatures are too coarse to be trusted.

**Open.** Add features that the proved rules actually use:

- whether the arc is the unique in-arc of its head;
- whether `G − e` still has a path `b ⇝ a`;
- arc-domination candidates;
- 2-cycle weight after cancellation.

Then ask which uniform signatures survive. A survivor that no proved rule explains is a lead;
one that a proved rule explains is a consistency check.

**First step.** Add these features in `fas.mining._arc_label` and its signature function, and
rerun `fas mine arc --falsify 200`.

## Q4. A cheaper certificate than `L(v)`

**Background.** Vertex mining found that "delete `v` and pay its in-arcs" is always optimal at a
signature `(w_in, w_out, L, ν)` **only** when `w_in ≤ L(v)` (0 unexplained signatures on both
the digraph and oriented datasets). The ν(v) generalisation is refuted with a 3-vertex
counterexample (`candidate_rules.md`).

**Open.** Find a local certificate between `L(v)` (cycles of length 2, arcs at `v`) and ν(v)
(any arc-disjoint cycles), for example arc-disjoint cycles through `v` whose arcs away from `v`
are not shared with any other cycle. Such a condition can be tested immediately as a new
candidate (`adding_a_candidate.md`).

## Q5. Near-modules

**Background.** Exact modules are rare in sparse graphs: `module_contraction` matched in 3,074
of 10,896 search graphs, mostly small or dense ones.

**Open.** If `M` fails to be a module only on `t` arcs, does
`|OPT(G) − OPT(G[M]) − OPT(G/M)| ≤ t·c` hold for a small constant `c`? Such a bound would not
give an exact rule, but it would give a certified bound for branch-and-bound.

**First step.** Write a measurement script: perturb planted modules, then record the gap
against `t`.

## Q6. Safe partitions in sparse digraphs

**Background.** Bessy et al. (Lemma 2.4, [V-src]) is general, but finding safe partitions is
only known to work in tournaments. **Open:** a heuristic search for safe partitions in sparse
graphs, certified by arc-disjoint cycle packings. This needs a new certificate checker in the
core; lower tractability.

## Not ranked: interesting but outside this tool's reach

- Polynomial kernel for FAS by solution size.
- Better-than-2ⁿ exact algorithms.
- Characterising Hecht's resolvable graphs (review §7 item 7).

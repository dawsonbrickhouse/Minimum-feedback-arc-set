# Research notebook

Dated entries, newest last. Each entry records what was done and what was observed, with the
resulting status.

## Status vocabulary

The same vocabulary is used in `fas.candidates.base.Status`.

| Status | Meaning |
|---|---|
| IDEA | Written down, not yet stated precisely. |
| CONJECTURE | Precise statement with preconditions; no evidence yet. |
| TESTED_ON_FINITE_INSTANCES | No counterexample in a stated, finite search. **Not** a proof. |
| COUNTEREXAMPLE_FOUND | A verified counterexample exists (saved and replayable). |
| PROOF_ATTEMPT | A proof is being written; gaps remain. |
| PROVED_WITHIN_STATED_ASSUMPTIONS | A complete proof, re-read critically, is in `proof_obligations.md`. |
| NOVELTY_UNVERIFIED | No prior art was found by a stated (limited) search. This is **not** a novelty claim. |
| PRIOR_ART_FOUND | A citation for the result exists (see `literature_review.md`). |

---

### 2026-10-29: Platform

- **Core.** Graph model, exact solvers (brute force ≤ 9 vertices, subset DP ≤ 20 vertices per
  SCC), verifier and generators.
  - Brute force and DP agree on every labelled digraph with n ≤ 4, on all 9,608 digraph
    classes with n = 5, on all 56 tournaments with n = 6, and on random graphs.
  - The class counts match OEIS A000273, A001174 and A000568.
- **Baseline reductions B1–B6.** Each is tested individually and combined, on exhaustive and
  random graphs (`baseline_reductions.md`).
- **Harness, minimiser, CLI, benchmark and mining tools** built.
- The test suite is the source of truth; see `final_report.md` for the current count.

### 2026-10-29: `two_cycle_local_bound`

- IDEA: pay for `v`'s in-arcs when its 2-cycles already force that much cost at `v`.
- Moved straight to PROOF_ATTEMPT, then **PROVED_WITHIN_STATED_ASSUMPTIONS** (PO-1). It is also
  a corollary of 2-cycle cancellation plus source deletion.
- Standard search: no counterexample (27,695 passing matches).
- Kept as the teaching example. Status: PROVED + NOVELTY_UNVERIFIED (trivial corollary; not
  interesting as a novelty question).

### 2026-10-29: `arc_disjoint_cycle_bound` (generalisation of the above)

- CONJECTURE: replace `L(v)` by ν(v), the number of arc-disjoint cycles through `v`.
- The standard search found a counterexample on the 18th graph. It was minimised to
  `0→1, 1→2, 2→0, 2→1` (OPT 1, claimed 2). Status **COUNTEREXAMPLE_FOUND**.
- Insight: ν(v) counts cycles whose cutting arcs need not be at `v`. A single arc (1→2) breaks
  a cycle through `v` *and* another cycle.

### 2026-10-29: `in_degree_one_contraction`

- CONJECTURE (naive FAS version of DFVS IN1), already flagged false in the review (§3.4).
- **COUNTEREXAMPLE_FOUND** on the 18th graph, with the same 3-vertex graph as above. The review's
  4-arc example is reproduced in a test (`u=0, v=2`).

### 2026-10-29: `in_degree_one_exchange` (the corrected version)

- CONJECTURE from review R9 [OWN]: instead of contracting, decide which side pays.
- **PROVED_WITHIN_STATED_ASSUMPTIONS** (PO-7) by an exchange argument.
- No counterexample (24,968 passing matches). Status: PROVED + NOVELTY_UNVERIFIED.

### 2026-10-29: `greedy_max_delta_first`

- CONJECTURE (expected false): the Eades–Lin–Smyth greedy choice is always safe.
- **COUNTEREXAMPLE_FOUND** on the 61st graph, minimised to 4 vertices / 5 arcs.

### 2026-10-29: `two_cycle_cancellation`

- From review R4 [OWN]. **PROVED** order by order (PO-2), with no counterexample (27,440
  passes).
- A web search found Brandenburg & Hanauer (2011, §2.1), read directly, so the status is
  **PRIOR_ART_FOUND**.

### 2026-10-29: `module_contraction`

- From review R13 [OWN]. **PROVED** (PO-3).
- First standard search: **RULE_BUG**, with 17 PRECONDITION_INVALID outcomes. The targeted
  generator planted 3-vertex modules in 9-vertex graphs, and the matcher (pairs only for
  n > 8) missed them. This was a completeness bug, not a soundness bug.
- Fixed with module closures and a regression test. The rerun found no counterexample (4,935
  passes).
- A search found no prior art. One search summary wrongly claimed a 2026 LOP heuristic paper
  used modular decomposition; the fetched text did not. Status: PROVED + NOVELTY_UNVERIFIED.

### 2026-10-29: `two_terminal_separator`

- Built after boundary mining (see below). **PROVED** (PO-4) as the k = 2 case of the gluing
  lemma. No counterexample (145,020 passes).
- The Nutov–Penn (2000) abstract describes composition across 2-vertex cuts. Status:
  **PRIOR_ART_FOUND** (abstract level).

### 2026-10-29: Boundary mining leads to `three_terminal_gadget`

- Mining recorded the 3-terminal boundary functions of all sides with 1 internal vertex
  (64 sides) and 2 internal vertices (16,384 sides).
  - 1 internal vertex: 58 pairwise, 6 not; residual shapes `[1,0]`, `[0,1]`, `[-1,-1]`, two
    each.
  - 2 internal vertices: 2,922 not pairwise; residuals in the cone of those three.
- That pattern suggested the realisation theorem: three stars positively span the
  2-dimensional residual lattice using at most two at a time. **PROVED** (PO-5); the star
  residuals are checked computationally at run time.
- No counterexample (168,901 passes). Status: PROVED + NOVELTY_UNVERIFIED. The gluing lemma is
  folklore; the protrusion literature gives the framework but no FAS statement.

### 2026-10-29: `neighborhood_dominance`, `arc_domination`

- `neighborhood_dominance`: swap argument. **PROVED** (PO-6); 20,827 passes.
- `arc_domination`: review R16 [OWN], exchange argument. **PROVED** (PO-8); 58,672 passes.
- Both: NOVELTY_UNVERIFIED. Neither shrinks the graph by itself.

### 2026-10-29: Vertex-forcing mining

- Over 9,842 digraph classes (n = 3–5) and 22,111 oriented classes (n = 3–6), the
  local signature `(w_in, w_out, L(v), ν(v))` gives **zero** signatures where "delete v, pay one
  side" is always optimal but not explained by `w_side ≤ L(v)`.
- Status of the hypothesis "no other local forcing at this granularity": TESTED_ON_FINITE_INSTANCES.
- Insight: at this granularity, nothing beyond PO-1 is forced. Finer features are needed
  (`open_questions.md`, Q3–Q4).

### 2026-10-29: Arc-status mining (a cautionary example)

- 400 arc signatures; 103 uniform hypotheses with ≥ 10 occurrences. Falsification on 600 random
  graphs (n = 6–8) refuted 36; 56 survived with at least one confirmation.
- A survivor was refuted by hand with a 7-vertex graph: signature `(0,2,1,1,3)` claimed "never
  in an optimal FAS", but it is in some.
- **Lesson:** survival of random falsification is weak evidence; the hand example is now a test.
  None of the mined hypotheses has a status above TESTED_ON_FINITE_INSTANCES.

### 2026-10-29: Harness integrity fixes

Two weaknesses were found while writing the student guide. Both are fixed and tested.

1. A search with some passes and some INCONCLUSIVE cases, or one stopped by its time or graph
   limit, used to report `NO_COUNTEREXAMPLE_IN_SEARCH_SPACE`. It now reports
   `INCONCLUSIVE_CASES` or `NO_COUNTEREXAMPLE_BEFORE_LIMIT`.
2. Matches beyond the per-graph cap (64) were evaluated and then discarded from the counts, so a
   counterexample there could have been dropped. Now only the first 64 are evaluated and the
   rest are counted in `matches_skipped`.

All earlier verdicts in this notebook had no INCONCLUSIVE cases and completed their plans. The
standard and deep searches were rerun with the fixed harness (`final_report.md`).

The cap had skipped matches for two rules: 18,579 for `three_terminal_gadget` and 192 for
`two_terminal_separator`. Uncapped reruns checked all of them (187,480 and 145,212 passes),
with no counterexample.

### 2026-10-29: 4-terminal span experiment

- `experiments/four_terminal_rank.py`: one-internal-vertex sides span rank 20 of 24.
  Sampled two-internal-vertex sides reach 24.
- Status of "4-terminal sides have bounded weighted gadgets": CONJECTURE
  (`open_questions.md`, Q2).

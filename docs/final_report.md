# Final report: FAS reduction research platform

Date: 2026-10-29. Every number below comes from files in `results/` produced by the commands
quoted here. Repository: this directory; git history on branch `master`.

## 1. Summary

**What works.** A working, tested platform for finding and checking exact reduction rules for
unweighted Minimum Feedback Arc Set:

- exact solvers;
- six proven baseline reductions;
- a candidate-rule harness that separates pass, counterexample, inconclusive and rule bugs;
- a counterexample minimiser, mining tools and a benchmark;
- a CLI and a student guide.

**Tests.** 171 pass, 0 fail (72.6 s, including slow tests).

**Candidates.** Eleven candidate rules were studied.

- **Eight are proved** within stated assumptions, with full proofs in `proof_obligations.md`:
  - two have prior art found;
  - six are `NOVELTY_UNVERIFIED`, and several of these are very plausibly folklore.
- **Three natural generalisations are refuted**, with minimised 3–4-vertex counterexamples.

**Exploratory results.**

- Vertex-local forcing in all small digraphs is fully explained by a 2-cycle bound.
- Degree-level arc signatures are too coarse to trust.
- 3-terminal boundary functions led to a proved gadget theorem.
- 4-terminal boundary functions span the full 24-dimensional space once 2-internal-vertex
  sides are included.

**Most important unresolved question.** Can small-interface replacement be made to keep
graphs **unweighted** and **smaller**? Constant-size unweighted gadgets are impossible
(`open_questions.md`, Q1), so the real question is the minimum gadget size as a function of
the boundary function.

## 2. What was implemented

| Component | File(s) | Notes |
|---|---|---|
| Graph model | `src/fas/graph.py` | Immutable multigraph with loops. Duplicate handling: `error`, `count` or `merge`. Iterative Tarjan SCC (topological order) and Hopcroft–Tarjan blocks, a lexicographic topological sort, reachability, JSON I/O. |
| Exact solvers | `src/fas/exact_solver.py` | Brute force (≤ 9 vertices, lexicographically first optimum) and subset DP (≤ 20 vertices per piece; ties go to the smallest id). Both return the cost, an ordering and the removed arcs. Limits raise `SolverLimitError`. |
| Verification | `src/fas/verify.py` | Independent re-check of every solution (`problem_definition.md`). |
| Baseline reductions | `src/fas/reductions.py` | B1–B6 with lifts (§6). |
| Generators | `src/fas/generators.py` | Labelled enumeration (n ≤ 5); isomorphism classes of digraphs (n ≤ 5), oriented graphs (n ≤ 6) and tournaments (n ≤ 7). Nine random families: sparse, dense, oriented-dense, tournament, multigraph, planted cycles, SCC-DAG, repeated triangles, overlapping cycles. All seeded and size-limited. |
| Candidate framework | `src/fas/candidates/` | `CandidateRule` interface and registry with 11 rules. Isolated: nothing in the core imports it. |
| Harness | `src/fas/harness.py` | Outcomes are PASS, COUNTEREXAMPLE, INCONCLUSIVE, PRECONDITION_INVALID and MALFORMED. Search verdicts are listed in §4. Searches are bounded and checkpointed every 2,000 graphs. |
| Minimiser | `src/fas/minimize.py` | Greedy shrinking (vertex, then arc, then multiplicity); saves JSON plus a Markdown explanation with a replay check. |
| Boundary functions | `src/fas/boundary.py` | Gluing lemma, pairwise decomposition, star gadgets, 3-terminal gadget construction. |
| Mining | `src/fas/mining.py`, `experiments/` | Vertex forcing, arc status, 3-terminal boundaries, 4-terminal span. |
| Benchmark | `src/fas/benchmark.py` | Five pipelines; config validated up front; median of trials, peak Python allocation, JSONL/CSV/MD/meta outputs, per-instance checkpoint. |
| CLI | `src/fas/cli.py` | `fas solve`, `reduce`, `generate`, `candidates`, `check`, `test-candidate`, `mine`, `benchmark`. |

**Conventions** (`problem_definition.md`):

- A self-loop is always in every FAS.
- Duplicates are multiplicities (integer weights); an arc pair is removed with all its copies.
- The empty graph has OPT 0.
- Disconnected graphs are solved per SCC, and OPT is additive.

## 3. How to run

```bash
python3.12 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt && pip install -e .
python -m pytest -q                       # full suite (about 75 s); add -m "not slow" for about 17 s
fas solve graph.txt                       # edge list "u v" per line, or JSON
fas test-candidate all --profile standard --out results/candidates
./experiments/run_all.sh                  # regenerate everything in results/ (DEEP=1 adds deep searches)
```

See `NEXT_STEPS.md` for a guided start and `adding_a_candidate.md` for adding rules.

## 4. Tests and actual results

Full suite on 2026-10-29: **`171 passed in 72.64s`** (`results/test_log.txt`). Without the slow
marker: 163 passed in 16.0 s.

| File | Tests | What they establish |
|---|---|---|
| `test_exact_solver.py` | 32 | See below. |
| `test_generators.py` | 18 | OEIS class counts; limits enforced; determinism by seed. |
| `test_graph.py` | 10 | Construction conventions; SCCs and blocks agree with NetworkX on random graphs. |
| `test_reductions.py` | 30 | Each baseline rule alone and combined: identity plus lift optimality on all 4,096 labelled n=4 digraphs, all 9,608 n=5 classes, and random multigraphs with loops. |
| `test_candidates.py` | 66 | See below. |
| `test_tools.py` | 15 | See below. |

`test_exact_solver.py` checks:

- hand-checked OPT values;
- brute force against DP on every labelled digraph with n ≤ 4, all 9,608 classes with n = 5, and
  all 56 tournaments with n = 6;
- randomized differential tests;
- verification of every solution.

`test_candidates.py` checks:

- each outcome kind on toy rules;
- INCONCLUSIVE is never a pass, and mixed or stopped-early searches never get the clean verdict;
- skipped matches are counted;
- metadata of every rule;
- every proved rule on all n ≤ 4 classes plus random graphs, and all n = 5 classes (slow);
- every refuted rule is refuted and minimised to ≤ 4 vertices;
- the literature counterexample;
- the `module_contraction` regression.

`test_tools.py` checks:

- CLI, including replaying a saved counterexample with `fas check` and merging `index.json`;
- benchmark smoke test, config validation and empty-group summaries;
- mining smoke test;
- the hand refutation of a mined hypothesis;
- star residuals and 3-terminal gadget exactness.

### Candidate search results

**Standard profile** (`results/candidates/`, seed 0, 10,596–10,896 graphs per rule). For every
proved rule: no counterexample, 0 inconclusive, 0 invalid, and every source exhausted. The
uncapped reruns cover the matches beyond the 64-per-graph cap. Per-rule counts are in
`candidate_rules.md`.

**Deep profile** (`results/candidates_deep/`, 600 s cap per rule). Every proved rule completed
its plan within the cap, with no counterexample and 0 inconclusive. Rules with a targeted
generator examined 34,082 graphs; the others examined 33,482.

The deep search adds:

- all 21,480 oriented graphs on 6 vertices;
- all 456 tournaments on 7 vertices;
- larger random graphs (n up to 12).

Per-rule counts are in §7. The deep runs kept the 64-match cap, so 91,636 matches
(`three_terminal_gadget`) and 2,289 matches (`two_terminal_separator`) were not checked. They
are reported as `matches_skipped`.

## 5. What is known correct, and why

1. **The exact solvers.** Two independent algorithms (permutation brute force and subset DP)
   agree on exhaustive families. Lemma 1 (`problem_definition.md`) proves that the ordering
   formulation equals the FAS formulation for multigraphs with loops. Every returned solution is
   re-verified by an independent acyclicity check.
2. **The generators really enumerate everything they claim.** The class counts match OEIS for
   digraphs (n ≤ 5), oriented graphs (n ≤ 6) and tournaments (n ≤ 7).
3. **Baseline reductions B1–B6.** Proofs are in `baseline_reductions.md`; sources are in
   `literature_review.md`. Exhaustive tests cover n ≤ 5.
4. **Eight candidate rules.** Their proofs in `proof_obligations.md` were re-read against the
   code. Each also passes every check in its finite searches.

The proofs have **not** been independently reviewed by a second person. That is the top item in
"Remaining obligations".

## 6. Baseline reductions (all from the literature; none claimed new)

| Id | Rule | Source (tag) |
|---|---|---|
| B1 | Self-loop removal (pay the loop) | Baharev et al. 2021 Fig. 4(1) [V-src] |
| B2 | Source/sink deletion | standard; Eades–Lin–Smyth use it [V-sec] |
| B3 | Inter-SCC arc deletion, SCC split | standard [V-src] |
| B4 | Degree-two bypass (chain contraction, merges into existing arcs) | Baharev Fig. 4(4–6), Hecht Def. 4 [V-src] |
| B5 | Pendant 2-cycle | Baharev patterns 2 and 3 [V-src] |
| B6 | Biconnected-block split at solve time | Park–Akers 1992 [V-sec] |

## 7. Candidates explored

Full cards are in `candidate_rules.md`, proofs in `proof_obligations.md`, and the dated
history in `research_notebook.md`.

| Rule | Status | Standard passes | Deep profile |
|---|---|---|---|
| `two_cycle_local_bound` | PROVED, NOVELTY_UNVERIFIED (trivial corollary of the next rule plus source deletion) | 27,695 | 29,571 passes / 34,082 graphs |
| `two_cycle_cancellation` | PROVED, PRIOR_ART_FOUND (Brandenburg–Hanauer 2011) | 27,440 | 31,702 / 34,082 |
| `module_contraction` | PROVED, NOVELTY_UNVERIFIED (likely folklore) | 4,935 | 15,437 / 34,082 |
| `two_terminal_separator` | PROVED, PRIOR_ART_FOUND (Nutov–Penn 2000, abstract) | 145,212 (uncapped) | 583,160 / 34,082 (2,289 matches over the cap not checked) |
| `three_terminal_gadget` | PROVED, NOVELTY_UNVERIFIED | 187,480 (uncapped) | 824,961 / 34,082 (91,636 matches over the cap not checked) |
| `neighborhood_dominance` | PROVED, NOVELTY_UNVERIFIED | 20,827 | 116,298 / 33,482 |
| `in_degree_one_exchange` | PROVED, NOVELTY_UNVERIFIED (review R9 [OWN]) | 24,968 | 107,831 / 33,482 |
| `arc_domination` | PROVED, NOVELTY_UNVERIFIED (review R16 [OWN]) | 58,672 | 237,404 / 33,482 |
| `arc_disjoint_cycle_bound` | COUNTEREXAMPLE_FOUND | — | — |
| `in_degree_one_contraction` | COUNTEREXAMPLE_FOUND (also in the review) | — | — |
| `greedy_max_delta_first` | COUNTEREXAMPLE_FOUND | — | — |

**Did any candidate survive?** Yes: eight did. None is claimed new.

- `two_cycle_cancellation` and `two_terminal_separator` have prior art.
- `three_terminal_gadget` is the most substantial, and its novelty is unverified. Its theorem
  says every integer function on the 6 orders of 3 terminals is realised, up to a constant, by
  arcs plus ≤ 2 weighted stars. The gluing lemma underneath it is standard.

## 8. Smallest counterexamples

All are minimal under the greedy minimiser; details are in `candidate_rules.md`.

| Rule | Graph | OPT | Claimed |
|---|---|---|---|
| `arc_disjoint_cycle_bound` | 0→1, 1→2, 2→0, 2→1 (v = 0) | 1 | 2 |
| `in_degree_one_contraction` | the same graph (u = 1, v = 2) | 1 | 2 |
| `greedy_max_delta_first` | 1→3, 2→0, 2→1, 3→1, 3→2 (v = 2) | 1 | 2 |

**Shape.** In each case one arc breaks several cycles at once, and the rule pays for those
cycles somewhere else. A vertex-local charge is safe only when it is certified by cycles whose
arcs are all at that vertex, which is the 2-cycle bound `L(v)`.

## 9. Exploratory aids (second priority) and what they showed

Produced by `fas mine ...` and `experiments/` (`results/mining/summary.md`).

1. **Forced vertex structures.** Data: 9,842 digraph classes (n = 3–5) and 22,111 oriented
   classes (n = 3–6), with vertex signature `(w_in, w_out, L(v), ν(v))`. **Zero** signatures
   force "delete v, pay one side" without being explained by `w_side ≤ L(v)`. Twenty "always
   forced" hypotheses survived falsification on 600 random graphs. All of them are explained
   by `L(v)`, so they add nothing new.
2. **Failing hypotheses.**
   - Arc signatures: 103 uniform hypotheses; 36 refuted by random falsification; 56 survived.
     One survivor was refuted by a hand-built 7-vertex graph, which is now a test.
     Conclusion: degree-level arc data is not a reliable guide.
   - The three refuted rules share one counterexample shape (§8).
3. **Characterisable structures.** 3-terminal boundary functions of all sides with ≤ 2
   internal vertices: 2,922 of 16,384 are not pairwise, and their residuals lie in the cone of
   `[1,0]`, `[0,1]`, `[-1,-1]`. This led to the proved 3-terminal gadget theorem.
4. **4-terminal span.** One-internal-vertex sides span rank 20 of 24. Adding 1,000 sampled
   two-internal-vertex sides reaches 24. This is a necessary condition only
   (`open_questions.md`, Q2).
5. **Ranked open questions:** `open_questions.md`.

## 10. Benchmark (reproducible)

**Command:** `fas benchmark --config experiments/benchmark_default.json --out results/benchmark`.

**Setup.**

- Seed 2026; 5 instances per (family, n); 3 timed trials (median reported) plus one
  `tracemalloc` run.
- Component limit 18 vertices; plain DP limited to n ≤ 18.
- Machine: 4-core VM, Python 3.12, pure Python.
- Outputs: `default_raw.jsonl` (675 rows), `default_summary.csv`, `default_summary.md`,
  `default_meta.json`.

**Correctness during the benchmark.** On every instance, every completed pipeline agreed on
OPT, and every returned FAS passed verification (609 of 675 pipeline runs completed). The rest
hit the 18-vertex limit and are reported as not completed.

**Findings.** Times are median seconds; "piece" is the mean largest piece the DP must solve.

| Family, n | baseline | + 2-cycle cancellation | + module contraction |
|---|---|---|---|
| sparse 30 | 0.00015 s, piece 0.8 | 0.00028 s, piece 0 | 0.00027 s, piece 0.8 |
| multigraph 16 | 0.108 s, piece 15 | 0.050 s, piece 14.4 | 0.109 s, piece 15 |
| overlapping cycles 12 | 0.0038 s, piece 12 | 0.0025 s, piece 3.6 | 0.0046 s, piece 12 |
| overlapping cycles 18 | 0.343 s, piece 18 | 0.039 s, piece 14.4 | 0.347 s, piece 18 |
| repeated triangle 36 | 3/5 completed | **5/5 completed** | 3/5 completed |
| dense 12 | 0.0039 s, piece 12 | 0.0078 s, piece 10.2 | 0.0046 s, piece 12 |
| tournament 16 | 0.077 s, piece 16 | 0.079 s, piece 16 | 0.080 s, piece 16 |
| planted 24 | 2/5 completed | 2/5 completed | 2/5 completed |

**Interpretation.**

- **Baseline rules matter most on sparse graphs.** On sparse n = 30 the SCC split alone leaves
  pieces of 13 on average, while the baseline kernel has 0.8 vertices.
- **2-cycle cancellation is the one candidate with a clear effect.** It helps on 2-cycle-rich
  families: overlapping cycles, multigraphs and repeated triangles. On dense digraphs it costs
  time, because the pure-Python match-and-test loop costs more than the DP it saves at n = 12.
- **Module contraction rarely applies.** It changed the kernel only on `scc_dag` and sparse
  n = 60.
- **Nothing reduces tournaments or oriented dense graphs**, as expected: they have no 2-cycles
  and rarely have modules.

**Caveats.**

- Means are over *completed* instances only, so rows with different completion counts are not
  directly comparable.
- Times are pure Python and include the rule-matching overhead.

## 11. Literature reviewed

`literature_review.md` condenses the project's verified literature review and keeps its
verification tags. [OWN] entries are treated as candidates, never as literature.

Section 7 adds this author's own searches:

- Brandenburg–Hanauer 2011, read directly;
- Nutov–Penn 2000, abstract only;
- the protrusion-replacement framework (Garnero–Paul–Sau–Thilikos; arXiv:1609.09304), whose
  definitions were read.

Two automated search summaries were found to be unsupported by the fetched text, and are
recorded as such.

## 12. Does anything look novel?

**No novelty is claimed.** The candidates whose status is `NOVELTY_UNVERIFIED` after a short
search:

- `module_contraction`: likely folklore, through the Kemeny "clones" analogy;
- `three_terminal_gadget`: the realisation theorem is not found as such, but it sits squarely
  inside the protrusion-replacement framework and treewidth DP for ordering problems;
- `neighborhood_dominance`, `in_degree_one_exchange`, `arc_domination`: simple exchange
  arguments, likely known in some form;
- `two_cycle_local_bound`: a trivial corollary.

**The most interesting candidate for further work** is the 3-terminal realisation together with
the 4-terminal span data. It is interesting as a *tool*, not as a claim.

## 13. Proof and prior-art work still needed

From `proof_obligations.md`.

Proofs:

1. Independent review of PO-3, PO-4 and PO-5.
2. Hand derivation of the star residuals; the code currently asserts them at run time.
3. The 4-terminal analogue of PO-5 is open.

Prior art:

- read Nutov–Penn in full;
- search the linear-ordering and Kemeny literature for the module quotient;
- search treewidth-DP and LOP-polytope work for 3-terminal realisability;
- search FAS preprocessing papers (Baharev 2021 appendix, Hecht 2018) for the exchange rules.

## 14. Bugs and limitations

**Fixed this session:**

- `module_contraction` matcher incompleteness (found by the harness as `RULE_BUG`);
- clean verdicts despite inconclusive cases or early stops;
- matches beyond the cap being evaluated and discarded;
- benchmark config errors surfacing only at the end;
- unbuffered progress output and missing checkpoints;
- `test-candidate NAME` not updating `index.json`;
- benchmark summary showing `True` for groups with no completed instance.

Each has a regression test except the output-buffering fix.

**Known limitations:**

- **Exact solving** is pure-Python subset DP: practical up to about 18–20 vertices per piece
  (n = 18 takes about 0.35 s; memory about 2 MB of Python allocations).
- **Isomorphism classes** are limited to n ≤ 5 (digraphs), 6 (oriented) and 7 (tournaments).
- **The minimiser** is greedy, so a "minimised" counterexample is locally minimal only.
- **Searches** test at most 64 matches per graph by default (`--max-matches` raises this).
  Skipped matches are reported, and both affected rules were rerun uncapped.
- **The benchmark** applies candidate rules only when they shrink the instance, and uses only
  proved rules. Its timings include Python overhead and should not be compared with compiled
  solvers.
- **Gadget weights.** The 3-terminal gadgets are weighted and can be larger than the side they
  replace, so the rule is not always a size reduction.
- **Mining signatures** are deliberately coarse; survival of falsification is weak evidence.

## 15. The three most promising next steps

1. **Q1: unweighted gadgets.** Tabulate the smallest unweighted side realising each 2- and
   3-terminal boundary function (extend `mine_boundary`). Try to prove a size bound in terms
   of `max f − min f`. This is the direct route to size-reducing, unweighted-closed rules.
2. **Q2: the 4-terminal cone.** Compute the residuals of all 262,144 two-internal-vertex sides
   (a checkpointed run) and test with an LP whether they positively span. A positive answer
   would give a 4-terminal gadget rule.
3. **Q3: richer arc features.** Add the features the proved rules use (unique in-arc,
   `b ⇝ a` connectivity after deletion, domination) to arc mining. Look for uniform signatures
   that no proved rule explains, and turn each into a candidate with
   `adding_a_candidate.md`.

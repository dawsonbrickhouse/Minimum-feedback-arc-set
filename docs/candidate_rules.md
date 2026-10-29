# Candidate rules

Candidate rules are proposed exact reductions. They live in `src/fas/candidates/` and are kept
isolated from the trusted core (`exact_solver`, `reductions`). Each candidate claims

    OPT(G) = OPT(G') + correction

at every *match* (one concrete occurrence of its pattern that satisfies its preconditions).
Optionally it also gives a *lift* that turns an optimal FAS of `G'` into one of `G`.

The harness (`src/fas/harness.py`) checks both claims with the exact solver. `fas candidates`
lists the rules, and `fas candidates <name>` prints one rule's full card.

Status vocabulary: see `research_notebook.md`. Proofs: see `proof_obligations.md`.
How to add a rule: see `adding_a_candidate.md`.

## What the searches cover

The **standard profile** (`fas test-candidate all --profile standard`, seed 0) has three parts.
Every source is finite, with a 300 s cap per rule.

- Exhaustive: every isomorphism class of digraphs (loops allowed) with n = 1–5,
  1 + 3 + 16 + 218 + 9,608 = 9,846 graphs.
- Random families: 750 graphs.
  - `sparse` n=8 ×150, `dense` n=7 ×150, `multigraph` n=6 ×150
  - `planted` n=9 ×100, `scc_dag` n=10 ×60, `overlapping_cycles` n=8 ×40, `tournament` n=7 ×100
- Targeted: 300 graphs from the rule's own generator (n=6 ×200, n=9 ×100), for rules that have
  one.

The harness tests at most 64 matches per graph. The exact oracle handles strongly connected
pieces of up to 14 vertices. A larger piece gives INCONCLUSIVE, and the verdict for that rule is
then never "no counterexample".

The **deep profile** adds:

- all 21,480 oriented graphs with n = 6;
- all 456 tournaments with n = 7;
- larger random families (n = 8–12);
- 600 targeted graphs (n = 7 and 10).

Each deep run is capped at 600 s per rule.

Results are in `results/candidates/` (standard) and `results/candidates_deep/` (deep). Each
rule has a `summary.json` with per-source counts; refuted rules also have a minimised
counterexample (`.json` + `.md`). `index.json` lists all verdicts.

## Results

Standard profile, 2026-10-29. "Graphs with matches" counts graphs where the pattern occurred at
least once. "Passes" counts matches checked, both the identity and the lift. All runs produced
0 INCONCLUSIVE, 0 PRECONDITION_INVALID and 0 MALFORMED outcomes.

| Rule | Status | Verdict | Graphs examined | Graphs with matches | Passes |
|---|---|---|---|---|---|
| `two_cycle_local_bound` | PROVED, NOVELTY_UNVERIFIED | no counterexample | 10,896 | 9,387 | 27,695 |
| `two_cycle_cancellation` | PROVED, PRIOR_ART_FOUND | no counterexample | 10,896 | 10,080 | 27,440 |
| `module_contraction` | PROVED, NOVELTY_UNVERIFIED | no counterexample | 10,896 | 3,074 | 4,935 |
| `two_terminal_separator` | PROVED, PRIOR_ART_FOUND | no counterexample | 10,896 | 10,889 | 145,020 |
| `three_terminal_gadget` | PROVED, NOVELTY_UNVERIFIED | no counterexample | 10,896 | 10,874 | 168,901 |
| `neighborhood_dominance` | PROVED, NOVELTY_UNVERIFIED | no counterexample | 10,596 | 7,789 | 20,827 |
| `in_degree_one_exchange` | PROVED, NOVELTY_UNVERIFIED | no counterexample | 10,596 | 9,326 | 24,968 |
| `arc_domination` | PROVED, NOVELTY_UNVERIFIED | no counterexample | 10,596 | 9,155 | 58,672 |
| `arc_disjoint_cycle_bound` | COUNTEREXAMPLE_FOUND | counterexample | 18 | — | 34 before the first failure |
| `in_degree_one_contraction` | COUNTEREXAMPLE_FOUND | counterexample | 18 | — | 24 before the first failure |
| `greedy_max_delta_first` | COUNTEREXAMPLE_FOUND | counterexample | 61 | — | 56 before the first failure |

Three of the proved rules have no targeted generator, so they examine 300 fewer graphs: 10,596
instead of 10,896.

The deep-profile results are summarised in `final_report.md`, section 4.

"No counterexample" is evidence on the listed finite instances, and nothing more. The PROVED
statuses rest on `proof_obligations.md`, not on these searches.

### History worth knowing

The first standard run of `module_contraction` reported `RULE_BUG` (4,876 passes,
17 PRECONDITION_INVALID). The rule's own generator planted 3-vertex modules in 9-vertex graphs,
but the matcher, which only tried vertex pairs for n > 8, did not find them.

This was an incompleteness in the matcher, not a soundness bug. The harness caught it because
"a targeted graph without a match" is reported as PRECONDITION_INVALID rather than ignored. The
matcher now uses module closures, and a regression test was added.

## Rule cards

Each card lists the pattern, preconditions, transformation and claimed identity in short form.
The authoritative text is the class attributes in the source file.

### Proved rules

**`two_cycle_local_bound`** (`two_cycle_local_bound.py`; the worked example in the guide)

- Pattern: vertex `v` with `L(v) = Σ_u min(w(u,v), w(v,u))` over the 2-cycles at `v`.
- Preconditions: no loop at `v`; `w_in(v) ≤ L(v)` (side `in`), or `w_out(v) ≤ L(v)` (side `out`).
- Transformation: `G' = G − v`. Correction: `w_in(v)` (or `w_out(v)`).
- Note: implied by `two_cycle_cancellation` followed by source/sink deletion.

**`two_cycle_cancellation`** (`two_cycle_cancellation.py`)

- Pattern: a 2-cycle `u ↔ v` with `a = w(u, v)` and `b = w(v, u)`.
- Transformation: subtract `min(a, b)` from both multiplicities. Correction: `min(a, b)`.
- Prior art: Brandenburg & Hanauer (2011).

**`module_contraction`** (`structural.py`)

- Pattern: a module `M` (multiplicity-uniform to and from every outside vertex), `2 ≤ |M| < n`.
- Transformation: `G[M]` disjoint union with the quotient `G/M`, where `M` becomes one vertex
  with arcs of weight `|M|·w`. Correction: 0.

**`two_terminal_separator`** (`structural.py`)

- Pattern: terminals `x, y` and a component `C` of `G − {x, y}`.
- Transformation: replace `C` by `|f_xy − f_yx|` parallel arcs between `x` and `y`.
  Correction: `min(f_xy, f_yx)`.
- Prior art: Nutov–Penn (2000), checked at abstract level.

**`three_terminal_gadget`** (`structural.py`, `boundary.py`)

- Pattern: terminals `T = {x, y, z}` and a component `C` of `G − T`.
- Transformation: replace `C` by a weighted gadget with at most 2 internal vertices.
  The correction is a constant `c`.

**`neighborhood_dominance`** (`structural.py`)

- Pattern: an ordered pair `(u, v)` with no arc `(u, v)` and no loops at `u`, `v`. Every other
  vertex sends `v` at most what it sends `u`, and receives from `u` at most what it receives
  from `v`.
- Transformation: force `v` before `u` (heavy arc `(v, u)`). Correction: 0.

**`in_degree_one_exchange`** (`structural.py`)

- Pattern: a vertex `v` with a single in-arc pair `(t, v)` whose weight is at most every out-arc
  weight of `v`. The out-side version is symmetric.
- Transformation: make all out-arcs of `v` undeletable. Correction: 0.

**`arc_domination`** (`structural.py`)

- Pattern: arcs `e = (a, b)` and `f` with `w(f) ≤ w(e)`, where every `b ⇝ a` path uses `f`.
- Transformation: make `e` undeletable. Correction: 0.

### Refuted rules

These are kept in the registry on purpose. They show which natural generalisations fail, and
they keep the harness honest: a test checks that each one is still refuted and minimised to at
most 4 vertices.

**`arc_disjoint_cycle_bound`.** This generalises `two_cycle_local_bound` from 2-cycles to
ν(v), the maximum number of arc-disjoint cycles through `v`. It claims: if `w_in(v) ≤ ν(v)`,
delete `v` and pay its in-arcs.

**`in_degree_one_contraction`.** The naive FAS translation of the DFVS rule IN1: contract the
unique in-arc `(u, v)`.

**`greedy_max_delta_first`.** Claims that the vertex maximising `w_out − w_in` (the
Eades–Lin–Smyth 1993 greedy choice) can always be placed first.

## Smallest counterexamples and their shape

All three were found within the first 61 graphs of the exhaustive enumeration. The
greedy minimiser (`fas.minimize`) could not shrink them further. Files:
`results/candidates/<rule>/<rule>.{json,md}`.

| Rule | Minimised graph | Match | OPT(G) | Claimed | Shape |
|---|---|---|---|---|---|
| `arc_disjoint_cycle_bound` | n=3: 0→1, 1→2, 2→0, 2→1 | v=0, side `in` | 1 | 2 | A triangle sharing the arc 1→2 with a 2-cycle 1↔2. |
| `in_degree_one_contraction` | n=3: 0→1, 1→2, 2→0, 2→1 | u=1, v=2 | 1 | 2 | The same graph; isomorphic to the review's 4-arc example. |
| `greedy_max_delta_first` | n=4: 1→3, 2→0, 2→1, 3→1, 3→2 | v=2 | 1 | 2 | A 2-cycle 1↔3 plus a triangle 1→3→2→1; vertex 2 also has the pendant out-arc 2→0. |

**What the shape shows.** All three failures occur when one cheap arc breaks several cycles at
once (1→2 in the first two graphs, 1→3 in the third), and the rule pays for those cycles at a
different place.

- `arc_disjoint_cycle_bound` deletes vertex 0 and pays its in-arc 2→0. The single arc 1→2
  already breaks both the triangle and the 2-cycle, so the rule pays 1 more than needed.
- `in_degree_one_contraction` merges 2 into 1. The 2-cycle 1↔2 becomes a loop at 1, and the
  triangle becomes a 2-cycle 0↔1. The contracted graph then needs 2 arcs: the loop plus one arc
  of the 2-cycle.
- `greedy_max_delta_first` puts vertex 2 first and pays its in-arc 3→2. One arc, 1→3,
  breaks every cycle, but the greedy rule pays 3→2 and still has to break the 2-cycle.
  (Only 1→3 works: 3→1 breaks the 2-cycle but not the triangle.)

**Lesson used in the open questions.** A rule that charges a *vertex-local* quantity is only safe
if it is certified against cycles *through the same arcs*. `L(v)` counts arc-disjoint 2-cycles at
`v`, whose arcs are all incident to `v`; that certification is what PO-1 uses. ν(v) is not
certified this way.

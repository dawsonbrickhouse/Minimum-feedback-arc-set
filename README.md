# fas-platform: a test bench for exact Feedback Arc Set reductions

This project gives a student an exact solver for the unweighted **Minimum Feedback Arc Set**
problem (FAS), plus a harness that tries hard to *break* proposed reduction rules before anyone
believes them. Multigraphs are allowed, and multiplicities act as integer weights.

What it provides:

- **Exact solvers.**
  - Brute force over orderings (≤ 9 vertices).
  - Subset dynamic programming (≤ 20 vertices per strongly connected piece).
  - Both return the optimal value, an optimal ordering and the removed arcs, and both are
    independently verified.
- **Baseline reductions with proofs**: self-loops, sources/sinks, SCC split, degree-2 bypass,
  pendant 2-cycles and biconnected-block split. See `docs/baseline_reductions.md`.
- **A candidate-rule framework**, isolated from the core. Rules state a pattern,
  preconditions, transformation, claimed identity and proof sketch. A bounded search
  classifies every case as pass, counterexample, inconclusive, precondition-invalid or
  malformed. Counterexamples are minimised and saved as JSON plus a readable explanation.
- **Generators**: exhaustive isomorphism classes, with counts checked against OEIS, and nine
  random families with seeds and limits.
- **Exploratory mining**: forced structures in exhaustive small-graph data, plus boundary
  functions of small separators.
- **A reproducible benchmark**, writing JSONL, CSV and Markdown.

It is a research tool. It has no external solver and uses only Python plus `pytest`, with
`networkx` used only in tests to cross-check graph algorithms.

## Install

```bash
python3.12 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt     # pytest==8.3.3, networkx==3.4.2 (tests only)
pip install -e .                        # provides the `fas` command
python -m pytest -q -m "not slow"       # fast suite; drop -m to include the slow tests
```

You need Python ≥ 3.11; the project was developed on 3.12.

## Command line

Graphs are read from JSON or from an edge list. The JSON form is
`{"vertices": [0, 1], "arcs": [[0, 1, 2], [1, 0]]}`, where the third entry is the
multiplicity and defaults to 1. An edge list has one `u v` per line, and repeated lines mean
multiplicity. Use `-` to read stdin.

| Command | What it does |
|---|---|
| `fas solve G` | Exact OPT, an optimal ordering and the removed arcs. Baseline reductions are on unless `--no-reduce`; `--json` gives machine-readable output. |
| `fas reduce G` | Apply the baseline reductions and print the kernel and offset. |
| `fas generate FAMILY --n N --count C --seed S --out DIR` | Write random graphs as JSON. |
| `fas candidates [NAME]` | List the candidate rules with their statuses, or print one rule's card. |
| `fas check NAME G` | Evaluate one candidate at every match in one graph. |
| `fas test-candidate NAME\|all --profile quick\|standard\|deep` | Bounded counterexample search. Writes `summary.json`, a minimised counterexample if one is found, and `index.json`. |
| `fas mine vertex\|arc\|boundary ...` | Exploratory mining over exhaustive small graphs (`docs/final_report.md` §5). |
| `fas benchmark --config experiments/benchmark_default.json --out results/benchmark` | Reproducible benchmark. |

Example:

```bash
printf '0 1\n1 0\n0 2\n2 0\n1 2\n' > /tmp/ex.txt
fas solve /tmp/ex.txt
# opt: 2
# removed_arcs: [[0, 1], [2, 0]]
# ordering: [1, 0, 2]
# method: dp+baseline
# verified: True
```

`experiments/run_all.sh` regenerates every file in `results/`. Set `DEEP=1` to add the deep
searches.

## Where to read next

| File | Content |
|---|---|
| `NEXT_STEPS.md` | Exact commands, what to read first, and the next mathematical question. |
| `docs/final_report.md` | What was built, test status, results, limitations and next steps. |
| `docs/adding_a_candidate.md` | **How to add and test a new rule**: a worked exercise. |
| `docs/problem_definition.md` | Conventions (self-loops, duplicates, empty graphs) and solver correctness. |
| `docs/baseline_reductions.md` | Proven baseline rules with sources. |
| `docs/candidate_rules.md` | Every candidate: card, search results, smallest counterexamples. |
| `docs/proof_obligations.md` | Full proofs and critical reviews behind each PROVED status. |
| `docs/research_notebook.md` | Dated log with statuses. |
| `docs/open_questions.md` | Open questions ranked by promise and tractability. |
| `docs/literature_review.md` | Literature with verification tags, plus this project's own prior-art searches. |

## Layout

```
src/fas/            graph.py exact_solver.py verify.py reductions.py generators.py
                    harness.py minimize.py mining.py boundary.py benchmark.py cli.py
src/fas/candidates/ base.py (interface) + one module per rule family; __init__.py is the registry
tests/              pytest suite (slow tests marked `slow`)
experiments/        benchmark configs, run_all.sh, mining summary, 4-terminal span experiment
results/            generated outputs (candidates/, candidates_deep/, candidates_uncapped/, mining/, benchmark/)
scripts/            sync_to_store.sh (project-specific copy to the shared store)
```

## Rules of the road

- A candidate's status changes to PROVED only with a written proof in
  `docs/proof_obligations.md`. A clean search is evidence, not proof.
- INCONCLUSIVE (a solver limit was hit) never counts as a pass. A search that stops at its time
  or graph limit, or has inconclusive cases, never gets the clean verdict.
- "Not found in the literature" is recorded as `NOVELTY_UNVERIFIED`, never as "new".

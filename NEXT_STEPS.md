# Next steps

## 1. Get running (about 5 minutes)

```bash
cd fas-platform
python3.12 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt && pip install -e .
python -m pytest -q -m "not slow"              # expect: all passed (about 17 s)
fas candidates                                 # the 11 rules and their statuses
fas solve - <<< $'0 1\n1 2\n2 0\n2 1'          # OPT 1: the shared counterexample graph
```

## 2. Read first, in this order

1. `docs/final_report.md` §1 and §7: what exists and what is known.
2. `docs/adding_a_candidate.md`: do the exercise. It takes about an hour and teaches the whole
   workflow.
3. `docs/problem_definition.md`: the ordering formulation every proof uses.
4. `docs/proof_obligations.md`, PO-4 and PO-5: the boundary-function method behind the next
   question.
5. `docs/open_questions.md`.

## 3. The next mathematical question

**Q1. Given the boundary function of an unweighted 2- or 3-terminal side, what is the smallest
unweighted simple digraph realising the same function up to a constant?**

**Why this question.**

- The proved separator rules (PO-4, PO-5) replace a side by a *weighted* gadget.
- Constant-size unweighted gadgets are impossible: sides with k parallel x→c→y paths are
  pairwise inequivalent (`open_questions.md`, Q1).
- A bound on gadget size in terms of `max f − min f` would give reductions that are both
  unweighted-closed and size-reducing.

**Start with 2 terminals.** There the function is just `(f_xy, f_yx)`. Guess and prove the
smallest unweighted gadget for `d = |f_xy − f_yx|`: is it `d` paths of length 2, or can
2-cycles do better? Then move to 3 terminals using `results/mining/boundary_3terminal.json`.

## 4. Exact commands for the planned work

```bash
# re-run everything (about 10 minutes; DEEP=1 adds about 30-60 minutes of deep searches)
./experiments/run_all.sh

# Q1 data: 3-terminal boundary functions for sides with <= 2 internal vertices
fas mine boundary --max-internal 2 --out results/mining/boundary_3terminal.json
#   then extend fas.mining.mine_boundary to record the smallest side per boundary function

# Q2 data: 4-terminal span (necessary condition) - already run, seed 0
python experiments/four_terminal_rank.py --samples 2000 --seed 0

# test a new rule (after following docs/adding_a_candidate.md)
fas test-candidate my_rule --profile quick --out results/candidates
fas test-candidate my_rule --profile standard --out results/candidates
fas test-candidate my_rule --profile deep --max-seconds 600 --out results/candidates_deep

# check one rule on one graph, e.g. a counterexample you want to understand
fas check arc_disjoint_cycle_bound results/candidates/arc_disjoint_cycle_bound/arc_disjoint_cycle_bound.json

# benchmark (about 15 minutes with the default config; experiments/benchmark_smoke.json takes seconds)
fas benchmark --config experiments/benchmark_default.json --out results/benchmark
```

## 5. Housekeeping still open

- Have a second person review PO-3, PO-4 and PO-5 (`docs/proof_obligations.md`, "Remaining
  obligations").
- Do the prior-art checks listed at the end of `docs/proof_obligations.md`. Do this before
  writing about any rule.
- `scripts/sync_to_store.sh` copies the tree to this project's shared store. It is
  project-specific and not needed for local work.

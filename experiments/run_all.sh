#!/usr/bin/env bash
# Reproduce every result under results/ (fixed seeds). Each step is bounded by
# its own time/size limits; outputs are JSON/CSV/Markdown.
# DEEP=1 also runs the deep-profile searches for the proved candidates (up to 10 min each).
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-python}
PROVED="two_cycle_local_bound two_cycle_cancellation module_contraction two_terminal_separator
three_terminal_gadget neighborhood_dominance in_degree_one_exchange arc_domination"
$PY -m pytest -q 2>&1 | tee results/test_log.txt
$PY -m fas test-candidate all --profile standard --seed 0 --out results/candidates
for r in two_terminal_separator three_terminal_gadget; do
  $PY -m fas test-candidate "$r" --profile standard --max-matches 100000 --max-seconds 900 --out results/candidates_uncapped
done
$PY -m fas mine vertex --kind digraph --n-min 3 --n-max 5 --falsify 40 --out results/mining/vertex_digraph_n3-5.json
$PY -m fas mine vertex --kind oriented --n-min 3 --n-max 6 --out results/mining/vertex_oriented_n3-6.json
$PY -m fas mine arc --kind digraph --n-min 3 --n-max 5 --falsify 40 --out results/mining/arc_digraph_n3-5.json
$PY -m fas mine boundary --max-internal 2 --out results/mining/boundary_3terminal.json
$PY experiments/summarize_mining.py results/mining results/mining/summary.md
$PY experiments/four_terminal_rank.py --samples 2000 --seed 0 --out results/mining/four_terminal_rank.json
$PY -m fas benchmark --config experiments/benchmark_default.json --out results/benchmark
if [[ "${DEEP:-0}" == "1" ]]; then
  for r in $PROVED; do
    $PY -m fas test-candidate "$r" --profile deep --max-seconds 600 --out results/candidates_deep
  done
fi

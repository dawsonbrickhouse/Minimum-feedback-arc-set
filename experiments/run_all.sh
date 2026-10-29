#!/usr/bin/env bash
# Reproduce every result under results/ (fixed seeds). Each step is bounded by
# its own time/size limits; outputs are JSON/CSV/Markdown.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-python}
$PY -m pytest -q 2>&1 | tee results/test_log.txt
$PY -m fas test-candidate all --profile standard --seed 0 --out results/candidates
$PY -m fas mine vertex --kind digraph --n-min 3 --n-max 5 --falsify 40 --out results/mining/vertex_digraph_n3-5.json
$PY -m fas mine vertex --kind oriented --n-min 3 --n-max 6 --out results/mining/vertex_oriented_n3-6.json
$PY -m fas mine arc --kind digraph --n-min 3 --n-max 5 --falsify 40 --out results/mining/arc_digraph_n3-5.json
$PY -m fas mine boundary --max-internal 2 --out results/mining/boundary_3terminal.json
$PY experiments/summarize_mining.py results/mining results/mining/summary.md
$PY -m fas benchmark --config experiments/benchmark_default.json --out results/benchmark

"""Reproducible benchmark of exact solving with and without reductions.

Pipelines
---------
``plain``                       subset DP on the whole graph (no decomposition).
``scc``                         SCC decomposition + DP per SCC.
``baseline``                    baseline rules to a fixpoint, SCC + block split, DP per piece.
``baseline+<candidate>``        as ``baseline``, interleaved with a *proved* candidate rule
                                applied at matches that shrink the instance (see ``_shrinks``).

Correctness is checked on every instance (all completed pipelines must agree on OPT
and every returned FAS is re-verified), but correctness *testing* lives in the
test-suite; this module measures size reduction and time. Wall-clock time is the
median over ``trials`` runs; peak memory (Python allocations via ``tracemalloc``)
is measured in a separate run because tracing slows execution.
"""

from __future__ import annotations

import csv
import json
import platform
import statistics
import time
import tracemalloc
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .candidates import Oracle, Status, get_rule
from .exact_solver import SolverLimitError, solve_dp, solve_exact
from .generators import random_family
from .graph import Arc, Graph, strongly_connected_components
from .reductions import reduce_graph
from .verify import verify_removed_set

ALLOWED_STATUS = Status.PROVED_WITHIN_STATED_ASSUMPTIONS


@dataclass
class PipelineResult:
    opt: int
    removed: frozenset[Arc]
    kernel_n: int
    kernel_m: int
    pieces: list[int]
    applications: int = 0


def _max_piece(g: Graph) -> int:
    red = reduce_graph(g)
    return max((p.n for p in red.pieces()), default=0)


def _shrinks(before: Graph, after: Graph) -> bool:
    """Accept a candidate application if it lowers (largest piece, total arc weight)."""
    return (_max_piece(after), after.m) < (_max_piece(before), before.m)


def _solve_baseline(g: Graph, max_component: int) -> PipelineResult:
    red = reduce_graph(g)
    removed: set[Arc] = set()
    for piece in red.pieces():
        removed |= solve_exact(piece, max_component_size=max_component).removed_arcs
    lifted = red.lift(removed)
    return PipelineResult(g.arc_weight(lifted), lifted, red.kernel.n, red.kernel.m,
                          sorted((p.n for p in red.pieces()), reverse=True))


def _solve_with_candidate(g: Graph, name: str, max_component: int, max_applications: int) -> PipelineResult:
    rule = get_rule(name)
    if ALLOWED_STATUS not in rule.statuses:
        raise ValueError(f"{name} is not proved; benchmarks only use proved candidates")
    oracle = Oracle(max_component)
    lifts: list[Callable[[frozenset[Arc]], frozenset[Arc]]] = []
    offset = 0
    current = reduce_graph(g).kernel
    applications = 0
    progress = True
    while progress and applications < max_applications:
        progress = False
        for match in rule.find_matches(current):
            app = rule.apply(current, match, oracle)
            if _shrinks(current, app.reduced):
                if app.lift is None:
                    raise ValueError(f"{name} has no lift; cannot reconstruct solutions")
                lifts.append(app.lift)
                offset += app.correction
                current = app.reduced
                applications += 1
                progress = True
                break
    inner = _solve_baseline(current, max_component)
    removed = inner.removed
    for lift in reversed(lifts):
        removed = lift(removed)
    removed = reduce_graph(g).lift(removed)
    return PipelineResult(g.arc_weight(removed), removed, inner.kernel_n, inner.kernel_m, inner.pieces, applications)


def run_pipeline(g: Graph, pipeline: str, cfg: dict[str, Any]) -> PipelineResult:
    max_component = cfg.get("max_component", 18)
    if pipeline == "plain":
        if g.n > cfg.get("plain_max_n", 16):
            raise SolverLimitError(f"plain DP limited to n <= {cfg.get('plain_max_n', 16)}")
        res = solve_dp(g, max_vertices=cfg.get("plain_max_n", 16))
        return PipelineResult(res.cost, res.removed_arcs, g.n, g.m, [g.n])
    if pipeline == "scc":
        res = solve_exact(g, max_component_size=max_component)
        sizes = sorted((len(c) for c in strongly_connected_components(g) if len(c) > 1), reverse=True)
        return PipelineResult(res.cost, res.removed_arcs, g.n, g.m, sizes)
    if pipeline == "baseline":
        return _solve_baseline(g, max_component)
    if pipeline.startswith("baseline+"):
        return _solve_with_candidate(g, pipeline.split("+", 1)[1], max_component, cfg.get("max_applications", 200))
    raise ValueError(f"unknown pipeline {pipeline!r}")


def _measure(g: Graph, pipeline: str, cfg: dict[str, Any]) -> dict[str, Any]:
    times = []
    result: PipelineResult | None = None
    try:
        for _ in range(cfg.get("trials", 3)):
            t0 = time.perf_counter()
            result = run_pipeline(g, pipeline, cfg)
            times.append(time.perf_counter() - t0)
    except SolverLimitError as exc:
        return {"completed": False, "reason": str(exc)}
    assert result is not None
    row: dict[str, Any] = {
        "completed": True,
        "opt": result.opt,
        "seconds_median": round(statistics.median(times), 6),
        "seconds_all": [round(t, 6) for t in times],
        "kernel_n": result.kernel_n,
        "kernel_m": result.kernel_m,
        "piece_sizes": result.pieces,
        "largest_piece": max(result.pieces, default=0),
        "candidate_applications": result.applications,
        "solution_valid": verify_removed_set(g, result.removed, expected_cost=result.opt).ok,
    }
    if cfg.get("measure_memory", True):
        tracemalloc.start()
        run_pipeline(g, pipeline, cfg)
        row["peak_python_alloc_kib"] = round(tracemalloc.get_traced_memory()[1] / 1024, 1)
        tracemalloc.stop()
    return row


def run_benchmark(cfg: dict[str, Any], progress: Callable[[str], None] | None = print,
                  on_rows: Callable[[list[dict[str, Any]]], None] | None = None) -> list[dict[str, Any]]:
    """Run every (family, n, instance, pipeline); ``on_rows`` receives each instance's rows as a checkpoint."""
    validate_config(cfg)
    rows: list[dict[str, Any]] = []
    for setting in cfg["settings"]:
        family, count = setting["family"], setting.get("count", cfg.get("count", 5))
        for n in setting["n"]:
            for idx, g in enumerate(random_family(family, n, count, seed=cfg["seed"])):
                per_pipeline = {p: _measure(g, p, cfg) for p in cfg["pipelines"]}
                opts = {r["opt"] for r in per_pipeline.values() if r["completed"]}
                batch = [{"family": family, "n": n, "instance": idx, "seed": cfg["seed"], "graph_n": g.n,
                          "graph_m": g.m, "pipeline": pipeline, "opt_agree": len(opts) <= 1, **r}
                         for pipeline, r in per_pipeline.items()]
                rows.extend(batch)
                if on_rows:
                    on_rows(batch)
                if progress:
                    progress(f"{family} n={n} #{idx}: " + ", ".join(
                        f"{p}={r.get('seconds_median', 'skip')}" for p, r in per_pipeline.items()))
    return rows


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple, list[dict[str, Any]]] = {}
    for r in rows:
        groups.setdefault((r["family"], r["n"], r["pipeline"]), []).append(r)
    out = []
    for (family, n, pipeline), rs in groups.items():
        done = [r for r in rs if r["completed"]]
        out.append({
            "family": family, "n": n, "pipeline": pipeline, "instances": len(rs), "completed": len(done),
            "median_seconds": round(statistics.median(r["seconds_median"] for r in done), 5) if done else None,
            "max_seconds": round(max(r["seconds_median"] for r in done), 5) if done else None,
            "mean_kernel_n": round(statistics.mean(r["kernel_n"] for r in done), 2) if done else None,
            "mean_kernel_m": round(statistics.mean(r["kernel_m"] for r in done), 2) if done else None,
            "mean_largest_piece": round(statistics.mean(r["largest_piece"] for r in done), 2) if done else None,
            "max_largest_piece": max((r["largest_piece"] for r in done), default=None),
            "median_peak_kib": (round(statistics.median(r["peak_python_alloc_kib"] for r in done), 1)
                                if done and "peak_python_alloc_kib" in done[0] else None),
            "all_valid": all(r["solution_valid"] for r in done) if done else None,
            "all_agree": all(r["opt_agree"] for r in done) if done else None,
        })
    return out


def load_config(path: Path) -> dict[str, Any]:
    cfg = json.loads(path.read_text())
    validate_config(cfg)
    return cfg


def validate_config(cfg: dict[str, Any]) -> None:
    """Fail before any work if a family, size or pipeline is invalid (generators check limits lazily)."""
    for setting in cfg["settings"]:
        for n in setting["n"]:
            for _ in random_family(setting["family"], n, 0, seed=cfg["seed"]):
                pass
    for pipeline in cfg["pipelines"]:
        if pipeline.startswith("baseline+"):
            rule = get_rule(pipeline.split("+", 1)[1])
            if ALLOWED_STATUS not in rule.statuses:
                raise ValueError(f"{rule.name} is not proved; benchmarks only use proved candidates")
        elif pipeline not in ("plain", "scc", "baseline"):
            raise ValueError(f"unknown pipeline {pipeline!r}")


def write_outputs(rows: list[dict[str, Any]], out_dir: Path, cfg: dict[str, Any]) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    name = cfg.get("name", "benchmark")
    raw = out_dir / f"{name}_raw.jsonl"
    raw.write_text("".join(json.dumps(r) + "\n" for r in rows))
    summary = summarize(rows)
    csv_path = out_dir / f"{name}_summary.csv"
    with csv_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)
    meta = out_dir / f"{name}_meta.json"
    meta.write_text(json.dumps({"config": cfg, "python": platform.python_version(),
                                "machine": platform.machine(), "platform": platform.platform()}, indent=1))
    md = out_dir / f"{name}_summary.md"
    cols = ["family", "n", "pipeline", "instances", "completed", "median_seconds", "mean_kernel_n",
            "mean_largest_piece", "max_largest_piece", "median_peak_kib", "all_valid", "all_agree"]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(str(s[c]) for c in cols) + " |" for s in summary]
    md.write_text("\n".join(lines) + "\n")
    return [raw, csv_path, md, meta]

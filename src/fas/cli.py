"""Command-line interface: ``python -m fas <command>`` (or ``fas <command>`` once installed).

Run ``python -m fas --help`` or ``python -m fas <command> --help`` for details.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

from .candidates import REGISTRY, Oracle, get_rule
from .exact_solver import SolverLimitError, solve_exact
from .generators import FAMILIES, random_family
from .graph import Graph, GraphError
from .harness import PROFILES, evaluate_graph, run_search
from .minimize import minimize_counterexample, save_counterexample
from .reductions import BASELINE_RULES, reduce_graph, solve_with_reductions
from .verify import verify_result


def load_graph(path: str) -> Graph:
    """Read a graph from JSON (``{"vertices": [...], "arcs": [[u, v], [u, v, k], ...]}``)
    or from an edge list (``u v [multiplicity]`` per line)."""
    text = sys.stdin.read() if path == "-" else Path(path).read_text()
    stripped = text.lstrip()
    return Graph.from_json(text) if stripped.startswith("{") else Graph.from_edge_list(text)


def _print(obj: object, as_json: bool) -> None:
    if as_json:
        print(json.dumps(obj, indent=1))
    else:
        for k, v in obj.items():  # type: ignore[union-attr]
            print(f"{k}: {v}")


# ---------------------------------------------------------------------- commands


def cmd_solve(args: argparse.Namespace) -> int:
    g = load_graph(args.graph)
    if args.no_reduce:
        res = solve_exact(g, method=args.method, max_component_size=args.max_component)
        info: dict = {}
    else:
        res, red = solve_with_reductions(g, method=args.method, max_component_size=args.max_component)
        info = red.summary()
    report = verify_result(g, res)
    out = {"opt": res.cost, "removed_arcs": sorted(map(list, res.removed_arcs)), "ordering": list(res.ordering),
           "method": res.method, "verified": report.ok, **({"reduction": info} if info else {})}
    _print(out, args.json)
    return 0 if report.ok else 2


def cmd_reduce(args: argparse.Namespace) -> int:
    g = load_graph(args.graph)
    red = reduce_graph(g, args.rules or BASELINE_RULES)
    out = red.summary()
    out["kernel"] = red.kernel.to_dict()
    if args.steps:
        out["steps"] = [s.describe() for s in red.steps]
    _print(out, args.json)
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, g in enumerate(random_family(args.family, args.n, args.count, args.seed)):
        (out_dir / f"{args.family}_n{args.n}_s{args.seed}_{i:04d}.json").write_text(g.to_json())
    print(f"wrote {args.count} graphs to {out_dir}")
    return 0


def cmd_candidates(args: argparse.Namespace) -> int:
    if args.name:
        print(json.dumps(get_rule(args.name).card(), indent=1))
        return 0
    for name, rule in REGISTRY.items():
        print(f"{name:28s} [{', '.join(s.value for s in rule.statuses)}]  {rule.title}")
    return 0


def _run_one(name: str, args: argparse.Namespace) -> dict:
    rule = get_rule(name)
    cfg = replace(PROFILES[args.profile], seed=args.seed)
    if args.max_seconds is not None:
        cfg = replace(cfg, max_seconds=args.max_seconds)
    out_dir = Path(args.out) / name
    summary = run_search(rule, cfg, checkpoint=out_dir / "summary.json")
    record = summary.to_dict()
    if summary.first_counterexample and not args.no_minimize:
        g = Graph.from_dict(summary.first_counterexample["graph"])
        oracle = Oracle(cfg.max_component_size)
        res = minimize_counterexample(rule, g, oracle)
        path = save_counterexample(rule, res, out_dir, oracle)
        record["minimized_counterexample"] = str(path)
        record["minimized_size"] = {"n": res.minimized.n, "m": res.minimized.m}
    (out_dir / "summary.json").write_text(json.dumps(record, indent=1))
    return record


def cmd_test_candidate(args: argparse.Namespace) -> int:
    names = sorted(REGISTRY) if args.name == "all" else [args.name]
    rows = []
    for name in names:
        rec = _run_one(name, args)
        rows.append(rec)
        extra = f" minimized n={rec['minimized_size']['n']} m={rec['minimized_size']['m']}" if "minimized_size" in rec else ""
        print(f"{name:28s} {rec['verdict']:34s} {rec['outcome_counts']} graphs={rec['graphs_examined']} "
              f"({rec['stopped_reason']}, {rec['elapsed_seconds']}s){extra}", flush=True)
    _update_index(Path(args.out) / "index.json", rows, args.profile)
    return 0


def _update_index(index: Path, rows: list[dict], profile: str) -> None:
    """Merge ``rows`` into the index, replacing earlier entries for the same rule."""
    entries = {e["rule"]: e for e in json.loads(index.read_text())} if index.exists() else {}
    for r in rows:
        entry = {k: r[k] for k in ("rule", "verdict", "outcome_counts", "graphs_examined",
                                   "stopped_reason", "elapsed_seconds")}
        entry["profile"] = profile
        if "minimized_size" in r:
            entry["minimized_size"] = r["minimized_size"]
        entries[r["rule"]] = entry
    index.write_text(json.dumps([entries[k] for k in sorted(entries)], indent=1))


def cmd_check(args: argparse.Namespace) -> int:
    """Evaluate one candidate on one graph file (all matches)."""
    g, rule = load_graph(args.graph), get_rule(args.name)
    for case in evaluate_graph(rule, g, Oracle(args.max_component)):
        d = case.to_dict()
        print(json.dumps({k: d[k] for k in ("outcome", "match", "opt_original", "opt_reduced", "correction",
                                             "failure_kind", "message")}))
    return 0


def cmd_mine(args: argparse.Namespace) -> int:
    from . import mining

    oracle = Oracle()
    n_values = tuple(range(args.n_min, args.n_max + 1))
    if args.analysis == "vertex":
        result = mining.mine_vertex_forcing(args.kind, n_values, oracle)
    elif args.analysis == "arc":
        result = mining.mine_arc_status(args.kind, n_values, oracle)
    else:
        result = mining.mine_boundary(args.max_internal, oracle)
    if args.falsify and args.analysis in ("vertex", "arc"):
        graphs = [g for fam in ("sparse", "dense", "planted", "overlapping_cycles", "multigraph")
                  for n in range(args.n_max + 1, args.n_max + 4)
                  for g in random_family(fam, n, args.falsify, seed=args.seed)]
        fn = mining.falsify_vertex_signatures if args.analysis == "vertex" else mining.falsify_arc_signatures
        result["falsification"] = {"graphs": len(graphs), "seed": args.seed, "hypotheses": fn(result, graphs, oracle)}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1))
    print(f"wrote {out}")
    return 0


def cmd_benchmark(args: argparse.Namespace) -> int:
    from .benchmark import load_config, run_benchmark, write_outputs

    config = load_config(Path(args.config))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    partial = out / f"{config.get('name', 'benchmark')}_partial.jsonl"
    with partial.open("w") as fh:
        def checkpoint(batch: list[dict]) -> None:
            fh.writelines(json.dumps(r) + "\n" for r in batch)
            fh.flush()

        rows = run_benchmark(config, progress=lambda s: print(s, flush=True), on_rows=checkpoint)
    paths = write_outputs(rows, out, config)
    partial.unlink()
    print("wrote " + ", ".join(str(p) for p in paths))
    return 0


# ---------------------------------------------------------------------- parser


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="fas", description="Minimum feedback arc set research platform")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("solve", help="exact OPT of a graph file (JSON or edge list, '-' for stdin)")
    s.add_argument("graph")
    s.add_argument("--method", choices=["dp", "brute"], default="dp")
    s.add_argument("--no-reduce", action="store_true", help="skip baseline reductions (SCC split still used)")
    s.add_argument("--max-component", type=int, default=None, help="largest SCC/block the exact solver accepts")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_solve)

    s = sub.add_parser("reduce", help="apply baseline reductions and print the kernel")
    s.add_argument("graph")
    s.add_argument("--rules", nargs="*", choices=BASELINE_RULES)
    s.add_argument("--steps", action="store_true", help="list every applied step")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_reduce)

    s = sub.add_parser("generate", help="write random graphs of a family as JSON files")
    s.add_argument("family", choices=sorted(FAMILIES))
    s.add_argument("--n", type=int, required=True)
    s.add_argument("--count", type=int, default=10)
    s.add_argument("--seed", type=int, default=0)
    s.add_argument("--out", default="results/scratch/graphs")
    s.set_defaults(func=cmd_generate)

    s = sub.add_parser("candidates", help="list candidate rules, or show one rule's card")
    s.add_argument("name", nargs="?")
    s.set_defaults(func=cmd_candidates)

    s = sub.add_parser("test-candidate", help="bounded counterexample search for a rule ('all' for every rule)")
    s.add_argument("name")
    s.add_argument("--profile", choices=sorted(PROFILES), default="standard")
    s.add_argument("--seed", type=int, default=0)
    s.add_argument("--max-seconds", type=float, default=None)
    s.add_argument("--no-minimize", action="store_true")
    s.add_argument("--out", default="results/candidates")
    s.set_defaults(func=cmd_test_candidate)

    s = sub.add_parser("check", help="evaluate one candidate on one graph file")
    s.add_argument("name")
    s.add_argument("graph")
    s.add_argument("--max-component", type=int, default=14)
    s.set_defaults(func=cmd_check)

    s = sub.add_parser("mine", help="exploratory mining of exhaustive small-graph data")
    s.add_argument("analysis", choices=["vertex", "arc", "boundary"])
    s.add_argument("--kind", choices=["digraph", "oriented", "tournament"], default="digraph")
    s.add_argument("--n-min", type=int, default=3)
    s.add_argument("--n-max", type=int, default=5)
    s.add_argument("--max-internal", type=int, default=2, help="boundary: internal vertices per side")
    s.add_argument("--falsify", type=int, default=0, help="re-test mined hypotheses on this many random graphs per family and size")
    s.add_argument("--seed", type=int, default=0)
    s.add_argument("--out", required=True)
    s.set_defaults(func=cmd_mine)

    s = sub.add_parser("benchmark", help="run a benchmark configuration (JSON)")
    s.add_argument("--config", default="experiments/benchmark_default.json")
    s.add_argument("--out", default="results/benchmark")
    s.set_defaults(func=cmd_benchmark)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (GraphError, SolverLimitError, KeyError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

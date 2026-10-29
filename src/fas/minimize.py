"""Greedy counterexample minimisation and reproducible counterexample reports.

Starting from a verified counterexample, repeatedly try (in a fixed order)
deleting a vertex, deleting an arc pair, and lowering a multiplicity, keeping
any change after which *some* match of the rule still yields a verified
counterexample (preconditions are re-checked by the harness on every attempt).
The result is 1-minimal with respect to these operations, not necessarily a
globally smallest counterexample.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from .candidates.base import CandidateRule, Oracle
from .harness import CaseResult, Outcome, evaluate_graph, evaluate_match
from .graph import Graph


@dataclass
class MinimizationResult:
    rule: str
    original: Graph
    minimized: Graph
    case: CaseResult
    attempts: int
    accepted: list[str] = field(default_factory=list)


def _first_counterexample(rule: CandidateRule, g: Graph, oracle: Oracle) -> CaseResult | None:
    for case in evaluate_graph(rule, g, oracle):
        if case.outcome is Outcome.COUNTEREXAMPLE:
            return case
    return None


def _shrink_moves(g: Graph) -> Iterator[tuple[str, Graph]]:
    for v in g.vertices:
        yield f"delete vertex {v}", g.remove_vertices([v])
    for (u, v), _ in g.arcs():
        yield f"delete arc {u}->{v}", g.remove_arc_pairs([(u, v)])
    for (u, v), k in g.arcs():
        if k > 1:
            yield f"lower {u}->{v} to x{k - 1}", g.with_multiplicity(u, v, k - 1)


def minimize_counterexample(
    rule: CandidateRule, g: Graph, oracle: Oracle | None = None, max_attempts: int = 20_000,
) -> MinimizationResult:
    oracle = oracle or Oracle()
    case = _first_counterexample(rule, g, oracle)
    if case is None:
        raise ValueError("graph is not a counterexample for this rule")
    current, attempts, accepted = g, 0, []
    improved = True
    while improved and attempts < max_attempts:
        improved = False
        for label, candidate in _shrink_moves(current):
            attempts += 1
            found = _first_counterexample(rule, candidate, oracle)
            if found is not None:
                current, case, improved = candidate, found, True
                accepted.append(label)
                break
            if attempts >= max_attempts:
                break
    compact, mapping = current.compact()
    final = _first_counterexample(rule, compact, oracle)
    if final is None:  # relabelling cannot change validity; fall back defensively
        compact, final = current, case
    accepted.append(f"relabel {mapping}")
    return MinimizationResult(rule.name, g, compact, final, attempts, accepted)


def _arcs_text(g: Graph) -> str:
    return ", ".join(f"{u}->{v}" + (f" (x{k})" if k > 1 else "") for (u, v), k in g.arcs()) or "(none)"


def counterexample_report(rule: CandidateRule, res: MinimizationResult, oracle: Oracle | None = None) -> tuple[dict, str]:
    """Machine-readable record plus a human-readable explanation."""
    oracle = oracle or Oracle()
    case = res.case
    g, gr = case.graph, case.reduced
    assert gr is not None and case.match is not None
    sol_g, sol_r = oracle.solve(g), oracle.solve(gr)
    replay = evaluate_match(rule, g, case.match, oracle)
    record = {
        "rule": rule.name,
        "claimed_identity": rule.claimed_identity,
        "original_graph": res.original.to_dict(),
        "minimized_graph": g.to_dict(),
        "match": case.match,
        "reduced_graph": gr.to_dict(),
        "opt_original": sol_g.cost,
        "opt_reduced": sol_r.cost,
        "claimed_correction": case.correction,
        "discrepancy": case.discrepancy,
        "failure_kind": case.failure_kind,
        "witness_optimal_solution_original": sol_g.to_dict(),
        "witness_optimal_solution_reduced": sol_r.to_dict(),
        "preconditions_explanation": rule.explain_preconditions(g, case.match),
        "replay_outcome": replay.outcome.value,
        "minimization_steps": res.accepted,
        "minimization_attempts": res.attempts,
    }
    text = f"""# Counterexample: `{rule.name}`

**Claim:** {rule.claimed_identity}

**Minimised graph G** (n={g.n}, m={g.m}): {_arcs_text(g)}

**Match:** `{json.dumps(case.match)}`

**Why the preconditions hold:** {record['preconditions_explanation']}

**Reduced graph G'** (n={gr.n}, m={gr.m}): {_arcs_text(gr)}

| quantity | value |
|---|---|
| OPT(G) | {sol_g.cost} (optimal FAS: {sorted(sol_g.removed_arcs)}) |
| OPT(G') | {sol_r.cost} (optimal FAS: {sorted(sol_r.removed_arcs)}) |
| claimed correction | {case.correction} |
| OPT(G') + correction | {sol_r.cost + (case.correction or 0)} |
| discrepancy OPT(G) - (OPT(G') + c) | {case.discrepancy} |
| failure kind | {case.failure_kind} |

Replaying the match on the saved graph gives outcome **{replay.outcome.value}**.
Original (unminimised) graph: {_arcs_text(res.original)}.
Minimisation: {res.attempts} attempts; accepted moves: {'; '.join(res.accepted)}.
"""
    return record, text


def save_counterexample(rule: CandidateRule, res: MinimizationResult, out_dir: Path, oracle: Oracle | None = None) -> Path:
    record, text = counterexample_report(rule, res, oracle)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{rule.name}.json").write_text(json.dumps(record, indent=1))
    (out_dir / f"{rule.name}.md").write_text(text)
    return out_dir / f"{rule.name}.json"

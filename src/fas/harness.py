"""Test harness for candidate reduction rules.

Outcomes are kept strictly apart:

* ``pass``                  identity held and (if provided) the lift was optimal.
* ``counterexample``        a *verified* violation: both OPT values were computed
                            exactly, the preconditions were re-checked, and the
                            identity (or the lift) failed.
* ``inconclusive``          an exact computation hit a solver limit. Never a pass.
* ``precondition_invalid``  the rule reported a match that its own independent
                            precondition check rejects (a bug in the rule code),
                            or a targeted generator produced no valid match.
* ``malformed``             the rule raised, or returned something that is not a
                            graph / integer correction / arc set of ``G``.
"""

from __future__ import annotations

import json
import random
import time
import traceback
from collections import Counter
from collections.abc import Iterator
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .candidates.base import Application, CandidateRule, Match, Oracle
from .exact_solver import SolverLimitError
from .generators import isomorphism_classes, random_family
from .graph import Graph, GraphError
from .verify import verify_removed_set


class Outcome(str, Enum):
    PASS = "pass"
    COUNTEREXAMPLE = "counterexample"
    INCONCLUSIVE = "inconclusive"
    PRECONDITION_INVALID = "precondition_invalid"
    MALFORMED = "malformed"


@dataclass
class CaseResult:
    rule: str
    outcome: Outcome
    graph: Graph
    match: Match | None
    opt_original: int | None = None
    opt_reduced: int | None = None
    correction: int | None = None
    reduced: Graph | None = None
    failure_kind: str = ""  # "identity" or "lift" for counterexamples
    message: str = ""

    @property
    def discrepancy(self) -> int | None:
        if None in (self.opt_original, self.opt_reduced, self.correction):
            return None
        return self.opt_original - (self.opt_reduced + self.correction)  # type: ignore[operator]

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule": self.rule,
            "outcome": self.outcome.value,
            "graph": self.graph.to_dict(),
            "match": self.match,
            "opt_original": self.opt_original,
            "opt_reduced": self.opt_reduced,
            "correction": self.correction,
            "discrepancy": self.discrepancy,
            "reduced": self.reduced.to_dict() if self.reduced is not None else None,
            "failure_kind": self.failure_kind,
            "message": self.message,
        }


def evaluate_match(rule: CandidateRule, g: Graph, match: Match, oracle: Oracle) -> CaseResult:
    """Check the claimed identity (and lift) of ``rule`` at one match of ``g``."""
    case = CaseResult(rule.name, Outcome.MALFORMED, g, match)
    try:
        reason = rule.check_preconditions(g, match)
    except Exception:  # noqa: BLE001 - any rule bug must surface as MALFORMED
        case.message = "check_preconditions raised:\n" + traceback.format_exc()
        return case
    if reason is not None:
        case.outcome = Outcome.PRECONDITION_INVALID
        case.message = reason
        return case
    try:
        app = rule.apply(g, match, oracle)
    except SolverLimitError as exc:
        case.outcome, case.message = Outcome.INCONCLUSIVE, f"apply: {exc}"
        return case
    except Exception:  # noqa: BLE001
        case.message = "apply raised:\n" + traceback.format_exc()
        return case
    if not isinstance(app, Application) or not isinstance(app.reduced, Graph) or not isinstance(app.correction, int):
        case.message = f"apply returned {app!r}; expected Application(Graph, int, ...)"
        return case
    case.reduced, case.correction = app.reduced, app.correction
    try:
        sol_g = oracle.solve(g)
        sol_r = oracle.solve(app.reduced)
    except SolverLimitError as exc:
        case.outcome, case.message = Outcome.INCONCLUSIVE, str(exc)
        return case
    case.opt_original, case.opt_reduced = sol_g.cost, sol_r.cost
    if sol_g.cost != sol_r.cost + app.correction:
        case.outcome, case.failure_kind = Outcome.COUNTEREXAMPLE, "identity"
        case.message = (f"OPT(G)={sol_g.cost} but OPT(G')+correction={sol_r.cost}+{app.correction}"
                        f"={sol_r.cost + app.correction}")
        return case
    if app.lift is not None:
        try:
            lifted = app.lift(sol_r.removed_arcs)
        except SolverLimitError as exc:
            case.outcome, case.message = Outcome.INCONCLUSIVE, f"lift: {exc}"
            return case
        except Exception:  # noqa: BLE001
            case.message = "lift raised:\n" + traceback.format_exc()
            return case
        report = verify_removed_set(g, lifted, expected_cost=sol_g.cost)
        if not report.ok:
            unknown = [a for a in lifted if not g.has_arc(*a)]
            case.outcome = Outcome.MALFORMED if unknown else Outcome.COUNTEREXAMPLE
            case.failure_kind = "lift"
            case.message = "lifted solution invalid: " + "; ".join(report.problems)
            return case
    case.outcome = Outcome.PASS
    return case


def evaluate_graph(rule: CandidateRule, g: Graph, oracle: Oracle) -> list[CaseResult]:
    """Evaluate every match of ``rule`` in ``g`` (empty list: rule not applicable)."""
    try:
        matches = rule.find_matches(g)
    except Exception:  # noqa: BLE001
        return [CaseResult(rule.name, Outcome.MALFORMED, g, None,
                           message="find_matches raised:\n" + traceback.format_exc())]
    return [evaluate_match(rule, g, m, oracle) for m in matches]


# ---------------------------------------------------------------------- search driver


@dataclass
class SearchConfig:
    """Bounded search plan. Every source is finite; ``max_seconds`` and
    ``max_graphs`` cap the whole run."""

    exhaustive: list[tuple[str, int]] = field(default_factory=lambda: [("digraph", n) for n in range(1, 6)])
    random_families: list[tuple[str, int, int]] = field(default_factory=lambda: [
        ("sparse", 8, 150), ("dense", 7, 150), ("multigraph", 6, 150), ("planted", 9, 100),
        ("scc_dag", 10, 60), ("overlapping_cycles", 8, 40), ("tournament", 7, 100),
    ])
    targeted: list[tuple[int, int]] = field(default_factory=lambda: [(6, 200), (9, 100)])
    seed: int = 0
    max_seconds: float = 300.0
    max_graphs: int = 200_000
    max_component_size: int = 14
    stop_at_first_counterexample: bool = True
    max_matches_per_graph: int = 64


@dataclass
class SearchSummary:
    rule: str
    config: dict[str, Any]
    outcome_counts: dict[str, int]
    graphs_examined: int
    graphs_with_matches: int
    per_source: dict[str, dict[str, int]]
    elapsed_seconds: float
    stopped_reason: str
    first_counterexample: dict[str, Any] | None = None
    first_inconclusive: dict[str, Any] | None = None
    first_invalid: dict[str, Any] | None = None

    @property
    def verdict(self) -> str:
        c = self.outcome_counts
        if c.get("counterexample"):
            return "COUNTEREXAMPLE_FOUND"
        if c.get("malformed") or c.get("precondition_invalid"):
            return "RULE_BUG"
        if not c.get("pass"):
            return "NO_EVIDENCE"
        return "NO_COUNTEREXAMPLE_IN_SEARCH_SPACE"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["verdict"] = self.verdict
        return d


def _sources(rule: CandidateRule, cfg: SearchConfig) -> Iterator[tuple[str, Graph | None]]:
    for kind, n in cfg.exhaustive:
        if kind not in rule.exhaustive_kinds and kind != "digraph":
            continue
        for g in isomorphism_classes(n, kind):  # type: ignore[arg-type]
            yield f"exhaustive:{kind}:n={n}", g
    for family, n, count in cfg.random_families:
        for g in random_family(family, n, count, seed=cfg.seed):
            yield f"random:{family}:n={n}", g
    rng = random.Random(f"targeted:{rule.name}:{cfg.seed}")
    for n, count in cfg.targeted:
        for _ in range(count):
            yield f"targeted:n={n}", rule.generate(rng, n)


def run_search(rule: CandidateRule, cfg: SearchConfig, checkpoint: Path | None = None) -> SearchSummary:
    """Run the bounded search; stops at the first verified counterexample if configured."""
    oracle = Oracle(cfg.max_component_size)
    counts: Counter[str] = Counter()
    per_source: dict[str, Counter[str]] = {}
    examined = with_matches = 0
    first: dict[str, dict[str, Any] | None] = {"cx": None, "inc": None, "inv": None}
    start = time.monotonic()
    stopped = "exhausted all sources"
    for source, g in _sources(rule, cfg):
        if g is None:
            if source.startswith("targeted"):
                break  # rule has no targeted generator
            continue
        if time.monotonic() - start > cfg.max_seconds:
            stopped = f"time limit {cfg.max_seconds}s"
            break
        if examined >= cfg.max_graphs:
            stopped = f"graph limit {cfg.max_graphs}"
            break
        examined += 1
        src_counts = per_source.setdefault(source, Counter())
        src_counts["graphs"] += 1
        results = evaluate_graph(rule, g, oracle)[: cfg.max_matches_per_graph]
        if source.startswith("targeted") and not results:
            results = [CaseResult(rule.name, Outcome.PRECONDITION_INVALID, g, None,
                                  message="targeted generator produced a graph without matches")]
        if results:
            with_matches += 1
        for case in results:
            counts[case.outcome.value] += 1
            src_counts[case.outcome.value] += 1
            key = {"counterexample": "cx", "inconclusive": "inc",
                   "precondition_invalid": "inv", "malformed": "inv"}.get(case.outcome.value)
            if key and first[key] is None:
                first[key] = {"source": source, **case.to_dict()}
        if checkpoint is not None and examined % 2000 == 0:
            _write_checkpoint(checkpoint, rule, counts, examined, time.monotonic() - start)
        if first["cx"] is not None and cfg.stop_at_first_counterexample:
            stopped = "first counterexample"
            break
    summary = SearchSummary(
        rule=rule.name,
        config=asdict(cfg),
        outcome_counts=dict(counts),
        graphs_examined=examined,
        graphs_with_matches=with_matches,
        per_source={k: dict(v) for k, v in per_source.items()},
        elapsed_seconds=round(time.monotonic() - start, 3),
        stopped_reason=stopped,
        first_counterexample=first["cx"],
        first_inconclusive=first["inc"],
        first_invalid=first["inv"],
    )
    if checkpoint is not None:
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        checkpoint.write_text(json.dumps(summary.to_dict(), indent=1))
    return summary


def _write_checkpoint(path: Path, rule: CandidateRule, counts: Counter[str], examined: int, elapsed: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"rule": rule.name, "partial": True, "graphs_examined": examined,
                                "outcome_counts": dict(counts), "elapsed_seconds": round(elapsed, 3)}, indent=1))


def case_from_dict(data: dict[str, Any]) -> tuple[Graph, Match]:
    """Recover (graph, match) from a saved case, e.g. to replay a counterexample."""
    try:
        return Graph.from_dict(data["graph"]), data["match"]
    except (KeyError, GraphError) as exc:
        raise ValueError(f"not a saved case: {exc}") from exc

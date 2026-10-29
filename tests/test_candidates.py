"""Candidate framework: outcome classification, registered rules, minimisation."""

import json
import random

import pytest

from fas.candidates import REGISTRY, Application, CandidateRule, Oracle, Status, get_rule
from fas.generators import isomorphism_classes, random_multigraph
from fas.graph import Graph
from fas.harness import (
    Outcome,
    SearchConfig,
    evaluate_graph,
    evaluate_graph_limited,
    evaluate_match,
    run_search,
)
from fas.minimize import counterexample_report, minimize_counterexample, save_counterexample

TRUE_RULES = sorted(n for n, r in REGISTRY.items() if r.expected == "true")
FALSE_RULES = sorted(n for n, r in REGISTRY.items() if r.expected == "false")
TRIANGLE = Graph.from_arcs([(0, 1), (1, 2), (2, 0)])


# ---------------------------------------------------------------------- toy rules exercising each outcome


class _Toy(CandidateRule):
    name = "toy"
    title = pattern = preconditions = transformation = claimed_identity = "toy"
    statuses = (Status.IDEA,)

    def find_matches(self, g):
        return [{"v": v} for v in g.vertices]

    def check_preconditions(self, g, match):
        return None

    def apply(self, g, match, oracle):
        return Application(g, 0)


class _Raises(_Toy):
    def apply(self, g, match, oracle):
        raise RuntimeError("boom")


class _BadReturn(_Toy):
    def apply(self, g, match, oracle):
        return "not an application"


class _InvalidMatches(_Toy):
    def check_preconditions(self, g, match):
        return "never valid"


class _WrongIdentity(_Toy):
    def apply(self, g, match, oracle):
        return Application(g, 1)


class _BadLift(_Toy):
    def apply(self, g, match, oracle):
        return Application(g, 0, lift=lambda removed: frozenset())


class _LiftOutsideGraph(_Toy):
    def apply(self, g, match, oracle):
        return Application(g, 0, lift=lambda removed: frozenset({(99, 98)}))


@pytest.mark.parametrize("rule, outcome", [
    (_Toy(), Outcome.PASS),
    (_Raises(), Outcome.MALFORMED),
    (_BadReturn(), Outcome.MALFORMED),
    (_InvalidMatches(), Outcome.PRECONDITION_INVALID),
    (_WrongIdentity(), Outcome.COUNTEREXAMPLE),
    (_BadLift(), Outcome.COUNTEREXAMPLE),
    (_LiftOutsideGraph(), Outcome.MALFORMED),
])
def test_outcome_classification(rule, outcome):
    cases = evaluate_graph(rule, TRIANGLE, Oracle())
    assert cases and all(c.outcome is outcome for c in cases)


def test_solver_limit_is_inconclusive_not_pass():
    big = Graph.from_arcs([(i, (i + 1) % 6) for i in range(6)])
    case = evaluate_match(_Toy(), big, {"v": 0}, Oracle(max_component_size=4))
    assert case.outcome is Outcome.INCONCLUSIVE
    cfg = SearchConfig(exhaustive=[], random_families=[("planted", 9, 5)], targeted=[], max_component_size=3)
    summary = run_search(_Toy(), cfg)
    assert summary.outcome_counts.get("pass", 0) == 0
    assert summary.outcome_counts.get("inconclusive", 0) > 0
    assert summary.verdict == "NO_EVIDENCE"


def test_mixed_pass_and_inconclusive_is_not_a_clean_verdict():
    # digraphs n <= 3 pass with component limit 2; a 3-cycle piece is inconclusive
    cfg = SearchConfig(exhaustive=[("digraph", n) for n in range(1, 4)], random_families=[], targeted=[],
                       max_component_size=2)
    summary = run_search(_Toy(), cfg)
    assert summary.outcome_counts.get("pass") and summary.outcome_counts.get("inconclusive")
    assert summary.verdict == "INCONCLUSIVE_CASES"


def test_search_stopped_by_limit_is_not_a_clean_verdict():
    cfg = SearchConfig(exhaustive=[("digraph", 3)], random_families=[], targeted=[], max_graphs=5)
    summary = run_search(_Toy(), cfg)
    assert summary.graphs_examined == 5 and summary.verdict == "NO_COUNTEREXAMPLE_BEFORE_LIMIT"


def test_matches_beyond_cap_are_counted_as_skipped():
    class LastMatchWrong(_Toy):
        def apply(self, g, match, oracle):
            return Application(g, 1 if match["v"] == max(g.vertices) else 0)

    cfg = SearchConfig(exhaustive=[], random_families=[], targeted=[], max_matches_per_graph=2)
    g = Graph.from_arcs([(0, 1), (1, 2), (2, 0)])
    results, skipped = evaluate_graph_limited(LastMatchWrong(), g, Oracle(), cfg.max_matches_per_graph)
    assert [r.outcome for r in results] == [Outcome.PASS, Outcome.PASS] and skipped == 1
    assert any(c.outcome is Outcome.COUNTEREXAMPLE for c in evaluate_graph(LastMatchWrong(), g, Oracle()))


def test_find_matches_raising_is_malformed():
    class Broken(_Toy):
        def find_matches(self, g):
            raise ValueError("bad")

    assert evaluate_graph(Broken(), TRIANGLE, Oracle())[0].outcome is Outcome.MALFORMED


# ---------------------------------------------------------------------- registered rules


@pytest.mark.parametrize("name", sorted(REGISTRY))
def test_rule_metadata(name):
    card = get_rule(name).card()
    for key in ("pattern", "preconditions", "transformation", "claimed_identity", "proof_sketch"):
        assert card[key], (name, key)
    assert card["statuses"] and card["expected"] in ("true", "false", "unknown")


def test_unknown_rule():
    with pytest.raises(KeyError):
        get_rule("nope")


def _assert_no_failures(rule, graphs, oracle):
    for g in graphs:
        for case in evaluate_graph(rule, g, oracle):
            assert case.outcome in (Outcome.PASS, Outcome.INCONCLUSIVE), (rule.name, case.to_dict())


@pytest.mark.parametrize("name", TRUE_RULES)
def test_true_rules_exhaustive_n4_and_random(name):
    rule, oracle = get_rule(name), Oracle()
    graphs = [g for n in range(1, 5) for g in isomorphism_classes(n, "digraph")]
    rng = random.Random(name)
    graphs += [random_multigraph(rng.randint(2, 6), 0.35, 3, rng) for _ in range(60)]
    graphs += [g for g in (rule.generate(rng, 7) for _ in range(40)) if g is not None]
    _assert_no_failures(rule, graphs, oracle)


@pytest.mark.slow
@pytest.mark.parametrize("name", TRUE_RULES)
def test_true_rules_exhaustive_n5(name):
    _assert_no_failures(get_rule(name), isomorphism_classes(5, "digraph"), Oracle())


@pytest.mark.parametrize("name", FALSE_RULES)
def test_false_rules_are_refuted_and_minimised(name, tmp_path):
    rule = get_rule(name)
    cfg = SearchConfig(exhaustive=[("digraph", n) for n in range(1, 5)], random_families=[], targeted=[])
    summary = run_search(rule, cfg)
    assert summary.verdict == "COUNTEREXAMPLE_FOUND"
    graph = Graph.from_dict(summary.first_counterexample["graph"])
    res = minimize_counterexample(rule, graph)
    assert res.minimized.n <= graph.n and res.minimized.n <= 4
    record, text = counterexample_report(rule, res)
    assert record["replay_outcome"] == "counterexample"
    assert record["opt_original"] != record["opt_reduced"] + record["claimed_correction"]
    path = save_counterexample(rule, res, tmp_path)
    assert json.loads(path.read_text())["rule"] == name
    assert "Counterexample" in text


def test_minimizer_rejects_non_counterexample():
    with pytest.raises(ValueError):
        minimize_counterexample(get_rule("in_degree_one_contraction"), Graph.from_arcs([(0, 1)]))


def test_in_degree_one_contraction_matches_literature_example():
    # Literature review §3.4: arcs 0->2, 2->0, 2->1, 1->0; OPT = 1, contraction gives 2.
    g = Graph.from_arcs([(0, 2), (2, 0), (2, 1), (1, 0)])
    case = evaluate_match(get_rule("in_degree_one_contraction"), g, {"u": 0, "v": 2}, Oracle())
    assert case.outcome is Outcome.COUNTEREXAMPLE and case.opt_original == 1 and case.opt_reduced == 2


def test_two_terminal_separator_example():
    # two triangles through terminals 0,1 on each side; each side needs 1 either way
    g = Graph.from_arcs([(0, 2), (2, 1), (1, 0), (0, 3), (3, 1)])
    cases = evaluate_graph(get_rule("two_terminal_separator"), g, Oracle())
    assert cases and all(c.outcome is Outcome.PASS for c in cases)


@pytest.mark.parametrize("seed", range(20))
def test_module_contraction_targeted_generator_always_matches(seed):
    # Regression: for n > MODULE_SUBSET_LIMIT, planted modules of size >= 3 must still be found.
    rule = get_rule("module_contraction")
    g = rule.generate(random.Random(seed), 11)
    assert g is not None
    cases = evaluate_graph(rule, g, Oracle())
    assert cases and all(c.outcome is Outcome.PASS for c in cases)

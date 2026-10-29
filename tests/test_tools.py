"""Smoke tests for the CLI, the benchmark runner and the mining tools."""

import json

import pytest

from fas import mining
from fas.benchmark import run_benchmark, summarize, validate_config
from fas.boundary import boundary_function, pairwise_decomposition, star_templates, three_terminal_gadget
from fas.candidates import Oracle
from fas.cli import main
from fas.graph import Graph


def test_cli_solve_and_reduce(tmp_path, capsys):
    path = tmp_path / "g.txt"
    path.write_text("0 1\n1 2\n2 0\n2 3\n3 2\n")
    assert main(["solve", str(path), "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["opt"] == 2 and out["verified"]
    assert main(["solve", str(path), "--no-reduce", "--method", "brute", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["opt"] == 2
    assert main(["reduce", str(path), "--json", "--steps"]) == 0
    assert json.loads(capsys.readouterr().out)["offset"] == 2


def test_cli_errors_are_reported(tmp_path, capsys):
    bad = tmp_path / "bad.txt"
    bad.write_text("0 x\n")
    assert main(["solve", str(bad)]) == 1
    assert "error" in capsys.readouterr().err


def test_cli_candidates_and_search(tmp_path, capsys):
    assert main(["candidates"]) == 0
    assert "two_cycle_cancellation" in capsys.readouterr().out
    assert main(["test-candidate", "in_degree_one_contraction", "--profile", "quick", "--out", str(tmp_path)]) == 0
    summary = json.loads((tmp_path / "in_degree_one_contraction" / "summary.json").read_text())
    assert summary["verdict"] == "COUNTEREXAMPLE_FOUND"
    assert (tmp_path / "in_degree_one_contraction" / "in_degree_one_contraction.md").exists()


def test_cli_generate_and_check(tmp_path, capsys):
    assert main(["generate", "planted", "--n", "6", "--count", "2", "--out", str(tmp_path)]) == 0
    files = sorted(tmp_path.glob("*.json"))
    assert len(files) == 2
    assert main(["check", "two_cycle_cancellation", str(files[0])]) == 0


def test_benchmark_smoke():
    cfg = {"seed": 1, "trials": 1, "count": 2, "max_component": 14, "plain_max_n": 10, "measure_memory": True,
           "pipelines": ["plain", "scc", "baseline", "baseline+two_cycle_cancellation", "baseline+module_contraction"],
           "settings": [{"family": "dense", "n": [8]}, {"family": "scc_dag", "n": [12]}]}
    rows = run_benchmark(cfg, progress=None)
    assert all(r["opt_agree"] for r in rows)
    assert all(r["solution_valid"] for r in rows if r["completed"])
    assert any(not r["completed"] for r in rows)  # plain DP skipped above its limit
    assert {s["pipeline"] for s in summarize(rows)} == set(cfg["pipelines"])


@pytest.mark.parametrize("bad", [
    {"settings": [{"family": "scc_dag", "n": [80]}]},
    {"settings": [{"family": "no_such_family", "n": [8]}]},
    {"pipelines": ["baseline+greedy_max_delta_first"]},
    {"pipelines": ["fastest"]},
])
def test_benchmark_config_validated_before_work(bad):
    cfg = {"seed": 1, "pipelines": ["baseline"], "settings": [{"family": "dense", "n": [6]}]} | bad
    with pytest.raises((ValueError, KeyError)):
        validate_config(cfg)


def test_cli_benchmark_writes_outputs_and_removes_checkpoint(tmp_path):
    cfg = {"name": "t", "seed": 1, "trials": 1, "count": 1, "measure_memory": False,
           "pipelines": ["scc", "baseline"], "settings": [{"family": "dense", "n": [6]}]}
    path = tmp_path / "cfg.json"
    path.write_text(json.dumps(cfg))
    assert main(["benchmark", "--config", str(path), "--out", str(tmp_path / "out")]) == 0
    names = sorted(p.name for p in (tmp_path / "out").iterdir())
    assert names == ["t_meta.json", "t_raw.jsonl", "t_summary.csv", "t_summary.md"]


def test_mining_smoke():
    o = Oracle()
    v = mining.mine_vertex_forcing("digraph", (3, 4), o)
    assert v["rows"] and not any(r["unexplained_always_forced"] for r in v["rows"])
    a = mining.mine_arc_status("digraph", (3,), o)
    assert sum(r["occurrences"] for r in a["rows"]) > 0
    b = mining.mine_boundary(1, o)
    assert b["rows"][0]["sides"] == 64 and b["rows"][0]["non_pairwise"] == 6


def test_mined_hypothesis_refuted_by_hand_example():
    """Arc signature (no antiparallel, tail out 2 / in 1, head out 1 / in 3) is 'never in an optimum'
    on all digraphs with n <= 5 and survived random falsification, but this 7-vertex graph refutes it."""
    g = Graph.from_arcs([(0, 1), (1, 2), (2, 0), (3, 1), (2, 3), (3, 4), (4, 2), (0, 5), (6, 1)])
    o = Oracle()
    assert mining.arc_signature(g, 0, 1) == (0, 2, 1, 1, 3)
    assert mining._arc_label(g, 0, 1, 1, o.opt(g), o) == "some"


def test_star_residuals_and_gadget_exactness():
    o = Oracle()
    terms = (0, 1, 2)
    for key, expected in {"A": [1, 0], "B": [0, 1], "C": [-1, -1]}.items():
        star = star_templates(terms, 3)[key]
        assert pairwise_decomposition(boundary_function(star, terms, o), terms)[1] == expected
    for side in mining.enumerate_sides(1):
        f = boundary_function(side, terms, o)
        gadget, const = three_terminal_gadget(f, terms, 10, o)
        assert len(gadget.vertices) <= 5
        fg = boundary_function(gadget, terms, o)
        assert all(fg[s] + const == f[s] for s in f)

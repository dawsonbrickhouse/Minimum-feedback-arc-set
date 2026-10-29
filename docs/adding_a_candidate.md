# How to add and test a new candidate rule

This guide is for someone who knows Python but is new to graph theory. It takes about an hour
the first time.

You will:

1. read one finished rule;
2. write a new rule that turns out to be false;
3. watch the tool refute it and shrink the counterexample;
4. learn what to do next.

Every command and output below was run on 2026-10-29. Your timings will differ.

## 0. Setup and five words of vocabulary

```bash
cd fas-platform
python3.12 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt && pip install -e .
python -m pytest -q -m "not slow"        # should end with "... passed"
```

Vocabulary:

- **Digraph.** Vertices (numbered 0, 1, 2, …) joined by *arcs*. An arc is a one-way arrow
  `u -> v`. We allow parallel copies of an arc; the number of copies is its *weight* or
  *multiplicity* `w(u, v)`. A *loop* is an arc `v -> v`.
- **Cycle.** A path that returns to its start, such as `0 -> 1 -> 2 -> 0`. A *2-cycle* is a pair
  `u -> v -> u`.
- **FAS (feedback arc set).** A set of arcs whose removal leaves no cycle. Its cost is the total
  weight removed. **OPT(G)** is the minimum cost. Equivalently: put the vertices in a row and pay
  for every arc that points backwards; OPT is the cheapest row
  (`docs/problem_definition.md`).
- **Reduction rule.** A recipe that turns `G` into a smaller or simpler `G'` with
  `OPT(G) = OPT(G') + correction`, where the correction is a number the rule computes.
- **Match.** One place in a graph where the rule applies, stored as a small dict, for example
  `{"vertex": 3}`.

## 1. Read a finished rule

Open `src/fas/candidates/two_cycle_local_bound.py`; it is 80 lines long. A rule is a class with:

- **Text fields**: `name`, `title`, `pattern`, `preconditions`, `transformation`,
  `claimed_identity`, `proof_sketch`, `open_questions`. They are printed by
  `fas candidates <name>` and are the rule's documentation.
- **`statuses`**: what we know about it. A new rule starts as `(Status.CONJECTURE,)`. Never write
  `PROVED_WITHIN_STATED_ASSUMPTIONS` without a written proof in `docs/proof_obligations.md`.
- **`expected`**: your guess, `"true"`, `"false"` or `"unknown"`. It decides which automatic
  tests include the rule (step 5). It never changes a verdict.
- **`find_matches(g)`**: return every match in `g`.
- **`check_preconditions(g, match)`**: re-check one match. Return `None` if it is valid, or a
  string saying why not. The harness calls this independently of `find_matches`, which catches
  bugs in either.
- **`apply(g, match, oracle)`**: return `Application(reduced_graph, correction, lift)`.
  - `lift` is optional. It maps an optimal FAS of the reduced graph (a frozenset of `(u, v)`
    pairs) back to a FAS of `g`.
  - `oracle.solve(h)` gives you an exact solution if your rule needs one.
- **`generate(rng, n)`**: optional. Build a random graph that contains a match. This lets the
  search test your rule on bigger graphs than the exhaustive lists.

Useful `Graph` methods (`src/fas/graph.py`):

- adjacency: `vertices`, `in_arcs(v)` and `out_arcs(v)` (dicts mapping neighbour to weight),
  `in_weight(v)`, `multiplicity(u, v)`, `has_arc(u, v)`;
- derived graphs: `remove_vertices([...])`, `remove_arc_pairs([...])`, `with_arcs({(u, v): k})`;
- reachability: the free function `reachable(g, s)`.

Try the finished rule on a graph file (one arc `u v` per line):

```bash
printf '0 1\n1 0\n0 2\n2 0\n1 2\n' > /tmp/ex.txt
fas check two_cycle_local_bound /tmp/ex.txt
```

Each output line is one match, with OPT before and after and the outcome:

```
{"outcome": "pass", "match": {"vertex": 0, "side": "in"}, "opt_original": 2, "opt_reduced": 0, "correction": 2, ...}
```

## 2. Write a new rule

The idea to test: *"If a vertex `v` is entered by exactly one arc `(u, v)` of weight 1, then
deleting `v` and paying 1 is optimal."* It sounds plausible, because every cycle through `v`
must use that arc.

Create `src/fas/candidates/single_in_arc.py`:

```python
"""Exercise rule from docs/adding_a_candidate.md (expected to be false)."""

from __future__ import annotations

from ..graph import Graph, reachable
from .base import Application, CandidateRule, Match, Oracle, Status


class SingleInArc(CandidateRule):
    name = "single_in_arc"
    title = "A vertex entered by one arc of weight 1: delete it and pay that arc"
    statuses = (Status.CONJECTURE,)
    expected = "unknown"
    pattern = "vertex v whose only in-arc pair is (u, v) with w(u, v) = 1, u != v"
    preconditions = "v has no self-loop and v has at least one out-arc"
    transformation = "G' = G - v"
    claimed_identity = "OPT(G) = OPT(G - v) + 1"
    proof_sketch = "none yet"

    def find_matches(self, g: Graph) -> list[Match]:
        return [{"vertex": v} for v in g.vertices if self.check_preconditions(g, {"vertex": v}) is None]

    def check_preconditions(self, g: Graph, match: Match) -> str | None:
        v = match.get("vertex")
        if not g.has_vertex(v):
            return f"malformed match {match}"
        ins = g.in_arcs(v)
        if g.has_arc(v, v):
            return f"self-loop at {v}"
        if len(ins) != 1 or list(ins.values()) != [1]:
            return f"in-arcs of {v} are {dict(ins)}, expected exactly one arc of weight 1"
        if not g.out_arcs(v):
            return f"{v} has no out-arc"
        return None

    def apply(self, g: Graph, match: Match, oracle: Oracle) -> Application:
        v = match["vertex"]
        (u,) = g.in_arcs(v)
        return Application(g.remove_vertices([v]), 1, lambda removed: removed | {(u, v)})
```

Register it in `src/fas/candidates/__init__.py`. Add the import, then add an instance to
`_RULES`:

```python
from .single_in_arc import SingleInArc
...
_RULES: list[CandidateRule] = [
    ...
    SingleInArc(),
]
```

Check that it is visible:

```bash
fas candidates single_in_arc
```

## 3. Search for a counterexample

```bash
fas test-candidate single_in_arc --profile quick --out results/candidates
```

Output:

```
single_in_arc   COUNTEREXAMPLE_FOUND   {'pass': 4, 'counterexample': 1} graphs=9 ... minimized n=3 m=2
```

The tool writes `results/candidates/single_in_arc/single_in_arc.md`:

```
**Minimised graph G** (n=3, m=2): 1->2, 2->0
**Match:** {"vertex": 2}
| OPT(G) | 0 |   | OPT(G') + correction | 1 |
```

The graph `1 -> 2 -> 0` has no cycle at all, so paying 1 is wasteful. Add the missing
precondition "v lies on a cycle". `v` is on a cycle exactly when `u` can be reached from `v`:

```python
        (u,) = ins
        if u not in reachable(g, v):
            return f"{v} lies on no cycle"
```

> **A real mistake made while writing this guide.** The first version tested
> `v not in reachable(g, u)`. That is always false, because the arc `u -> v` exists. The
> harness then reported a "counterexample" on the 1-arc graph `1 -> 0`, while claiming the
> precondition "v lies on a cycle" held. If a counterexample violates what you *meant*, your
> precondition code is wrong. That is also a useful finding.

Run again:

```
single_in_arc   COUNTEREXAMPLE_FOUND   {'pass': 16, 'counterexample': 1} graphs=18 ... minimized n=3 m=4
```

```
**Minimised graph G** (n=3, m=4): 0->1, 1->2, 2->0, 2->1
**Match:** {"vertex": 0}
| OPT(G) | 1 (optimal FAS: [(1, 2)]) |   | OPT(G') + correction | 2 |
```

**Read the counterexample.**

- The graph is a triangle `0 -> 1 -> 2 -> 0` that shares the arc `1 -> 2` with a 2-cycle
  `1 <-> 2`.
- Removing `1 -> 2` alone breaks both cycles, so OPT = 1.
- The rule pays for `2 -> 0` and still has to break the 2-cycle, for a total of 2.

The idea is wrong: a single arc elsewhere can break the cycles through `v` *and* other cycles
for the same price. The registered rule `arc_disjoint_cycle_bound` fails on exactly the same
graph (`docs/candidate_rules.md`).

## 4. Interpret the verdict honestly

| Verdict | Meaning |
|---|---|
| `COUNTEREXAMPLE_FOUND` | The claim is false. Set `statuses = (Status.COUNTEREXAMPLE_FOUND,)` and `expected = "false"`. |
| `NO_COUNTEREXAMPLE_IN_SEARCH_SPACE` | Every match in the finite search passed. This is **evidence, not proof**. The status may become `TESTED_ON_FINITE_INSTANCES`. |
| `NO_EVIDENCE` | The pattern never occurred. Write a `generate` method, or rethink the pattern. |
| `RULE_BUG` | Your code is inconsistent. Either `find_matches` returned matches that `check_preconditions` rejects (PRECONDITION_INVALID), or the rule raised an exception (MALFORMED). Fix the code. |

A case is **INCONCLUSIVE** when a graph piece was too large for the exact solver. Inconclusive
cases never count as passes. If there are any, the verdict cannot be
`NO_COUNTEREXAMPLE_IN_SEARCH_SPACE`.

Profiles:

- `quick`: about a second.
- `standard`: all digraphs up to 5 vertices plus random and targeted graphs; seconds to
  minutes.
- `deep`: adds all 6-vertex oriented graphs and all 7-vertex tournaments; up to 30 minutes,
  or the cap set by `--max-seconds`.

Use `--seed` to vary the random part.

## 5. From "no counterexample" to a status in the docs

1. **Write tests.** `tests/test_candidates.py` includes rules automatically:
   - `expected = "true"`: no failures on all digraphs with n ≤ 4, plus random graphs. A slow
     test covers n = 5.
   - `expected = "false"`: must be refuted, and minimised to ≤ 4 vertices.

   Also add one hand-checked example of your own.
2. **Try to prove it.** Write the proof in `docs/proof_obligations.md` with a "Critical review"
   paragraph that lists every assumption. Only then use `PROVED_WITHIN_STATED_ASSUMPTIONS`.
3. **Look for prior art** and record it in `docs/literature_review.md`. Use
   `NOVELTY_UNVERIFIED` until you have searched properly, or `PRIOR_ART_FOUND` with the
   citation. Never call a rule new because you did not find it.
4. **Add a dated entry** to `docs/research_notebook.md`.

## 6. Pitfalls

- **Multiplicities matter.** A rule that is true for simple graphs may fail when arcs have
  weight > 1. The searches include multigraphs on purpose.
- **Self-loops** are always in every FAS. Most rules should exclude them in their preconditions.
- **Forcing rules interact.** Two "v before u" rules that are each sound can contradict each
  other if applied at once, for example twins `u` and `v` dominating each other. The harness
  checks one match at a time. A pipeline must re-find matches after every application, as
  `fas.benchmark` does.
- **Keep matches JSON-serialisable** (ints, lists, strings) so counterexamples can be saved
  and replayed.
- **Do not edit the core** (`exact_solver.py`, `reductions.py`) to make a candidate pass. Only
  proved rules with a lift should ever be used outside the harness.

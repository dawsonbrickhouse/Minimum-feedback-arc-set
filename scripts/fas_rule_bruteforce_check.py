"""Brute-force sanity checks of elementary FAS identities on random small digraphs.

Weighted FAS = min over linear orders of total weight of backward arcs (LOP view).
"""
import itertools
import random
from collections import defaultdict


def opt(n_nodes, w):
    """w: dict (u,v)->weight, nodes 0..n_nodes-1. Subset DP: f(S)=min cost ordering S first."""
    nodes = list(range(n_nodes))
    INF = float("inf")
    f = [INF] * (1 << n_nodes)
    f[0] = 0
    into = defaultdict(list)  # into[v] = [(u, wt)] arcs u->v
    for (u, v), wt in w.items():
        into[v].append((u, wt))
    outof = defaultdict(list)
    for (u, v), wt in w.items():
        outof[u].append((v, wt))
    for s in range(1 << n_nodes):
        if f[s] == INF:
            continue
        for v in nodes:
            if s >> v & 1:
                continue
            # placing v after S: arcs v->x with x in S become backward
            c = sum(wt for x, wt in outof[v] if s >> x & 1)
            t = s | (1 << v)
            if f[s] + c < f[t]:
                f[t] = f[s] + c
    return f[(1 << n_nodes) - 1]


def relabel(arcs_w, keep):
    idx = {v: i for i, v in enumerate(sorted(keep))}
    out = defaultdict(int)
    for (u, v), wt in arcs_w.items():
        if u in idx and v in idx and u != v:
            out[(idx[u], idx[v])] += wt
    return len(idx), dict(out)


def rand_graph(n, p):
    return {(u, v): 1 for u in range(n) for v in range(n) if u != v and random.random() < p}


def check_digon(trials=300):
    for _ in range(trials):
        n = random.randint(2, 8)
        g = rand_graph(n, random.uniform(0.2, 0.6))
        digons = [(u, v) for (u, v) in g if u < v and (v, u) in g]
        if not digons:
            continue
        u, v = random.choice(digons)
        h = {a: w for a, w in g.items() if a not in ((u, v), (v, u))}
        assert opt(n, g) == opt(n, h) + 1, (g, u, v)
    print("digon rule OK")


def check_bypass(trials=400):
    """v with exactly one in-arc (u,v) and one out-arc (v,w), u!=w: replace by arc u->w (weights add)."""
    for _ in range(trials):
        n = random.randint(3, 8)
        g = rand_graph(n, random.uniform(0.2, 0.6))
        v = random.randrange(n)
        others = [x for x in range(n) if x != v]
        u, w = random.sample(others, 2)
        g = {a: wt for a, wt in g.items() if v not in a}
        g[(u, v)] = 1
        g[(v, w)] = 1
        h = defaultdict(int)
        for a, wt in g.items():
            if v not in a:
                h[a] += wt
        h[(u, w)] += 1
        n2, h2 = relabel(h, [x for x in range(n) if x != v])
        assert opt(n, g) == opt(n2, h2), (g, v)
    print("bypass (in=out=1) rule OK")


def check_baharev_digon(trials=400):
    """digon u<->v where v has out-degree 1 (only v->u): OPT(G) = 1 + OPT(G - v)."""
    for _ in range(trials):
        n = random.randint(2, 8)
        g = rand_graph(n, random.uniform(0.2, 0.6))
        u, v = random.sample(range(n), 2)
        g = {a: wt for a, wt in g.items() if a[0] != v}
        g[(v, u)] = 1
        g[(u, v)] = 1
        n2, h2 = relabel(g, [x for x in range(n) if x != v])
        assert opt(n, g) == 1 + opt(n2, h2), (g, u, v)
    print("Baharev digon (outdeg 1) rule OK")


def check_module(trials=300):
    """M module (every x outside has the same arcs to/from all of M). Then
    OPT(G) = OPT(G[M]) + OPT_w(G/M), arcs between x and M contracted with weight |M| each way."""
    for _ in range(trials):
        n_out = random.randint(1, 5)
        m = random.randint(2, 4)
        n = n_out + m
        M = list(range(n_out, n))
        g = {}
        for u in range(n_out):
            for v in range(n_out):
                if u != v and random.random() < 0.4:
                    g[(u, v)] = 1
        for a in M:
            for b in M:
                if a != b and random.random() < 0.5:
                    g[(a, b)] = 1
        for x in range(n_out):
            to_m, from_m = random.random() < 0.4, random.random() < 0.4
            for y in M:
                if to_m:
                    g[(x, y)] = 1
                if from_m:
                    g[(y, x)] = 1
        nm, gm = relabel(g, M)
        q = defaultdict(int)
        c = n_out
        for (u, v), wt in g.items():
            uu = c if u in M else u
            vv = c if v in M else v
            if uu != vv:
                q[(uu, vv)] += wt
        assert opt(n, g) == opt(nm, gm) + opt(n_out + 1, dict(q)), g
    print("module/quotient rule OK")


def blocks_split_ok(trials=300):
    """Glue two random digraphs at a cut vertex: OPT adds."""
    for _ in range(trials):
        a, b = random.randint(2, 5), random.randint(2, 5)
        g1, g2 = rand_graph(a, 0.5), rand_graph(b, 0.5)
        # identify vertex a-1 of g1 with vertex 0 of g2
        g = dict(g1)
        for (u, v), wt in g2.items():
            g[(u + a - 1, v + a - 1)] = wt
        assert opt(a + b - 1, g) == opt(a, g1) + opt(b, g2)
    print("cut-vertex (block) additivity OK")


def check_digon_then_scc(trials=300):
    """After deleting all digons (paying 1 each), FAS is additive over SCCs of the remainder."""
    import sys
    sys.setrecursionlimit(10000)
    for _ in range(trials):
        n = random.randint(2, 8)
        g = rand_graph(n, random.uniform(0.3, 0.7))
        digs = {(u, v) for (u, v) in g if (v, u) in g}
        h = {a: w for a, w in g.items() if a not in digs}
        # SCCs of h via simple reachability
        reach = [[False] * n for _ in range(n)]
        for i in range(n):
            reach[i][i] = True
        for (u, v) in h:
            reach[u][v] = True
        for k in range(n):
            for i in range(n):
                for j in range(n):
                    reach[i][j] = reach[i][j] or (reach[i][k] and reach[k][j])
        comps, seen = [], set()
        for i in range(n):
            if i not in seen:
                c = [j for j in range(n) if reach[i][j] and reach[j][i]]
                seen.update(c)
                comps.append(c)
        total = len(digs) // 2 + sum(opt(*relabel(h, c)) for c in comps)
        assert opt(n, g) == total
    print("digon-then-SCC decomposition OK")


def _reaches(arcs, s, t):
    stack, seen = [s], {s}
    while stack:
        x = stack.pop()
        if x == t:
            return True
        for a, b in arcs:
            if a == x and b not in seen:
                seen.add(b)
                stack.append(b)
    return False


def check_indeg1_and_domination(trials=1500, big=1000):
    """R9: u with a single in-arc -> its out-arcs can be made undeletable.
    R16: if every cycle through e uses f (no head(e)->tail(e) path in G-f), e can be made undeletable."""
    for _ in range(trials):
        n = random.randint(3, 8)
        g = rand_graph(n, random.uniform(0.25, 0.6))
        if not g:
            continue
        base = opt(n, g)
        for u in range(n):
            if sum(1 for a in g if a[1] == u) == 1:
                h = {a: (big if a[0] == u else w) for a, w in g.items()}
                assert base == opt(n, h), (g, u)
        arcs = list(g)
        for e in arcs:
            for f in arcs:
                if f != e and not _reaches([x for x in arcs if x != f], e[1], e[0]):
                    h = dict(g)
                    h[e] = big
                    assert base == opt(n, h), (g, e, f)
    print("in-degree-1 exchange and arc domination OK")


if __name__ == "__main__":
    random.seed(1)
    check_digon()
    check_bypass()
    check_baharev_digon()
    check_module()
    blocks_split_ok()
    check_digon_then_scc()
    random.seed(7)
    check_indeg1_and_domination()

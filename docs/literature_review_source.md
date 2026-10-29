---
cursor:
  subagentId: "bc-725ebffa-e712-5c96-819d-6f3c62bd72cb"
---

# Minimum Feedback Arc Set: targeted literature review for exact reduction rules

Compiled 2026-10-29. This review supports a search for new exact reduction rules of the form OPT(G) = OPT(G') + c for the minimum feedback arc set problem (FAS) on unweighted directed graphs.

## 0. Conventions and verification legend

**Notation.** G = (V, A) is a directed graph. OPT(G) = fas(G) is the minimum number of arcs whose deletion makes G acyclic. OPT_w is the weighted version. Most rules below create weights or parallel arcs, so the student's framework should allow positive integer arc weights (equivalently multigraphs) even when the input is unweighted.

**Ordering view (used throughout).** OPT_w(G) = min over linear orders σ of V of the total weight of arcs that point backward in σ. A minimal FAS, once reversed, leaves an acyclic graph (Bessy et al., Lemma 2.1, citing Raman–Saurabh 2006). Baharev et al. (2021, §2, "sorting heuristics") use the same view. Every arc-weighted identity below can be checked against this formula.

**Verification tags** (attached to each entry and claim):
- **[V-src]**: I verified the statement against the primary full text (arXiv or author PDF, or the published PDF).
- **[V-abs]**: I verified it against the publisher or arXiv abstract or metadata only. Bibliographic data were checked through Crossref.
- **[V-sec]**: I verified it only through a named secondary source that cites the work.
- **UNVERIFIED**: I could not check it against any source. It is included only as a pointer.
- **[OWN]**: my own derivation, not found stated in the sources I read. I give a proof sketch, and the rule passed a brute-force check (§8).

---

## 1. The general problem: hardness and approximability

| # | Citation | Venue / ID | Status | Relevance |
|---|---|---|---|---|
| 1.1 | R. M. Karp, "Reducibility among combinatorial problems," in *Complexity of Computer Computations*, Plenum, 1972, pp. 85–103. | doi:10.1007/978-1-4684-2001-2_9 | Peer-reviewed book chapter. [V-abs] metadata. FAS is on Karp's list [V-sec: Baharev et al. 2021 §1.1: "item 8 on the list"]. | NP-completeness. |
| 1.2 | V. Kann, *On the Approximability of NP-Complete Optimization Problems*, PhD thesis, KTH Stockholm, 1992. | (thesis) | [V-sec] Baharev et al. 2021 cite it for "FAS is APX-hard; no PTAS unless P = NP". Primary text UNVERIFIED. | APX-hardness. |
| 1.3 | G. Even, J. Naor, B. Schieber, M. Sudan, "Approximating minimum feedback sets and multicuts in directed graphs," *Algorithmica* 20(2):151–174, 1998. Conference version: IPCO 1995, LNCS, pp. 14–28. | doi:10.1007/PL00009191 | Peer-reviewed. [V-abs] metadata. [V-sec] Baharev §1.1: O(log n log log n)-approximation. They also give approximation-preserving FAS↔FVS reductions ("equally hard to approximate"). | Approximation; FAS/DFVS equivalence. |
| 1.4 | P. D. Seymour, "Packing directed circuits fractionally," *Combinatorica* 15(2):281–288, 1995. | doi:10.1007/BF01200760 | Peer-reviewed. [V-abs]. [V-sec] Baharev: the O(log n log log n) bound is implicit in this proof. | Integrality gap of the cycle-cover LP. |
| 1.5 | V. Guruswami, R. Manokaran, P. Raghavendra, "Beating the random ordering is hard: inapproximability of maximum acyclic subgraph," FOCS 2008, pp. 573–582. Journal: V. Guruswami, J. Håstad, R. Manokaran, P. Raghavendra, M. Charikar, "Beating the random ordering is hard: every ordering CSP is approximation resistant," *SIAM J. Comput.* 40(3):878–914, 2011. | doi:10.1109/FOCS.2008.51 ; doi:10.1137/090756144 | Peer-reviewed. [V-abs]. [V-sec] Baharev §1.1: under the Unique Games Conjecture (UGC), FAS has no constant-factor approximation (Cor. 1.2 of the SICOMP paper), and Max Acyclic Subgraph cannot be approximated within 1/2 + ε. | Approximation resistance. |
| 1.6 | P. Eades, X. Lin, W. F. Smyth, "A fast and effective heuristic for the feedback arc set problem," *Inf. Process. Lett.* 47(6):319–323, 1993. | doi:10.1016/0020-0190(93)90079-O | Peer-reviewed. [V-abs]. [V-sec] Baharev: a linear-time ordering heuristic giving FAS ≤ m/2 − n/6, by exploiting the fact that sources and sinks lie on no cycle. | Upper bound; source/sink peeling. |
| 1.7 | F. Gavril, "Some NP-complete problems on graphs," Proc. 11th Conf. Information Sciences and Systems, 1977. | (proceedings) | UNVERIFIED primary. [V-sec] Hecht 2017, §1: FAS remains NP-complete when every vertex has in-degree and out-degree ≤ 3, and on line digraphs. | Hardness for bounded degree. |

---

## 2. Exact algorithms

### 2.1 Subset dynamic programming / exponential time
- **E. L. Lawler, "A comment on minimum feedback arc sets," *IEEE Trans. Circuit Theory* 11(2):296–297, 1964.** doi:10.1109/TCT.1964.1082291. Peer-reviewed. [V-abs] metadata only. The classical O*(2^n) subset DP over linear orders is commonly attributed to this paper; I did not read the text, so the attribution is UNVERIFIED. The DP is f(S) = min over v ∈ S of f(S∖{v}) + w(v → S∖{v}), where S∖{v} is the set already placed before v. I implemented it for §8.
- **H. L. Bodlaender, F. V. Fomin, A. M. C. A. Koster, D. Kratsch, D. M. Thilikos, "A note on exact algorithms for vertex ordering problems on graphs," *Theory Comput. Syst.* 50(3):420–432, 2012 (online 2011).** doi:10.1007/s00224-011-9312-0. Peer-reviewed. [V-abs] metadata. Its content (O*(2^n) time and polynomial-space variants for vertex-ordering problems including FAS) is UNVERIFIED.
- **I. Razgon, "Computing minimum directed feedback vertex set in O*(1.9977^n)," ICTCS 2007, pp. 70–81.** doi:10.1142/9789812770998_0010. Peer-reviewed. [V-abs] title. This is for DFVS. I found no comparable better-than-2^n result specific to FAS (open, my assessment).
- **M. Hecht, "Exact localisations of feedback sets," *Theory Comput. Syst.* 62(5):1048–1084, 2018 (online 2017); arXiv:1702.07612.** doi:10.1007/s00224-017-9777-6. Peer-reviewed. [V-src] arXiv v1. Weighted FAS/FVS admit a "Bellman decomposition" with DP running in O(2^m |E|^4 log|V|) for FAS, where m ≤ |E| − |V| + 1 is the maximum cycle-space dimension of the "meta graphs" (abstract). It also gives reductions (§3.3 below).

### 2.2 Branch and bound / ILP / cycle (row) generation
- **M. Grötschel, M. Jünger, G. Reinelt, "A cutting plane algorithm for the linear ordering problem," *Oper. Res.* 32(6):1195–1220, 1984.** doi:10.1287/opre.32.6.1195. [V-abs]. Linear ordering polytope; branch and cut for dense instances.
- **M. Grötschel, M. Jünger, G. Reinelt, "On the acyclic subgraph polytope," *Math. Program.* 33(1):28–42, 1985.** doi:10.1007/BF01582009. [V-abs]. [V-sec] Baharev §1.1: Max Acyclic Subgraph is polynomial on weakly acyclic digraphs, which include planar digraphs.
- **A. Baharev, H. Schichl, A. Neumaier, T. Achterberg, "An exact method for the minimum feedback arc set problem," *ACM J. Exp. Algorithmics* 26, Art. 1.4, 28 pp., 2021.** doi:10.1145/3446429. Peer-reviewed. [V-src] (author PDF arnold-neumaier.at/ms/feedback.pdf).
  - **Method:** set-cover ILP over simple cycles. Cycles are enumerated lazily, and the incomplete cycle matrix is extended iteratively (Gurobi lazy constraints). The paper also covers the triangle-inequality LOP formulation (§3.1). The test set has 4,468 sparse graphs.
  - **Reductions:** Appendix A, "Safely removing arcs" (precise statements in §6, rules R5–R8).
- **M. Grötschel, M. Jünger, G. Reinelt, "Comments on 'An exact method for the minimum feedback arc set problem'," *ACM J. Exp. Algorithmics* 27, Art. 1.3, 2022.** doi:10.1145/3545001. Peer-reviewed. [V-src]. A straightforward modern implementation of their 1985 branch-and-cut, which separates violated cycles in polynomial time via shortest paths, is "competitive and mostly superior" to Baharev et al.'s method.
- **M. Hecht, B. Gonciarz, S. Horvát, "Tight localizations of feedback sets," *ACM J. Exp. Algorithmics* 26, 2021, pp. 1–19.** doi:10.1145/3447652. Peer-reviewed. [V-abs] metadata only; content UNVERIFIED. This is the follow-up to Hecht 2018 and worth reading for its localization/reduction ideas.
- **F. Chudigiewitsch, K.-M. Klein, M. Wienöbst, "PACE solver description: UzL exact solver for one-sided crossing minimization," IPEC 2024, LIPIcs, Art. 28.** doi:10.4230/LIPIcs.IPEC.2024.28. Solver description (lightly reviewed). [V-src] excerpt. It reduces one-sided crossing minimization to weighted FAS and solves it as an implicit hitting set with ILP. MaxSAT was "significantly worse" on those instances.
- **R. Martí, G. Reinelt, *The Linear Ordering Problem: Exact and Heuristic Methods in Combinatorial Optimization*, Springer Applied Math. Sci. 175, 2011.** doi:10.1007/978-3-642-16729-4. Monograph. [V-abs] metadata.
- **I. Charon, O. Hudry, "A survey on the linear ordering problem for weighted or unweighted tournaments," *4OR* 5(1):5–60, 2007** (doi:10.1007/s10288-007-0036-6), and **"An updated survey…," *Ann. Oper. Res.* 175(1):107–158, 2010** (doi:10.1007/s10479-009-0648-7). Peer-reviewed surveys. [V-abs] metadata. They survey branch-and-bound methods for tournaments; content UNVERIFIED here.
- **R. Kudelić, *Feedback Arc Set: A History of the Problem and Algorithms*, SpringerBriefs in CS, 2022.** doi:10.1007/978-3-031-10515-9. Book. [V-abs] metadata.

---

## 3. Preprocessing and reduction rules in the literature

### 3.1 Standard decompositions
- **SCC decomposition.** Every cycle lies inside one strongly connected component (SCC), so arcs between SCCs are never needed. Stated in Baharev §2 and the PACE 2022 report (Großmann et al., §"Reduction Rules"). [V-src]
- **Biconnected components.** S. Park, S. B. Akers, "An efficient method for finding a minimal feedback arc set in directed graphs," Proc. IEEE ISCAS 1992, vol. 4, pp. 1863–1866 (doi:10.1109/ISCAS.1992.230449). Peer-reviewed conference. [V-abs] metadata. [V-sec] Baharev §2 and Pustoslemšek et al. 2024: each SCC is further split at articulation points of the underlying undirected graph. Primary text UNVERIFIED.

### 3.2 Baharev et al. 2021, Appendix A [V-src]
**Definition.** "A set of arcs is safe to remove if removing these arcs from G and adding them to the feedback arc set does not change the minimum cost solution", that is, some minimum FAS contains them.

**General rule (A.2).** Take any induced subgraph G' of G. Let c1 = OPT(G') (exact). Let F' ⊆ A(G') be an arc set of cost c2 that both makes G' acyclic and breaks every cycle of G that has an arc in G'. If c1 = c2, then F' is safe to remove. (Always c1 ≤ c2, and F' may be found heuristically.)

**Hand-coded patterns (Fig. 4, weighted).** I rendered and read the figure.
1. A self-loop is always in the solution.
2. A 2-cycle a ⇄ b with weights w1 = w(a,b) and w2 = w(b,a), where b has out-degree 1 in G: if w2 ≤ w1, delete b with all its arcs and put (b,a) into the solution.
3. Same 2-cycle, where b has in-degree 1: if w1 ≤ w2, delete b and put (a,b) into the solution.
4. A run a → b → c with b of in- and out-degree 1 becomes a single arc a → c of weight min(w1, w2).
5. A 3-arc bypass a → b → c plus a → c (weight w3), with b of in- and out-degree 1, becomes a → c of weight min(w1, w2) + w3.
6. A 3-cycle a → b → c → a, with b of in- and out-degree 1, becomes a 2-cycle: a → c of weight min(w1, w2) and c → a of weight w3.

The authors report the general A.2 rule as too expensive for presolve. They used the patterns, plus SCC splitting, iteratively.

### 3.3 Hecht 2018, "Exact Localisations of Feedback Sets" [V-src, arXiv v1]
- **Line digraph equivalence (Prop. 1).** Unweighted FAS on G is equivalent to unweighted FVS on the line digraph L(G).
- **Essential minor (Def. 4, Prop. 2).**
  - Repeatedly (i) collapse each maximal branch-point-free directed path (internal vertices have in- and out-degree 1) into one arc whose weight is the minimum of the path's arc weights, and (ii) merge parallel arcs, summing their weights.
  - The fixed point (C, δ) satisfies Ω(G, ω) = Ω(C, δ), and solutions correspond. The construction takes O(|E|²) (Prop. 3).
- **Isolated cycles (Def. 6, §6).** An arc e is isolating for cycle c if c meets no cycle that avoids e and its parallel arcs. Hecht's argument: if the weight of F⁺(e) (e and its parallel copies) equals the optimum FAS weight of the subgraph G_I(e) of isolated cycles through e, then some optimal FAS of G contains F⁺(e).
  - Lemma 1: the FAS of the subgraph G_el(e) of all elementary cycles through e is min{w(e), min e⁻–e⁺ cut}, computable by max-flow.
  - Graphs fully solvable by iterating this are called "resolvable"; they are solved in polynomial time (Thm. 3).
- **Caution.** Hecht states the theorem "The unweighted FASP and FVSP are APX complete" (Thm. 1). APX-completeness of FAS would require a constant-factor approximation, which is not known (see 1.5). Treat that claim with caution.

### 3.4 DFVS reduction rules (relevant via the line digraph and by analogy)
Restated precisely in R. Kiesel, A. Schidler, "A dynamic MaxSAT-based approach to directed feedback vertex sets," ALENEX 2023, pp. 39–52 (doi:10.1137/1.9781611977561.ch4; arXiv:2211.06109). Peer-reviewed. [V-src] Appendix A. This was the PACE 2022 exact-track winner (solver "DAGer").

Notation: a bi-edge is a 2-cycle. The exclusion G∘v = G − v + N_pred(v) × N_succ(v), i.e., v is bypassed and declared not in the solution.
- **LOOP** (Levy–Low): a vertex with a self-loop is in the solution.
- **IN0/1, OUT0/1** (Levy–Low): if v has ≤ 1 in-arc (or ≤ 1 out-arc), replace G by G∘v.
- **INDICLIQUE / OUTDICLIQUE, DICLIQUE-2/3** (Lemaic 2008).
- **PIE** (Lin–Jou): delete a non-bi-edge arc (u,v) if every v→u path uses a bi-edge.
- **DOME** (Lin–Jou): delete a non-bi-edge arc (v,u) if every non-bi-edge in-neighbour of v is an in-neighbour of u, or every non-bi-edge out-neighbour of u is an out-neighbour of v.
- **CORE** (Lin–Jou): if all arcs at v are bi-edges and N(v) is a diclique, take N(v) into the solution (written there as G∘v).
- **New in Kiesel–Schidler.** DOME++ (paths of any length), ALLCYCLES, and lifted vertex-cover reductions such as SUBSET, 4PATH, UNCONFINED and MANYFOLD (Thms 4.1–4.7).

Primary sources [V-abs] metadata:
- H. Levy, D. W. Low, "A contraction algorithm for finding small cycle cutsets," *J. Algorithms* 9(4):470–493, 1988 (doi:10.1016/0196-6774(88)90013-2).
- H.-M. Lin, J.-Y. Jou, "On computing the minimum feedback vertex set of a directed graph by contraction operations," *IEEE TCAD* 19(3):295–307, 2000 (doi:10.1109/43.833199); conference version ICCD 1999.
- M. Lemaic, PhD thesis, Univ. Köln, 2008.

Related PACE 2022 sources:
- **E. Großmann, T. Heuer, C. Schulz, D. Strash, "The PACE 2022 Parameterized Algorithms and Computational Experiments Challenge: Directed Feedback Vertex Set," IPEC 2022, LIPIcs 249, Art. 26.** doi:10.4230/LIPIcs.IPEC.2022.26. [V-src].
  - Organizers' rules: SCC splitting; contracting in-/out-degree-1 vertices; deleting arcs that join two SCCs of G minus all bi-edges (the PIE generalization).
  - Exact-track results: (1) Kiesel and Schidler, solving 185 of 200 instances with reductions and incremental MaxSAT; (2) the Bremen team with reductions plus hitting-set/ordering ILP and vertex-cover solvers; (3) the HPI team with reductions and repeated vertex-cover solving.
- **A. Meiburg, "Reduction rules and ILP are all you need: minimal directed feedback vertex set," arXiv:2208.01119, 2022.** Preprint. [V-src].
  - Graph rules: SCC split, IN/OUT-degree ≤ 1, and the observation that a 2-cycle can be extracted as a size-2 cover constraint and both arcs then removed (valid for DFVS).
  - It then applies vertex-cover rules (domination, funnel, desk, generalized desk) to the cycle-cover instance, and considers but does not use a "vertex domination" rule.

**Important for FAS: these DFVS rules do not transfer verbatim.** For example, the FAS analogue of IN1 ("contract the unique in-arc of v") is not exact. Minimal counterexample, found by brute force [OWN]: arcs 0→2, 2→0, 2→1, 1→0. Here OPT = 1 (delete 0→2). Contracting 0→2 creates a forced self-loop and the 2-cycle 0⇄1, giving 2. The exact FAS counterpart of IN1 is the exchange lemma R9 in §6.

### 3.5 Other preprocessing sources
- J. Pustoslemšek, E. Črne, N. Rihter, "Improvement and evaluation of a heuristic method for the minimal feedback arc set problem," SCORES 2024 (student conference; peer-review status UNVERIFIED), doi:10.18690/um.feri.6.2024.5. [V-src]. They implement Baharev patterns 1–4 plus SCC and biconnected splitting.

---

## 4. Kernelization and fixed-parameter algorithms

### 4.1 General digraphs (DFVS ≡ DFAS for parameter k)
- **J. Chen, Y. Liu, S. Lu, B. O'Sullivan, I. Razgon, "A fixed-parameter algorithm for the directed feedback vertex set problem," *J. ACM* 55(5), Art. 21, 2008** (STOC 2008, pp. 177–186). doi:10.1145/1411509.1411511. Peer-reviewed. [V-abs]. DFVS solvable in 4^k k! n^{O(1)}. [V-sec] Baharev: the same bound applies to FAS through the solution- and cost-preserving reductions.
- **D. Lokshtanov, M. S. Ramanujan, S. Saurabh, "When recursion is better than iteration: a linear-time algorithm for acyclicity with few error vertices," SODA 2018, pp. 1916–1933** (doi:10.1137/1.9781611975031.125). Journal version: *J. Combin. Theory Ser. B* 177:143–185, 2026 (doi:10.1016/j.jctb.2025.11.002). [V-abs] titles. A DFVS FPT algorithm linear in input size for fixed k; the exact bound is UNVERIFIED.
- **M. Bonamy, Ł. Kowalik, J. Nederlof, M. Pilipczuk, A. Socała, M. Wrochna, "On directed feedback vertex set parameterized by treewidth," WG 2018, LNCS, pp. 65–78; arXiv:1707.01470.** doi:10.1007/978-3-030-00256-5_6. [V-abs]. 2^{O(t log t)} n^{O(1)}, which is ETH-tight; 2^{O(t)} n^{O(1)} on planar digraphs.
- **B. Bergougnoux, E. Eiben, R. Ganian, S. Ordyniak, M. S. Ramanujan, "Towards a polynomial kernel for directed feedback vertex set," *Algorithmica* 83(5):1201–1221, 2021 (online 2020).** doi:10.1007/s00453-020-00777-5. [V-abs].
  - A polynomial kernel for DFVS parameterized by the feedback vertex set number of the underlying undirected graph; a linear kernel on bounded-genus inputs.
  - Whether DFVS has a polynomial kernel in k "has become one of the largest open problems" in parameterized algorithms.
- **D. Lokshtanov, M. S. Ramanujan, S. Saurabh, R. Sharma, M. Zehavi, "Wannabe bounded treewidth graphs admit a polynomial kernel for DFVS," *ACM Trans. Comput. Theory* 17(1):1–28, 2025.** doi:10.1145/3711669. [V-abs] title and metadata. The exact parameter is UNVERIFIED (the page fetch timed out).
- **Polynomial kernel for FAS by solution size k:** open, to my knowledge. It is tied to the DFVS question because the standard reductions preserve k. This is my assessment and is not stated for FAS in a source I read.
- **R. Crowston, G. Gutin, M. Jones, "Directed acyclic subgraph problem parameterized above the Poljak–Turzík bound," FSTTCS 2012, LIPIcs 18; arXiv:1207.3586.** Peer-reviewed. [V-src] arXiv. DOI not re-verified (Crossref was rate-limited); it is likely 10.4230/LIPIcs.FSTTCS.2012.400 but this is UNVERIFIED.
  - Problem: connected oriented graphs (no 2-cycles) with an acyclic subgraph of ≥ m/2 + (n−1)/4 + k arcs. The paper gives a (12k)! n^{O(1)} algorithm (abstract) and an O(k²) kernel.
  - "Two-way" Rules 1 and 2 are exact OPT identities (§6, R14).
- **M. Mnich, G. Philip, S. Saurabh, O. Suchý, "Beyond Max-Cut: λ-extendible properties parameterized above the Poljak–Turzík bound," *JCSS* 80(7):1384–1403, 2014.** doi:10.1016/j.jcss.2014.04.011. [V-abs].
- **V. Raman, S. Saurabh, "Parameterized algorithms for feedback set problems and their duals in tournaments," *TCS* 351(3):446–458, 2006.** doi:10.1016/j.tcs.2005.10.010. [V-abs]. Bessy et al. cite it for Lemma 2.1: reversing a minimal FAS yields an acyclic digraph.

### 4.2 Tournaments (FAST)
- **NP-hardness.** N. Alon, "Ranking tournaments," *SIAM J. Discrete Math.* 20(1):137–142, 2006 (doi:10.1137/050623905). P. Charbit, S. Thomassé, A. Yeo, "The minimum feedback arc set problem is NP-hard for tournaments," *Combin. Probab. Comput.* 16(1):1–4, 2007 (doi:10.1017/S0963548306007887). [V-abs].
- **Approximation.**
  - C. Kenyon-Mathieu, W. Schudy, "How to rank with few errors," STOC 2007, pp. 95–103 (doi:10.1145/1250790.1250806). PTAS for weighted FAST with bounded weights [V-sec: Bessy et al. intro].
  - N. Ailon, M. Charikar, A. Newman, "Aggregating inconsistent information: ranking and clustering," *J. ACM* 55(5), 2008 (doi:10.1145/1411509.1411513; STOC 2005). [V-abs].
- **Subexponential FPT.**
  - N. Alon, D. Lokshtanov, S. Saurabh, "Fast FAST," ICALP 2009, LNCS 5555, pp. 49–58 (doi:10.1007/978-3-642-02927-1_6): O*(k^{O(√k)}) [V-sec: Karpinski–Schudy abstract].
  - U. Feige, "Faster FAST," arXiv:0911.5094, 2009 (preprint): n^{O(1)} 2^{O(√k)} [V-abs].
  - M. Karpinski, W. Schudy, "Faster algorithms for feedback arc set tournament, Kemeny rank aggregation and betweenness tournament," ISAAC 2010, LNCS, pp. 3–14 (doi:10.1007/978-3-642-17517-6_3; arXiv:1006.4396): O*(2^{O(√OPT)}) for FAST and Kemeny [V-abs].
- **Quadratic kernel.** M. Dom, J. Guo, F. Hüffner, R. Niedermeier, A. Truß, CIAC 2006, LNCS 3998, pp. 320–331 (doi:10.1007/11758471_31). Journal: *J. Discrete Algorithms* 8(1):76–86, 2010 (doi:10.1016/j.jda.2009.08.001). [V-src] JDA author PDF. The journal footnote says the kernel section was omitted from the long version. The two kernel rules are restated in Bessy et al. as Rules 3.1 and 3.2 (§6, R12). The journal also gives a 3.373^k n^{O(1)} search tree for FAS in bipartite tournaments, based on a forbidden-subgraph characterization.
- **Linear kernel.** S. Bessy, F. V. Fomin, S. Gaspers, C. Paul, A. Perez, S. Saurabh, S. Thomassé, "Kernels for feedback arc set in tournaments," FSTTCS 2009 (LIPIcs 4) and *J. Comput. Syst. Sci.* 77(6):1071–1078, 2011. doi:10.1016/j.jcss.2010.10.001; arXiv:0907.2165. Peer-reviewed. [V-src] arXiv v2 and the JCSS author PDF.
  - Lemma 2.4 (safe partition) holds for **general ordered digraphs**.
  - Rule 3.3 (safe partition) and Rule 3.4 (transitive module).
  - Theorem 3.10: for each fixed ε > 0, a vertex kernel with ≤ (2+ε)k vertices (uses the PTAS).
  - Rules in §6 (R10–R12).
- **Conflict packing.** C. Paul, A. Perez, S. Thomassé, "Conflict packing yields linear vertex-kernels for k-FAST, k-dense RTI and a related problem," MFCS 2011, LNCS, pp. 497–507 (doi:10.1007/978-3-642-22993-0_45). Journal: "Linear kernel for Rooted Triplet Inconsistency and other problems based on conflict packing technique," *JCSS* 82(2):366–379, 2016 (doi:10.1016/j.jcss.2015.08.002); arXiv:1101.4491. [V-abs]. A safe partition is found by greedily packing conflicts (cycles), giving a simpler linear kernel for FAST and a quadratic kernel for FAS in bipartite tournaments.
- **Kemeny rank aggregation (weighted tournaments).** N. Betzler, R. Bredereck, R. Niedermeier, "Theoretical and empirical evaluation of data reduction for exact Kemeny rank aggregation," *Auton. Agents Multi-Agent Syst.* 28(5):721–748, 2014 (doi:10.1007/s10458-013-9236-y); IPEC 2010 version "Partial kernelization for rank aggregation". Peer-reviewed. [V-src] author PDF. Lemma 1 (3/4-majority), Lemma 2 (Extended Condorcet criterion), Lemma 3 and the Extended Condorcet Rule are in §6, R15.

### 4.3 Bipartite tournaments
- J. Guo, F. Hüffner, H. Moser, "Feedback arc set in bipartite tournaments is NP-complete," *Inf. Process. Lett.* 102(2–3):62–65, 2007. doi:10.1016/j.ipl.2006.11.016. [V-abs].
- S. Gupta, "Feedback arc set problem in bipartite tournaments," *Inf. Process. Lett.* 105(4):150–154, 2008. doi:10.1016/j.ipl.2007.08.023. [V-abs] metadata. The approximation ratio is UNVERIFIED.
- M. Xiao, J. Guo, "A quadratic vertex kernel for feedback arc set in bipartite tournaments," MFCS 2012, LNCS, pp. 825–835 (doi:10.1007/978-3-642-32589-2_71); *Algorithmica* 71(1):87–97, 2015 (online 2013; doi:10.1007/s00453-013-9783-2). [V-abs] title. Rules UNVERIFIED.
- Dom et al. (JDA 2010): 3.373^k n^{O(1)} [V-src]. Paul–Perez–Thomassé: quadratic kernel via conflict packing [V-abs].

---

## 5. Restricted graph classes (summary)

| Class | Status | Source / tag |
|---|---|---|
| Planar digraphs | Polynomial: FAS in a planar digraph is a minimum dijoin in the planar dual, solved via Lucchesi–Younger. | C. L. Lucchesi, D. H. Younger, "A minimax theorem for directed graphs," *J. London Math. Soc.* (2) 17(3):369–374, 1978, doi:10.1112/jlms/s2-17.3.369 [V-abs]. Polynomiality [V-sec: Baharev §1.1 citing Lucchesi 1976 thesis and L–Y 1978]. Dijoin algorithm also in A. Frank, "How to make a digraph strongly connected," *Combinatorica* 1(2):145–153, 1981, doi:10.1007/BF02579270 [V-abs]. The duality argument itself: my summary, UNVERIFIED wording. |
| Weakly acyclic digraphs (includes planar) | Polynomial (LP over the acyclic subgraph polytope) | Grötschel–Jünger–Reinelt 1985 [V-sec: Baharev] |
| Reducible flow graphs | Polynomial | V. Ramachandran, *J. Algorithms* 9(3):299–313, 1988, doi:10.1016/0196-6774(88)90022-3 [V-abs; V-sec Baharev] |
| Tournaments | NP-hard; PTAS; 2^{O(√k)} n^{O(1)}; (2+ε)k vertex kernel | §4.2 |
| Bipartite tournaments | NP-complete; 3.373^k n^{O(1)}; quadratic vertex kernel | §4.3 |
| Max in/out-degree ≤ 3; line digraphs | NP-complete | Gavril 1977 [V-sec: Hecht 2018]; primary UNVERIFIED |
| Bounded treewidth | FPT by treewidth (DFVS: 2^{O(t log t)}, ETH-tight). FAS by treewidth: not verified here. | Bonamy et al. 2018 [V-abs] |
| "Resolvable" graphs (Hecht) | Polynomial via isolated-cycle peeling | Hecht 2018, Thm 3 [V-src] |

---

## 6. Known safe reduction rules

Each rule lists its precondition, the transformation, the OPT identity, the source, and its verification tag. Weighted means positive integer arc weights; unweighted inputs become weighted after these rules. "Brute-force checked" means the identity held on hundreds of random digraphs with n ≤ 8 (§8).

**R1. SCC decomposition.**
- Precondition: none.
- Transformation: let C_1, …, C_t be the SCCs. Delete all arcs between distinct SCCs and solve each G[C_i] separately.
- Identity: OPT_w(G) = Σ_i OPT_w(G[C_i]). Includes deleting sources, sinks and vertices in no cycle.
- Source: standard; stated in Baharev §2 and the PACE 2022 report. [V-src]

**R2. Block (biconnected) decomposition.**
- Precondition: v is an articulation point of the underlying undirected graph, splitting G into G_1 and G_2 that share only v.
- Identity: OPT_w(G) = OPT_w(G_1) + OPT_w(G_2), since every cycle lies in one block.
- Source: Park–Akers 1992 [V-sec via Baharev §2]. Brute-force checked.

**R3. Self-loop (multigraph setting).**
- Precondition: a loop of weight w at v.
- Transformation: delete the loop.
- Identity: OPT_w(G) = OPT_w(G − loop) + w.
- Source: Baharev Fig. 4(1) [V-src].

**R4. 2-cycle cancellation.**
- Precondition: arcs (u,v) and (v,u) with weights a and b.
- Transformation: subtract min(a,b) from both arcs and delete any arc that drops to weight 0.
- Identity: OPT_w(G) = OPT_w(G') + min(a,b). Unweighted: OPT(G) = OPT(G − {uv, vu}) + 1.
- Proof: in every linear order exactly one of the two arcs points backward. [OWN], brute-force checked. This is the standard LOP "c_ij − c_ji" normalization in spirit, but I did not find it stated in this form in a source I read.

**R4b. 2-cycle cancellation, then SCC (FAS analogue of PIE).**
- Transformation: apply R4 to all 2-cycles, then R1 to the result. Arcs joining different SCCs of G minus all 2-cycles are discarded.
- Identity: OPT(G) = #2-cycles + Σ_i OPT(G''[C_i]), where G'' = G minus both arcs of every 2-cycle.
- This is strictly stronger than R1. It is the arc analogue of the DFVS rule in the PACE 2022 report ("remove arcs connecting two SCCs of G minus undirected edges") and of Lin–Jou PIE.
- It is also the unweighted digraph case of the **Extended Condorcet Rule** (Betzler et al., Lemma 2 and Lemma 3: SCCs of the strict majority graph, i.e., net-weight arcs, may be solved independently and concatenated).
- Tag: [OWN] for the FAS statement; brute-force checked. Kemeny analogue [V-src].

**R5. Baharev 2-cycle rules (weighted).**
- Precondition: a 2-cycle a ⇄ b with w1 = w(a,b) and w2 = w(b,a).
- (i) If out-deg(b) = 1 (only b→a) and w2 ≤ w1: delete b and all its arcs. Identity: OPT_w(G) = OPT_w(G − b) + w2.
- (ii) If in-deg(b) = 1 (only a→b) and w1 ≤ w2: delete b. Identity: OPT_w(G) = OPT_w(G − b) + w1.
- Source: Baharev Fig. 4(2,3) and §A.1 [V-src]. The unweighted case of (i) is brute-force checked.

**R6. Chain bypass / essential minor.**
- Precondition: v has exactly one in-arc (u,v) with weight w1 and one out-arc (v,w) with weight w2, and u ≠ w.
- Transformation: delete v and add an arc u → w of weight min(w1,w2), merging into an existing u → w by **summing** weights.
- Identity: OPT_w(G) = OPT_w(G').
- If u = w, the 2-cycle u ⇄ v is resolved by R5. If w → u exists, R4 may then fire.
- Sources: Baharev Fig. 4(4) "runs", 4(5) "3-arc bypass", 4(6) "3-cycle" [V-src]; Hecht, Def. 4 and Prop. 2 (essential minor: collapse branch-point-free paths with min, merge parallel arcs with sum) [V-src]. The unweighted case is brute-force checked.

**R7. Parallel-arc merge.**
- Precondition: parallel arcs u → v with weights a and b.
- Transformation: replace them by one arc of weight a + b.
- Identity: OPT unchanged.
- Source: Hecht Def. 4 (G/Φ) [V-src].

**R8. Baharev general safe-arc rule.**
- Precondition: an induced subgraph G' and F' ⊆ A(G') such that F' breaks all cycles of G' and all cycles of G that use an arc of G', and w(F') = OPT_w(G').
- Transformation: delete F' (pay for it).
- Identity: OPT_w(G) = w(F') + OPT_w(G − F').
- Source: Baharev §A.2 [V-src]. Patterns R5 and R6 are special cases.

**R9. In-degree-1 / out-degree-1 exchange lemma (exact FAS counterpart of DFVS IN1/OUT1).**
- Precondition: u has exactly one in-arc e = (t,u), with weight at most the weight of each out-arc of u (always true when unweighted).
- Statement: some optimal FAS contains no out-arc of u. Equivalently, OPT_w(G) = OPT_w(G with u's out-arcs made undeletable, weight ∞). The out-degree case is symmetric.
- Proof: replace any out-arcs of u in F by e; every cycle through such an arc passes through e.
- This is not a size reduction by itself. Naively contracting e is **not** exact (counterexample in §3.4).
- Tag: [OWN], brute-force checked. Underlying idea: Levy–Low IN1/OUT1 for DFVS [V-src via Kiesel–Schidler].

**R10. Safe partition (Bessy et al., Lemma 2.4, general digraphs).**
- Precondition: an ordering σ of V and a partition into σ-intervals V_1, …, V_l. Let A_B be the arcs between intervals and F the backward arcs in A_B. F can be certified using only arcs of A_B: there are pairwise arc-disjoint certificates c(f), each a directed path from head(f) to tail(f) that uses only forward arcs in the span of f.
- Transformation: delete F (in tournaments, reverse F) and drop the remaining inter-interval arcs.
- Identity: OPT(D) = |F| + Σ_i OPT(D[V_i]). Lemma 2.4 states fas(D_σ) = fas(D_σ[A_I]) + fas(D_σ[A_B]), with fas(D_σ[A_B]) = |F|, and some minimum FAS contains F.
- Source: Bessy et al. 2011, Lemma 2.4 and Rule 3.3 [V-src].

**R11. Transitive module rule (tournaments).**
- Precondition: V_m is a maximal transitive module of size p in tournament T; I and O are its in- and out-neighbours; Z is the set of arcs from O to I, with q = |Z| < p.
- Transformation: reverse Z.
- Identity: OPT(T) = OPT(T') + q (Rule 3.4 is a safe partition {I, V_m, O}).
- Source: Bessy et al., Rule 3.4 and Lemma 3.3 [V-src].

**R12. Tournament kernel rules (Dom et al. / Alon et al.).**
- Rule 3.1: delete a vertex in no triangle. In tournaments this is OPT-preserving and coincides with R1.
- Rule 3.2: if an arc is in > k triangles, reverse it and set k := k − 1. This is a decision-version rule that depends on the bound k, **not** an OPT identity on its own.
- Source: Bessy et al., Lemma 3.1 citing Dom et al. 2006 and Alon et al. 2009 [V-src restatement].

**R13. Module / quotient rule (general digraphs, weighted).**
- Precondition: M ⊆ V is a module: every x ∉ M has the same arcs to all of M (to all or none) and from all of M (all or none).
- Transformation: solve G[M] separately, and contract M to a single vertex m* where each arc x → M (or M → x) becomes x → m* (or m* → x) with weight |M| (times the arc weight in weighted inputs).
- Identity: OPT_w(G) = OPT_w(G[M]) + OPT_w(G/M).
- Proof: in any order, move all of M to the position of the M-vertex with the cheapest external cost, keeping M's internal order. External costs are identical functions of position for all M-vertices, so the cost does not increase.
- Tag: [OWN], brute-force checked. Related: Bessy et al. use modules (Rule 3.4). The voting analogue (clones contiguous in an optimal Kemeny ranking, treated as one candidate with multiplied weight) appears on Wikipedia's "Independence of clones" page; I did not locate a primary source.

**R14. Crowston–Gutin–Jones two-way rules (oriented, connected G).**
- Rule 1: x is a vertex and S is a set of two vertices such that G[S] is a component of G − x and G[S ∪ {x}] is a directed 3-cycle. G' := G − S. Identity: OPT(G) = OPT(G') + 1. (Their proof gives a(G') = a(G) − 2 with m' = m − 3; also implied by R2.)
- Rule 2: G[a,b,c] and G[c,d,e] are directed 3-cycles, G[a..e] is their union, and only a and e have neighbours outside. Replace b, c, d by a new x with a directed 3-cycle on {a, x, e}. Identity: OPT(G) = OPT(G') + 1.
- Source: Crowston–Gutin–Jones 2012, Rules 1 and 2, Lemmas 3 and 4 [V-src arXiv].

**R15. Kemeny-specific rules (weighted tournaments from votes).**
- Extended Condorcet Rule (Lemma 2 and Lemma 3): split into the SCCs of the strict majority graph and concatenate optimal rankings. OPT is additive.
- 3/4-Majority Rule (Lemma 1): a non-dirty candidate is ordered according to the ≥ 3/4-majority in every Kemeny ranking. Remove it and split.
- Source: Betzler–Bredereck–Niedermeier 2014 [V-src]. These are valid only for Kemeny instances (weights from voter profiles), not arbitrary weighted digraphs.

**R16. Arc domination.**
- Precondition: arcs e = (a,b) and f ≠ e with w(f) ≤ w(e), such that G − f has no b → a path (every cycle through e uses f).
- Statement: some optimal FAS avoids e, so e can be made undeletable. Via R9-style exchange this enables later rules.
- Tag: [OWN], brute-force checked. The DFVS analogue is "vertex domination" (Meiburg 2022) [V-src].

**R17. Isolated-cycle rule (Hecht).**
- Precondition: e is an isolating arc and w(F⁺(e)) equals the optimum FAS weight on G_I(e).
- Statement: some optimal FAS contains F⁺(e).
- Source: Hecht 2018, §6 [V-src]. Exact preconditions are as in Defs. 6–7; my paraphrase.

**DFVS-only rules.** LOOP, IN/OUT0/1, DICLIQUE, PIE, DOME, CORE, DOME++ and the vertex-cover lifts (§3.4) apply to FAS only through L(G) (Hecht, Prop. 1), not directly on G.

---

## 7. Areas where new rules might plausibly exist / open questions (MY OWN ASSESSMENT)

1. **Arc-level translations of DFVS rules.** Kiesel–Schidler's rules (DOME++, lifted vertex-cover rules such as crown, funnel, desk, unconfined) are exact on L(G). For each, characterize when applying it on L(G) yields a graph that is again a line digraph (or a weighted graph). That gives FAS rules directly on G. R4b and R9 show some translate cleanly while naive contraction does not. DOME in particular has a plausible FAS analogue: "an arc whose cycles are all covered by a cheaper dominating arc" (generalizing R16 to sets of arcs).
2. **Unweighted-closed rules.** R5–R7 and R13 leave the unweighted class. A useful target is rules whose output stays unweighted, such as R14-style gadget replacements ("replace subgraph H with interface vertices by a smaller H' with the same interface cost function, shifted by c").
   - This is protrusion replacement for FAS. For an interface of size s, the cost of H depends only on the relative order of the interface vertices, a function on s! orders. Small-interface tables could be enumerated by computer.
   - Examples: s = 2 is two-terminal ("series-parallel") gadgets; s = 3 generalizes Crowston–Gutin–Jones Rule 2.
3. **Safe partitions in sparse digraphs.** Lemma 2.4 is fully general, but only tournaments have an algorithm to find safe partitions (PTAS plus certificate packing). In sparse graphs, certificates are arc-disjoint cycles with exactly one backward arc, which is a packing/flow problem. Heuristic search for safe partitions from a good heuristic ordering (cycle-packing lower bound = local upper bound) is a promising preprocessing direction.
4. **Modules and near-modules.** R13 needs exact modules, which are rare in sparse graphs. Open: relaxed "near-module" rules where the vertices differ on a few arcs, with a bounded additive correction, perhaps checkable by a small LP. Also, "twins" with identical in- and out-neighbourhoods are the 2-vertex special case.
5. **2-cycle-rich structure.** After R4, a 2-cycle-heavy graph becomes much sparser. Rules that look at G minus 2-cycles (e.g., degree-1 conditions holding only after cancellation) seem underexplored.
6. **Isolated / localized cycles.** Hecht's isolated-cycle rule (R17) and Baharev's A.2 (R8) are general but expensive "local optimum = local upper bound" certificates. Cheaper sufficient conditions, such as min-cut duality restricted to cycles through one arc (Hecht Lemma 1), could yield polynomial-time special cases.
7. **Theory gaps.**
   - A polynomial kernel for FAS by k (equivalent in spirit to the open DFVS kernel question).
   - Better-than-2^n exact algorithms for general FAS (none found).
   - A characterization of Hecht's resolvable graphs (stated open in Hecht 2018).
   - Whether FAS by treewidth matches the DFVS 2^{O(t log t)} bound.

---

## 8. Evidence: brute-force checks

The script is `internal/fas_rule_bruteforce_check.py`. It is an exact subset DP over linear orders (weighted), checked on known instances: a 3-cycle gives 1, a 2-cycle gives 1, and the 5-vertex rotational tournament gives 3.

All of the following identities held on every trial (random digraphs with n ≤ 8, seeded):
- R4 (2-cycle cancellation)
- R4b (cancellation then SCC)
- R5(i) (unweighted)
- R6 (in = out = 1 bypass, summing into existing arcs)
- R13 (module quotient)
- R2 (cut-vertex additivity)
- R9 (≈2,000 instances)
- R16 (≈32,000 instance–pair checks)

A deliberately false rule (naive in-degree-1 contraction) produced counterexamples (34 of 300 random trials), so the checker discriminates. These checks are empirical support, not proofs. The proof sketches are given with each [OWN] rule.

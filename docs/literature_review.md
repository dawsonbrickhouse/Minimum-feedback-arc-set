# Literature review (project copy)

This document condenses the verified literature review compiled for this Project by a separate literature worker (the Project store file `internal/literature_review.md`, dated 2026-10-29). Sections 1–6 contain only citations from that review. Section 7 lists the platform author's own web searches, with the same tags. Every entry keeps the **verification tag** it carries in that review:

| Tag | Meaning |
|---|---|
| [V-src] | Checked against the primary full text. |
| [V-abs] | Checked against the abstract or metadata only. |
| [V-sec] | Checked only via a named secondary source. |
| UNVERIFIED | Pointer only. |
| [OWN] | The reviewer's own derivation, not found in a source. **These are not literature.** This project treats them as candidates needing proof. |

Anything this project derived itself is marked "this project" and appears in `candidate_rules.md` and `proof_obligations.md`, not here.

## 1. Hardness and approximation

- **R. M. Karp**, "Reducibility among combinatorial problems," *Complexity of Computer Computations*, Plenum, 1972, pp. 85–103. doi:10.1007/978-1-4684-2001-2_9. [V-abs]. FAS is on Karp's list [V-sec: Baharev et al. 2021 §1.1].
- **V. Kann**, PhD thesis, KTH, 1992: FAS is APX-hard [V-sec: Baharev et al.]; primary text UNVERIFIED.
- **G. Even, J. Naor, B. Schieber, M. Sudan**, *Algorithmica* 20(2):151–174, 1998. doi:10.1007/PL00009191. [V-abs]. Gives an O(log n log log n) approximation [V-sec].
- **P. D. Seymour**, *Combinatorica* 15(2):281–288, 1995. doi:10.1007/BF01200760. [V-abs]. Fractional packing of directed circuits.
- **V. Guruswami, J. Håstad, R. Manokaran, P. Raghavendra, M. Charikar**, *SIAM J. Comput.* 40(3):878–914, 2011. doi:10.1137/090756144. [V-abs]. Under UGC, no constant-factor approximation [V-sec].
- **P. Eades, X. Lin, W. F. Smyth**, "A fast and effective heuristic for the feedback arc set problem," *Inf. Process. Lett.* 47(6):319–323, 1993. doi:10.1016/0020-0190(93)90079-O. [V-abs]/[V-sec]. A greedy linear-time ordering heuristic. This is the basis of the refuted candidate `greedy_max_delta_first`; its exactness was never claimed by the authors.

## 2. Exact algorithms

- **E. L. Lawler**, *IEEE Trans. Circuit Theory* 11(2):296–297, 1964. doi:10.1109/TCT.1964.1082291. [V-abs]. The O*(2^n) subset DP is *commonly attributed* to this paper; the attribution is UNVERIFIED.
- **H. L. Bodlaender, F. V. Fomin, A. M. C. A. Koster, D. Kratsch, D. M. Thilikos**, *Theory Comput. Syst.* 50(3):420–432, 2012. doi:10.1007/s00224-011-9312-0. [V-abs]. Exact algorithms for vertex ordering problems; content UNVERIFIED.
- **M. Hecht**, "Exact localisations of feedback sets," *Theory Comput. Syst.* 62(5):1048–1084, 2018. doi:10.1007/s00224-017-9777-6; arXiv:1702.07612. [V-src]. Covers the essential minor (chain contraction plus parallel merge), isolated cycles and resolvable graphs.
- **A. Baharev, H. Schichl, A. Neumaier, T. Achterberg**, "An exact method for the minimum feedback arc set problem," *ACM J. Exp. Algorithmics* 26, Art. 1.4, 2021. doi:10.1145/3446429. [V-src]. Lazy cycle-matrix ILP; Appendix A gives the safe-removal rules (R5–R8 below).
- **M. Grötschel, M. Jünger, G. Reinelt**, *Oper. Res.* 32(6), 1984 (doi:10.1287/opre.32.6.1195) [V-abs]; *Math. Program.* 33(1), 1985 (doi:10.1007/BF01582009) [V-abs]; "Comments on …", *ACM JEA* 27, 2022 (doi:10.1145/3545001) [V-src].
- **M. Hecht, B. Gonciarz, S. Horvát**, "Tight localizations of feedback sets," *ACM JEA* 26, 2021. doi:10.1145/3447652. [V-abs]; content UNVERIFIED.
- **R. Martí, G. Reinelt**, *The Linear Ordering Problem*, Springer, 2011. doi:10.1007/978-3-642-16729-4. [V-abs].
- **I. Charon, O. Hudry**, surveys, *4OR* 2007 (doi:10.1007/s10288-007-0036-6) and *Ann. Oper. Res.* 2010 (doi:10.1007/s10479-009-0648-7). [V-abs].
- **R. Kudelić**, *Feedback Arc Set: A History of the Problem and Algorithms*, Springer, 2022. doi:10.1007/978-3-031-10515-9. [V-abs].

## 3. Kernelization and parameterized algorithms

- **J. Chen, Y. Liu, S. Lu, B. O'Sullivan, I. Razgon**, *J. ACM* 55(5), 2008. doi:10.1145/1411509.1411511. [V-abs]. DFVS (and hence FAS) is FPT in k.
- **Polynomial kernel for FAS by solution size:** open, to the reviewer's knowledge (reviewer's assessment, tied to the open DFVS kernel question; Bergougnoux et al., *Algorithmica* 83(5), 2021, doi:10.1007/s00453-020-00777-5 [V-abs]).
- **R. Crowston, G. Gutin, M. Jones**, FSTTCS 2012; arXiv:1207.3586. [V-src] arXiv. Two-way reduction Rules 1 and 2 (R14).
- **M. Dom, J. Guo, F. Hüffner, R. Niedermeier, A. Truß**, *J. Discrete Algorithms* 8(1):76–86, 2010. doi:10.1016/j.jda.2009.08.001. [V-src].
- **S. Bessy, F. V. Fomin, S. Gaspers, C. Paul, A. Perez, S. Saurabh, S. Thomassé**, "Kernels for feedback arc set in tournaments," *JCSS* 77(6):1071–1078, 2011. doi:10.1016/j.jcss.2010.10.001. [V-src]. Safe partitions (Lemma 2.4 holds for general digraphs) and the transitive module rule.
- **C. Paul, A. Perez, S. Thomassé**, *JCSS* 82(2), 2016. doi:10.1016/j.jcss.2015.08.002. [V-abs]. Conflict packing.
- **N. Betzler, R. Bredereck, R. Niedermeier**, *Auton. Agents Multi-Agent Syst.* 28(5):721–748, 2014. doi:10.1007/s10458-013-9236-y. [V-src]. Kemeny-specific data reduction (Extended Condorcet rule).
- **R. Kiesel, A. Schidler**, ALENEX 2023. doi:10.1137/1.9781611977561.ch4. [V-src]. DFVS reduction rules (PACE 2022 winner); these apply to FAS only via the line digraph.
- **E. Großmann, T. Heuer, C. Schulz, D. Strash**, PACE 2022 report, IPEC 2022, LIPIcs 249 Art. 26. doi:10.4230/LIPIcs.IPEC.2022.26. [V-src].
- **Tournaments:** NP-hard (Alon 2006, doi:10.1137/050623905; Charbit–Thomassé–Yeo 2007, doi:10.1017/S0963548306007887) [V-abs]; subexponential FPT (Alon–Lokshtanov–Saurabh 2009; Feige 2009; Karpinski–Schudy 2010) [V-abs]/[V-sec].

## 4. Polynomial special cases (summary)

The reviewer classes these as polynomial, with the tags shown:
- planar digraphs (via Lucchesi–Younger, doi:10.1112/jlms/s2-17.3.369 [V-abs]);
- weakly acyclic digraphs [V-sec];
- reducible flow graphs (Ramachandran 1988, doi:10.1016/0196-6774(88)90022-3) [V-abs];
- Hecht's "resolvable" graphs [V-src].

FAS remains NP-complete for maximum in- and out-degree at most 3 (Gavril 1977; [V-sec], primary UNVERIFIED).

## 5. Known safe reduction rules and how this project uses them

| Review id | Rule | Tag | Used here as |
|---|---|---|---|
| R1 | SCC decomposition | [V-src] | baseline B3 |
| R2 | Block (biconnected) decomposition (Park–Akers 1992) | [V-sec] | baseline B6 |
| R3 | Self-loop | [V-src] Baharev Fig. 4(1) | baseline B1 |
| R4 | 2-cycle cancellation | **[OWN]** | candidate `two_cycle_cancellation` (proved in `proof_obligations.md`) |
| R4b | Cancellation + SCC | **[OWN]**; the Kemeny analogue (Extended Condorcet) is [V-src] | not separately implemented (it is the composition of the two) |
| R5 | Baharev 2-cycle patterns | [V-src] | baseline B5 |
| R6 | Chain bypass / essential minor | [V-src] Baharev Fig. 4(4–6), Hecht Def. 4 | baseline B4 |
| R7 | Parallel-arc merge | [V-src] Hecht | built into the multigraph representation |
| R8 | Baharev general safe-arc rule | [V-src] | not implemented (cost) |
| R9 | In-degree-1 exchange | **[OWN]** | candidate `in_degree_one_exchange` |
| R10 | Safe partition (Bessy et al. Lemma 2.4) | [V-src] | not implemented; future work |
| R11, R12 | Tournament module / kernel rules | [V-src] | not used (tournament- or k-specific) |
| R13 | Module / quotient | **[OWN]** | candidate `module_contraction` |
| R14 | Crowston–Gutin–Jones two-way rules | [V-src] | not implemented. Rule 1 is implied by B6 (blocks); Rule 2 is a 3-terminal replacement, compare `three_terminal_gadget` |
| R15 | Kemeny rules | [V-src] | not applicable to general digraphs |
| R16 | Arc domination | **[OWN]** | candidate `arc_domination` |
| R17 | Hecht isolated-cycle rule | [V-src] | not implemented |

**Naive in-degree-1 contraction is not exact for FAS.** The review gives a 4-arc counterexample ([OWN] brute force). This project's harness rediscovers it independently, and minimises an 8-vertex instance to an isomorphic 3-vertex, 4-arc graph (see `candidate_rules.md`).

## 6. Where new rules might exist (reviewer's assessment, §7 of the review)

The reviewer's assessment lists these directions:

1. arc-level translations of DFVS rules (DOME++ and the vertex-cover lifts);
2. unweighted-closed gadget replacement for small interfaces ("protrusion replacement"; s = 2 and s = 3 terminals);
3. safe partitions in sparse digraphs;
4. near-modules;
5. structure that remains after 2-cycle cancellation;
6. cheaper isolated-cycle certificates;
7. theory gaps:
   - a polynomial kernel for FAS by k;
   - a better-than-2^n exact algorithm;
   - a characterisation of resolvable graphs;
   - the treewidth dependence.

This project followed up items 2, 4 and 5 (see `research_notebook.md`).

## 7. Own searches by the platform author (2026-10-29)

These are web searches made to check the candidates' prior art. They were short. "Not found" means only that these searches did not find a source.

| Candidate | Source found | Tag | What it establishes |
|---|---|---|---|
| `two_cycle_cancellation` | F. J. Brandenburg, K. Hanauer, "Sorting heuristics for the feedback arc set problem," Univ. Passau tech. report MIP-1104, Feb 2011, §2.1 | [V-src] (read directly) | Preprocessing for 2-cycles: erase both arcs and later re-insert the one that agrees with the order. This is the unweighted form of the cancellation. Status: **PRIOR_ART_FOUND**. |
| `two_terminal_separator` | Z. Nutov, M. Penn, "On integrality, stability and composition of dicycle packings and covers," *J. Comb. Optim.* 4(2):235–251, 2000, doi:10.1023/A:1009802905533 | [V-abs] (Springer abstract page) | The abstract says: "Assume D has a 2-vertex cut. We show how to derive a minimum dicycle cover … by composing certain covers … of the corresponding pieces. The composition of the covers is simple and was partially considered in the literature before." The exact gadget is unverified. Status: **PRIOR_ART_FOUND** (abstract level). |
| block (biconnected) splitting, baseline B6 | Wikipedia, "Feedback arc set" | [V-sec] | Cites Park–Akers 1992 for biconnected splitting and Nutov–Penn for triconnected decomposition. Consistent with review R2. |
| `three_terminal_gadget` | Protrusion replacement / finite integer index: Garnero, Paul, Sau, Thilikos, arXiv:1207.0835 (ICALP 2013 version doi:10.1007/978-3-642-39206-1_52); van Bevern et al.-style lower bounds, arXiv:1609.09304 | [V-src] for definitions only (ar5iv text) | These give the general framework: replace a t-boundaried piece by an equivalent representative. Neither paper states anything about FAS, and no FAS 3-terminal realisation was found. The gluing lemma is standard. Status: **NOVELTY_UNVERIFIED**. |
| `module_contraction` | Ando, Sugimoto, Sukegawa, "Decomposition-based constructive heuristics for the linear ordering problem," arXiv:2606.24558 (2026) | [V-src] (text fetched) | **Not prior art.** The search engine's summary claimed it uses modular decomposition. The fetched text contains no occurrence of "module"; it partitions by heuristic minimum cuts. No source for the weighted module quotient identity was found. Status: **NOVELTY_UNVERIFIED** (very plausibly folklore). |
| `in_degree_one_exchange`, `arc_domination`, `neighborhood_dominance` | none searched beyond the review | — | **NOVELTY_UNVERIFIED** |

**A caution recorded for future searches.** Automated search summaries made two unsupported claims in this session:

- that a heuristic paper used modular decomposition;
- that protrusion results "establish" facts about FAS.

Only claims checked against fetched text are tagged [V-src] above.

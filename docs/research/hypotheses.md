# Hypotheses Log

Track beliefs, confidence levels, and validation status.

**Last Updated:** 2026-02-13

---

## Summary

| Status | Count |
|--------|-------|
| Validated | 0 |
| Invalidated | 0 |
| Uncertain | 3 (H1a: 65%, H1b: 80%, H1c: 75%) |
| Retired | 1 |
| **Total Active** | **3** |

---

## Active Hypotheses

### H1a: Token efficiency of hierarchical retrieval

**Status:** uncertain
**Confidence:** 65%
**Created:** 2026-02-13
**Last Updated:** 2026-02-13

**Statement:**
Under hard token budgets (<400 tokens), hierarchical coarse-to-fine retrieval achieves equivalent or better answer accuracy than flat similarity retrieval with unconstrained token spend over the same corpus.

**Evidence For:**
- RB-001: Prior art shows hierarchical systems (RAPTOR, LATTICE) outperform flat RAG by 2-20pp on complex tasks
- RB-001: No existing system targets hard token budgets as primary constraint — this is an untested but structurally sound niche
- RB-002: Hierarchy provably reduces search space, which directly maps to fewer retrieved tokens
- RB-004: Federated search finding — 300–500 sampled documents per source produce effective routing (CORI) — suggests routing index can work even with partial source access under tight budgets

**Evidence Against:**
- RB-002: Strict elimination compounds error at (1-ε)^d — token savings from aggressive pruning come at accuracy cost
- RB-001: RAPTOR's collapsed-tree approach (enter at any level) suggests rigid top-down traversal isn't optimal — token efficiency may require flexible entry points

**Implications:**
- If true: HCR's core value proposition is validated — correct answers with minimum context
- If false: Hierarchy may still help quality but not enough to justify the constraint; token budgets may need to be relaxed or the approach rethought

**Validation Path:**
- RB-003 (scoring mechanics) informs feasibility of maintaining accuracy under tight budgets
- RB-006 (benchmark design) will define the experimental protocol
- Empirical test: compare HCR (<400 tokens) vs flat retrieval (unconstrained) on precision-critical queries

**History:**
- 2026-02-13: Created at 65%. Split from original H1 after RB-002 theoretical analysis. Prior art supports hierarchy advantage; token budget constraint is novel and untested.
- 2026-02-13: RB-004 adds federated search evidence (CORI: effective routing from partial representations). No confidence change — RB-006 benchmark needed to test token budget claim directly.

---

### H1b: Hybrid coarse-to-fine superiority

**Status:** uncertain
**Confidence:** 80%
**Created:** 2026-02-13
**Last Updated:** 2026-02-13

**Statement:**
Coarse elimination (hierarchy-guided routing) combined with fine similarity search within surviving branches outperforms either pure elimination or pure similarity retrieval alone on precision and recall.

**Evidence For:**
- RB-002: Three independent sources converge — hybrid coarse-to-fine is theoretically optimal under realistic conditions
- RB-002: RAPTOR's collapsed-tree result empirically demonstrates that flexible traversal (a form of coarse-to-fine) beats strict top-down
- RB-002: Information-theoretic analysis shows hierarchy reduces entropy (good for routing) while similarity handles residual ambiguity (good for selection)
- RB-004: Three-source convergence on top-down divisive clustering + beam search traversal — the construction literature independently recommends the hybrid architecture as the natural design, not just the theoretical optimum
- RB-004: Selective search (shard selection → flat search within selected shards) is structurally identical to HCR's hybrid approach and is a proven paradigm in federated search
- RB-004: Bonsai/PECOS from XMC literature confirms shallow+wide (K=100, depth 1–2) outperforms deep binary trees — empirical support for coarse routing

**Evidence Against:**
- RB-002: Under stringent conditions (strong clustering, admissible scoring, modest depth), strict elimination alone can match or beat hybrid — but these conditions are hard to guarantee in practice
- No direct empirical comparison of hybrid vs enriched flat RAG (with reranking, HyDE, etc.) under identical conditions

**Implications:**
- If true: HCR's traversal strategy should be "route coarsely, search finely" — beam width > tree depth
- If false: One of the pure approaches dominates, simplifying the architecture but narrowing the advantage

**Validation Path:**
- ~~RB-003 will determine scoring feasibility for the coarse routing stage~~ — **confirmed** (cascade architecture, ε ≈ 0.01–0.02)
- ~~RB-004 (tree construction) will determine if trees can be built to support coarse routing effectively~~ — **confirmed** (convergent construction recipe with principled methods)
- Empirical test: compare pure elimination, pure similarity, and hybrid on same corpus and queries (RB-006)

**History:**
- 2026-02-13: Created at 75%. Strongest theoretical support of the three sub-hypotheses. Three-source consensus from RB-002.
- 2026-02-13: Updated to 80%. RB-004 provides three-source construction consensus directly supporting the hybrid architecture. Top-down divisive clustering + beam search IS the hybrid approach. Selective search from federated search literature is a proven analog. Both validation gates (RB-003 scoring, RB-004 construction) now confirmed — remaining uncertainty is purely empirical (RB-006).

---

### H1c: Scoring quality as exponential lever

**Status:** uncertain
**Confidence:** 75%
**Created:** 2026-02-13
**Last Updated:** 2026-02-13

**Statement:**
Per-level scoring quality is the primary determinant of hierarchical retrieval quality, with error compounding at (1-ε)^d where ε is per-level error rate and d is tree depth. Achieving admissible or calibrated scoring is both feasible and necessary for HCR to outperform flat retrieval.

**Evidence For:**
- RB-002: All three sources identify (1-ε)^d as the governing equation — small improvements in ε yield exponential gains
- RB-002: This is mathematically derived, not empirical speculation — the compounding is structural
- RB-001: LATTICE uses LLM-as-judge scoring and achieves strong results, suggesting high-quality scoring is feasible
- RB-003: Cascade architecture (hybrid pre-filter → cross-encoder) achieves ε ≈ 0.01–0.02 per level at ~40–80ms latency — feasible and within target
- RB-003: LATTICE ablations confirm scoring calibration has large impact on end-to-end performance; path-relevance EMA is the highest-leverage component
- RB-004: Summary quality confirmed as the #1 upstream factor with a convergent construction recipe — structured contrastive routing summaries, entity preservation, and ColBERT-style multi-vector representations directly enable low-ε scoring

**Evidence Against:**
- RB-002: "Admissible" scoring (never incorrectly prune the correct branch) may be unrealistically strict in practice
- RB-001: No system in the prior art reports achieving formally admissible scoring bounds
- RB-003: Strict admissibility confirmed impossible for semantic relevance — only achievable for embedding-distance proximity, not answer relevance
- RB-003: ε is dominated by summary quality and query distribution, not scoring method alone — "scoring quality" is a system property, not a function property
- RB-004: Summary hallucination risk (~4% in RAPTOR) could inject false routing signals — hallucinated hook terms are more dangerous than hallucinated narrative because hooks drive elimination decisions

**Implications:**
- If true: Scoring is where R&D effort should concentrate — it's the highest-leverage component
- If false: Scoring quality has diminishing returns, and the architecture should compensate with wider beams or shallower trees instead

**Validation Path:**
- **RB-003 (scoring mechanics) is the direct test** — what scoring methods exist, what accuracy is achievable, at what cost
- Empirical: measure per-level accuracy of different scoring methods (embeddings, LLM-as-judge, hybrid, geometric bounds)
- Sensitivity analysis: how does retrieval quality degrade as ε increases?

**History:**
- 2026-02-13: Created at 70%. Mathematically grounded via RB-002. Feasibility of admissible scoring is the open question — RB-003 will address this directly.
- 2026-02-13: Updated to 75%. RB-003 confirms (1-ε)^d mechanism and demonstrates feasible cascade architecture achieving ε ≈ 0.01–0.02. Strict admissibility ruled out; probabilistic ε control is the path. Key nuance: "scoring quality" = full system (summaries + cascade + calibration + beam), not one function.
- 2026-02-13: RB-004 adds construction-side evidence. Routing summaries (structured, contrastive, entity-preserving) are the upstream enabler for low ε. Also adds hallucination risk as a new "evidence against" factor. No confidence change — H1c is about scoring feasibility (already confirmed by RB-003); construction quality supports but doesn't independently change the scoring claim.

---

## Retired Hypotheses

### H1 (original): Elimination vs similarity

**Status:** retired (reframed)
**Final Confidence:** 55% (strict elimination) / 70% (hybrid reframing)
**Created:** 2026-02-13 (project inception)
**Retired:** 2026-02-13

**Original Statement:**
Retrieval by elimination (narrowing through tree layers) outperforms retrieval by similarity (nearest-neighbour in vector space) for precision-critical, token-sensitive LLM systems.

**Reason for Retirement:**
RB-002 theoretical analysis from three independent sources concluded this framing is too binary. Strict elimination is theoretically fragile (error compounds at (1-ε)^d). The real question isn't elimination *vs* similarity — it's how to combine them optimally. Reframed as three independent, testable sub-hypotheses: H1a (token efficiency), H1b (hybrid superiority), H1c (scoring as lever).

**Legacy:**
The original hypothesis drove the right research. Its failure as stated is a feature — it forced us to find a more precise, testable set of claims.

---

## Validated Hypotheses

*None yet.*

---

## Invalidated Hypotheses

*None yet.*

---

## How to Update

1. **New hypothesis:** Add to Active Hypotheses with initial confidence
2. **Evidence found:** Update confidence %, add to Evidence For/Against
3. **Validated:** Move to Validated section, document final evidence
4. **Invalidated:** Move to Invalidated section, document why

**Confidence Guidelines:**
- 0-25%: Speculation, little evidence
- 26-50%: Plausible, some supporting evidence
- 51-75%: Likely, substantial evidence
- 76-90%: High confidence, strong evidence
- 91-100%: Near certain, overwhelming evidence

**Always justify confidence changes** with specific evidence references.

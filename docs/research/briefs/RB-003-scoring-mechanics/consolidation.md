# RB-003: Scoring Mechanics — Consolidation

**Date:** 2026-02-13
**Status:** Complete (3/4 sources — Gemini unavailable)
**Brief:** [RB-003 Prompt](./prompt.md)
**Sources:** GPT, Claude, Perplexity

## Summary

Three sources independently analysed the scoring landscape for hierarchical retrieval routing. The convergence is exceptionally strong — all three arrive at the same architectural recommendation through complementary analytical routes: **a per-level cascade of cheap high-recall pre-filtering (embeddings + BM25) followed by expensive high-precision reranking (cross-encoder) is the practical optimum for HCR's tree parameters (b=8–12, d=2–3), achieving per-level error rates ε ≈ 0.01–0.02 at sub-100ms latency.** Formal admissibility (guaranteed zero false negatives) is achievable only via metric-tree bounds on embedding geometry, not on semantic relevance — all three sources agree this is a structural impossibility, not an engineering gap. The most actionable surprise finding is LATTICE's ablation result: **path-relevance smoothing (EMA across tree depth) matters more than per-node scoring sophistication**, suggesting HCR should invest in path-level score aggregation before optimising individual node scorers. For token-budget selection, the submodular knapsack framing (AdaGReS) provides a theoretically grounded approach with (1−1/e) approximation guarantees via greedy algorithms.

---

## Consensus

All three sources agree on the following. Confidence reflects strength and independence of corroboration.

| # | Finding | GPT | Perplexity | Claude | Confidence |
|---|---------|-----|------------|--------|------------|
| 1 | **Cascaded scoring is the recommended architecture.** Cheap pre-filter (embedding/BM25 hybrid) → cross-encoder rerank → optional LLM escalation. No single scoring method dominates across accuracy, cost, and reliability. | Yes — frames as attentional cascade with near-zero false negatives at stage 1 | Yes — three-stage cascade (hybrid → cross-encoder → LLM for borderline) | Yes — two-stage cascade per level; embedding top-3 → cross-encoder top-1–2; ~80ms total | **Very High** |
| 2 | **Strict admissibility is unattainable for semantic relevance.** Only metric-tree bounds (triangle inequality over embedding centroids/radii) provide formal guarantees, and only for "nearest in embedding space" — not for "answer relevance." Text summaries are structurally different from geometric envelopes. | Yes — Ram & Gray MIPS bounds; but summaries are not geometric envelopes | Yes — explicitly: "essentially unattainable for semantic relevance"; metric bounds are tautological for actual QA relevance | Yes — ball tree bounds require centroids, not summaries; curse of dimensionality degrades them in 768d+ | **Very High** |
| 3 | **Top-k selection > threshold-based filtering.** Keeping top-3 of b=10 branches achieves recall@3 of 97–99% and is more robust than absolute score thresholds, which fail when score distributions shift across queries. | Yes — wide beam at level 1, conservative acceptance | Yes — "keep top-2–3 branches per level, not top-1"; cumulative probability ≥ 0.99 | Yes — top-k is invariant to score distribution shifts; recall@3 ≈ 97–99% | **Very High** |
| 4 | **Cross-level calibration is a first-order design concern.** RAPTOR's collapsed-tree result is direct empirical evidence that naive top-down scoring loses relevant results. Ranking losses produce inherently uncalibrated scores — a score of 0.72 at level 1 and 0.72 at level 2 reflect entirely different relevance distributions. | Yes — RAPTOR's collapsed tree outperforms traversal; level-conditioned calibration needed | Yes — "breaks any naive strategy that compares scores across levels"; level-specific normalisation required | Yes — "first-order design concern, not an optimization"; five concrete techniques enumerated | **Very High** |
| 5 | **LATTICE's path-relevance EMA is the most critical component.** Ablations show removing path smoothing causes the largest performance degradation — more than removing reasoning or per-node calibration. | GPT: LATTICE ablations confirm calibration is pivotal | Perplexity: "removing path smoothing or calibration degrades nDCG@10 by several points" | Claude: "single most important component"; path-relevance EMA with α=0.5 | **Very High** |
| 6 | **Pure embedding similarity on summaries is insufficient for ε ≤ 0.02.** Embedding anisotropy compresses cosine scores into narrow ranges. Summary embeddings systematically underestimate descendant relevance for detail queries (DPI). Per-level error in high single digits or worse on challenging queries. | Yes — anisotropy reduces discrimination; detail queries fail against thematic summaries | Yes — "not sufficient on its own"; per-level ε in high single digits on hard queries | Yes — 85–92% top-1 accuracy (i.e., 8–15% error); top-3 recall 97–99% only partially mitigates | **Very High** |
| 7 | **ε ≤ 0.02 per level is achievable with cascade + calibration.** For b=10, d=2: embedding pre-filter (top-3) → cross-encoder rerank → yields combined ε ≈ 0.005–0.02 per level. Requires treating routing as supervised classification, not just raw similarity. | Yes — "buy down false negatives" via conservative acceptance + stronger scorers on borderline | Yes — "plausible but not trivial"; requires supervised calibration, top-2–3 branches, and cross-encoder on ambiguous nodes | Yes — specific cascade: ε ≈ 0.005–0.015 per level; ~80ms latency; ~98% end-to-end for d=2 | **High** |
| 8 | **Routing is subtree membership prediction, not ranking.** The question at each node is "does any descendant contain the answer?" — closer to binary classification than top-k document selection. This distinction matters for how scoring models are trained and evaluated. | Yes — "subtree membership prediction"; prior art reports wrong metrics (nDCG, not per-level recall) | Yes — "does this subtree contain at least one answer?" frames the label for calibration models | Yes — implicit in the cascade design; coarse routing = high-recall binary filter | **High** |
| 9 | **AdaGReS / submodular knapsack is the right framing for token-budget selection.** Greedy selection under token budget with relevance − redundancy penalty yields near-optimal subsets due to ε-approximate submodularity. (1−1/e) approximation guarantee. | Yes — MMR + submodular summarisation; AdaGReS directly aligned | Yes — AdaGReS formalisation; closed-form adaptive β*; "frontier, but well founded" | Yes — submodular knapsack; MMR, DPPs, per-token value scoring; RAPTOR 18.5–57% non-leaf nodes as density signal | **High** |
| 10 | **Cross-encoders are feasible at HCR's tree scale.** With b=10 and beam k=3, you score only ~10–40 nodes per query. Even full cross-encoder scoring of this set takes <20ms on GPU. The b/d regime makes expensive methods practical that would be impractical at scale. | Yes — "tens to low hundreds of pairs"; engineering question, not combinatorial | Yes — "<10–20ms" GPU for 10–30 nodes; feasible even on CPU | Yes — MiniLM-L6 at 1,800 docs/sec; batch of 10 takes ~59ms; 3 survivors ~20ms | **High** |
| 11 | **LATTICE validates LLM-guided hierarchical routing.** Recall@100 = 74.8% vs BM25 65.3% and ReasonIR-8B 70.8% on BRIGHT. Zero-shot, no fine-tuning. Competitive with fine-tuned SOTA (nDCG@10 51.6 vs DIVER-v2 52.2). Cost grows logarithmically with corpus size. | Yes — LATTICE is best concrete reference for LLM-based tree traversal; ~250 docs evaluated per query | Yes — detailed LATTICE analysis; nDCG@10 51.6 vs 47.4 (BM25+LLM rerank); latent-score calibration mechanism | Yes — detailed architecture; contextual calibration via anchor nodes; beam=2 sufficient; EMA path smoothing | **High** |
| 12 | **Summary quality is the #1 upstream factor.** No amount of scoring sophistication compensates for poorly differentiated summaries. Well-crafted, distinctive node descriptions that clearly separate branch content are the single most impactful factor in achievable error rates. | Implicit — summary-driven traversal failures are structural when summaries are poor | Implicit — "summaries as lossy channels (DPI) systematically hurt detail-heavy queries" | Explicit — "Quality of summaries is the single most impactful factor" in the five-factor ranking | **High** |
| 13 | **ColBERT/late-interaction is an underexplored middle ground.** Multi-vector scoring preserves "detail hooks" (rare entities, code tokens) that single-vector embeddings wash out. Approaches cross-encoder quality at much lower cost. | Yes — "detail hooks" preserved; scalable and pruning-friendly | Yes — matches/exceeds cross-encoders; FastLane for routed late interaction | Yes — ColBERTv2 MRR@10=39.7; 2 orders of magnitude fewer FLOPs than cross-encoder | **Medium** |

---

## Conflicts

| # | Point of Conflict | Position A | Position B | Assessment |
|---|-------------------|-----------|-----------|------------|
| 1 | **Practical value of metric-tree bounds** | Claude and GPT describe dual-representation (summary + centroid/radius) as a viable "belt and suspenders" safety net. GPT specifically cites Ram & Gray's MIPS bounds as "what buys HCR safe pruning." | Perplexity argues metric-tree bounds are "tautological" for semantic relevance — they only guarantee nearest-in-embedding, not answer-relevance. Using them is "just doing nearest-neighbor search." | **Perplexity's framing is more precise.** Metric bounds guarantee you won't miss the closest embedding, but that's not the same as not missing the answer. However, Claude's point about curse of dimensionality is also correct — even for the embedding-distance guarantee, bounds are rarely tight in 768d. The dual-representation idea has merit only if embedding distance correlates strongly with answer relevance in the specific domain. **Not worth the architectural complexity as a default.** |
| 2 | **Specific ε estimates** | Claude provides concrete ε ≈ 0.005–0.015 per level for the embedding → cross-encoder cascade, with detailed probability calculations. | GPT and Perplexity are more cautious: "plausible but not trivial" (Perplexity); "buy down effective false negatives" without specific numbers (GPT). | **Claude's numbers are reasonable but optimistic.** The P(miss) ≈ 0.02 × 0.03 = 0.0006 calculation assumes independence of embedding and cross-encoder errors, which likely doesn't hold (both may fail on the same hard queries). Real ε is probably in the **0.01–0.02 range** rather than 0.005. Perplexity's caution is warranted — actual ε depends heavily on query distribution and summary quality. |
| 3 | **Whether to include BM25 in the hybrid** | Perplexity explicitly recommends hybrid sparse+dense (BM25 + embeddings) as the base signal, arguing lexical matching catches tail cases (error codes, identifiers, rare names). | Claude's cascade starts with dense embeddings only; BM25/SPLADE mentioned but not in the primary recommendation. GPT mentions sparse/lexical as a separate method. | **Perplexity is right.** Hybrid sparse+dense is strictly superior to dense-only for coarse routing. BM25 catches precisely the "needle" queries where embedding similarity fails (specific identifiers, code references). RRF fusion is cheap and proven. **Hybrid should be the default first stage.** |
| 4 | **Three-stage vs two-stage cascade** | Perplexity recommends a three-stage cascade: hybrid scoring → cross-encoder on borderline → LLM-as-judge only if necessary. This is adaptive — LLM cost only incurred for hard cases. | Claude recommends a simpler two-stage cascade: embedding → cross-encoder, with LLM mentioned as optional escalation but not part of the primary design. | **Both are valid; the choice depends on query distribution.** For Su's use case (organisation knowledge, not academic reasoning), the two-stage cascade likely suffices. Three-stage adds complexity and latency for marginal gain on in-domain queries. **Default to two-stage; add LLM escalation only if empirical ε is too high.** |

---

## Gaps

### Between sources
- **Gemini unavailable** — unlikely to change conclusions given strong three-source convergence.
- **No source provided empirical per-level ε measurements** from any real hierarchical system. All ε estimates are extrapolated from standard retrieval benchmarks (MS MARCO, BEIR). LATTICE reports end-to-end Recall@100 but not per-level routing accuracy. This is the most important missing data point.
- **GPT uniquely surfaced** Cohen et al.'s Bayesian retrieval calibration framework (uncertainty-aware scoring with ranking-based calibration metrics) — relevant for SPRT-style routing decisions.
- **Claude uniquely surfaced** Penha and Hauff's finding that BERT rankers are NOT robustly calibrated, and that MC Dropout stochastic scoring yields better calibration — potentially valuable for critical routing decisions.
- **Perplexity uniquely surfaced** CalibRAG (calibrating document-level confidence in RAG specifically) and ToolRerank (hierarchy-aware reranking/truncation policies).
- **Claude uniquely provided** HyDE as a cross-level calibration technique — generating hypothetical answers at different abstraction levels to bridge the query-summary gap.

### In the theory
1. **No per-level ε measurements exist for any hierarchical retrieval system.** All systems report end-to-end metrics (Recall@K, nDCG). The metric that matters for HCR — "probability that the correct subtree is in the top-k at level l" — has never been reported. This must be part of HCR's benchmark design (RB-006).
2. **No paper solves SPRT for hierarchical retrieval end-to-end.** The pieces exist (probability calibration, uncertainty modelling, risk-aware cutoffs) but have not been composed into a framework for optimal traversal stopping.
3. **Cascade threshold optimisation for hierarchical routing is theoretically uncharted.** Standard cascade theory (Viola-Jones, Wang-Lin-Metzler) applies to flat pipelines. How to optimally set per-level thresholds when errors compound multiplicatively across depth is an open problem.
4. **No formal connection between summary quality and achievable routing ε.** All three sources flag summary quality as the #1 upstream factor, but no one quantifies the relationship. What makes a "good enough" summary for routing? What summary properties predict routing failure?

---

## Key Takeaways

### 1. The scoring architecture for HCR is a per-level cascade

All three sources converge on the same design:

**Per level:** Hybrid sparse+dense scoring (all children) → top-3 selection → cross-encoder rerank (survivors) → top-1–2 selection

- **Stage 1 cost:** <2ms (embedding lookup + BM25 + RRF fusion)
- **Stage 2 cost:** ~10–20ms (cross-encoder on 3 candidates)
- **Total per query (d=2):** ~40–80ms
- **Expected per-level ε:** 0.01–0.02 (with calibration)
- **End-to-end recall (d=2):** ~96–98%

LLM-as-judge is reserved for adaptive escalation when the cross-encoder score margin between top candidates is small — not applied uniformly.

### 2. Path-relevance smoothing is higher leverage than per-node scoring

LATTICE's ablation is the single most important empirical finding in this brief. Removing path-relevance EMA (α=0.5 smoothing across tree depth) degrades performance more than removing reasoning or per-node calibration. This means:

- **Invest in path-level aggregation before optimising individual node scorers**
- A simple path relevance estimate — `p_path(v) = α · p_path(parent) + (1-α) · calibrated_score(v)` — provides cross-level smoothing, noise reduction, and global comparability
- This is cheap to implement and can work with any base scorer

### 3. Admissibility is a design philosophy, not a formal guarantee

Strict admissibility (zero false negatives) is structurally impossible for semantic relevance. The practical approach is **probabilistic admissibility**:

- Top-k selection (k=3, b=10) provides recall ≈ 97–99% at negligible cost
- Calibrated probability thresholds give empirical control over ε
- Uncertainty-aware scoring (Bayesian/MC Dropout) adds a principled mechanism for detecting unreliable routing decisions
- **Design HCR around calibrated probabilities, not worst-case guarantees**

Metric-tree bounds (centroid + radius) are not worth the architectural complexity as a default — they guarantee embedding proximity, not answer relevance, and degrade severely in high dimensions.

### 4. Cross-level calibration requires level-specific treatment

Five techniques, in order of practical priority:

1. **Level-specific Platt scaling** — fit P(answer_in_subtree | score) per level; minimum viable approach
2. **Path-relevance EMA** (LATTICE-style) — smooths noise, enables cross-level comparison
3. **Sibling-relative ranking** — compare nodes only to siblings, not across levels; use RRF
4. **Child-representative embeddings** — aggregate children's embeddings at parent nodes for detail-query matching
5. **HyDE at different abstraction levels** — generate hypothetical answers matched to each tree level; one LLM call per query

### 5. Token-budget selection is a submodular knapsack problem

After routing produces a candidate set of leaf chunks, final selection under the 400-token budget should use:

- **AdaGReS-style greedy selection**: relevance − redundancy penalty, under token constraint
- **Per-token value scoring**: relevance(chunk) / token_count(chunk) as the marginal-gain metric
- **(1−1/e) ≈ 0.632 approximation guarantee** via greedy algorithms under approximate submodularity
- MMR as the simplest practical implementation; DPPs for the principled probabilistic version

### 6. Summary quality gates everything

All three sources identify summary quality as the dominant upstream factor. No amount of scoring sophistication compensates for poorly differentiated summaries. This feeds directly into RB-004 (tree construction):

- Summaries must clearly differentiate sibling branches
- Summaries should preserve "detail hooks" — rare identifiers, specific terms — not just thematic content
- The DPI bottleneck means summaries that are "too abstract" are structurally worse for routing than summaries that preserve key details

### 7. H1c (scoring as exponential lever) is confirmed — with nuance

The (1-ε)^d equation governs, exactly as theorised. But the nuance is:

- **Path-level aggregation matters more than per-node scoring precision** (LATTICE ablation)
- **The cascade architecture converts the problem from "achieve impossibly low ε with one method" to "compose multiple methods for effectively low ε"**
- **ε is dominated by summary quality and query distribution, not scoring method** for in-domain queries
- The exponential lever is real, but it's controlled by the full system (summaries + scoring + calibration + beam width), not by scoring alone

---

## Recommendation

**Decision required:** Yes — scoring architecture direction for Phase 1.

### Recommended Scoring Architecture

Based on three-source consensus, the recommended scoring design for HCR:

**Coarse routing (per internal node):**
1. Score all b children with hybrid BM25 + dense embedding (RRF fusion) — <2ms
2. Keep top-3 children
3. Cross-encoder rerank of 3 survivors — ~15ms
4. Keep top-1–2 for expansion
5. Adaptive escalation: if cross-encoder score margin between top-2 is below threshold, invoke LLM-as-judge for those candidates only

**Path-level aggregation:**
- Maintain path relevance: `p(v) = α · p(parent) + (1-α) · calibrated_score(v)`, α=0.5
- Use path relevance for best-first frontier expansion (beam search)

**Calibration:**
- Level-specific Platt scaling on (score, answer_is_below) labels
- Frame routing as binary classification: P(subtree contains answer | features)
- Measure ε empirically per level on held-out set with subtree-level ground truth

**Leaf selection under token budget:**
- Cross-encoder or ColBERT scoring of all leaves in surviving subtrees
- AdaGReS-style greedy packing: relevance − redundancy, subject to token budget ≤ 400

**Not recommended (for now):**
- Metric-tree bounds (architectural complexity, poor ROI for semantic relevance)
- LLM-as-judge at every node (latency, cost; reserve for escalation only)
- Strict admissibility targets (design for probabilistic ε control instead)

### What This Means for H1c

H1c stated: "Per-level scoring quality is the primary determinant of hierarchical retrieval quality."

The evidence **confirms the exponential sensitivity** ((1-ε)^d) but **refines what "scoring quality" means**:

- It's not about a single scoring function achieving impossibly low ε
- It's about the **system-level composition**: summaries → hybrid pre-filter → cross-encoder → path smoothing → calibration → beam width
- Path-level aggregation and cascade design are as important as per-node accuracy
- Summary quality upstream gates everything downstream

**Recommendation: Update H1c confidence from 70% to 75%.** The mechanism is confirmed; the achievability via cascade architecture is stronger than expected. The nuance that "scoring" means "the full scoring system, not one function" is an important refinement but doesn't weaken the hypothesis.

---

## Next Steps

1. **Update H1c confidence** to 75% based on confirmed exponential sensitivity + cascade feasibility
2. **RB-004 (Tree construction)** — now critical. Summary quality is the #1 upstream factor for scoring accuracy. How should trees be built to produce well-differentiated summaries? Shallow + wide is confirmed. What clustering produces the best routing-friendly summaries?
3. **RB-005 (Failure modes)** — cross-branch queries remain the structural weakness. But with beam k=3 and d=2, the exposure is manageable. Quantify: what fraction of real queries in target domains are cross-branch?
4. **RB-006 (Benchmark design)** must include **per-level ε measurement** — no existing system reports this metric. This is HCR's opportunity to set a new standard for hierarchical retrieval evaluation.
5. **When Phase 1 begins:** implement the cascade scorer as the first component. It's the most architecturally independent piece and can be validated before the tree construction is finalised.

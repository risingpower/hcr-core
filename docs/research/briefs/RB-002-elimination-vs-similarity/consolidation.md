# RB-002: Theoretical Basis — Consolidation

**Date:** 2026-02-13
**Status:** Complete (3/4 sources — Gemini unavailable)
**Brief:** [RB-002 Prompt](./prompt.md)
**Sources:** GPT, Claude, Perplexity

## Summary

Three sources independently analysed the theoretical foundations of elimination-based retrieval vs similarity-based retrieval. The convergence is striking — all three arrive at essentially the same conclusion through different analytical routes: **the tree structure creates genuine value through representation enrichment, but navigating it top-down via strict elimination is theoretically fragile and empirically dominated by flat search over the enriched representations (collapsed tree).** The conditions required for safe hierarchical elimination are stringent and rarely met in practice.

The theoretical toolkit is well-established — information theory (DPI, Information Bottleneck), decision theory (branch-and-bound, SPRT, cascade analysis), and classical IR (cluster hypothesis) — but **no unified formal theory exists for LLM-based hierarchical retrieval.** All three sources flag this as a critical gap.

The most actionable finding for HCR: strict top-down elimination is the wrong default. **Hybrid strategies** (shallow coarse filtering + flat search within surviving subtrees, or wide beam traversal) are theoretically grounded and avoid the compounding-error penalty that makes deep elimination fragile. HCR's design should orient toward "hierarchy for enrichment and coarse routing, flat search for final retrieval" — unless specific corpus/query conditions strongly favour elimination.

---

## Consensus

All three sources agree on the following. Confidence reflects strength and independence of corroboration.

| # | Finding | GPT | Perplexity | Claude | Confidence |
|---|---------|-----|------------|--------|------------|
| 1 | **Error compounding is the central fragility.** Per-level miss rate ε compounds as (1-ε)^d across depth d. At ε=0.10, d=5: recall ≈ 59%. At ε=0.10, d=10: recall ≈ 35%. This is structural to any sequential elimination scheme. | Yes — derives union bound and cascade analysis | Yes — derives same formula, connects to chain-of-thought error propagation | Yes — provides numerical table, derives power-law decay in corpus size | **Very High** |
| 2 | **Summaries are lossy channels, not sufficient statistics.** By the Data Processing Inequality, information about query-relevance monotonically decreases ascending the tree. LLM summaries are not sufficient statistics for descendant relevance — they discard information that may be critical for specific queries. | Yes — frames via IB, channel capacity | Yes — DPI Markov chain argument | Yes — DPI + IB, explicit sufficient statistic condition | **Very High** |
| 3 | **Branch-and-bound optimality requires admissible bounds, which summary embeddings do not provide.** Safe pruning requires provable upper bounds on descendant relevance. Cosine similarity to summary embeddings trivially violates this — detail queries can score low against high-level summaries but high against leaf chunks. | Yes — connects to metric-tree pruning and triangle inequality | Yes — notes no exact bounds exist for LLM retrieval | Yes — proves inadmissibility by counterexample (detail query vs thematic summary) | **Very High** |
| 4 | **The cluster hypothesis is necessary but not sufficient for safe elimination.** It is collection-dependent, not universal. Voorhees (1985) showed 8% failure in narrow domains but 46% failure in broad collections. Hard partitions are brittle when documents are multi-topic; overlapping clusters help but contradict single-path hierarchies. | Yes — cites cluster hypothesis limits, overlapping clusters | Yes — cites Voorhees, cluster search less effective than document search | Yes — cites Voorhees, anisotropy in embedding spaces, intrinsic dimensionality | **Very High** |
| 5 | **Cross-branch queries are the #1 failure mode.** When relevant information spans multiple semantic clusters (multi-hop, cross-cutting topics), elimination that commits to few branches early systematically misses evidence. This is structural, not fixable by better scoring alone. | Yes — notes multi-topic leaves and cross-branch evidence | Yes — details multi-hop queries as acute failure, cites HotpotQA/MuSiQue | Yes — identifies cross-cutting, multi-hop, and adversarial queries | **Very High** |
| 6 | **RAPTOR's collapsed-tree advantage is theoretically predicted.** Collapsed tree avoids compounding routing errors, adapts granularity per query, and can retrieve from any branch/level. All three sources derive this from first principles, not just empirical observation. | Yes — frames as "flattening" remedy for error propagation in deep hierarchies | Yes — five-part explanation (DPI, granularity mismatch, cross-branch, rank fusion, error propagation) | Yes — two-part explanation (enrichment value + elimination cost) | **Very High** |
| 7 | **Hybrid coarse-to-fine strategies are theoretically optimal.** Shallow hierarchy for coarse filtering (1-2 levels, low error compounding) then flat search within surviving subtrees. This mirrors IVF-style vector search, multi-stage retrieval cascades, and cascade design principles. | Yes — IVF analogy, cascade design principles | Yes — multi-stage cascade theory, explicit recall formula R1 × R2 | Yes — coarse-to-fine cascade, Matryoshka multi-resolution search | **Very High** |
| 8 | **Beam search dramatically mitigates error compounding.** Keeping top-k branches per level transforms recall from (1-ε)^d to approximately (1-(1-p)^k)^d, which is vastly better for modest k. The computational cost scales linearly with beam width. | Yes — connects to IVF nprobe parameter | Yes — derives formula, connects to rank fusion | Yes — provides numerical example (k=5, p=0.8 → near-perfect recall) | **Very High** |
| 9 | **No formal end-to-end theory exists for LLM-based hierarchical retrieval.** The theoretical tools exist (DPI, B&B, SPRT, cascades, cluster hypothesis) but have not been unified into a framework that models LLM summarisation noise, embedding-based scoring, and token budget constraints together. | Yes — explicit about what's proven vs conjectured | Yes — lists four specific gaps (summarisation sufficiency, correlated errors, cluster-recall bounds, optimal hybrid strategy) | Yes — details what a proper theory would need (generative model + non-asymptotic bounds + empirical calibration) | **Very High** |
| 10 | **Tight token budgets shift the objective from recall to precision/utility per token.** Under a 400-token budget, false positives are catastrophic (waste irreplaceable slots). This makes elimination higher-variance (correct routing → excellent context, misrouting → completely wasted budget). | Yes — frames as budgeted information acquisition, IB rate constraint | Yes — frames as knapsack problem over tree-structured candidates | Yes — frames as precision-oriented retrieval, variance analysis | **Very High** |
| 11 | **SPRT / sequential testing provides the right conceptual model for elimination decisions, but calibration is the missing piece.** If node scores were likelihood ratios with known distributions, SPRT would give optimal stopping rules. In practice, relevance scores are uncalibrated, shift by query type and abstraction level, breaking classical optimality premises. | Yes — derives SPRT framework, notes calibration gap | Yes — notes HE implements "very aggressive" one-shot elimination, far from SPRT optimality | Yes — derives SPRT expected stopping time, notes premature commitment cost | **High** |
| 12 | **Hierarchical softmax is the computational precursor.** Same promise (O(log N) vs O(N)), same limitation (accuracy degrades when tree doesn't match target distribution). Existence proof that tree-induced factorisations trade accuracy for efficiency unless hierarchy aligns with conditional distributions. | Yes — cites Morin & Bengio, performance degradation with poor trees | Yes — cites as "exactly analogous" condition set | Yes — notes proven optimality only with Bayes-optimal internal decisions | **High** |

---

## Conflicts

| # | Point of Conflict | Position A | Position B | Assessment |
|---|-------------------|-----------|-----------|------------|
| 1 | **Severity of optimal stopping limitation** | Claude cites the secretary problem: even with optimal stopping, probability of selecting the best single branch is at most ~37% (1/e) when branches are evaluated sequentially without recall. Calls this "sobering." | GPT and Perplexity do not invoke the secretary problem framing. | **Claude's application is illustrative but imprecise for retrieval.** The secretary problem assumes no information about candidates before evaluation and no ability to score candidates against a query. In retrieval, we have query-conditioned similarity scores, making the setting more favourable than the bare 1/e bound suggests. The qualitative point stands — sequential irrevocable decisions are structurally suboptimal — but the 37% number overstates the severity. |
| 2 | **Whether token budgets favour or disfavour elimination** | GPT and Claude argue tight budgets make elimination higher-risk due to catastrophic failure on misrouting (entire budget wasted). | Perplexity notes elimination *can* help under tight budgets when the tree is well-aligned, because concentrated context from one coherent region may outperform fragmented context from flat search. | **Both are correct — different conditions.** Tight budgets amplify both the upside and downside of elimination. If routing is correct, concentrated context is coherent and high-utility. If routing is wrong, the loss is total. The expected value depends entirely on routing accuracy. This is not a conflict but a conditional analysis — elimination under tight budgets is a high-variance strategy. |
| 3 | **Emphasis on enrichment vs elimination** | Claude states the "deepest insight" is architectural: "the value of hierarchy lies in representation enrichment, not in search-path restriction." Presents this as a strong conclusion. | GPT and Perplexity present the same finding more conditionally — acknowledging conditions where elimination can still win. | **All three agree on the direction; the difference is rhetorical emphasis.** Claude's framing is sharper but risks overstating certainty. The theoretical analysis supports "enrichment > elimination as default" but does not prove elimination can never win. The conditions for elimination winning (strong clustering, admissible bounds, calibrated scoring) are stringent but not impossible. |

---

## Gaps

### Between sources
- **Gemini unavailable** — unlikely to change the core finding given the strength of convergence across three independent sources.
- **Claude uniquely provided** the power-law recall decay formula: Recall(N) ≈ N^(log_b(1-ε)), connecting error compounding to corpus size. Neither GPT nor Perplexity derived this.
- **Claude uniquely cited** embedding anisotropy (Ethayarajh 2019, Godey et al. 2024) and intrinsic dimensionality (13-122 effective dimensions despite 128-5120 nominal) as factors that degrade hierarchical partitioning. This is relevant to scoring mechanics (RB-003).
- **Perplexity uniquely framed** the token budget problem as a knapsack optimisation over tree-structured candidates — a clean formalisation that could inform RB-003 and implementation design.
- **Perplexity uniquely connected** error compounding to chain-of-thought error propagation literature, drawing a structural parallel between multi-step reasoning failure and multi-level retrieval failure.
- **GPT uniquely highlighted** that ANN indexing (IVF, coarse quantisers) already embodies "hybrid elimination" — coarse cluster selection then fine search. This is the strongest argument that the hybrid approach is not speculative but already proven at scale.

### In the theory
1. **No formal characterisation of when LLM summarisation produces approximate sufficient statistics for retrieval relevance.** All three sources flag this. The IB framework provides the conceptual apparatus but the bridge to natural language summarisation is unbuilt.
2. **No recall bounds that account for correlated errors across tree levels.** The (1-ε)^d formula assumes independence. In practice, a bad parent summary affects all descendant scores — errors are positively correlated, making the independent model optimistic for some failure modes.
3. **No formal connection between cluster quality metrics and retrieval recall bounds.** Silhouette scores and Davies-Bouldin indices don't predict retrieval effectiveness. Different cluster hypothesis tests are negatively correlated with one another (Raiber & Kurland, 2014).
4. **No theory for optimal hybrid strategy parameters** (beam width, coarse-filtering depth, token allocation across granularities). The theoretical frameworks exist in pieces but have not been composed.

---

## Key Takeaways

### 1. The central equation: (1-ε)^d

This single formula captures the core theoretical challenge for HCR. Everything else follows from it:
- **Depth is dangerous.** Every level multiplies error. Shallow trees (d ≤ 3) with wide branching factors are strongly preferred.
- **Per-level accuracy must be extreme.** For d=5 at 95% overall recall, each level needs ≥99.0% accuracy. For d=10, ≥99.5%.
- **Beam search is the primary mitigation.** Keeping k branches per level transforms (1-ε)^d into (1-(1-p)^k)^d — exponentially better with modest k.

### 2. The RAPTOR result is theoretically inevitable, not anomalous

All three sources derive the collapsed-tree advantage from first principles. The tree creates valuable multi-granularity representations (enrichment), but forcing retrieval through the tree topology imposes irrecoverable routing decisions on lossy compressed representations (elimination cost). The enrichment benefit requires only that summarisation preserves *some* query-relevant information — a weak condition. Safe elimination requires admissible bounds, strong cluster alignment, and calibrated scoring — stringent conditions rarely met simultaneously.

**This is not a RAPTOR-specific result. It is a structural prediction for any system doing strict top-down elimination over LLM-generated summaries.**

### 3. HCR's design should be "enrichment + coarse routing", not "strict elimination"

The theoretical consensus points clearly: use the hierarchy for:
- **Enrichment** — creating multi-granularity representations worth searching
- **Coarse routing** — shallow (1-2 level) filtering to reduce search space, tuned for very high recall (low false negatives)
- **Not strict elimination** — deep sequential pruning with irrevocable branch cutting

The final retrieval within surviving subtrees should be flat similarity search (or reranking) across multiple abstraction levels, exactly as RAPTOR's collapsed tree operates within a candidate set.

### 4. The conditions where elimination wins are real but narrow

Elimination-based traversal can outperform enriched flat retrieval when **all** of:
1. **Partition-aligned relevance** — most queries have evidence in ≤ few subtrees
2. **High-information routing** — internal representations preserve enough MI to discriminate correctly
3. **Bounded-loss or calibrated pruning** — either admissible bounds (metric-tree style) or calibrated miss-probability control (cascade style)
4. **Modest depth or wide beam** — keeping (1-ε)^d manageable

The theoretical niche: highly structured, narrowly-scoped corpora (technical manuals partitioned by subsystem, regulatory codes partitioned by domain) where the cluster hypothesis holds strongly. HCR should not assume this is the general case.

### 5. Token budgets are a double-edged sword for elimination

Under a 400-token constraint:
- **Upside:** Correct routing → highly coherent, concentrated, high-utility context
- **Downside:** Misrouting → total budget waste (near-zero utility)
- **Implication:** Elimination under tight budgets is a high-variance strategy. The expected value depends entirely on routing accuracy.

The theoretically optimal approach under tight budgets: shallow coarse filtering → flat search within candidates → select mix of granularities (summary for context + leaf chunks for detail) to maximise information density per token.

### 6. H1 needs to be reframed

The original hypothesis — "retrieval by elimination outperforms retrieval by similarity" — is too blunt. The theoretical analysis reveals a more nuanced picture:

- **Hierarchy outperforms flat:** Yes, consistently. Building a tree creates valuable multi-level representations.
- **Elimination outperforms similarity:** Only under narrow conditions (strong clustering, admissible scoring, modest depth).
- **Enrichment + flat search outperforms both:** Theoretically predicted, empirically confirmed by RAPTOR.

H1 should be reframed to reflect HCR's actual value proposition, which the theory suggests lies in **precision under token constraints** and **coarse-to-fine efficiency at scale**, not in strict elimination per se.

---

## Recommendation

**Decision required:** No — but findings materially affect HCR's design direction and H1 framing.

### For HCR Design

The theoretical evidence strongly suggests HCR should not pursue strict top-down elimination as its primary retrieval strategy. Instead:

1. **Build the tree for enrichment and routing.** The hierarchy creates multi-granularity representations and enables coarse candidate filtering. This value is uncontroversial.
2. **Use shallow elimination (1-2 levels) for coarse filtering,** tuned for very high recall (≥99%). This exploits elimination's efficiency without incurring deep error compounding.
3. **Use flat search within surviving subtrees** across multiple abstraction levels for final retrieval. This captures the collapsed-tree benefit (adaptive granularity, no compounding errors) within a reduced search space.
4. **Beam width is the key parameter** — not tree depth. Wide beam + shallow depth > narrow beam + deep depth.
5. **Token budget optimisation becomes a knapsack problem** over the candidate set from step 3 — select the mix of nodes that maximises information density within the 400-token constraint.

This is a "coarse elimination + fine similarity" hybrid. It's not a retreat from hierarchy — it's the theoretically grounded way to use hierarchy.

### For H1

Reframe from:
> "Retrieval by elimination outperforms retrieval by similarity"

To something like:
> "Hierarchical coarse-to-fine retrieval with hard token budgets outperforms flat similarity retrieval for precision-critical, token-sensitive LLM systems"

This preserves HCR's differentiators (hierarchy, token budget, external source pointers) while aligning with the theoretical consensus that strict elimination is fragile.

### For RB-003 (Scoring Mechanics)

The theoretical analysis elevates scoring quality as the most critical design decision:
- Per-level accuracy drives (1-ε)^d — even small improvements in ε have exponential returns
- Calibration across levels is essential (LATTICE's key insight)
- Admissible bounds would be transformative — investigate whether geometric scoring (balls/radii) rather than summary embeddings could provide them
- The SPRT framework suggests: score interpretation should approximate likelihood ratios, not just similarity

### For RB-004 (Tree Construction)

Tree quality determines whether the stringent conditions for safe elimination are met:
- Cluster alignment with typical query relevance patterns is the key metric
- Shallow, wide trees are strongly preferred over deep, narrow ones
- Overlapping clusters may be necessary for multi-topic documents
- The tree should be designed for coarse routing reliability, not fine-grained discrimination

### For RB-005 (Failure Modes)

Cross-branch queries are theoretically the primary failure mode:
- Multi-hop queries violate the cluster hypothesis by construction
- Wide beam search mitigates but does not eliminate the problem
- Failure is structural for any tree-partitioned search when relevance crosses partition boundaries
- Quantify: what fraction of real queries in target domains are cross-branch?

---

## Next Steps

1. **Update H1** — reframe based on theoretical findings. Confidence should move from 65% to ~55% for strict elimination, but may increase for the hybrid formulation.
2. **RB-003: Scoring mechanics** — now the highest-priority brief. Scoring accuracy is the exponential lever. Investigate admissible bounds, calibration methods, and geometric scoring alternatives.
3. **Socialise the "coarse-to-fine hybrid" framing** — this is the design direction the theory supports. Confirm alignment before detailed design work.
4. **If Gemini produces results later**, add to this consolidation — but given the strength of three-source convergence, the conclusions are unlikely to change.

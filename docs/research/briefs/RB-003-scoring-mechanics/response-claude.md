# RB-003: Scoring Mechanics — Claude Response

# Scoring mechanics for hierarchical context retrieval

**The scoring component is the exponential lever of any hierarchical context retrieval system, and the design space is richer than it first appears.** Across eight distinct scoring methods analyzed, a cascade combining embedding pre-filtering with cross-encoder reranking emerges as the practical optimum for trees with branching factor 8–12 and depth 2–3, achieving per-level error rates of ε ≈ 0.005–0.015 at sub-200ms latency—meeting the ε ≤ 0.02 target. Formal admissibility (guaranteed zero false negatives) is achievable only through metric-tree bounds, but these require storing geometric centroids rather than text summaries, creating a fundamental tension with the system's information architecture. LATTICE's contextual calibration via reference anchor nodes represents the current state of the art for LLM-based hierarchical scoring, with its path-relevance EMA being the single most important component. The abstraction mismatch problem—where detail-oriented queries score low against thematic summaries—is confirmed empirically by RAPTOR's finding that collapsed-tree search outperforms top-down traversal, making cross-level calibration a first-order design concern rather than an optimization.

---

## The full landscape of scoring methods reveals a sharp accuracy-cost frontier

Eight distinct scoring methods apply to hierarchical routing decisions. Each captures a different signal, operates at a different cost, and offers different guarantees. The table below summarizes the landscape; the sections following provide depth.

| Method | Signal captured | Est. top-1 accuracy (b=10) | Latency (10 nodes) | Admissible bounds? |
|---|---|---|---|---|
| Dense embeddings (cosine) | Semantic similarity in learned space | 85–92% | <1ms | No (without metric overlay) |
| BM25 / SPLADE | Lexical / learned sparse overlap | 70–85% / 85–90% | <1ms | Yes, via WAND max-impacts |
| Cross-encoder | Joint query-document cross-attention | 90–95% | ~60ms (MiniLM-L6) | No |
| LLM-as-judge | Multi-step reasoning over text | 95–98% | 500–1000ms | No |
| Learned routing classifier | Subtree-relevance binary signal | ~90% (estimated) | 1–10ms | No (but trainable for high recall) |
| Metric-tree bounds | Geometric distance in embedding space | N/A (pruning, not ranking) | <1ms | **Yes (formally guaranteed)** |
| ColBERT MaxSim | Token-level alignment scores | 88–94% | 1–10ms | No |
| Matryoshka embeddings | Coarse-to-fine semantic similarity | 83–90% (low-dim) / 85–92% (full) | <1ms (low-dim) | No |

**Dense embeddings** are the workhorse. Bi-encoders like sentence-transformers achieve MRR@10 of 33–37 on MS MARCO and nDCG@10 in the 50s–60s on MTEB benchmarks. For routing among 10 well-differentiated summaries (far easier than open-domain retrieval over millions), top-1 accuracy of **85–92%** is reasonable, with top-3 recall reaching **97–99%**. Cost is negligible: 10 dot products in 768 dimensions takes microseconds. The fundamental weakness is that cosine similarity over summary embeddings has no formal relationship to the maximum relevance of any descendant leaf.

**Cross-encoders** provide the highest neural scoring quality by jointly encoding query and document through full cross-attention. On MS MARCO they achieve MRR@10 > 40, consistently **4+ nDCG@10 points above bi-encoders** on out-of-domain tasks (Rosa et al., 2022). MiniLM-L6-v2 processes ~1,800 docs/sec on a V100, meaning a batch of 10 routing candidates takes ~59ms. For hierarchical routing, this is the sweet spot of accuracy-to-cost: high enough quality to approach ε ≤ 0.02, cheap enough to run at every tree level.

**LLM-as-judge** captures the richest signal—multi-step reasoning about whether a summary could contain a relevant answer. LATTICE achieves nDCG@10 improvements of up to 5% over the next-best zero-shot baseline on BRIGHT (reasoning-intensive retrieval). The cost is ~500–1000ms per level with 10 candidates. At GPT-4o-mini pricing (~$0.15/M input tokens), scoring 10 summaries costs ~$0.00015 per level. This is viable for high-value queries but excessive for bulk retrieval.

**ColBERT-style MaxSim** occupies an underexplored middle ground. By maintaining per-token embeddings and computing the sum of maximum token-to-token similarities, ColBERTv2 achieves MRR@10 of 39.7 on MS MARCO—approaching cross-encoder quality at two orders of magnitude fewer FLOPs. For summary nodes that describe multiple sub-topics, MaxSim's per-token alignment naturally captures diverse matching signals that single-vector embeddings compress away.

**Matryoshka embeddings** enable a natural coarse-to-fine cascade within the embedding paradigm itself. At **8.3% of full embedding size, they preserve 98.37% of retrieval performance** (MRL, NeurIPS 2022). OpenAI's text-embedding-3-large truncated to 256 dimensions outperforms the older ada-002 at 1536 dimensions. For hierarchical routing, using 64-dimensional prefixes at upper tree levels and full 768 dimensions at leaf level provides a 12× cost reduction in similarity computation with minimal accuracy loss. The Funnel retrieval strategy achieves **14× real-world speedup** with bounded accuracy degradation.

Two additional approaches merit attention. **Hybrid/fusion scoring** (BM25 + dense + ColBERT via reciprocal rank fusion) consistently outperforms any single method; IBM's Blended RAG study confirms three-way hybrid as optimal. **HNSW graph navigation** implicitly creates hierarchical routing through its layered graph structure, representing a well-engineered solution to coarse-to-fine search that the field has converged on independently.

---

## Admissibility is achievable in principle but requires architectural compromise

The admissibility question—can any scoring method guarantee zero false negatives?—has a precise answer: **only metric-tree bounds provide formal guarantees, and only under conditions that partially conflict with the text-summary architecture.**

A ball tree stores at each node a centroid *C* (geometric center of all contained point embeddings) and radius *r* (maximum distance from centroid to any descendant). For query *q*, the triangle inequality gives: dist(*q*, any descendant) ≥ dist(*q*, *C*) − *r*. If this lower bound exceeds the current best distance found, the entire subtree is safely pruned with **zero false negatives guaranteed**. Schubert (SISAP 2021) derived a tight triangle inequality specifically for cosine similarity: arccos(sim(*x*,*y*)) ≤ arccos(sim(*x*,*z*)) + arccos(sim(*z*,*y*)), enabling VP-trees, cover trees, and M-trees to operate in cosine space.

The critical constraint: ball tree bounds assume internal nodes store the **geometric centroid of descendant leaf embeddings** with an accurate radius. The HCR system stores *text summaries* whose embeddings diverge from geometric centroids. This breaks the formal guarantee. The practical resolution is a dual-representation architecture: each internal node maintains (1) a text summary for rich scoring and (2) the actual geometric centroid plus maximum radius of all descendant leaf embeddings for admissible pruning. This "belt and suspenders" approach uses the summary for ranking quality and the metric bound as a safety net.

In high-dimensional spaces (768d+), however, metric-tree bounds suffer severe degradation. The **curse of dimensionality** concentrates distances, making bounds rarely tight enough to prune effectively. For 768-dimensional text embeddings, ball tree pruning eliminates far fewer branches than in low-dimensional settings. This limits practical utility unless embeddings are projected to lower dimensions first.

**WAND-style max-impact bounds** offer a complementary path for sparse retrieval. The WAND algorithm (Broder et al.) pre-computes maximum term impact scores per posting list, enabling safe-to-rank-*k* guarantees: it prunes >90% of evaluations while producing identical top-*k* results to exhaustive search. For hierarchical routing with BM25-style scoring, storing per-term maximum impacts from all descendants at each internal node creates admissible pruning bounds. BlockMaxWAND extends this with block-level granularity. The limitation is that BM25 over summaries faces the same abstraction mismatch that afflicts all summary-based approaches.

**Conservative thresholding** provides a practical alternative to formal admissibility. The relationship is straightforward: for branching factor *b*, lowering threshold *τ* increases the expected number of surviving branches as E[survivors] = *b* × P(score > *τ*). At *τ* = 0, all branches survive (perfect recall, no pruning benefit). The practical strategy is top-*k* selection: keeping the top 3 of 10 branches with embedding similarity achieves recall@3 of 97–99%, which for most applications is "admissible enough." The key insight is that **top-*k* selection is more robust than threshold-based filtering** because it adapts to the score distribution of each query, avoiding catastrophic failures when all scores are uniformly low or high.

| Admissibility approach | Formal guarantee? | Practical effectiveness | Architectural cost |
|---|---|---|---|
| Metric-tree bounds (centroid + radius) | Yes | Low in high dimensions | Requires storing centroid/radius per node |
| WAND max-impacts (sparse) | Yes (for top-*k*) | High for lexical scoring | Requires per-term max-impact storage |
| Top-*k* selection (*k*=3, *b*=10) | No | High (recall@3 ≈ 97–99%) | None |
| Dual-representation (summary + metric) | Yes (for metric component) | Medium | Doubles storage per node |

---

## Cross-level calibration is the first-order design concern

The abstraction mismatch problem—a query about a specific API parameter scoring low against a "Software Architecture" summary but high against the leaf chunk containing the answer—is not merely theoretical. **RAPTOR's empirical finding that collapsed-tree search (querying all nodes across all levels simultaneously) significantly outperforms layer-by-layer tree traversal** is direct evidence that naive top-down routing loses relevant results. This is the strongest warning signal for the HCR system design.

The root cause is that ranking losses (pairwise, listwise) produce **inherently uncalibrated scores** (Yan et al., KDD 2022). A score of 0.72 at level 1 and 0.72 at level 2 reflect entirely different relevance distributions. The Google-authored "Scale Calibration of Deep Ranking Models" paper demonstrates that virtually all advanced ranking functions have freedom to add arbitrary constants to scores without changing relative order—scores are meaningful only within a single comparison context.

Five concrete calibration techniques address this:

**Level-specific Platt scaling** is the most practical approach. Fit a sigmoid P(answer_in_subtree | score) = 1/(1 + exp(A·score + B)) with separate parameters (A, B) per tree level. This requires labeled data (query, node, answer_is_below) at each level but converts raw scores into comparable probability estimates. Temperature scaling—a single-parameter variant—is "surprisingly effective" at fixing miscalibration (Guo et al., ICML 2017) and can serve as a lightweight alternative.

**Sibling-relative ranking** sidesteps cross-level comparison entirely by ranking nodes only against their siblings at each tree level, using rank position rather than absolute score. Reciprocal Rank Fusion scoring (1/(rank + *k*)) is inherently robust to different score scales. The limitation: relative ranking cannot decide *whether* to explore any branch at all—it always selects the top-ranked option even when nothing is relevant. The recommended hybrid is sibling-relative ranking for ordering, plus a calibrated probability threshold for deciding how many branches to explore.

**Child-representative embeddings** mitigate abstraction mismatch directly. Instead of (or alongside) the summary embedding, each internal node maintains an aggregation of its children's embeddings—giving detail-oriented queries something to match against even at higher tree levels. AGRaME (2024) demonstrates that ColBERTv2's multi-vector representations enable scoring at finer granularity than the encoding level through multi-granular contrastive training.

**Hypothetical Document Embeddings (HyDE)** bridge the query-summary gap by using an LLM to generate a hypothetical answer, then embedding it for retrieval (Gao et al., ACL 2023). For hierarchical routing, generating the hypothetical answer at different abstraction levels—a one-sentence topic statement for upper-level routing and a detailed answer for leaf matching—directly addresses abstraction mismatch. The cost is one LLM call per query.

**Bayesian per-level calibration** provides the most principled framework. Compute P(answer_below | score, level) using Bayes' theorem with fitted score distributions. Manmatha et al. (2010) show that IR score distributions can be modeled as normal-exponential mixtures, with the relevant and non-relevant components fit separately. At each tree level, collecting (score, is_answer_below) pairs enables fitting these distributions and computing proper posterior probabilities for routing decisions.

A finding that deserves emphasis: **Penha and Hauff (EACL 2021) show that BERT-based rankers are NOT robustly calibrated**, with stochastic variants (using MC Dropout) yielding meaningfully better calibration. This suggests that routing decisions should incorporate uncertainty estimates—not just point scores—and that **stochastic scoring** (multiple forward passes with dropout) may be worth the 3–5× computational overhead at critical routing junctures.

---

## Cascaded scoring has well-established theory and strong empirical support

The cascade framework—fast cheap scoring to eliminate obvious non-matches, then expensive accurate scoring for survivors—has deep roots in IR theory and strong empirical validation. Wang, Lin, and Metzler (SIGIR 2011) formalized cascade ranking as a sequence of increasingly complex ranker-pruner stages with joint training. The key theoretical insight connects to the **reject option in classification**: at each cascade stage, items scoring below threshold are "rejected" (excluded), while borderline items are deferred to the more expensive next stage. This is formally equivalent to Chow's Rule (1970), where the rejection cost equals the cost of invoking the next stage.

Concrete numbers from production systems and benchmarks demonstrate the tradeoffs. On the BEIR benchmark, adding cross-encoder reranking (184M parameter DeBERTa-v3) to BM25 top-100 improves average nDCG@10 from **0.426 to 0.565 (+33%)**. On individual datasets the gains are dramatic: Natural Questions jumps from 0.33 to 0.62 (+90%), MS MARCO from 0.23 to 0.42 (+85%). Larger rerankers push further: bge-reranker-v2-gemma (2B params) reaches nDCG@10 of 0.568. The latency cost is modest—cross-encoder scoring of 200 candidates on GPU takes 15–30ms, making the total pipeline (BM25 + rerank) under 50ms.

For LLM cascades, FrugalGPT (Chen et al., 2023) demonstrates that learning optimal model sequences and threshold values as a constrained optimization problem can **match GPT-4 accuracy with up to 98% cost reduction**, or improve accuracy by 4% at the same cost. The key mechanism is a DistilBERT-based scoring function that predicts when a cheap model's answer is reliable enough to skip the expensive model. C3PO (2025) extends this with conformal prediction-based bounds that control cascade inference cost under a user-specified budget with arbitrary probability—providing PAC-style guarantees.

**Optimal threshold setting** has three practical approaches. Static per-stage thresholds (Viola-Jones style) are simple but suboptimal for varying query difficulty. Dynamic cutoff prediction (Culpepper, Clarke, and Lin, 2016) adapts the number of candidates passed between stages based on score distribution features. The most robust approach for hierarchical routing is **top-*k* selection rather than threshold-based filtering**: always keep the top 3 of 10 branches at level 1, rather than setting an absolute score cutoff. Top-*k* is invariant to score distribution shifts across queries and provides predictable computational cost.

The formal connection to reject-option classification yields the optimal cascade threshold: invoke the next stage when E[quality_gain] × value_per_quality_unit > cost_of_next_stage. For routing where missing the correct branch is catastrophic, this asymmetric cost structure favors liberal thresholds (high recall, more candidates passed through) at early stages. The standard practice of BM25 targeting recall@1000 > 95% reflects this asymmetry.

Applied to the HCR tree (b=10, d=2), the recommended cascade per level is: embedding similarity over all 10 branches (<1ms) → keep top 3 → cross-encoder rerank of 3 survivors (~20ms) → keep top 1–2. Total latency: ~40ms per level, ~80ms for both levels. The embedding stage catches ~97–99% of correct branches; the cross-encoder catches ~99.5% of what survives. The combined per-level error rate is approximately **ε ≈ 0.005–0.015**, meeting the target.

---

## LATTICE introduces contextual calibration as a training-free alternative

LATTICE (Gupta, Chang, Bui, Hsieh, and Dhillon; UT Austin; arXiv 2510.13217, October 2025) is the most directly relevant existing system, using LLM-as-judge with a novel calibration approach for hierarchical retrieval.

The architecture operates in two phases. Offline, the corpus is organized into a semantic tree via bottom-up agglomerative clustering with LLM-generated summaries (branching factor M ≈ 10–20). Online, a "search LLM" (default: Gemini-2.5-flash) navigates the tree using beam search. At each traversal step, the LLM receives a **slate of sibling candidate nodes** along with **calibration nodes**—high-relevance candidates from sibling branches and previously encountered leaf documents. The LLM produces chain-of-thought reasoning plus relevance scores for each candidate.

The core innovation is **contextual calibration**: rather than using statistical post-hoc calibration (Platt scaling, isotonic regression), LATTICE inserts known-good reference nodes as scoring anchors in each LLM evaluation call. This forces the LLM to produce globally comparable scores across different evaluation contexts without any trained calibration function. Individual calibrated scores are then aggregated into a **path relevance score via exponential moving average (EMA)** with momentum α = 0.5 along the root-to-current-node path, smoothing noise so that a single misleading node score doesn't derail the search.

Ablation studies reveal a clear component hierarchy. **Removing path relevance smoothing causes the largest performance degradation**—it is the most critical component. Removing LLM reasoning (setting thinking budget to zero) costs 2.2+ nDCG points. Removing score calibration (using raw LLM scores) causes significant but smaller degradation. This ordering matters for system design: if budget is constrained, path-level score aggregation is more important than per-node calibration sophistication.

On the BRIGHT benchmark (reasoning-intensive retrieval), LATTICE achieves **Recall@100 of 74.8%, a +9.5 percentage point improvement** over BM25 with GPT-4 query expansion and +4.0 points over ReasonIR-8B (a fine-tuned dual encoder with GPT-4 expansion). It is competitive with fine-tuned state-of-the-art systems (DIVER-v2: 52.2 nDCG@10 vs. LATTICE: 51.6 on StackExchange subsets) despite being entirely zero-shot. The system evaluates ~250 documents per query via LLM, with cost growing **logarithmically** with corpus size.

LATTICE's limitations are significant for practical deployment. Each query requires ~250 LLM calls, translating to seconds-to-tens-of-seconds latency. The approach assumes a fixed corpus (tree reconstruction needed for updates). The training-free design is both a strength (zero-shot generalization) and a weakness (cannot adapt to domain-specific relevance patterns). Beam size of just 2 is sufficient for their benchmarks, but this means the system explores only 2 paths simultaneously—vulnerable to early routing errors that the EMA smoothing cannot fully recover from.

HIRO provides a useful contrast: it uses embedding-based DFS traversal with a **delta threshold** (Δ*S* = S(*Q*, child) − S(*Q*, parent); explore child only if Δ*S* > Δ). Default parameters are selection_threshold = 0.6 and delta_threshold = 0.08. This is dramatically cheaper than LATTICE but handles reasoning-heavy queries poorly. HIRO achieves +10.85% on NarrativeQA ROUGE scores but slightly underperforms collapsed-tree querying on QuALITY.

---

## Information density scoring formalizes the token-budget problem as submodular optimization

Under a hard 400-token budget, pure relevance scoring is insufficient—the system must maximize **unique, non-redundant information per token**. This is formally a submodular knapsack problem, and recent work provides both theory and practical algorithms.

**AdaGReS** (December 2025, arXiv 2512.25052) directly addresses token-budgeted RAG with a redundancy-aware context selection framework. It optimizes a set-level objective combining query-chunk relevance with intra-set redundancy penalties, uses greedy selection under token-budget constraints with marginal gains, and proves **ε-approximate submodularity** under practical embedding similarity conditions. The key result: diversity in initial retrieval is more critical than ranking-stage optimization. It reports up to 5% higher macro-F1 over baselines on biomedical NLP tasks.

The theoretical foundation is well-established. Submodular function maximization under cardinality constraints achieves a **(1 − 1/*e*) ≈ 0.632 approximation ratio** via greedy algorithms (Nemhauser et al., 1978). For knapsack constraints (token budget), greedy ordering by marginal gain per unit cost provides bounded approximations. Lin and Bilmes (2010) first applied submodular optimization to text summarization under budget constraints—the direct ancestor of token-budgeted retrieval.

Three practical diversity mechanisms apply:

- **Maximal Marginal Relevance (MMR)** by Carbonell and Goldstein (1998) iteratively selects chunks maximizing λ·Sim(chunk, query) − (1−λ)·max Sim(chunk, already_selected). This is widely implemented (LangChain includes built-in MMR support). The λ parameter controls the relevance-diversity tradeoff, and Probabilistic Latent MMR (SIGIR 2010) derives it from a principled graphical model.

- **Determinantal Point Processes (DPPs)** provide a probabilistic framework where the selection probability of a subset is proportional to the determinant of its similarity kernel—geometrically representing the "volume" spanned by selected items. YouTube deployed DPPs in production for diversified recommendations (CIKM 2018). The computational cost is O(N³) for exact inference but fast greedy approximations exist.

- **Per-token value scoring** computes relevance(chunk)/token_count(chunk) as a benefit-to-cost ratio, directly analogous to the greedy knapsack heuristic. This can be combined with marginal gain computation: the value of the *next* chunk depends on what has already been selected, naturally implementing diminishing returns.

For hierarchical systems specifically, information density at a subtree can be estimated before expansion. The summary's embedding similarity to the query provides a first-order relevance estimate. The summary's token count relative to the subtree's total tokens gives a compression ratio. A practical scoring heuristic is: Score(subtree) = Relevance(summary, query) × EstimatedUniqueInfo / ExpectedTokenCost, where EstimatedUniqueInfo is estimated from summary diversity relative to already-selected content. RAPTOR's finding that **18.5–57% of retrieved nodes come from non-leaf summary layers** confirms that summaries carry substantial unique information that can serve as density signals.

---

## Achieving ε ≤ 0.02 per level is realistic with a hybrid cascade strategy

The ε ≤ 0.02 target—correctly routing to the branch containing the answer 98% of the time at each tree level—is achievable but requires careful strategy selection. The critical insight: **routing among 10 well-differentiated summaries is fundamentally easier than open-domain passage retrieval**, making it analogous to 10-class classification where SOTA models routinely exceed 90% accuracy.

For the specified tree (b=10, d=2), the recommended architecture is a **per-level two-stage cascade**:

**Stage 1 — Embedding pre-filter.** Score all 10 branch summaries via cosine similarity with pre-computed embeddings. Keep top 3. Cost: <1ms. Expected recall@3: 97–99%. This eliminates 70% of candidates for negligible cost.

**Stage 2 — Cross-encoder rerank.** Score the 3 surviving candidates with MiniLM-L6-v2 (22.7M params, 1,800 docs/sec on V100). Select top 1–2 branches. Cost: ~20ms. Expected accuracy among survivors: 95–98%.

**Combined per-level performance:** P(correct branch missed by embeddings) × P(correct branch missed by cross-encoder | survived embeddings) ≈ 0.02 × 0.03 = 0.0006. Even with conservative estimates, **ε ≈ 0.005–0.015 per level**. For d=2: cumulative P(success) ≈ (1 − 0.01)² = 0.98, yielding **~98% end-to-end routing accuracy**.

Total latency per query: ~80ms across both levels. Total cost: effectively $0 with local GPU inference.

For applications requiring even higher accuracy, replacing the cross-encoder with LLM-as-judge at level 1 (where the routing decision is most consequential) pushes top-1 accuracy to 95–98% at the cost of 500–1000ms latency. A pragmatic hybrid: use the fast cascade for most queries, escalate to LLM scoring when the cross-encoder's score margin between the top two candidates is small (i.e., the decision is uncertain). This adaptive depth approach allocates expensive compute only where it matters.

**Five factors dominate achievable error rates**, roughly in order of importance: (1) Quality of summaries—well-crafted, distinctive summaries that clearly differentiate branch content are the single most impactful factor. (2) Query ambiguity—queries matching multiple branches increase error regardless of scoring quality. (3) Branching factor—b=8 is meaningfully easier than b=12. (4) Summary overlap—sibling branches with similar content create near-ties that any scoring method struggles with. (5) Domain specificity—specialized domains with clear topic boundaries achieve lower error. No amount of scoring sophistication can compensate for poorly differentiated summaries.

---

## Conclusion: three design decisions matter most

This analysis reveals that the scoring design space, while rich, converges on a few key architectural choices.

**First, the cascade beats any single method.** No scoring approach dominates across accuracy, cost, and admissibility. The embedding → cross-encoder cascade at each tree level achieves near-optimal accuracy at practical cost. For the specified tree parameters, this translates to ~80ms latency and ε ≈ 0.01 per level. LLM-as-judge should be reserved for adaptive escalation on ambiguous routing decisions, not applied uniformly.

**Second, admissibility requires dual representation.** Formal zero-false-negative guarantees are possible only through metric-tree bounds, which require storing geometric centroids and radii alongside text summaries. In practice, top-3 selection from b=10 branches provides "admissibility enough" (recall > 97%) without the architectural overhead. The system should implement metric-tree safety nets only if the application domain has catastrophic false-negative costs.

**Third, cross-level calibration is non-optional.** RAPTOR's empirical evidence that collapsed search outperforms tree traversal, combined with the theoretical result that ranking losses produce uncalibrated scores, makes calibration a first-order concern. Level-specific Platt scaling on (score, answer_is_below) pairs is the minimum viable approach. LATTICE's contextual calibration via reference anchor nodes is more sophisticated and training-free but requires LLM scoring. The Bayesian per-level approach—fitting separate score distributions for relevant and non-relevant branches at each level—provides the most principled framework for converting scores to routing probabilities.

Three findings surface that were not in the original research scope. The **submodular knapsack framing** for information density (with (1 − 1/e) approximation guarantees via greedy algorithms) provides a rigorous foundation for the token-budget problem that goes beyond ad-hoc relevance scoring. **Stochastic scoring via MC Dropout** yields better-calibrated relevance estimates than deterministic inference, at modest computational overhead—potentially valuable for the highest-stakes routing decisions. And **LATTICE's ablation showing path-relevance EMA as more important than per-node calibration** suggests that smoothing scores across the tree path is a higher-leverage investment than perfecting individual node scoring.
# RB-003: Scoring Mechanics — Perplexity Response


### 0. Executive summary

- **Pure embedding-on-summary scoring at internal nodes is not good enough** for HCR’s routing role: it cannot be made admissible, and in practice tends to have per-level miss rates (ε) in the high single digits or worse on hard queries. Hierarchy becomes a liability rather than a win in that regime.
- **Strict admissibility (“never prune a true branch”) is essentially unattainable** for semantic relevance with current text models. Only in the degenerate case where “relevance” is literally defined as distance in a true metric space (e.g., Euclidean embedding distance) do metric-tree–style guarantees apply, and then you are just doing nearest-neighbor in embedding space, not “answer relevance” in the RB‑002 sense.
- **The most promising strategy for HCR is a calibrated cascade**:
    - **Coarse routing (levels 1–2):**
        - Use **hybrid sparse+dense retrieval** (BM25 + dense) at node level for cheap, high-recall routing.
        - Optionally add a **small cross-encoder** or **LLM-as-judge** for a *few* borderline branches, not for all children.
        - Treat this stage probabilistically: estimate $P(\text{answer in subtree} \mid \text{scores})$ with Platt / isotonic or a small calibration model.
    - **Fine selection (within surviving branches):**
        - Use a **cross-encoder / late-interaction reranker** (e.g., BERT cross-encoder or ColBERT-style scoring) on leaf chunks.
        - Add a **redundancy or information-density term** à la AdaGReS (relevance–redundancy objective under a token budget) to approximate “information per token” rather than plain relevance.[^1_1][^1_2]
    - **Cross-level calibration** is handled via:
        - Level-aware score normalization,
        - plus a **path relevance smoother** similar to LATTICE’s latent-score + exponential moving average.[^1_3]
- **LATTICE shows the upper end of what’s currently feasible** with LLM-as-judge routing:
    - It builds a semantic tree and uses listwise LLM scoring plus a global **latent-score calibration model** (one global scale and per-slate biases) and **path smoothing** to get cross-branch, cross-level comparable scores.[^1_3]
    - On BRIGHT, LATTICE reaches **Recall@100 ≈ 74.8% vs 65.3% (BM25) and 70.8% (ReasonIR-8B)** and beats a strong BM25+LLM reranker baseline by **+4.2 nDCG@10** on StackExchange subsets, at ~250 LLM-evaluated documents per query.[^1_3]
    - This is strong evidence that **LLM-guided hierarchical routing can outperform flat rerankers at similar or lower LLM token cost**, but it still has no formal admissibility guarantee.
- For a tree with **branching factor 8–12 and depth 2–3**, a **realistic target** of per-level ε ≈ 0.01–0.02 (98–99% per-level subtree recall) is **plausible but not trivial**:
    - Achievable only if:
        - **Routing at each level is treated as a supervised classification / calibration problem** (not just raw cosine similarity),
        - you allow **top-2–3 branches per level**, not top-1,
        - and you are willing to pay for a modest amount of cross-encoder or LLM scoring on ambiguous nodes.

What follows is a more detailed map of the landscape and how it connects to your RB‑002 constraints.

***

## 1. Landscape of scoring methods for hierarchical routing

Below, “routing decision” means: *does this subtree contain at least one answer?* and possibly *how much mass of answer-probability does it hold?*

### 1.1 Dense embeddings

**Signal.** Semantic similarity in a learned vector space (bi-encoder style). Each node has an embedding of its description/summary; routing uses cosine or dot-product similarity between query and node.

**Routing accuracy.**

- At document/passage level, modern dense retrievers (e.g., MS MARCO–tuned) often get **Recall@100 in the 80–95% range**, but Recall@10/20 can be much lower, especially for long-tail or compositional queries.
- For *node-level routing* with ~10 children, you care about: “Is the true child among the top-k?”:
    - For reasonably well-separated topical clusters, empirical top‑3 accuracy above 95% is achievable.
    - For fine-grained or cross-cutting topics, accuracy degrades; and **summaries as lossy channels** (DPI) systematically hurt detail-heavy queries, as you already observed.

**Cost.**

- Embedding lookup + dot product for 10–100 nodes is **sub-millisecond** on CPU; negligible compared to any transformer inference.
- Tokens: none beyond the offline embedding cost.

**Admissibility.**

- If “true relevance” were literally monotone in a metric distance (e.g., nearest neighbor under Euclidean), then a **metric tree** over embeddings with triangle inequality bounds can be admissible for *metric* nearest neighbor.[^1_4][^1_5][^1_6]
- For actual semantic answer relevance, there is **no guarantee** that a low cosine similarity at a summary implies low similarity for some descendant chunk; the DPI and anisotropy arguments from RB‑002 make this structural, not just empirical.
- Conclusion: **cannot be made admissible for semantic routing**, only high-recall in practice via conservative thresholds.

**Best use.** First-pass, very cheap **screening at internal nodes**, combined with lexical signals; not sufficient on its own to hit ε ≤ 0.02 at all levels.

***

### 1.2 Sparse retrieval (BM25, SPLADE) at node level

**Signal.** Exact and fuzzy term overlap, IDF weighting; SPLADE and similar add learned term expansions.

**Routing accuracy.**

- First-stage BM25 over millions can hit **≈90–95% recall@1000** on standard QA benchmarks.[^1_7]
- For node descriptions, usefulness depends heavily on whether the description surface-forms contain key query terms; for high-level thematic summaries, this is often *worse* than dense similarity for paraphrased queries.

**Cost.**

- BM25 over an inverted index is extremely cheap: **10–20 ms to score millions of docs** on commodity hardware.[^1_7]
- At node-level with hundreds or thousands of internal nodes, cost is negligible.

**Admissibility.**

- For literal keyword matching, you can get “if no term from query appears in subtree, it’s irrelevant” type rules, but that’s **not equivalent to “no answer in subtree”** in semantic tasks.
- Still not admissible in RB‑002 sense.

**Best use.**

- As a **lexical complement** to dense similarity: hybrid scores (e.g., RRF fusion) at internal nodes improve recall on tail cases (error codes, identifiers, rare names).[^1_8][^1_7]
- Very good candidate for **cheap, high-recall coarse routing signal**.

***

### 1.3 Cross-encoders (bi-directional transformers) as node scorers

**Signal.** Full cross-attention over concatenated query + node description; captures fine-grained matching patterns, analog of strong rerankers in standard pipelines.

**Routing accuracy.**

- Cross-encoder rerankers consistently boost nDCG and top‑k precision over dense-only baselines; e.g., in biomedical RAG, reranking top‑1000 with a cross-encoder improved MAP@10 from 0.158 (dense only) to 0.455 with an LLM-enhanced reranker ensemble.[^1_9][^1_10]
- For a **10-way routing decision**, cross-encoders can easily reach >95–98% top‑1 accuracy on in-distribution tasks with enough training; top‑2–3 accuracy can be even higher.
- They can also serve as **teachers** for calibration: train a small logistic model or temperature scaling over cross-encoder scores to approximate $P(\text{subtree contains answer})$.

**Cost.**

- In multi-stage web search, scoring ~1000 candidates with a BERT cross-encoder typically costs **50–100 ms on GPU**.[^1_10][^1_7]
- For hierarchical routing, you only need to score **8–12 children per expanded node**, a tiny candidate set:
    - Scoring 10–30 nodes per query with a small cross-encoder is often **<10–20 ms** on modern GPUs, and feasible even on CPU at tens of ms.

**Admissibility.**

- Still heuristic; no monotone guarantee. However, **calibration is much easier** because scores come from a consistent model and small label space.

**Best use.**

- **Root and level‑1 routing** when you really care about ε ≤ 0.02 and sequence of errors compounds.
- **Leaf reranking** within candidate branches when LLM-as-judge is too expensive.

***

### 1.4 LLM-as-judge (pointwise or listwise)

**Signal.** Free-form reasoning; can incorporate rich priors and multi-step reasoning, and score nodes via structured JSON outputs. LATTICE uses this as its core signal.[^1_3]

**Routing accuracy.**

- LATTICE shows that **LLM-as-judge with calibration + path smoothing** can beat strong BM25+LLM rerankers by **+4.2 nDCG@10** and achieve **Recall@100=74.8 vs 65.3 (BM25) and 70.8 (ReasonIR-8B)** on BRIGHT.[^1_3]
- That is **zero-shot, no fine-tuning**, on reasoning-heavy queries and up to 420k-corpus size.
- This is evidence that **LLM-guided hierarchical routing can substantially improve end-to-end recall/precision over flat pipelines** at similar LLM token budgets.

**Cost.**

- Per “slate” (a prompt including query and k node descriptions), token cost is roughly:
    - Input: $O(k \cdot L_{\text{node}} + L_{\text{query}})$.
    - Output: a few dozen tokens for scores + optional rationale.
- LATTICE with beam size $B=2$, iterations $N=20$, and $\ell=10$ calibration leaves evaluates **≈250 documents/nodes per query** with Gemini-2.5-flash. For typical 200-token node summaries, you’re in the **tens of thousands of tokens per query**, but still competitive with reranking baselines that score 100–500 full documents.[^1_3]

**Admissibility.**

- Fundamentally heuristic, but **can be globally calibrated**:
    - LATTICE’s latent-score model (global scale + per-slate bias, optimized by MSE) estimates a **slate-independent latent score** $\hat{s}_v$ and then smooths it along tree paths.[^1_3]
    - This is not a formal “never underestimates” bound, but does give **comparability across branches and levels** (essential for non-pathological pruning).

**Best use.**

- **Coarse routing for complex queries** where embeddings + lexical signals fail (reasoning-based, compositional).
- **Final high-precision reranking** of a small set of leaf nodes when answer quality matters more than latency.

***

### 1.5 Multi-vector / late-interaction models (ColBERT, etc.)

**Signal.** Token-level embeddings with late interaction; e.g., ColBERT uses MaxSim over query–document token embeddings and aggregates.[^1_11][^1_12][^1_13]

**Routing accuracy.**

- ColBERT frequently matches or exceeds cross-encoders in retrieval quality while being more scalable than naive cross-encoders.[^1_12][^1_13]
- For hierarchical routing, you can:
    - Represent each node as a multi-token summary and compute late-interaction similarity.
    - Or keep full token embeddings for leaf chunks and use **funnel / routed late-interaction** (e.g., FastLane) to score only promising views.[^1_14]

**Cost.**

- More expensive than a single dense vector dot-product (per token interactions), but:
    - Can be implemented vectorized and partially pruned.
    - New routing frameworks like FastLane learn to score only the **most informative token views**, reducing cost.[^1_14]

**Admissibility.**

- Still similarity-based; no metric-bound guarantees.
- However, multi-vector structure is more expressive; can help **cross-level calibration** because root summaries can aggregate per-topic token scores.

**Best use.**

- High-quality **leaf reranking** inside surviving branches when you want near cross-encoder quality but better throughput.

***

### 1.6 Learned routing classifiers / hierarchical text categorization

**Signal.** Supervised model that, given (query, node features), predicts whether the subtree contains an answer. Architecture can be:

- Local-classifier-per-node or per-level (as in Hierarchical Text Categorization),[^1_15]
- or a small NN over embedding scores and metadata.

**Routing accuracy.**

- HTC literature reports good accuracy when trained on ample labeled data; e.g., route-confidence models in HTC can significantly improve overall classification accuracy by rejecting low-confidence routes.[^1_15]
- For **routing in HCR**, you can train $P(y=1 \mid q, v)$ where y indicates subtree contains answer, using logs from your own system.

**Cost.**

- If using a shallow MLP or logistic regression over already-computed features (BM25 score, dense similarity, node depth, etc.), cost is **negligible**.

**Admissibility.**

- Still probabilistic; but because it’s explicitly a classifier, it is a **natural target for calibration** (Platt / isotonic) to get usable probability estimates.

**Best use.**

- As a **calibration head** on top of cheap base scores at internal nodes.
- For SPRT-style routing, this is the most natural way to get approximate likelihood ratios.

***

### 1.7 Geometric / metric-tree bounds (ball-trees, N-tree, HNSW)

**Signal.** Pure geometry: nodes store bounding balls/regions, and triangle inequality gives bounds on min/max possible distance to any descendant.[^1_5][^1_6][^1_4]

**Routing accuracy and admissibility.**

- For exact nearest-neighbor in a **true metric space**, ball-trees and related indexes are **admissible**: if node’s lower-bound distance exceeds best-so-far distance, you can safely prune.[^1_6][^1_4][^1_5]
- If your **ground-truth relevance** is explicitly defined as “closest under this metric,” this is a perfect setting for admissible hierarchical routing.
- For semantic QA, however, this reduces to: “the answer is defined as nearest neighbor under this learned embedding,” which is tautological and usually not what you want.

**Best use.**

- For **pure vector similarity search** where your evaluation metric is exactly “nearest under embedding distance.”
- Less useful for HCR’s notion of “answers” unless you are willing to equate embedding distance with relevance.

***

### 1.8 Multi-resolution / Matryoshka embeddings

**Signal.** Nested representations where prefixes (e.g., first 1/6 of dimensions) capture coarse semantics and longer prefixes finer details.[^1_16][^1_17][^1_18][^1_19]

**Routing accuracy.**

- Funnel search with Matryoshka embeddings shows that using reduced-dimension prefixes for **coarse search** yields modest recall loss, then larger prefixes refine results.[^1_17]
- This is a *different dimension of hierarchy*: by embedding dimension, not corpus structure.

**Cost.**

- Enables **cheap coarse scoring** on small prefixes, then more expensive scoring on larger prefixes for a narrowed candidate set.

**Best use.**

- For **coarse filtering of nodes** in combination with standard corpus hierarchy; gives another axis for cascades (dimension hierarchy).

***

### 1.9 Set-level, redundancy-aware scoring (information density)

**Signal.** Score subsets of candidates jointly for relevance **and** diversity / redundancy; AdaGReS formalizes this for token-budgeted RAG.[^1_2][^1_1]

- Objective:

$$
F(q, C) = \alpha \sum_{c \in C} \text{sim}(q, c) - \beta \sum_{i<j} \text{sim}(c_i, c_j)
$$
- Greedy selection under a **token budget** yields near-optimal subsets due to approximate submodularity.[^1_1][^1_2]

**Best use.**

- This is directly aligned with your “knapsack / information density” requirement: select **maximally relevant, minimally redundant** chunks under a token budget.
- Naturally plugs into the **leaf-stage selection** after hierarchical routing.

***

## 2. Admissibility: what is actually achievable?

### 2.1 Where admissibility is real: metric trees

In classic metric trees (ball-trees, N-tree, etc.), each node stores a **center** and **radius**, and the distance function $d$ satisfies triangle inequality. For a query point $q$ and current best distance $D^*$, you can derive:[^1_4][^1_5][^1_6]

- Lower bound on any descendant’s distance:

$$
d_{\min}(q, \text{subtree}) \ge |d(q, \text{center}) - \text{radius}|
$$

If $d_{\min} > D^*$, you can **provably prune** the entire subtree without missing the nearest neighbor. This is exactly the admissible-bound notion from RB‑002.

However, the guarantee is with respect to that metric distance, not an external “answer relevance” criterion. If evaluation is “distance to ground-truth neighbor in this metric,” all is well; but that is rarely the evaluation you care about.

### 2.2 Why admissible semantic routing is unattainable

For semantic QA-style relevance:

- The mapping from **text → embedding** is learned and imperfect.
- Relevance is defined by human labels or answer correctness, not by embedding distance.
- There is no known representation or summary that is guaranteed to be a **sufficient statistic** for all possible future queries over descendants (RB‑002 DPI argument).

Therefore:

- Any routing rule based on summary-level signals (embedding, BM25, LLM summary) will have **non-zero probability of false negatives**, and you **cannot make that formally zero** without trivializing the problem (e.g., including all descendants in every decision).

You *can*:

- Make ε **arbitrarily small empirically** on some distribution by:
    - Always exploring multiple branches,
    - Using conservative thresholds,
    - Adding expensive checks for borderline cases,
    - And calibrating aggressively.
- But this is **probabilistic admissibility**, not a hard guarantee.


### 2.3 Conservative thresholding as the practical analogue

In practice, “admissible enough” means:

- Set thresholds so that, on validation data, the event

$$
\text{“pruned branch contained an answer”}
$$

happens at rate ≤ target ε (e.g., 0.5–2%).
- Overprovision breadth, e.g., keep **top‑3 of 10 children at each level** instead of top‑1.
- Use **uncertainty-aware reranking**: Bayesian methods for deep retrievers show you can model per-document score distributions and derive **risk-aware rerankings and cutoff decisions** that respect user-specified risk levels.[^1_20][^1_21]

This yields **empirical bounds** on ε suitable for engineering decisions, but they are distribution-dependent and not worst-case guarantees.

***

## 3. Cross-level calibration

### 3.1 The problem

- Internal nodes are **abstract summaries**; leaf nodes are **concrete chunks**.
- A detail-heavy query might score:
    - Low vs. a vague thematic parent summary,
    - High vs. the exact leaf chunk.
- Raw scores across levels are **not on the same scale** (different description length, lexical density, etc.).

This breaks any naive strategy that compares scores across levels (e.g., “prune if parent score < threshold”).

### 3.2 LATTICE’s approach: latent scores + path smoothing

LATTICE explicitly addresses cross-branch and cross-level comparability:[^1_3]

1. **Listwise local scoring.** Search LLM scores a slate of candidates (children + calibration nodes) with scores $s^i_v \in [0,1]$.
2. **Latent-score model.** They assume:

$$
s^i_v \approx a \cdot \hat{s}_v + b^i
$$

where:
    - $\hat{s}_v$ is a **latent, slate-independent relevance**,
    - $a$ is a global scale,
    - $b^i$ is a per-slate bias.
These are updated by minimizing MSE over all observed scores so far (via Adam over ~100 steps per update).[^1_3]
3. **Path relevance smoothing.**

$$
\hat{p}_{\text{rel}}(v) = \alpha \cdot \hat{p}_{\text{rel}}(\text{parent}(v)) + (1 - \alpha)\cdot \hat{s}_v
$$

with $\alpha = 0.5$. The root starts at $\hat{p}_{\text{rel}}(root)=1$.[^1_3]

This accomplishes:

- **Cross-slate calibration** (a, b^i),
- **Cross-level smoothing** (path factor α),
- **Global comparability** of nodes by $\hat{p}_{\text{rel}}(v)$, which is used to drive best-first traversal.

Ablations show that removing **path smoothing** or calibration degrades nDCG@10 by several points, confirming these pieces matter in practice.[^1_3]

### 3.3 Other concrete techniques

For embedding- or cross-encoder–based HCR, analogous techniques are:

- **Level-specific normalization:**
    - For each level ℓ, estimate the distribution of raw similarities $s_\ell$ across many queries.
    - Map to standardized scores $z = (s_\ell - \mu_\ell)/\sigma_\ell$ or directly to calibrated probabilities via Platt scaling or isotonic regression (see §4).[^1_22][^1_23][^1_24][^1_25]
    - Then combine with a path prior, e.g.,

$$
\log \hat{p}(v) = \lambda_\ell \cdot \hat{z}_\ell(v) + (1-\lambda_\ell)\log \hat{p}(\text{parent}(v)).
$$
- **Delta-over-parent thresholds (HIRO-like).**
    - HIRO uses a “delta” condition: only prune if children don’t sufficiently improve over parent scores (you already noted this).
    - This is a form of cross-level normalization by **relative gain**, not absolute score.
- **Hierarchy-aware reranking (ToolRerank).**
    - ToolRerank adjusts reranking and truncation policies based on tool hierarchy and query type (single-tool vs multi-tool).[^1_26][^1_27][^1_28][^1_29]
    - Conceptually similar to giving different **priors per level and per branch type**.

These are less principled than LATTICE’s latent-score model, but they can be implemented with simpler ingredients when you’re not using LLM-as-judge everywhere.

***

## 4. Calibration for probabilistic routing

### 4.1 Classic calibration tools

Standard probability calibration methods:

- **Platt scaling**: logistic regression over raw scores to map them to calibrated probabilities.[^1_24][^1_22]
- **Isotonic regression**: non-parametric monotone mapping, better when you have lots of calibration data.[^1_25][^1_24]
- **Temperature scaling** (for softmax scores): rescales logits to fix overconfidence while preserving ranking.[^1_30][^1_31][^1_23]

These are widely used to turn classifier scores into $P(y=1 \mid x)$. They also apply to retrieval *if* you can frame routing as a binary classification: does this subtree contain an answer?

### 4.2 Calibration in retrieval specifically

IR work on calibration includes:

- **Bayesian deep retrieval with Monte Carlo dropout**, which explicitly models score uncertainty per document and defines ranking-based calibration metrics; they show improved confidence calibration and allow **risk-aware reranking and cutoff prediction**.[^1_21][^1_20]
- **CalibRAG**, which focuses on calibrating document-level confidence in RAG to improve reliability of downstream decisions and shows better calibration than standard rerankers across datasets.[^1_32]
- Older work on mapping ranking scores to probabilities of relevance (e.g., OpTranker).[^1_33]

These show that **retrieval scores can be calibrated to probabilities**, but typically at the document level and for flat retrieval, not explicitly for hierarchical routing.

### 4.3 Applying calibration to hierarchical routing

For HCR, you can:

1. For each internal node v, define a label $y_v=1$ if its subtree contains at least one gold-relevant leaf, else 0.
2. Collect base scores $s_v$ (embedding similarity, BM25, cross-encoder, or some combination) across many queries.
3. Fit a calibration model:

$$
P(y_v=1 \mid s_v, \text{level}, \text{depth}, \text{branching metadata}, \dots)
$$

using Platt scaling, isotonic, or a small NN.
4. Use this as the estimate of $P(\text{answer in subtree} \mid \text{observations})$.

This gives you the **likelihood terms** needed for an SPRT-style decision:

- Continue exploring a branch while

$$
\frac{P(\text{data} \mid \text{answer in subtree})}{P(\text{data} \mid \text{no answer})}
$$

is within bounds.
- In practice, you approximate this with calibrated posterior probabilities and simple thresholds.

There is **no paper that solves SPRT for HCR end-to-end**, but pieces (probability calibration, uncertainty modeling, risk-aware cutoffs) are in place.[^1_20][^1_21][^1_32]

***

## 5. Cascaded / hybrid scoring

### 5.1 Empirical practice: multi-stage retrieval

Modern IR and RAG systems almost universally use multi-stage pipelines:[^1_34][^1_9][^1_8][^1_10][^1_7]

- **Stage 1: Cheap, high-recall retrieval.**
    - BM25, dense, or hybrid; retrieve 500–10,000 candidates in **10–20 ms**.[^1_7]
- **Stage 2: Neural reranker.**
    - Cross-encoder or late-interaction; rerank top‑500–1000 in **50–100 ms** on GPU.[^1_10][^1_7]
- **Stage 3: LLM reranker / judge.**
    - Apply to top‑30–50 to refine further; more accurate but expensive.[^1_35][^1_9][^1_34]

Evidence:

- Ensemble of cross-encoder + GPT-based reranker improved MAP@10 from 0.158 to 0.4551 in biomedical retrieval.[^1_9][^1_10]
- Multi-stage pipelines with BM25-first consistently outperform pure dense or pure BM25 across tasks.[^1_8][^1_34][^1_7]


### 5.2 Recall/latency tradeoffs

General pattern:

- First-stage retrieval aims for **recall ≥ 95–99%** on “relevant doc in top‑K”, at **low latency**.
- Rerankers work on **small candidate sets** (tens to hundreds), so cost is manageable.
- LLM reranking is used **sparingly** due to token cost but gives extra accuracy on the hardest cases.[^1_35][^1_9]


### 5.3 Designing cascades for HCR

In HCR, a natural cascade per level is:

1. **Stage A: Embedding + BM25 hybrid scoring** for all children at a level.
    - Score all b children cheaply; keep all with $P(\text{subtree})$ above a **very generous threshold** or keep top‑k with k reasonably large (e.g., 3–5).
2. **Stage B: Cross-encoder on borderline children.**
    - For nodes where calibration model has high uncertainty or scores cluster tightly, run a **cross-encoder reranker** for those children to better separate them.
3. **Stage C: LLM-as-judge only if necessary.**
    - For remaining near-ties or for small but complex subtrees, call an LLM-as-judge that reads summaries and gives calibrated scores.

Theoretical work on optimal cascades in IR is limited; OpTranker and related works analyze how to map score distributions to probabilities and optimize cutoffs. In practice, thresholds are chosen empirically via:[^1_33]

- Maximizing expected utility = accuracy − λ·cost,
- Or Ray-tuned tradeoff curves of recall vs. latency.

This matches your **“exponential lever”** logic: invest a bit more compute where it most reduces ε.

***

## 6. LATTICE’s scoring in detail (closest prior art to HCR)

From the arXiv paper and its extended HTML:[^1_36][^1_37][^1_38][^1_3]

### 6.1 Core scoring and calibration mechanism

1. **Tree structure.**
    - Semantic tree with maximum branching factor $M \approx 10–20$, built either bottom-up (cluster + summarize) or top-down (LLM-driven divisive clustering).[^1_3]
    - Internal nodes store LLM-generated summaries; leaves store documents.
2. **Search LLM.**
    - Gemini‑2.5‑flash acts as a **listwise scorer**:

$$
\mathcal{L}(q, [\phi(v_1), \dots, \phi(v_k)]) \to [s_1,\dots,s_k], s_i \in [0,1]
$$
3. **Slate construction with calibration.**
    - For each node in the beam, slate = children C(v) + calibration nodes:
        - For internal nodes: add highest-scoring sibling.
        - For leaves: add $\ell$ leaf nodes sampled from current top predictions Pred, weighted by $e^{\hat{p}_{\text{rel}}(u)}$.[^1_3]
4. **Latent-score estimation.**
    - Observed scores modeled as:

$$
s^i_v = a \cdot \hat{s}_v + b^i + \epsilon
$$
    - Optimize $a$, per-slate $b^i$, and all latent scores $\hat{s}_v$ by minimizing MSE over all past slates (using Adam).[^1_3]
5. **Path relevance update.**
    - Recursive smoothing:

$$
\hat{p}_{\text{rel}}(v) = \alpha \cdot \hat{p}_{\text{rel}}(\text{parent}(v)) + (1-\alpha)\cdot \hat{s}_v, \quad \alpha=0.5
$$
    - Frontier is a max-priority queue on $\hat{p}_{\text{rel}}(v)$; leaf candidates Pred are sorted by $\hat{p}_{\text{rel}}$.[^1_3]
6. **Search budget.**
    - Beam size $B = 2$, iterations $N = 20$ ⇒ **≈250 nodes evaluated per query**.
    - This is the **logarithmic complexity** lever: many fewer nodes than flat reranking of 1000+ docs.

### 6.2 Performance and limitations

- On BRIGHT StackExchange subsets (static corpus):
    - LATTICE: **nDCG@10 = 51.6** vs BM25+LLM rerank (XRR2) **47.4**, fine-tuned DIVER‑v2 **52.2**.[^1_3]
- Overall Recall@100: **74.8 vs 65.3 (BM25) and 70.8 (ReasonIR-8B)**.[^1_3]
- Cost–performance curves show that as you allocate more token budget, **LATTICE’s performance increases steadily**, while reranking baselines plateau.[^1_3]
- Limitations:
    - Static semantic tree struggles with **dynamic corpora** and per-query exclusion lists (coding/math tasks), because internal summaries can become stale and mislead traversal.[^1_3]
    - Calibration model is linear; authors note future work could explore richer probabilistic models.[^1_3]
    - No formal admissibility or per-level ε bounds; performance is empirical.

For HCR, LATTICE validates:

- **LLM-as-judge + calibration + path smoothing** is a viable, high-accuracy hierarchical scoring method.
- Token budgets similar to multi-stage rerankers can produce **better overall recall/precision** than flat reranking.

***

## 7. Scoring for information density under a token budget

You’re explicitly framing selection as a **knapsack**: choose nodes maximising information per token under a budget.

### 7.1 Explicit information-density scoring: AdaGReS

AdaGReS (2025) is the most relevant recent work:[^1_2][^1_1]

- Formulates a **set-level objective**:

$$
F(q, C) = \alpha \sum_{c \in C} \text{sim}(q, c) - \beta \sum_{i<j} \text{sim}(c_i,c_j)
$$

where:
    - first term = total relevance,
    - second term = redundancy penalty.
- Performs **greedy selection** of chunks under a **token budget $T_{\max}$**:
    - At each step, add the chunk whose marginal gain $\Delta F$ is largest, as long as total tokens ≤ $T_{\max}$.
- Introduces a **closed-form, instance-adaptive $\beta^*$** based on observed candidate-pool stats and target expected set size, avoiding manual tuning.
- Shows $F$ is **$\epsilon$-approximately submodular**, so greedy selection is near-optimal under realistic assumptions.

This is directly aligned with “information density per token”:

- Relevance term approximates **information value**,
- Redundancy penalty captures **non-redundancy**,
- Token budget is the knapsack constraint.


### 7.2 Token budgets vs top‑k

Hindsight’s “Token budgets vs top‑k” argument makes a similar point qualitatively: selecting top‑k chunks wastes capacity if chunk sizes vary; you want to **fill tokens, not slots**.[^1_39]

Combined with AdaGReS, the picture is:

- Do **flat retrieval** within a pool (e.g., surviving leaves after hierarchical routing).
- Then **greedy pack** with an information-density objective until token budget is exhausted.


### 7.3 How this plugs into HCR

Concretely:

- For each leaf chunk $c$, compute:
    - Estimated **relevance score** $r_c$ (cross-encoder / ColBERT / LLM),
    - Embedding vector (for redundancy similarity),
    - Token length $L_c$.
- Run AdaGReS-style selection over the union of all leaves in the surviving subtrees:
    - $F(q,C)$ as above,
    - Stop when $\sum_{c\in C} L_c \le T_{\max}$ and next candidate would exceed budget.

To incorporate **hierarchical routing**:

- Use per-subtree estimates of expected **marginal gain per token**:

$$
\text{score}(v) \approx \frac{\mathbb{E}_{c \in \text{subtree}(v)}[\Delta F(c | C)]}{\mathbb{E}[L_c]}
$$
- Route into subtrees with the highest estimated marginal gain per token, recursively.

No one has published this exact HCR + AdaGReS combination yet, but the pieces exist; it’s “frontier, but well founded.”

***

## 8. Practical feasibility for b ≈ 8–12, d ≈ 2–3, ε ≤ 0.02

Let’s ground this in some numbers.

### 8.1 Tree shape and operations

Assume:

- Branching factor $b=10$,
- Depth $d=3$ (root, level‑1, level‑2, then leaves).
- At each internal node, you **keep top‑k branches**, say k = 3, based on routing scores.

Then:

- Level‑1: 10 children; you evaluate all 10.
- Level‑2: For 3 selected level‑1 nodes, each with 10 children, evaluate 30 nodes.
- Total internal-node evaluations ≈ 40 per query.

Even if you add some **exploration beyond top‑k** (e.g., dynamic branching based on uncertainty), the order remains **O(b·d) ≈ 20–100 nodes**.

### 8.2 Error targets

From RB‑002:

- For d=3, 95% overall recall ⇒ ε ≤ 1.7%.
- For d=2, 99% overall recall ⇒ ε ≤ 0.5%.

Given you’re planning **coarse-to-fine** (1–2 hierarchical levels, then flat within survivors), you mainly need:

- **Per-level ε ≤ 0.5–2%** on levels 1–2, measured as:
    - Probability that all selected children at that level **exclude** the true answer’s subtree.

This is easier than per-node classification:

- With k=3 out of b=10 kept, you can tolerate more noise while still keeping the true child.


### 8.3 Feasibility by method

#### A. Pure embedding similarity on summaries

- Empirically, embedding-based RAPTOR-style traversal loses to collapsed-tree search in its strict mode, which is consistent with **per-level ε in the high single digits or worse** on challenging queries (corroborated in prior art you cited).
- Anisotropy compresses similarities into a narrow range, hurting discrimination.
- Target ε ≈ 1–2% is **optimistic** here, especially for reasoning-heavy or compositional queries.

**Verdict:** Not sufficient on its own for HCR’s coarse routing; treat as one feature among many.

#### B. Hybrid sparse+dense + cross-encoder on ambiguous nodes

A minimal scoring stack per internal node:

1. Compute BM25 score and dense similarity $s_{\text{BM25}}, s_{\text{dense}}$ for all b children.
2. Fuse (e.g., RRF or small linear model) to rank children:
    - This alone, in flat retrieval, often reaches recall ≥ 95% for top‑K with modest K.[^1_8][^1_7]
3. For **ambiguous cases** (e.g., top‑3 scores within a small margin), run a small cross-encoder over the 3–5 borderline children to refine.

Expected properties:

- With **hybrid** scoring, correct child is in top‑3 with probability well above 98% on in-domain queries (based on experience with hybrid retrieval pipelines; not many papers report per-query “branch correctness,” but hybrid+reranker recall@10 of 98%+ is typical on focused QA tasks).
- Cross-encoder **sharpens** the worst cases; these tend to be where BM25/dense disagree or both are low-confidence.

**Cost estimate per query (internal nodes):**

- BM25 + dense for 40 nodes: negligible (~1–2 ms).
- Cross-encoder: assume 5–10 ambiguous nodes total per query:
    - With a compact 6-layer BERT cross-encoder, this can be **<10–20 ms** GPU time; CPU is slower but still manageable.

Hitting ε ≤ 0.02 per level is **plausible** if:

- You train the fusion + calibrator on your own task,
- Use **top‑k > 1** at each level,
- And allow cross-encoder only for borderline children.


#### C. LLM-as-judge with LATTICE-style calibration

If you follow LATTICE more closely for coarse routing:

- Use an LLM-as-judge for internal nodes with listwise scoring and latent-score calibration.
- Beam size 2, N ≈ tree depth + few extra iterations ⇒ you evaluate **a few hundred nodes max** (LATTICE uses ~250 nodes per query).[^1_3]

Given LATTICE’s end-to-end Recall@100 ≈ 75% on a notoriously hard benchmark where many baselines are much worse, it is reasonable to infer that:[^1_3]

- **Per-level ε is relatively low**, especially on the static StackExchange subsets where LATTICE matches fine-tuned SOTA.
- The main failures are due to static-tree artifacts on dynamic corpora, not scoring per se.[^1_3]

Token cost is higher than cross-encoder, but:

- You can **restrict LLM-as-judge to root and level‑1**, and use cheaper methods below.
- LATTICE shows this is still competitive with BM25+rerank baselines in terms of tokens vs nDCG.[^1_3]

**Verdict:** For high-stakes queries and modest corpora, LLM-as-judge coarse routing can likely achieve ε in the **sub-1% range** at acceptable cost.

***

## 9. How scoring should differ between abstraction levels

Putting it together:

- **Level 0 (root) and Level 1 (coarse topics).**
    - Goal: **near-perfect recall**, tolerate many false positives.
    - Use:
        - Hybrid BM25+dense scoring per child,
        - Level-specific calibration → $P(\text{answer under child})$,
        - Optional LLM-as-judge for borderline clusters (esp. for reasoning tasks).
    - Keep **multiple children (top‑k)** with cumulative probability ≥ target (e.g., 0.99).
- **Level 2 and leaves (fine selection).**
    - Goal: **high precision under token budget**.
    - Use:
        - Strong rerankers (cross-encoder, ColBERT, or LLM-as-judge) on candidates aggregated from surviving branches.
        - Information-density selection à la AdaGReS under token budget.
    - Here, false positives are expensive; incorporate redundancy penalties and token lengths into scoring.

Cross-level calibration (scores across levels) is handled via:

- Level-aware normalization,
- Path smoothing (like LATTICE’s $\hat{p}_{\text{rel}}$),
- And using *relative* improvements (child vs parent) rather than raw scores.

***

## 10. Recommendations for HCR RB‑003

Given the landscape and your RB‑002 constraints, a concrete scoring design that is feasible today:

1. **Base signals at every node:**
    - Dense similarity of query with node summary embedding.
    - BM25 / SPLADE score of query vs node summary.
    - Node-level metadata features: depth, summary length, number of leaves, etc.
2. **Learned routing classifier + calibration:**
    - Train a small model to estimate $P(\text{answer in subtree} \mid \text{features})$ for internal nodes.
    - Calibrate with Platt or isotonic regression to yield reliable probabilities.
3. **Per-level routing strategy:**
    - At each internal node:
        - **Score all children** with the cheap model.
        - Keep any child with calibrated $P$ above a conservative threshold, plus enough top‑k children so cumulative mass ≥ 0.99.
        - For ambiguous siblings, run a **small cross-encoder**; optionally escalate to an **LLM-as-judge** with a LATTICE-style latent-score model for the hardest cases.
4. **Path-level aggregation:**
    - Maintain a **path relevance estimate**:

$$
\hat{p}_{\text{path}}(v) = \alpha \cdot \hat{p}_{\text{path}}(\text{parent}(v)) + (1-\alpha)\cdot \text{calibrated\_P}(v)
$$
    - Use this to prioritize which frontier nodes to expand (beam-search or best-first).
5. **Leaf-level selection under token budget:**
    - For leaves in all surviving subtrees, compute strong relevance scores (cross-encoder or ColBERT).
    - Run an **AdaGReS-like greedy selection**:
        - Objective: relevance − redundancy penalty,
        - Constraint: total tokens ≤ budget.
6. **Measure ε empirically per level.**
    - On a held-out set with subtree-level ground truth, estimate:
        - Per-level probability that the correct branch is missing from the kept set.
    - Tune thresholds, k, and escalation rules to push ε into your target range (0.5–2%).
7. **Accept that strict admissibility is unattainable.**
    - Design HCR around **calibrated probabilities and conservative thresholds**, not worst-case guarantees.
    - Use uncertainty (via Bayesian retrieval, dropout, or ensembling) to drive SPRT-style stopping decisions where possible.[^1_21][^1_32][^1_20]

This design leverages:

- The empirical strengths of **multi-stage retrieval** and **hybrid scoring**,
- The **hierarchy-aware calibration** ideas from LATTICE,
- And modern **information-density selection** (AdaGReS) for the knapsack aspect.

Where the literature is silent (e.g., exact ε bounds for hierarchical routing), treat that as an open research area rather than something to approximate away. For RB‑003, capturing those gaps explicitly, and designing your offline evaluation to estimate ε directly, will be as important as the scoring mechanism itself.
<span style="display:none">[^1_40][^1_41][^1_42][^1_43][^1_44][^1_45][^1_46][^1_47][^1_48][^1_49][^1_50][^1_51][^1_52][^1_53][^1_54][^1_55]</span>

<div align="center">⁂</div>

[^1_1]: https://www.themoonlight.io/en/review/adagresadaptive-greedy-context-selection-via-redundancy-aware-scoring-for-token-budgeted-rag

[^1_2]: https://arxiv.org/abs/2512.25052

[^1_3]: https://arxiv.org/pdf/2510.13217.pdf

[^1_4]: http://arxiv.org/pdf/1511.0628.pdf

[^1_5]: https://www.geeksforgeeks.org/machine-learning/ball-tree-and-kd-tree-algorithms/

[^1_6]: https://dl.acm.org/doi/full/10.1145/3716825

[^1_7]: https://www.systemoverflow.com/learn/search-ranking/ranking-algorithms/multi-stage-retrieval-bm25-as-high-recall-first-stage

[^1_8]: https://devtechtools.org/zh/blog/production-rag-hybrid-search-cross-encoder-reranking

[^1_9]: https://arxiv.org/html/2507.05577v1

[^1_10]: https://aclanthology.org/2025.sdp-1.25.pdf

[^1_11]: http://arxiv.org/pdf/2004.12832.pdf

[^1_12]: https://arxiv.org/abs/2004.12832

[^1_13]: https://weaviate.io/blog/late-interaction-overview

[^1_14]: https://arxiv.org/html/2601.06389v2

[^1_15]: https://arxiv.org/abs/1206.0335

[^1_16]: https://www.emergentmind.com/topics/matryoshka-embedding

[^1_17]: https://milvus.io/docs/funnel_search_with_matryoshka.md

[^1_18]: https://milvus.io/ai-quick-reference/what-are-matryoshka-embeddings-in-nlp

[^1_19]: https://sbert.net/examples/sentence_transformer/training/matryoshka/README.html

[^1_20]: https://arxiv.org/pdf/2105.04651.pdf

[^1_21]: https://health-nlp.com/files/pubs/sigir21a.pdf

[^1_22]: https://en.wikipedia.org/wiki/Platt_scaling

[^1_23]: https://scikit-learn.org/stable/modules/calibration.html

[^1_24]: https://www.cs.cornell.edu/~alexn/papers/calibration.icml05.crc.rev3.pdf

[^1_25]: https://onlinelibrary.wiley.com/doi/full/10.1002/sim.9921

[^1_26]: https://arxiv.org/abs/2403.06551

[^1_27]: https://aclanthology.org/2024.lrec-main.1413.pdf

[^1_28]: https://arxiv.org/pdf/2403.06551.pdf

[^1_29]: https://aclanthology.org/2024.lrec-main.1413/

[^1_30]: https://www.rohan-paul.com/p/ml-interview-q-series-probability-95f

[^1_31]: https://blog.truegeometry.com/api/exploreHTML/4ca27c747e8752b42f7e8fdc84564709.exploreHTML

[^1_32]: https://arxiv.org/html/2411.08891v2

[^1_33]: http://web4.cs.ucl.ac.uk/staff/jun.wang/papers/2010-sigir10-optranker.pdf

[^1_34]: https://rajivshah.com/blog/rag-agentic-world.html

[^1_35]: https://www.youtube.com/watch?v=9QJXvNiJIG8

[^1_36]: https://chatpaper.com/paper/200267

[^1_37]: https://openreview.net/forum?id=p0gxvlUoZM

[^1_38]: https://huggingface.co/papers/2510.13217

[^1_39]: https://nicoloboschi.com/posts/20251210/

[^1_40]: https://blog.csdn.net/royole98/article/details/120503829

[^1_41]: https://designcreativetech.utexas.edu/work/lattice-2025-design-mfa-exhibition

[^1_42]: https://www.cs.utexas.edu/theory-seminar

[^1_43]: https://arxiv.org/html/2509.20415v1

[^1_44]: https://www.emergentmind.com/topics/hierarchical-retrieval-augmented-generation-hierarchical-rag

[^1_45]: https://arxiv.org/abs/2601.04945

[^1_46]: https://d-scholarship.pitt.edu/30526/1/Thesis_EDT_Mahdi%20(65).pdf

[^1_47]: https://arxiv.org/html/2403.06551v1

[^1_48]: https://supermemory.ai/blog/matryoshka-representation-learning-the-ultimate-guide-how-we-use-it/

[^1_49]: https://www.abhik.ai/concepts/embeddings/multi-vector-late-interaction

[^1_50]: https://www.iamdave.ai/blog/how-to-structure-data-for-rag-the-role-of-token-splitting/

[^1_51]: https://www.reddit.com/r/MachineLearning/comments/1bq3hwb/adaptive_rag_a_retrieval_technique_to_reduce_llm/

[^1_52]: https://pmc.ncbi.nlm.nih.gov/articles/PMC12886353/table/T13/

[^1_53]: https://d-nb.info/1385563486/34

[^1_54]: https://chatpaper.com/chatpaper/paper/108787

[^1_55]: https://icml.cc/virtual/2025/poster/45145


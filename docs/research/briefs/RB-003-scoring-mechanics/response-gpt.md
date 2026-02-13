# RB-003: Scoring Mechanics — GPT Response

# RB-003: Scoring Mechanics for Hierarchical Retrieval

## Problem framing and the accuracy bar

Hierarchical context retrieval (HCR) has a brittle failure mode: **a single false negative at an early routing step permanently deletes the correct subtree**, making downstream ranking and generation irrelevant. This is structurally the same constraint that shows up in classical cascaded decision systems: the early “attentional” filter must have *near-zero false negatives*, while tolerating many false positives because they only increase later compute. In the canonical cascade detector, the authors explicitly emphasise that the key measure is the attentional process’ false negative rate, and report achieving *under ~1% false negatives* while allowing *high false positives* in the first stage. citeturn22view0

For HCR, “routing” is also not a standard ranking problem. The target question at an internal node is:

**“Does any descendant leaf contain evidence that answers this query?”**

That makes node scoring closer to **subtree membership prediction** than to “top‑k best documents” selection. Most prior work reports end metrics (Recall@K, nDCG@K, QA accuracy), not calibrated *per-level subtree recall*, which is the metric your RB‑002 analysis identifies as the exponential lever. This mismatch in how systems are evaluated is part of why traversal-based hierarchies often underperform their “collapsed” counterparts despite being intuitively appealing. citeturn5view0

A practical implication is that scoring should be designed as **two different instruments** (as you outlined):

- **Coarse routing (levels 1–2):** optimise *recall of the correct subtree*, tolerate false positives, and behave like a “high detection rate” cascade stage. citeturn22view0  
- **Fine selection (within survivors):** optimise *precision under a hard token budget*, where each false positive burns irrevocable context capacity.

Those two objectives pull scoring in different directions and generally require different mechanisms or a cascade.

## Landscape of scoring mechanisms for hierarchical routing

The scoring landscape is best organised by what information the scorer can exploit (lexical overlap, semantic proximity, deep interaction, reasoning) and what it costs (precompute vs per‑query compute, latency, tokens).

### Vector similarity on node representations (bi-encoder style)

**Mechanism.** Encode query and node into vectors; score by cosine/dot product. This is the dominant “cheap routing” baseline in hierarchical RAG systems (e.g., RAPTOR embeds all nodes and traverses by cosine similarity). citeturn5view0

**Signal captured.** Contextual semantic similarity at the granularity of a *single vector per node*.

**Routing-specific strengths.**
- Extremely low per-node cost; scoring all children at a level is trivial when branching is ~10.
- Works well when node text is itself a good surrogate for what descendants contain.

**Routing-specific weaknesses.**
- When internal nodes are *summaries*, the score can systematically under-estimate descendant relevance for “detail queries” (a query about a specific fact may not match a thematic summary). RAPTOR directly reports that collapsed-tree retrieval “consistently performs better” than strict layer-by-layer traversal and attributes this partly to flexibility in retrieving at the right granularity rather than being constrained by traversal ratios. citeturn5view0
- In embedding spaces, cosine similarity can be compressed by anisotropy (embeddings “occupy a narrow cone”), reducing discrimination in exactly the regime you need for reliable pruning. citeturn24view0turn24view1

### Sparse / lexical routing (BM25-family and variants)

**Mechanism.** Treat each node (or subtree) as a pseudo-document; score with lexical term statistics (BM25 and extensions), or hybrid lexical scoring.

**Signal captured.** Exact/near-exact lexical overlap and term salience; tends to be robust for “needle-in-haystack” detail queries where the answer contains a rare identifier or phrase.

**Why it matters for routing.** The probabilistic relevance framework that underpins BM25 explicitly frames ranking as ordering by an (estimated) probability of relevance. citeturn23search2turn23search10 Although BM25 scores are not automatically *calibrated probabilities*, the modelling perspective is aligned with subtree-membership decisions and supports principled feature engineering for calibration (e.g., score normalisation per level). citeturn23search2turn23search7

### Late interaction (multi-vector) scorers

**Mechanism.** Represent documents with multiple token vectors; score by cheap token-level matching atop precomputed representations (late interaction). ColBERT is the canonical example. citeturn8search3turn8search15

**Signal captured.** Fine-grained matches between query tokens and document tokens, without paying full cross‑encoder cost per pair.

**Routing value.** For internal nodes, late interaction allows a node representation to preserve “detail hooks” (rare entities, formula fragments, code tokens) that single-vector summaries can wash out. ColBERT explicitly positions late interaction as both scalable and “pruning-friendly,” enabling indexed retrieval via vector similarity structures. citeturn8search3turn8search15

### Cross-encoder rerankers (deep interaction)

**Mechanism.** Run a transformer over the concatenated (query, text) pair; output a relevance score. BERT reranking (monoBERT / cross‑encoder) is the canonical paradigm. citeturn23search0turn23search12

**Signal captured.** Deep cross-attention over query and node text; substantially more precise than bi‑encoder similarity when text is ambiguous or requires multi-term reasoning.

**Routing relevance.** Cross-encoders are natural candidates for *level‑1 / level‑2 routing in shallow trees*, because you only evaluate tens to low hundreds of nodes—not thousands. However, they become impractical if you allow b^k to grow into the thousands without a cheaper first-stage filter. citeturn23search12turn20search13

### LLM-as-judge scoring

**Mechanism.** Prompt an LLM to score relevance (pointwise, pairwise, or listwise) given a query and node text; optionally ask for structured outputs.

**Signal captured.** Semantic reasoning over text; can handle “why” and “how” queries better than pure similarity scorers in some regimes, but is sensitive to prompt framing and context effects.

**Known issues.** A recent survey of LLM-as-a-judge methods stresses judge bias, vulnerability, and context-dependence, and notes ongoing work on calibration and debiasing to improve reliability. citeturn17view0 These issues matter more for routing than reranking because routing errors are irreversible.

### Learned routing functions / calibrated subtree classifiers

**Mechanism.** Train a model to output \(P(\text{subtree contains relevant leaf} \mid q, \text{node})\), using supervised labels derived from ground-truth relevant leaves.

**Signal captured.** Whatever features you feed: lexical, dense, structural (depth, subtree size), and historical.

**Why it fits your theoretical need.** This is the most direct route to “scores that approximate likelihood ratios” (RB‑002’s SPRT framing), because the objective can be trained for probabilistic calibration rather than purely ranking loss. citeturn23search7turn23search3  
The trade is data requirements and distribution shift risk (new corpus topics, new tree construction style).

## Admissible scoring and safe pruning

Your RB‑002 notion of “admissible” corresponds to an **upper bound** on descendant relevance: a node score that **never underestimates** the best possible descendant score. In IR and similarity search, this is exactly the property that enables branch-and-bound pruning.

### Where admissibility is achievable

**Metric trees for nearest neighbour.** In metric spaces with triangle inequality, hierarchical structures like cover trees enable pruning based on distance bounds while preserving exactness. Cover trees are explicitly designed for nearest neighbor operations in general metric spaces and rely on metric properties to bound search. citeturn8search1turn8search5

**Admissible bounds for maximum inner product / cosine.** For embedding retrieval where relevance is defined as **maximum inner product similarity (MIPS)** (and cosine similarity under normalisation), admissible upper bounds can be constructed for sets of vectors in a node. A concrete example is a ball-tree bound: for a node represented by a centre vector and radius, one can compute an analytical upper bound on the maximum possible inner product between the query and any point in the ball. Ram & Gray formalise this as an explicit theorem (bounding maximum inner product with a ball) and use it for branch-and-bound search. citeturn14view3turn14view0

**What this buys HCR.** If your routing score is defined as:

\[
\text{score(node)} = \max_{x \in \text{descendant leaf embeddings}} \langle q, x \rangle,
\]

then a ball/cone/metric bound can be **admissible** for that score, making *safe pruning solvable* in the classical sense. citeturn14view3turn8search1

### Where admissibility is not achievable (in the sense you want)

**Textual summaries are not geometric envelopes.** A summary embedding is not a bound on the set of descendant embeddings; it is a different object produced by a lossy channel. RAPTOR’s results—collapsed-tree retrieval outperforming strict traversal—are consistent with summary-node similarity being an unreliable pruning signal for certain query types. citeturn5view0

**LLM judgement scores are not monotone set bounds.** LLM-as-judge outputs are explicitly described (by LATTICE) as noisy, context-dependent, and unaware of the hierarchy—precisely the properties that break any notion of a guaranteed upper bound across nodes. citeturn4view3turn3view0

**Even LATTICE calls out summary-driven traversal failure modes.** LATTICE notes that precomputed summaries can misguide traversal in settings where the effective corpus changes (dynamic exclusion), because the summaries do not update in sync with the reachable leaves. citeturn21view0turn9view2

### Practical interpretation: “admissible enough” via conservative acceptance

Given the above, for HCR the most realistic interpretation of “admissible” is:

- **Provably admissible** only for *embedding-set bounds* (metric-tree style) relative to a fixed similarity function. citeturn14view3turn8search1  
- **Statistically controlled false negatives** for semantic routing: tune thresholds/beam widths so the empirical subtree recall is ≥99% at levels 1–2, allowing many false positives (cheap). This is exactly the operating principle of cascades: early stages tune for high detection even if precision is low. citeturn22view0turn20search2

image_group{"layout":"carousel","aspect_ratio":"16:9","query":["ball tree maximum inner product search diagram","cover tree nearest neighbor diagram","metric tree vantage point tree diagram"],"num_per_query":1}

## Cross-level calibration and representation design

Cross-level calibration is the core reason “summary embedding + cosine traversal” tends to underperform: as you move up the tree, representations become more abstract and less aligned to detail queries.

### Empirical evidence that cross-level mismatch matters

RAPTOR explicitly compares strict traversal (level-by-level pruning) with collapsed-tree retrieval (score all nodes across levels together) and reports that collapsed-tree retrieval “consistently performs better” in its QASPER controlled evaluation. The authors attribute this to collapsed retrieval’s ability to pick the “correct level of granularity” rather than being constrained by a fixed per-level selection ratio. citeturn5view0

LATTICE also builds a semantic tree with internal nodes represented by LLM-generated summaries, but frames the challenge differently: the key problem is that local LLM relevance judgements are not comparable across branches/levels unless calibrated. citeturn3view0turn4view3

### Techniques that actually address cross-level calibration

**Level-conditioned scoring and normalisation.** If you keep bi‑encoder similarity, you generally need level-specific calibration because similarity score distributions can shift with text length, abstraction, and embedding geometry. Embedding anisotropy (vectors concentrated in narrow cones) compresses cosine scores and can make “absolute score thresholds” brittle across contexts. citeturn24view0turn24view1  
A standard remedy in ML is post-hoc calibration (temperature scaling) on held-out data; the key is to do it **per level** (or per node type) rather than globally. citeturn23search7turn23search3

**Parent–child delta logic (conditional pruning).** HIRO introduces a two-threshold policy: a selection threshold selects promising parents, and a delta threshold prunes children only when they do not improve enough over the parent; otherwise the parent is retained as context. This effectively guards against the case where a query matches the parent summary but fails to match any single child strongly enough due to granularity mismatch, while also reducing redundancy (parent + many similar children). citeturn6view0turn7view0

**Multi-resolution embeddings.** Matryoshka Representation Learning (MRL) explicitly trains embeddings so that prefixes of the embedding vector form effective lower-dimensional representations, giving a built-in coarse-to-fine mechanism “with no additional cost during inference and deployment” and enabling cost-adaptive retrieval. citeturn8search0turn8search8  
For HCR, this suggests a concrete cross-level approach: route on low-dimensional prefixes (high-level semantics, cheap) while scoring survivors on larger prefixes (finer semantics).

**Multi-vector node representations (late interaction).** Late interaction models such as ColBERT represent a passage as a set of token vectors and score by aggregating max-similarities; this preserves “detail hooks” that single-vector abstractions can lose and provides a retrieval model that is explicitly designed to remain scalable. citeturn8search3turn8search15  
For internal nodes, you can approximate this by storing a small set of representative vectors per subtree (e.g., medoids) or a learned summary that is multi-vector rather than single-vector.

**Anchor-based cross-branch and cross-level calibration (LATTICE’s approach).** LATTICE’s key contribution for your RB‑003 questions is that it does not treat the LLM’s raw node scores as globally comparable. Instead, it:
- Constructs “slates” for the search LLM that include not only a node’s children but also *calibration items* (e.g., top-scoring siblings for internal nodes; previously good leaves for leaf-level scoring). citeturn4view3turn4view0  
- Models each observed local score as a **linear transformation** of a slate-independent latent relevance score with a per-slate bias, and estimates these latent scores by minimising MSE over all observed scores. citeturn4view3turn4view1  
- Aggregates calibrated latent scores into a **path relevance** signal via an exponentially weighted moving average, enabling comparison of nodes across different branches and depths. citeturn4view3turn3view0  

This is a concrete, implemented solution to the cross-level comparability problem—though it is not an admissible bound and not a calibrated probability model (see next section). citeturn4view3turn21view0

## Probability calibration for routing and stopping criteria

Your SPRT framing requires something stronger than “a score”: it wants **well-calibrated likelihood ratios** (or at least calibrated probabilities of subtree membership) so decisions can be made with optimal stopping guarantees.

### What calibration tools can and cannot do

**Classification calibration is well-developed.** Temperature scaling (a one-parameter logit rescaling) is a widely used post-hoc method and is described as “surprisingly effective” in the modern neural network calibration literature. citeturn23search3turn23search7

**Retrieval calibration is harder than classification calibration.** Retrieval scores are produced in a ranking context, not a pure classification context; score distributions vary by query, corpus, and candidate set. Cohen et al. argue that retrieval models produce deterministic scores that hide uncertainty, propose an approximate Bayesian framework to model score distributions, and introduce a ranking-based calibration metric; they show that uncertainty information can be actionable for downstream tasks like cutoff prediction (deciding how far down the ranked list to trust). citeturn16view0  
This is directly relevant because hierarchical routing has the same structural decision: *when to stop exploring / when to prune / how confident are we?* citeturn16view0turn4view3

### How to obtain “probability the answer is in this subtree” in practice

The most direct path is to operationalise subtree membership into a supervised binary target:

- Label an internal node as positive if at least one ground-truth relevant leaf is in its subtree.
- Train a scorer to predict \(P(\text{positive} \mid q, \text{node})\).
- Apply post-hoc calibration per level (temperature scaling or isotonic) to correct confidence. citeturn23search7turn23search3

This is conceptually clean, but the frontier is in (a) obtaining reliable training labels, (b) handling distribution shift (new corpora / new hierarchies), and (c) ensuring calibration remains stable under changing candidate sets.

### What LATTICE contributes and what it does not

LATTICE is explicitly built to address *cross-branch and cross-level comparability* of LLM judgements via latent score calibration and path relevance smoothing. citeturn4view3turn3view0  
However, its calibration is not presented as probability calibration; it is a **global consistency mechanism** for noisy slate-based scores (linear latent score + per-slate bias), optimised via MSE. citeturn4view3turn4view1  
So LATTICE is evidence that calibration matters and can be done effectively, but it is not (yet) a solved “scores as likelihood ratios” framework.

## Cascaded scoring and escalation policies

Cascades are the dominant practical answer to “we need both high recall and low cost,” and hierarchical routing is naturally a cascade:

- **Stage A:** cheap, high-recall filter (dense, sparse, or hybrid).
- **Stage B:** more expensive reranker / judge for borderline cases.
- **Stage C:** final context selection under budget with redundancy control.

This is not just industry lore; the empirical retrieval literature is explicitly built around multi-stage ranking pipelines. citeturn23search12turn20search13  
Recent work on effectiveness–efficiency tradeoffs in multi-stage ranking argues that you can retain much of transformer reranker effectiveness by careful pipeline design rather than running the expensive model everywhere. citeturn20search13

A modern variant relevant to your hybrid dense/sparse theme is to blend signals in a controlled second stage: Nardini et al. (2025) train a learning-to-rank model to combine dense representations with a large set of lexical features, reporting nDCG@10 gains alongside a small latency increase in their cascade setting. citeturn20search1turn20search9

For hierarchical routing, the cascade design principle mirrors the attentional cascade logic: each stage should be tuned for minimal false negatives even at the cost of false positives. citeturn22view0turn20search2  
This is the most robust way to get the effective per-level error \(\varepsilon\) into the low single-digit percentages (or below) without paying cross-encoder/LLM cost on every node.

## Cost models and feasibility at b=8–12, d=2–3

Your specified regime (branching factor 8–12, depth 2–3) is important because it shifts what is “practical” dramatically: **routing sets are small**.

### How many node evaluations are we really talking about?

Let branching factor be \(b\). If you score all children at:
- level 1: \(b\) nodes
- level 2: \(b^2\) nodes
- level 3: \(b^3\) nodes

With \(b \in [8,12]\), that’s:
- \(8\)–\(12\) nodes at level 1
- \(64\)–\(144\) at level 2
- \(512\)–\(1728\) at level 3

If you use a beam (keep \(k_1\) children from level 1), level‑2 scoring becomes \(k_1 \cdot b\). For example, with \(b=10\) and \(k_1=4\), level‑2 scoring is 40 nodes, not 100.

This matters because it means **cross-encoders are feasible at routing depth 1–2** in many deployments (tens to low hundreds of pairs), while LLM-as-judge becomes plausible only if you keep evaluated nodes similarly small.

### Cost profile by mechanism (relative, with concrete anchors from literature)

**Dense similarity (bi-encoder).** Per-node scoring is just a dot product; the dominant costs are query embedding inference and memory bandwidth. In this b/d regime, vector routing is effectively “free” compared to any transformer cross-attention. RAPTOR explicitly notes that collapsed-tree retrieval increases the number of similarity comparisons (all nodes), but points to FAISS-style ANN libraries as the standard remedy. citeturn5view0

**Cross-encoder reranking.** Cross-encoders are expensive because each (query, text) pair runs a transformer forward pass. But the literature routinely reranks hundreds to thousands of candidates in benchmark settings (e.g., BERT passage reranking over large candidate sets) because the gains can be large. citeturn23search12turn23search0  
In your b/d regime, routing might require only ~10–150 pairs, which is orders of magnitude less than typical “rerank top‑1000” benchmarks—so latency becomes an engineering question (batching, model size), not a combinatorial impossibility.

**Late interaction.** ColBERT empirically positions itself as far more efficient than full BERT cross-encoders while retaining strong effectiveness, and emphasises that its interaction mechanism is designed to support scalable retrieval. citeturn8search3turn8search15  
For routing, late interaction is particularly attractive if your internal node text must remain “summary-like,” because multi-vector scoring can still pick up a specific descendant cue.

**LLM-as-judge routing.** This is expensive in tokens, and token cost scales with the number and length of nodes you present. LATTICE is the best concrete reference here because it *directly uses an LLM to traverse a semantic hierarchy* and reports both effectiveness and cost tradeoffs. citeturn3view0turn21view0  
Key cost facts from LATTICE:
- It uses a search LLM to evaluate slates during traversal and reports configurations where **~250 documents are evaluated by the LLM per query**. citeturn21view3turn9view1  
- It measures cost as **tokens processed by the LLM** and shows a cost–quality curve where guided hierarchical traversal can scale more effectively than reranking long flat lists in certain settings. citeturn21view0turn21view2  
- It reports **Recall@100 of 74.8** on BRIGHT’s StackExchange subsets, outperforming BM25 and a specialised dual encoder baseline in that evaluation. citeturn21view0turn21view2  

For HCR’s coarse routing with b≈10 and depth 2, you could in principle evaluate only tens of internal nodes; that would be far cheaper than LATTICE’s “hundreds of documents” regime. But the deciding question is whether LLM judging is needed for your query distribution (reasoning-heavy) or whether cross-encoder / hybrid scoring suffices.

### The knapsack dimension for fine selection under token budget

Once routing has produced a candidate set, you still have the **budgeted subset selection** problem: choose chunks that maximise marginal utility per token and minimise redundancy.

This is a mature problem in IR/summarisation: MMR explicitly trades relevance against redundancy in sequential selection. citeturn18search0 Submodular summarisation formalises the same trade and provides greedy algorithms with approximation guarantees under submodularity assumptions. citeturn18search1turn18search25

For RAG specifically under strict token budgets, very recent work (AdaGReS, Dec 2025) proposes a set-level objective combining query relevance and intra-set redundancy penalties, performs greedy selection under a token budget, and analyses conditions under which the objective is approximately submodular (to justify near-optimal greedy selection). citeturn19view0  
This is directly aligned with your RB‑002 framing that selection must behave like a knapsack optimiser rather than “top‑k by relevance”.

### Practical feasibility of \(\varepsilon \le 0.02\) per routing level in this regime

The most defensible claim from prior art is not that any single scoring method “guarantees \(\varepsilon\le 0.02\)” universally, but that in shallow trees you can **buy down effective false negatives** using conservative acceptance:

- Keep a wide beam at level 1 (false positives cheap).
- Use a stronger scorer only on borderline nodes (cross-encoder or late interaction).
- Avoid hard pruning unless you have geometric admissible bounds over descendant embeddings. citeturn14view3turn22view0

This is essentially the same design pressure cascades face: per-stage detection must be extremely high to avoid compounding misses, so thresholds are tuned aggressively toward recall. citeturn22view0turn20search2

The strongest concrete evidence that *calibration is pivotal for hierarchical traversal* comes from LATTICE’s ablations: removing score calibration or path relevance smoothing measurably degrades performance, and cross-branch calibration improves results across settings. citeturn4view2turn4view3turn21view0
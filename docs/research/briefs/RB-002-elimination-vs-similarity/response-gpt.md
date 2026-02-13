# RB-002: Theoretical Basis — GPT Response

# Theoretical Basis of Elimination and Similarity Retrieval

**Internal reference:** RB-002 (status: open; date: 2026-02-13, Europe/London).

## Problem formalisation and what the two paradigms really optimise

Consider a corpus of atomic “evidence” units (leaf chunks) \(x_1,\dots,x_N\). A query \(q\) induces an (unknown) relevance set \(R(q)\subseteq\{1,\dots,N\}\) that contains the evidence needed to answer correctly. A retrieval policy selects a set of textual nodes \(S(q)\) subject to a token budget \(\sum_{n\in S(q)} \text{tokens}(n)\le B\), to maximise expected downstream utility (e.g. answer accuracy or expected log-likelihood of the correct answer). Token budget as a hard constraint is not cosmetic; it turns retrieval into a *budgeted information acquisition* problem (choose which “measurements” to pay for). citeturn8search23turn8search3turn3search6

Two retrieval families fit this abstraction:

**Flat similarity retrieval (standard RAG)** ranks leaf chunks by a similarity score \(s(q,x_i)\) (often cosine similarity between embeddings) and returns top-\(k\) or top tokens. It is “one-shot”: no intermediate commitments are required. Efficiency comes from approximate nearest-neighbour (ANN) indexing, not from early semantic commitments. citeturn2search1turn3search5turn1search3

**Elimination-based top-down traversal** adds a hierarchy. Internal nodes \(v\) represent subsets of leaves (a subtree) and have their own representation (e.g. summary text + embedding). Retrieval is sequential: score children of some node, keep a subset, recurse; pruned branches are never revisited. This is structurally identical to *top-down hierarchical classification*: internal decisions constrain which leaves remain reachable, so early errors are irrevocable. citeturn2search7turn2search11turn2search19

A crucial empirical anchor is that RAPTOR explicitly compared (i) layer-by-layer tree traversal vs (ii) “collapsed tree” retrieval that flattens all nodes across all levels and does ordinary similarity search over the entire enriched node set; on their QASPER subset experiment, the collapsed-tree approach “consistently performs better” and is chosen for main results. citeturn6view0turn6view1

The research question here is: when does sequential elimination *dominate* (a) flat leaf search and (b) flat search over enriched multi-level nodes?

## Information-theoretic view: hierarchies as lossy channels and multi-resolution codebooks

### Hierarchical traversal is a sequence of constrained decoding steps

At each internal node \(u\) with children \(\{c_1,\dots,c_m\}\), a traversal policy is implicitly trying to infer a latent discrete variable \(C_u\in\{1,\dots,m\}\): “which child(ren) contain(s) useful evidence for \(q\)?” The only signals available are (i) the query \(q\) and (ii) the internal-node representations (summaries, centroids, embeddings) for \(c_j\). This is a communication problem: the subtree’s leaves contain the “truth” about relevance, but the parent summary/embedding is a *compressed* representation that must carry enough information to route correctly. citeturn3search6turn1search10

A standard lower bound tool is **Fano’s inequality**, which ties any classifier’s minimum achievable probability of error to the mutual information between the latent label and the observation. In words: if the observation carries little mutual information about which child is correct, no decision rule can reliably route. citeturn1search10turn1search2

Applied to traversal: if, for some level, the mutual information \(I(C_u; \text{Obs}_u)\) is small relative to \(\log m\), misrouting has a *non-trivial lower bound* and cannot be eliminated by better thresholds. A traversal policy is only as strong as the **minimum-information bottleneck level**: one bad routing level dominates end-to-end recall because later levels never get to “correct” a misroute. citeturn1search10turn2search7

### Summaries are an information bottleneck, not just a token-saving trick

Internal nodes produced by summarisation are a textbook instance of the **Information Bottleneck**: find a compressed representation \(T\) of some signal \(X\) that preserves information about a “relevant variable” \(Y\) while discarding the rest. In IB terms, \(X\) could be the set of descendant leaf texts, \(T\) the parent summary/embedding, and \(Y\) the query-conditioned relevance event (“does this subtree contain evidence for \(q\)?”). The IB objective explicitly formalises the trade-off: compression reduces cost but can destroy query-relevant information unless the summariser preserves the right sufficient statistics. citeturn3search6turn3search2turn3search22

This immediately yields a sharp condition for when top-down elimination is *theoretically* safe:

- If internal node representations are **(approximately) sufficient statistics** for routing—i.e. they preserve (most of) the mutual information between subtree content and relevance—then elimination can be both efficient and high-recall. citeturn3search6turn1search10  
- If they are not, traversal imposes an *irrecoverable information loss* (once a subtree is pruned, no later computation can recover evidence inside it). citeturn2search7turn2search11

Collapsed-tree retrieval side-steps this failure mode: it does not require that high-level summaries be sufficient for routing. It only requires that *some* node (maybe a leaf, maybe a mid-level summary) has high similarity to the query, because all nodes compete in one global ranking. citeturn6view0turn6view1

### Connection to hierarchical softmax: efficiency via trees, accuracy limited by tree quality

Hierarchical softmax replaces an \(O(|V|)\) normalisation with a tree of binary decisions, producing \(O(\log |V|)\) evaluation. This is the same computational promise elimination-based retrieval aims at: reduce search from “inspect everything” to “make a small number of routing decisions.” citeturn0search2turn0search10

But language-model literature documents a key caution: hierarchical language models can be far faster yet perform worse than non-hierarchical counterparts when the tree is a poor match to the target distribution; a cited critique is that Morin & Bengio’s hierarchical approach was much faster but “performed considerably worse” than a non-hierarchical model, motivating improved tree construction. citeturn0search34turn0search2

That is an existence proof of the general phenomenon: *tree-induced factorisations trade accuracy for efficiency unless the hierarchy aligns with the conditional distributions you must model* (here: relevance given query). citeturn0search34turn1search10

### Vector-search indexing already embodies a “hybrid elimination” theory

Large-scale ANN systems often do a coarse-to-fine routine: (1) choose a small number of coarse clusters (coarse quantiser / IVF lists), then (2) search or rerank within those lists. This is elimination by another name; recall is controlled by how many coarse partitions you probe, and by quantisation distortion. citeturn3search5turn3search24turn2search20

This yields a transferable theoretical lens for HCR-style traversal:

- The “pruning” stage is a quantiser; its error is determined by how well coarse representatives predict nearest neighbours (or relevance). citeturn3search24turn3search5  
- Increasing the number of probed clusters is equivalent to widening the beam, trading compute for recall. citeturn3search5turn2search1  
- If the representation space has unfavourable geometry (high intrinsic dimension, weak cluster structure), tree-like partitioning becomes ineffective and may degenerate toward exhaustive search. citeturn1search3turn7search0

## Decision and search theory: when pruning is provably safe versus inherently fragile

image_group{"layout":"carousel","aspect_ratio":"16:9","query":["branch and bound pruning search tree diagram","vantage point tree nearest neighbor search diagram","hierarchical softmax tree diagram","HNSW graph layers diagram"],"num_per_query":1}

### Branch-and-bound: pruning is lossless only with admissible bounds

In classic **branch-and-bound**, a branch can be pruned without losing the optimum only when you have a bound proving the branch cannot contain a better solution than the current best. If bounds are unavailable or loose, B&B degenerates toward exhaustive enumeration. citeturn1search0turn1search4

For retrieval, the analogous requirement is:

> To prune a subtree without recall loss, you need an *upper bound* on the maximum relevance (or similarity) achievable by any descendant leaf, computable from the internal node representation.

This is not merely a conceptual analogy: nearest-neighbour search has long used branch-and-bound with such bounds when the distance function is metric. In particular, kNN branch-and-bound methods eliminate subsets when triangle-inequality-based distance bounds show no point inside can beat the current best. citeturn7search3turn7search6turn7search1

So the strongest theoretical condition under which elimination is optimal (lossless) is:

- **Metric structure + correct bounds**: a geometry in which internal nodes represent regions (balls, partitions) and where the scoring objective is bounded over regions (e.g. via triangle inequality). citeturn7search6turn7search1turn7search3

This highlights a mismatch with LLM retrieval trees built from summarisation: summary text is not generally an admissible bound on “maximum descendant relevance,” so pruning is heuristic, not guaranteed.

A partial bridge exists for cosine similarity: work has derived triangle-inequality-like tools for cosine distance/similarity, enabling metric-tree pruning techniques in cosine spaces under certain constructions. citeturn7search14  
But “summary fidelity” is still not a geometric bound; it is a learned, lossy compression.

### Alpha–beta and the role of monotonicity

**Alpha–beta pruning** is another example of elimination with *no loss of optimality*, but its guarantee relies on minimax structure and monotone bounds on achievable values within subtrees. Its efficiency improvements collapse if move ordering or bound tightness is poor. citeturn1search13turn1search5

Takeaway for retrieval-by-elimination: if your internal-node score is not monotone with respect to descendant relevance (i.e. high-level summaries can score low even when a deep leaf is relevant), then pruning has no theoretical safety net and will be recall-fragile.

### Sequential hypothesis testing: elimination is optimal when the score is a likelihood ratio

Top-down traversal can be modelled as sequentially testing hypotheses of the form:

- \(H_1\): “this subtree contains relevant evidence”
- \(H_0\): “it does not”

If each scored node yields observations with known (or well-estimated) distributions under \(H_0/H_1\), then **Sequential Probability Ratio Tests (SPRT)** provide stopping/continuation rules that (under classical assumptions) minimise the expected number of observations for given type-I/type-II error constraints. citeturn8search6turn8search26turn0search15

This gives a clean theoretical recipe for when elimination dominates flat search:

- You can interpret node scores as (approximately) log-likelihood ratio evidence about subtree relevance.
- You can set thresholds to aggressively reject negatives while keeping false negatives below a target.

In practical LLM retrieval, the missing piece is calibration: most relevance scores are not likelihood ratios, and score distributions shift by query type and by node abstraction level, which breaks the classical optimality premises even if SPRT is the right conceptual model. citeturn2search7turn2search11

### Cascades: the mathematics of compounding false negatives

Classifier cascades formalise the same compounding phenomenon elimination trees suffer from. Analyses of classical detection cascades describe per-stage targets in false positive/false negative rates and show the cascade embodies a Shannon-like resource allocation principle (spend more compute only on promising candidates). citeturn8search24turn8search1

The especially relevant fact is structural, not domain-specific:

- If a “positive” must survive *all* stages to be accepted, then the overall detection probability is (approximately) the product of per-stage detection probabilities, so small per-stage miss rates can become large end-to-end miss rates over many stages. citeturn8search24turn2search7

This directly transfers to elimination trees.

## Recall loss under pruning: simple bounds, what they imply, and why depth is dangerous

### A minimal formal model of elimination recall

Assume a tree of depth \(d\). Consider a single relevant leaf \(\ell\) with a unique ancestor path \(u_1\to u_2\to\cdots\to u_d=\ell\). Let \(A_k\) be the event “the traversal retains the correct child at level \(k\).” Then
\[
\Pr(\ell\ \text{retrieved}) = \Pr\Big(\bigcap_{k=1}^d A_k\Big).
\]

Without any independence assumptions, a conservative bound is the union bound on failure:
\[
\Pr(\ell\ \text{pruned}) \le \sum_{k=1}^d \Pr(\neg A_k).
\]
With per-level false-negative rates \(\epsilon_k=\Pr(\neg A_k)\), recall is at least \(1-\sum_k \epsilon_k\). This already shows the central fragility: deeper trees increase the number of opportunities to drop the only correct path. (This is the same core phenomenon discussed as “error propagation” in top-down hierarchical classification.) citeturn2search7turn2search11

If you *do* assume conditional independence and a uniform per-level miss rate \(\epsilon\), then
\[
\Pr(\ell\ \text{retrieved}) \approx (1-\epsilon)^d,
\]
which decays exponentially in depth. Cascade analyses use this multiplicative perspective when setting stage-wise detection targets to hit an overall miss-rate budget. citeturn8search24turn8search1

### Hierarchical classification theory matches the retrieval failure mode

The hierarchical classification literature is explicit that top-down approaches are efficient but can suffer poor accuracy because errors made high in the hierarchy cannot be corrected downstream; the effect worsens with hierarchy depth, motivating methods such as hierarchy “flattening.” citeturn2search7turn2search3turn2search11

This is not only qualitative. There are theoretical analyses giving data-dependent criteria and generalisation bounds for top-down hierarchical classification, and explicitly discussing when hierarchical vs flat approaches should be preferred given properties of the taxonomy and training distribution. citeturn2search19

For retrieval-by-elimination, the direct mapping is:

- Tree depth \(d\) ↔ number of irreversible routing decisions.
- Branching factor \(b\) ↔ number of classes at each decision.
- “Tree quality” ↔ separability of classes at each internal node; if classes are not separable under the available representation, a top-down policy must have a non-trivial error floor. citeturn1search10turn2search7

### The cluster hypothesis is necessary but not sufficient for safe elimination

The classic **cluster hypothesis** states that closely associated documents tend to be relevant to the same requests. This is the conceptual basis for hierarchical retrieval and cluster-based IR. citeturn11search9turn11search25

But multiple lines of evidence show two important limitations:

First, the cluster hypothesis may hold under specific tests yet cluster-based retrieval can still be less effective than document-based retrieval; a SIGIR Forum retrospective summarising early work reports cluster searches being less effective even when the hypothesis applies. citeturn11search21

Second, even when cluster-based methods can outperform document-based methods, effectiveness depends on corpus noise (e.g. spam) and on the nature of clustering (overlapping vs hard clusters); for large-scale web corpora, overlapping clusters can be more effective than hard clusters, suggesting that “single-path” hierarchies are brittle when items are naturally multi-topic. citeturn11search25

These limitations translate into precise conditions for elimination failure:

- **Cross-branch evidence**: if \(R(q)\) spans multiple semantically distant regions, any policy that commits to a small number of branches early is likely to miss part of the needed evidence, even if each region is internally well-clustered. citeturn11search9turn2search7  
- **Multi-topic leaves**: if leaves are inherently overlapping in topic space (a single chunk supports several intents), enforcing a strict partition makes the “correct branch” ill-defined; overlapping clusters empirically help, implying the tree should not be treated as a single routing path. citeturn11search25turn6view0

### Geometry matters: when tree structures help, and when they collapse

Nearest-neighbour theory shows hierarchical indexing is powerful when the data has favourable intrinsic structure (bounded expansion/doubling properties), as exploited by cover trees; with such properties, theoretical guarantees on construction and query complexity follow. citeturn7search0turn7search16

Conversely, classic treatments of the curse of dimensionality show that space-partitioning trees can fail in high dimensions, visiting many branches and approaching linear scan behaviour. citeturn1search3turn1search11

For elimination-based semantic routing, the analogous “geometry” is not only embedding dimension but *topic separability under the node representations you actually route on* (often summaries). If top-level summaries are too coarse, they behave like lossy quantisers with large distortion; misrouting becomes unavoidable and compounds with depth. citeturn3search6turn6view0

## Explaining RAPTOR’s collapsed-tree advantage and characterising when strict traversal could win

### RAPTOR’s own explanation is a granularity-allocation argument

RAPTOR defines two query strategies: tree traversal vs collapsed tree. It reports that collapsed tree performs better on their tested QASPER subset and attributes this to flexibility: searching all nodes simultaneously retrieves information at the “correct level of granularity” for a question. By contrast, traversal with fixed \(d\) and \(k\) enforces a constant ratio of abstract-to-granular nodes regardless of the question. citeturn6view0turn6view1

That explanation is consistent with a decision-theoretic framing: optimal allocation of a token budget across abstraction levels should depend on query type; fixed-per-level allocations are a rigid policy class. citeturn3search6turn8search23

### A deeper theoretical explanation: collapsed tree removes compounding decision risk

Collapsed-tree retrieval eliminates the need to correctly solve a sequence of multi-class routing problems. It converts “many dependent routing decisions” into a single global ranking problem over an expanded candidate set.

In hierarchical classification terms, it is a form of “flattening,” which is explicitly motivated in the literature as a remedy for error propagation in deep hierarchies. citeturn2search7turn2search19

So a clean theoretical characterisation of when collapsed tree beats strict traversal is:

- **When routing error is non-negligible at one or more upper levels** (low mutual information between query and child choice at that level), traversal has an irreducible recall penalty that compounds, whereas collapsed retrieval can still recover by directly matching to a deeper node that contains the distinguishing signal. citeturn1search10turn6view0turn2search7  
- **When relevant evidence is multi-region or multi-hop**, collapsed retrieval can return multiple nodes scattered across the tree, while strict traversal tends to prematurely concentrate budget under a small number of branches. citeturn11search25turn6view0  
- **When optimal token allocation across abstraction levels is query-dependent**, collapsed retrieval can implicitly adapt by returning whichever levels score well, while fixed-depth traversal forces a predetermined abstraction mix. citeturn6view0turn6view1turn3search6

This is not speculative; RAPTOR’s write-up explicitly highlights granularity flexibility as the driver and shows empirical dominance of collapsed retrieval under their tested settings. citeturn6view0turn6view1

### When strict elimination traversal can theoretically outperform enriched flat retrieval

For strict traversal to beat *enriched flat* retrieval (collapsed tree), it needs to offer something collapsed retrieval cannot: **guaranteed or highly reliable exclusion** that lets you spend substantially more scoring budget per surviving candidate, *without sacrificing recall*. The literature points to three conditions that can make this true.

**Bounded-loss pruning (admissible or near-admissible bounds).** If internal-node representations permit reliable upper bounds on descendant relevance/similarity (as in metric-tree branch-and-bound), you can prune vast regions safely and reallocate compute to deeper reranking. This is a regime where elimination’s asymptotic advantage is real. citeturn7search3turn7search6turn1search0  
In LLM retrieval trees built from summaries, “admissible bounds” are usually not available; but if you redesign internal nodes around geometric regions (balls/radii) rather than narrative summaries, bounded-loss pruning becomes more plausible. citeturn7search6turn7search14

**Extremely strong cluster alignment (“single-subtree relevance”).** If for most queries \(q\), almost all of \(R(q)\) lies within one (or a very small number) of subtrees, then routing is easy and early elimination preserves recall. This is essentially the strongest form of the cluster hypothesis; it is stronger than “relevant docs are similar,” because it requires relevance to be *partition-aligned* with your chosen tree. citeturn11search9turn11search21turn1search10

**Calibrated sequential decision rules.** If subtree scores can be calibrated so that rejecting a subtree corresponds to a controlled false-negative probability (sequential testing view), you can tune elimination to keep recall loss bounded while saving work on easy negatives. This is the theoretical niche where SPRT-style reasoning applies. citeturn8search6turn0search15turn8search26

Absent these conditions, strict traversal is structurally disadvantaged versus collapsed retrieval because it pays the compounding-error tax described earlier, while collapsed retrieval does not. citeturn2search7turn6view0

## Implications for HCR design and hybrid strategies under tight token budgets

### Token budgets change the objective: “recall” is not the only currency

With a hard context cap (e.g. 400 tokens), the goal is no longer “retrieve all possibly relevant evidence,” but “maximise expected answer utility per token.” This aligns almost exactly with the Information Bottleneck framing: compress aggressively while preserving information about the answer-relevant variable. citeturn3search6turn3search22

RAPTOR operationalises this by selecting nodes until a token limit is hit; it reports using collapsed tree with a 2000-token cap in general, and explicitly notes experiments where the downstream model (UnifiedQA) is given 400 tokens of context due to its short maximum context length. citeturn6view1  
So the “400-token regime” you care about is not hypothetical; it is a tested operating point in adjacent prior art. citeturn6view1

Under tight budgets, strict elimination can help only if it increases the **density of useful information** in the final context. The failure mode is brutal: one misroute and the returned 400 tokens are concentrated in the wrong region, yielding near-zero utility. That is why the theoretical emphasis shifts to *risk control* (bounding false negatives) rather than aggressive pruning. citeturn2search7turn8search24

### Hybrid strategies have firm theoretical grounding and mirror ANN best practice

A robust theoretical compromise is:

1. Use the hierarchy for coarse filtering to identify a *candidate set* of subtrees (do not commit to one path).
2. Do flat similarity search (or reranking) within the union of candidate subtrees and across multiple abstraction levels.

This is isomorphic to IVF-style vector search: coarse quantiser → probe multiple lists → fine search; recall rises with the number of probed lists (beam width / \(n_\text{probe}\)). citeturn3search5turn3search24turn2search20

In decision-theoretic terms, this is also how cascades are designed when false negatives are expensive: early stages are tuned for very high detection (low miss rate), and later stages do the heavy discrimination. citeturn8search24turn8search1

### A precise design implication for elimination: optimise for *low false negatives* at upper levels

If elimination is used, the theoretical priority at early tree levels is to keep \(\epsilon_k\) extremely small, because of compounding. This is exactly the cascade principle: each layer has explicit targets for false negatives/positives; you do not tune each layer for “best local accuracy,” you tune it for global operating characteristics. citeturn8search24turn1search4

In practice this pushes HCR away from “hard pruning” and toward:

- parallel/beam traversal (probe multiple branches),
- uncertainty-aware continuation rules (sequential testing lens),
- and fallback to collapsed multi-level similarity when routing confidence is low.

These are not implementation details here; they are the logical consequences of the compounding-error bounds and of the known error-propagation phenomenon in deep hierarchies. citeturn2search7turn8search6turn6view0

### Summary of theoretically grounded win conditions

Elimination-based top-down traversal can outperform flat similarity retrieval (and even enriched flat retrieval) when *all* of the following hold to a meaningful degree:

- **Partition-aligned relevance:** most queries have relevant evidence contained within few subtrees (strong, partition-specific form of the cluster hypothesis). citeturn11search9turn11search25  
- **High-information routing:** internal representations preserve enough mutual information to discriminate the correct child at each level (otherwise Fano-type bounds imply unavoidable error). citeturn1search10turn3search6  
- **Bounded-loss or calibrated pruning:** pruning decisions either have admissible bounds (metric-tree style) or are calibrated to control miss probability (sequential testing / cascade style). citeturn7search3turn8search6turn8search24  
- **Depth is modest or beam is wide enough:** because recall decays with depth under even small per-level miss rates (error propagation). citeturn2search7turn8search24

When these don’t hold—especially with cross-branch queries, weakly informative top summaries, or deep trees—collapsed enriched flat retrieval is predicted to win because it avoids compounding routing errors and can adapt its abstraction level per query, exactly matching RAPTOR’s reported behaviour. citeturn6view0turn6view1turn2search7
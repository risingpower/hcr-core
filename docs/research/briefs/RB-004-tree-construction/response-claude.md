# RB-004: Tree Construction — Claude Response

**Date:** 2026-02-13
**Model:** Claude
**Prompt:** [RB-004 Prompt](./prompt.md)

---

*Paste response below this line.*
# Tree construction for hierarchical context retrieval: a comprehensive analysis

**The most critical finding across all eight areas is that no single construction method solves the fundamental tension between routing efficiency and cross-branch coverage.** RAPTOR's bottom-up GMM clustering with LLM summarization delivers the strongest proven retrieval gains (+20% on QuALITY), but its soft-clustering mechanism is limited in practice. LATTICE's LLM-guided traversal achieves state-of-the-art zero-shot retrieval (+9% Recall@100 on BRIGHT), demonstrating that routing quality depends as much on traversal strategy as tree structure. The cross-branch failure mode remains unsolved by any single system—the emerging best practice combines proposition-based decomposition, soft clustering, knowledge-graph overlays, and multi-path retrieval. For tree quality evaluation, no routing-specific metric exists in the literature; this is a genuine research gap. Federated search's resource selection algorithms (CORI, ReDDE) provide the best conceptual framework for HCR's external-pointer architecture.

---

## 1. Ten construction methods compared on five axes

The landscape spans four paradigms: bottom-up agglomerative, top-down divisive, graph-based community detection, and topic modeling. Each makes fundamentally different assumptions about what makes documents "related."

**RAPTOR** (Sarthi et al., ICLR 2024) embeds chunks with SBERT, reduces dimensionality via UMAP, then applies Gaussian Mixture Models with BIC-selected cluster counts. GMM's soft assignments allow chunks to belong to multiple clusters—the only mainstream system with native multi-membership. An LLM (GPT-3.5-turbo) generates abstractive summaries per cluster, then the process recurses upward. The tree is **unbalanced with variable depth**, average cluster size ~6.7, and **72% compression per level** (summaries are 28% the length of concatenated children). On QuALITY, RAPTOR + GPT-4 achieved a **20% absolute accuracy improvement** over prior methods. On QASPER, it reached **55.7% F1**, beating DPR by 2.7 points. Crucially, RAPTOR's ablation showed that clustering-based trees significantly outperform contiguous-window trees (the LlamaIndex TreeIndex approach). Computational cost scales linearly with corpus size; the bottleneck is LLM summarization calls (~N/6.7 calls per tree level). For 10K chunks, expect ~1,750 calls; for 100K, ~17,500.

**GraphRAG** (Edge et al., Microsoft Research, 2024) partitions on entity-relationship graph structure rather than embedding similarity. An LLM extracts entities and relationships from every chunk, constructs a knowledge graph, then applies the **Leiden algorithm** for hierarchical community detection. Each community gets an LLM-generated summary. This produces a multi-level hierarchy (typically 3–5 levels) with variable branching driven by graph connectivity. On podcast transcripts and news articles, community summaries achieved **70–80% win rate** over naive RAG on comprehensiveness. The cost is steep: graph extraction constitutes ~75% of total indexing cost, and GraphRAG is **10–50× more expensive** than RAPTOR-style approaches. For the Wizard of Oz corpus (~40K words), costs ranged from $0.34 (GPT-4o-mini) to $5.35 (GPT-4-Turbo). A critical limitation: Leiden assigns each entity to exactly one community per level—despite operating on a graph, the community structure itself is a hard partition.

**LATTICE** (Gupta et al., 2025) offers both bottom-up agglomerative and top-down LLM-driven divisive construction, with branching factor M ≈ 10–20. Its key innovation is using an **LLM as an active traversal agent** rather than relying on embedding similarity for routing. On the BRIGHT benchmark (12 reasoning-intensive tasks, corpora up to 420K documents), LATTICE achieved **74.8% average Recall@100** (vs. BM25's 65.3% and fine-tuned ReasonIR-8B's 70.8%) and **51.57 nDCG@10**, comparable to fine-tuned SOTA. This is the strongest evidence that LLM-guided routing through hierarchical summaries substantially outperforms embedding-only routing.

**Bisecting k-means** (Steinbach, Karypis, Kumar, 2000; Zhao & Karypis, 2005) recursively bisects the largest cluster using 2-means. It produces balanced binary trees with hard assignment. Karypis et al.'s comprehensive study on 12 datasets found that "partitional algorithms always lead to better solutions than agglomerative algorithms" for document clustering quality, while being dramatically faster. Computational cost is O(n·d·k·I) per split—**minutes for 100K chunks** with embeddings. The major limitation for HCR: binary branching produces deep trees (depth ~17 for 100K items), violating the d=2–3 constraint. Adapting to k-way splits (bisecting into 8–12 children) is straightforward but less studied.

**BERTopic** (Grootendorst, 2022) uses sentence-transformer embeddings → UMAP → HDBSCAN density-based clustering → c-TF-IDF topic representations. Hierarchy is constructed post-hoc via agglomerative ward linkage over the discovered topic c-TF-IDF matrix. It produces a binary dendrogram over topics (not documents), cuttable at any level. Cost is low (no LLM calls), but HDBSCAN assigns each document to exactly one cluster (or the outlier class, a known issue). Not evaluated for retrieval routing—primarily an exploratory topic modeling tool.

**ArchRAG** (Wang et al., 2025) improves on GraphRAG with iterative KNN graph augmentation → weighted Leiden clustering → community summarization, building a C-HNSW hierarchical index. Results: **10% higher accuracy** than GraphRAG on specific questions with **250× fewer tokens** consumed. This represents the current best-in-class for graph-based hierarchical construction efficiency.

**PECOS/Bonsai** from the extreme multi-label classification (XMC) literature (Yu et al., 2022; Khandagale et al., 2020) provides strong topology evidence: Bonsai uses **shallow trees with branching factor K=100 and depth 1–2**, outperforming Parabel's balanced binary trees (depth ~17 for 500K labels). This directly supports HCR's shallow-wide design.

Three other methods are worth noting briefly. **hLDA** (Blei et al., NeurIPS 2004) uses the nested Chinese Restaurant Process for nonparametric tree-structured topic hierarchies—theoretically elegant but computationally expensive (MCMC, hours to days) and unsuitable for retrieval routing. **Spectral clustering** requires O(n³) eigendecomposition or expensive approximations; ArchRAG's evaluation showed weighted Leiden outperformed spectral methods for RAG. **LlamaIndex TreeIndex** groups contiguous chunks (no semantic clustering) and produces balanced trees; RAPTOR's ablation definitively showed this underperforms semantic clustering.

| Method | Signal | Multi-topic | Shape | Cost (100K chunks) | Best reported metric |
|--------|--------|-------------|-------|-------------------|---------------------|
| RAPTOR | Embedding + GMM | Soft (GMM) | Unbalanced, variable depth | ~$20–50 (GPT-4o-mini) | +20% QuALITY accuracy |
| GraphRAG | Entity graph + Leiden | Via graph edges | 3–5 level hierarchy | ~$150–250 (GPT-4o-mini) | 70–80% comprehensiveness win |
| LATTICE | Embedding + LLM routing | Hard | M=10–20, log depth | High (LLM construction + routing) | 74.8% Recall@100 BRIGHT |
| ArchRAG | Graph + KNN + Leiden | Attributed communities | C-HNSW hierarchy | Lower than GraphRAG | +10% vs GraphRAG, 250× fewer tokens |
| Bisecting k-means | TF-IDF / embedding | Hard | Balanced binary | Minutes (no LLM) | Strong on cluster quality (Karypis 2005) |
| BERTopic | Embedding + HDBSCAN | Hard + outliers | Dendrogram over topics | Low (no LLM) | Topic coherence only |
| Bonsai (XMC) | TF-IDF label features | Hard | K=100, depth 1–2 | Low–moderate | SOTA on XMC benchmarks |

---

## 2. Routing-quality summaries differ fundamentally from reading summaries

The distinction between summaries optimized for *routing* (answering "does my answer lie below this node?") versus *comprehension* (understanding a topic) is underexplored in the literature. No published system explicitly optimizes summaries for routing accuracy. However, converging evidence from several research streams points toward specific design principles.

**Contrastive summarization**—generating summaries that state "this branch covers X, NOT Y"—is theoretically well-motivated but **empirically unproven for HCR routing**. The contrastive/comparative summarization literature (Ren et al., SIGIR 2015; Wang et al., ACM TKDD 2013; STRUM, Gunel et al., 2023) establishes techniques for highlighting differences between document sets. Contrastive learning for dense retrievers achieves strong results (Izacard et al. showed unsupervised contrastive learning outperforms BM25 on 11/15 BEIR datasets for Recall@100). The principle is sound—**siblings should maximally differentiate**—but no one has directly tested contrastive summary generation for tree routing. This is a high-value research gap.

**Entity and identifier preservation ("detail hooks")** has strong supporting evidence. GraphRAG research explicitly identifies that "entity types like IDs, dates, and numbers have poor semantic embeddings." Berezin et al. (2023) demonstrated that standard abstractive summarizers **systematically omit named entities**, proposing custom pretraining to improve entity inclusion. RAPTOR's 72% compression rate (average summary: 131 tokens) aggressively compresses, risking loss of rare entities that detail-oriented queries target. For routing summaries, explicitly instructing LLMs to preserve rare entities, identifiers, and specific numbers is strongly recommended.

**Structured formats** (entities + keywords + narrative) show moderate evidence of advantage over pure prose. GraphiT research (2025) found that **keyphrases of neighbor nodes outperform full summaries** for node classification while requiring significantly fewer tokens. Shamsabadi & D'Souza (2024) argued that structured records improve IR effectiveness over keyword-based approaches. For routing, a hybrid format maximizes discriminative signal density: entity lists prevent omission, keywords align with BM25 scoring, and brief narrative captures semantic relationships.

**Summary length** has a sweet spot that hasn't been systematically mapped. RAPTOR's ~131-token summaries work empirically. GraphRAG's highest-level community summaries used ~2–3% of token cost per query while remaining competitive with exhaustive summarization. ColBERT token-pooling research shows that reducing vectors by 50% causes "virtually no retrieval performance degradation." The implication: moderate compression preserves routing-relevant information, but excessive compression loses detail hooks.

**ColBERT-style multi-vector representations** at the summary level are a **high-confidence recommendation**. ColBERT generates per-token embeddings and computes similarity via MaxSim, meaning each rare entity in a summary gets its own vector rather than being averaged away in a single embedding. MUVERA (NeurIPS 2024) converts multi-vector representations to fixed-dimensional encodings achieving 95% recall with dramatically reduced storage. Token pooling reduces ColBERT indexes by 50–75% with <5% degradation. For HCR, where detail queries against thematic summaries are the structural failure case, multi-vector representations directly address this by preserving token-level discriminative signals.

---

## 3. Cross-branch content remains the hardest unsolved problem

No existing system convincingly solves the cross-branch failure mode. The emerging best practice is a **layered defense combining multiple techniques**:

**Proposition-based decomposition** (inspired by Chen et al., "Dense X Retrieval," 2023) splits documents into atomic, self-contained factual statements before clustering. PropRAG (EMNLP 2025) demonstrated that propositions preserve significantly more context than triples, achieving **94% Recall@5 on HotpotQA** vs. 86.8% for HippoRAG 2. By creating single-topic atomic chunks, clustering produces cleaner partitions with fewer multi-topic items. The cost: multiple LLM calls per document, and quality degrades significantly with weaker LLMs.

**Soft clustering** via RAPTOR's GMM allows chunks to appear under multiple parents. However, a Stanford CS224N analysis found that in practice, RAPTOR's GMM implementation often produces **flat tree structures with minimal actual soft clustering** for standard document sizes. A Frontiers in Computer Science (2025) evaluation showed GMM achieves 55.17% accuracy as a baseline, while adaptive graph clustering with semantic chunking performed best—suggesting both better inputs and better structure are needed together. The GMM's Gaussian assumption is a poor fit for text embedding distributions.

**Graph-augmented structures** offer the strongest cross-branch connectivity. GraphRAG's entity graph naturally links content across communities via shared entities. **TagRAG** (2025) introduces hierarchical domain tag chains, achieving 78.36% win rate against baselines while being 14.6× cheaper to construct and 1.9× faster to retrieve than GraphRAG. KG2RAG (NAACL 2025) uses knowledge-graph-guided context organization, improving over both naive RAG and GraphRAG on HotpotQA. The trade-off: graph construction is expensive and introduces an auxiliary data structure beyond the tree.

**Query-time multi-path expansion** via beam search is well-studied. Zhuo et al. (ICML 2020) identified a critical "training-testing discrepancy"—tree models trained with node-wise scores but tested with beam search produce suboptimal results. They proposed training models to be "Bayes optimal under beam search." PropRAG found **beam width B=4** to be optimal, with diminishing returns beyond that. For HCR's shallow trees (depth 2–3), beam search with width 3–5 is computationally practical and significantly reduces miss rates. The latency cost is multiplicative: evaluating k × branching_factor candidates per level instead of branching_factor.

**Redundant leaf placement** (placing the same leaf in multiple branches) is the simplest approach but the least studied. Storage scales linearly with average membership count. When underlying content changes, all copies and summaries must be updated. No rigorous empirical study quantifies the storage-quality tradeoff for this approach.

The pragmatic recommendation for HCR: (1) decompose multi-topic documents into propositions before clustering; (2) use soft or overlapping clustering so multi-topic chunks appear in multiple branches; (3) maintain a lightweight entity index as a cross-branch link structure; (4) use beam search (width 3–5) at query time rather than greedy top-down routing; (5) implement collapsed-tree retrieval as a fallback for queries that don't match any branch well (RAPTOR showed this consistently outperforms traversal).

---

## 4. Shallow wide trees win, and the single-parent constraint should be relaxed

Within the d=2–3, b=8–12 design space, evidence converges on several topology principles.

**Allow moderate imbalance.** Karypis et al. (2005) found partitional methods (balanced) outperform agglomerative methods (unbalanced) for cluster quality. But RAPTOR's ablation showed content-driven clustering outperforms forced-balanced contiguous grouping. **Bonsai** (XMC literature) explicitly allows unbalanced trees and finds improved accuracy over Parabel's strict balance. The synthesis: let data drive cluster sizes with soft constraints to prevent degenerate branches (minimum 3 leaves, maximum 3× median branch size).

**Use variable branching within a range.** Natural topic structure means some domains subdivide more than others. LATTICE uses M ≈ 10–20 with actual branching varying per node. Fixed branching forces artificial splits in some branches and artificial merges in others. For HCR, allow b ∈ [6, 15] per node while targeting an average of ~10.

**Shallow beats deep.** Bonsai's result—K=100, depth 1–2 outperforming binary trees of depth ~17—is the strongest empirical evidence. For 10K–100K items with b ≈ 10: depth 2 covers 100 leaves (too few), depth 3 covers 1,000 leaves (borderline), depth 4 covers 10,000 leaves. At 100K chunks, you need either depth 5 (10⁵) or a two-level structure where level 1 has ~10 nodes each routing to ~100 mid-level nodes pointing to ~100 leaves each. **The error compounding formula (1−ε)^d makes every additional level expensive**: at ε=0.02, three levels yield 94.1% accuracy vs. 96.0% at two levels. This 2-point gap may matter at scale.

**Relax the single-parent constraint toward a DAG.** Overlapping Hierarchical Clustering (OHC, 2020) proposes quasi-dendrograms as DAGs, allowing clusters to overlap until strong attraction is reached. The Pachinko Allocation Model represents topic hierarchies as DAGs rather than trees, enabling shared sub-topics. RAPTOR's soft clustering effectively creates a DAG within a tree frame. For HCR, **allowing leaves to have 1–3 parents** captures cross-topic content without exploding storage. The routing implication: a query may reach the same leaf via multiple paths, requiring deduplication but improving recall.

No information-theoretic work directly addresses optimal branching factor for semantic routing. From decision-tree theory, each routing step provides log₂(b) bits of information. At b=10, each step provides ~3.3 bits. Two levels provide ~6.6 bits, distinguishing ~100 leaf groups. Three levels provide ~10 bits, distinguishing ~1,000 groups. The question is whether a scorer can reliably make 10-way distinctions—HCR's cascade scorer (BM25+dense → cross-encoder) at ε ≈ 0.01–0.02 per level suggests it can.

---

## 5. Dynamic maintenance requires GRINCH-style operations and staleness tracking

Full reconstruction is the quality gold standard but impractical for production. The literature offers a spectrum of incremental approaches.

**GRINCH** (Monath et al., KDD 2019) is the most relevant algorithm for HCR. It supports incremental hierarchical clustering via two operations: **rotate** (local rearrangement of parent-child-sibling relationships) and **graft** (global rearrangement that moves entire subtrees). Under consistent linkage functions, GRINCH produces cluster trees containing ground-truth independent of data arrival order—a strong theoretical guarantee. It is orders of magnitude faster than batch hierarchical agglomerative clustering while being more accurate than other scalable methods. Its predecessor **PERCH** (Kobren et al., KDD 2017) proved that under separability assumptions, tree rotations achieve perfect dendrogram purity regardless of arrival order.

**BIRCH** (Zhang et al., 1996) maintains Clustering Feature trees with summary statistics (N, linear sum, squared sum) enabling O(1) incremental updates per node. It processes data points with minimal I/O but is sensitive to insertion order and may require a periodic global clustering pass. For HCR, BIRCH's CF-tree concept—maintaining summary statistics at each node that enable cheap updates—is directly applicable even if the full BIRCH algorithm isn't used.

**Split/merge heuristics** for HCR should follow: split when a branch exceeds 2× target size OR intra-cluster cosine similarity drops below a threshold; merge when inter-cluster similarity between siblings exceeds a threshold OR a branch shrinks below minimum viable size. The Election Tree algorithm (Pattern Recognition, 2023) achieves better accuracy than PERCH and GRINCH with lower time consumption using node election for representative detection and merge-swap operations.

**Summary staleness** is the HCR-specific maintenance challenge. When leaf content changes, all ancestor summaries become potentially stale. The recommended approach: mark ancestor summaries "dirty" on leaf changes, then choose between lazy regeneration (regenerate only when accessed during routing AND dirty) or eager regeneration (background schedule prioritizing frequently-accessed nodes). GraphRAG's planned approach tracks which communities' memberships have changed and only re-summarizes those. An intermediate strategy—appending "delta summaries" noting what changed, with periodic full consolidation—balances freshness against LLM cost.

**Reconstruction triggers** should combine multiple signals: (1) branch size exceeding configurable bounds; (2) intra-cluster average similarity dropping below threshold; (3) routing accuracy on held-out queries declining; (4) number of insertions since last reconstruction exceeding 20–30% of subtree size; (5) summary age exceeding a freshness threshold. No empirical study quantifies degradation rates for RAG hierarchical trees specifically—this is an important gap. The pragmatic approach: schedule periodic full reconstructions (weekly or monthly) while using incremental GRINCH-style updates between rebuilds.

---

## 6. LLMs provide the highest value in summarization, less in partitioning

Across the construction pipeline, LLM involvement follows a clear value gradient.

**Summarization is the highest-value use**, with proven results. RAPTOR's LLM-generated summaries produced a 20% accuracy improvement on QuALITY. LATTICE demonstrated that LLM-guided traversal through hierarchical summaries outperforms embedding-only routing by 9+ points on Recall@100. The cost at scale: for RAPTOR-style construction, ~1,750 LLM calls for 10K chunks (~$2–5 with GPT-4o-mini) and ~17,500 calls for 100K chunks (~$20–50). This is affordable and scales linearly.

**Entity/relationship extraction** is critical for graph-based approaches but expensive. GraphRAG's extraction constitutes ~75% of indexing cost. At 100K chunks, costs reach $150–250 with GPT-4o-mini or $1,500–2,500 with GPT-4-Turbo. **FastGraphRAG** uses NLP libraries (spaCy/NLTK) instead of LLMs for entity extraction, reducing costs by ~75% while maintaining reasonable quality. For HCR, a hybrid approach—NLP-based entity extraction supplemented by LLM calls for ambiguous cases—optimizes the cost-quality tradeoff. GraphRAG's finding that ~65% of answer entities appear in constructed knowledge graphs (35% loss) sets expectations for extraction coverage.

**Semantic partitioning decisions** show minimal LLM value-add. The Stanford CS224N RAPTOR extension found that agglomerative clustering makes "the clustering component of tree construction computationally negligible," and embedding-based clustering performs well without LLM guidance. LATTICE's top-down divisive mode uses LLMs for splitting decisions, but the bottom-up embedding mode achieves comparable results for most corpus types. Partitioning can be safely left to embedding-based methods.

**Contrastive summary refinement** and **quality validation** are promising but unproven. No published system uses LLMs to iteratively refine summaries for sibling distinctiveness. GraphRAG uses GPT-4o-mini as a "rater" for dynamic community selection, achieving **77% cost reduction** with equivalent quality—demonstrating that classification tasks ("is this community relevant?") are "considerably easier than summarization" and can use cheap models. This suggests an LLM validation pass (is this summary discriminative? does it cover the key entities?) would be low-cost and potentially high-value.

---

## 7. Tree quality evaluation is a genuine research gap

**Standard cluster metrics are confirmed poor predictors of retrieval quality.** The Stanford IR textbook (Manning, Raghavan, Schütze, 2008) explicitly states that "good scores on an internal criterion do not necessarily translate into good effectiveness in an application." Fuhr et al. (2012, Information Retrieval Journal) note that "evaluations of the cluster hypothesis gave inconclusive results" and that "the (pre-)existence of a universally meaningful clustering cannot be expected."

**The Voorhees cluster hypothesis** (1985, SIGIR) and subsequent work establish three classical tests: the overlap test, the nearest neighbor test (NNT), and the density test. El-Hamdouchi & Willett (1989) found these tests **are not in complete agreement** and that the density test gives the most useful results—it is **most correlated with actual cluster-based retrieval improvement**. Hearst & Pedersen (1996) provided partial validation for search result clustering. The key implication for HCR: the cluster hypothesis holds for narrow domains (8% failure, per your RB-002) but fails for broad collections (46% failure), meaning tree quality evaluation must be domain-aware.

**No routing-specific tree quality metric exists in the literature.** The closest analog is **selective search's Rn recall metric** (Si & Callan, 2003; Kulkarni & Callan, 2010–2015), which measures what fraction of relevant documents are contained in the top-n selected shards. This is directly analogous to per-level routing accuracy. For HCR, the natural metric would be: at each tree level l, given query q with known relevant leaves L(q), routing accuracy = |correctly_routed(l)| / |L(q)|.

A principled tree quality framework for HCR should combine four components:

- **Per-level routing accuracy** on held-out queries with known relevant leaves (analogous to Rn). This requires ground-truth relevance judgments but is the most direct measure.
- **Sibling distinctiveness**: pairwise cosine distance between sibling summary embeddings, or better, vocabulary divergence. Low distinctiveness means the scorer cannot reliably differentiate siblings, structurally capping routing performance regardless of scorer quality.
- **Summary-to-descendant coverage**: embedding similarity between a node's summary and each descendant's content, or BERTScore between the summary and concatenated descendant content. Low coverage means the summary is a poor proxy for what lies below.
- **Cross-branch query detection**: fraction of multi-branch queries where the system identifies the need for content from multiple branches. This requires labeled multi-branch queries and is the hardest to obtain.

The **Optimum Clustering Framework** (Fuhr et al., 2012) proposes the most theoretically principled approach: define document similarity based on relevance to the same queries, then evaluate clusters against this query-based similarity. This requires a representative query set with relevance judgments but avoids the disconnect between geometric cluster metrics and retrieval effectiveness.

---

## 8. External source pointers map directly to federated search

HCR's architecture—leaves as pointers to external sources with summaries for routing—is precisely the **collection selection problem** from federated/distributed information retrieval, studied extensively since the 1990s.

**CORI** (Callan et al., 1995) is the most robust resource selection algorithm for HCR's use case. It treats each collection's resource description as a document and uses adapted retrieval techniques for ranking. Critically, CORI is **robust to incomplete representation sets**—performance remains almost unchanged even with sampled documents, unlike GlOSS and CVV which degrade dramatically with partial information. This directly addresses HCR's constraint that some sources may not be fully available at construction time.

**ReDDE** (Si & Callan, 2003) explicitly estimates the distribution of relevant documents across databases, then ranks by estimated count. It uses a centralized sample index (CSI) of sampled documents from all sources. ReDDE is more effective than CORI for environments with a wide range of database sizes, relevant if HCR's external sources vary significantly in scope.

**Query-Based Sampling** (Callan & Connell, 2001) is the primary technique for building resource descriptions when full content access is unavailable. It sends probe queries to external sources, downloads returned documents, and iteratively builds a representation. **300–500 sampled documents** are sufficient for effective resource selection with CORI. Adaptive stopping criteria (Caverlee et al., 2006) using proportion-distinct and proportion-of-vocabulary metrics improve sample quality. For HCR, this means summaries can be constructed from partial samples rather than requiring complete source access.

**Content drift detection** draws from both federated search and ML concept-drift literature. Shokouhi & Si (2011, Foundations and Trends in IR) found that federated search representations needed updates only every three months in stable environments. For dynamic environments, embedding-space drift detection methods (Evidently AI) monitor cosine distance between reference and current embedding distributions. The Maximum Concept Discrepancy method (Wang et al., 2024) handles high-dimensional distribution shifts. For HCR, periodic re-sampling of external sources combined with embedding drift monitoring would trigger summary regeneration when distributions shift beyond a threshold.

**Selective search** (Kulkarni & Callan, 2010–2015) provides the most direct modern analog to HCR: it partitions a corpus into 50–1,000 topical shards using sampled k-means, then uses resource selection (Rank-S, Taily, CORI) to select 3–5 shards per query. Effectiveness is "on par with exhaustive search" at substantially lower cost. Hendriksen et al. (ECIR 2025) demonstrated selective search as a first-stage retriever in multi-stage pipelines—essentially using topical shard selection as the first routing step, exactly analogous to HCR's tree traversal.

For HCR construction with external pointers, the recommended approach is: (1) use query-based sampling to build initial source representations from 300–500 sampled documents per source; (2) generate LLM summaries from these samples, following CORI-style term statistics plus semantic summaries; (3) construct the tree hierarchy using these representations; (4) monitor for content drift via periodic re-sampling and embedding distribution comparison; (5) regenerate summaries and potentially restructure branches when drift exceeds thresholds. The federated search literature's key lesson is that **imperfect representations work surprisingly well for routing**—CORI's robustness to incomplete samples means HCR need not require exhaustive source access.

---

## Conclusion: what the evidence recommends and where the frontier lies

The evidence points toward a specific construction strategy for HCR: **proposition-based decomposition of source content, followed by embedding-based soft clustering (GMM or graph-community detection), with LLM-generated structured summaries (entities + keywords + narrative) at each internal node, and ColBERT-style multi-vector representations for scoring**. Allow variable branching (b ∈ [6, 15]), moderate imbalance, and 1–3 parent memberships per leaf. Use GRINCH-style incremental maintenance between periodic full rebuilds. Evaluate using per-level routing accuracy on held-out queries (the Rn metric from selective search) and sibling distinctiveness scores.

Three genuine research gaps stand out. First, **contrastive summary generation for routing**—no system has tested whether "this branch covers X, NOT Y" summaries improve routing accuracy, but the theoretical motivation is strong. Second, **routing-specific tree quality metrics**—the disconnect between cluster metrics and retrieval quality is well-documented, but no replacement metric has been proposed. The Optimum Clustering Framework offers a principled direction. Third, **incremental maintenance quality degradation curves**—no empirical study quantifies how tree quality degrades with incremental insertion in RAG-specific systems, leaving practitioners to guess at reconstruction schedules.

The deepest insight from this analysis: **tree construction and traversal strategy are not independent**. RAPTOR's collapsed-tree retrieval (bypassing the hierarchy to evaluate all nodes simultaneously) consistently outperforms tree traversal, suggesting that the tree's value may lie more in organizing summarization than in providing a routing structure. LATTICE's LLM-guided traversal substantially outperforms embedding-based traversal on the same tree. The implication for HCR is that investing in summary quality and traversal strategy may yield higher returns than optimizing tree topology—which aligns with the prior finding that summary quality is the #1 upstream factor for scoring accuracy.
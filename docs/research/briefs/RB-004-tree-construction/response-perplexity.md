# RB-004: Tree Construction — Perplexity Response

**Date:** 2026-02-13
**Model:** Perplexity
**Prompt:** [RB-004 Prompt](./prompt.md)

---

<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# \# RB-004: Tree Construction for Hierarchical Retrieval

**Date:** 2026-02-13
**Status:** Open
**Decision Required:** Yes — tree construction strategy is a core architectural decision
**Related:** H1a (token efficiency), H1b (hybrid superiority), H1c (scoring lever), RB-001 (prior art), RB-002 (theoretical basis), RB-003 (scoring mechanics)

## Context

RB-003 established that **summary quality is the \#1 upstream factor** for scoring accuracy in hierarchical retrieval. The cascade scoring architecture (hybrid BM25+dense → cross-encoder rerank) can achieve per-level error rates ε ≈ 0.01–0.02, but only if node summaries clearly differentiate sibling branches and preserve "detail hooks" — rare identifiers, specific terms, and structural markers that enable routing decisions.

This makes tree construction the critical enabler for everything downstream. A poorly constructed tree — with overlapping siblings, vague summaries, or unnatural partitions — structurally caps scoring accuracy regardless of how sophisticated the scorer is. Conversely, a well-constructed tree with clearly differentiated branches makes even simple scoring methods effective.

Previous briefs established:

- **RB-001:** Tree construction is "brittle and dataset-dependent" — clustering algorithm choice dramatically affects performance. No principled method exists for automatically selecting clustering algorithms and parameters. All sources flagged this as an open problem.
- **RB-002:** Shallow wide trees (d=2–3, b=8–12) are strongly preferred over deep narrow trees due to (1-ε)^d error compounding. The tree should be designed for coarse routing reliability, not fine-grained discrimination. Overlapping clusters may be necessary for multi-topic documents.
- **RB-003:** The DPI (Data Processing Inequality) bottleneck means summaries that are "too abstract" are structurally worse for routing than summaries that preserve key details. Summary embeddings systematically underestimate descendant relevance for detail queries. Path-relevance EMA smoothing partially compensates but cannot fix fundamentally poor summaries.

HCR's unique constraints add further requirements:

- **Leaves are external source pointers**, not content stores. The tree is a pure routing index.
- **Hard token budget (<400 tokens)** means the tree must produce candidate sets that are compact and information-dense.
- **The consumer (Su) is an agentic system** with an organisational knowledge base that grows over time — dynamic maintenance matters.


## Research Question

How should HCR's tree be constructed to maximise routing accuracy, and what makes a "good" node summary for hierarchical retrieval?

Specifically:

1. **What clustering/partitioning methods produce trees that align well with query-relevance patterns?** Bottom-up agglomerative (RAPTOR), top-down divisive (k-means, bisecting k-means), community detection (Leiden, Louvain — GraphRAG), spectral clustering, LLM-guided clustering — what does the landscape look like? For each, characterise: (a) what signal it uses, (b) how it handles multi-topic documents, (c) resulting tree shape (depth, branching factor, balance), (d) computational cost, (e) empirical performance where available.
2. **What makes a good node summary for routing?** RB-003 identified summary quality as the \#1 upstream factor. But what specific properties make a summary "good" for routing decisions? Distinctiveness from siblings? Preservation of rare entities and detail hooks? Explicit boundary descriptions ("this branch covers X but NOT Y")? Structured format (keywords + narrative)? What does the evidence say about summary generation strategies that optimise for routing rather than reading comprehension?
3. **How should multi-topic and cross-cutting content be handled?** RB-001 and RB-002 identified cross-branch queries as the \#1 failure mode. Documents or content that spans multiple topics violate the assumption that each piece belongs in one branch. Soft clustering (topic models, mixed membership), content duplication across branches, link structures between siblings — what are the options and their tradeoffs? Does any system solve this well?
4. **What tree topology is optimal for HCR's parameters?** RB-002 established shallow+wide (d=2–3, b=8–12). But within those bounds: balanced vs unbalanced trees? Fixed vs variable branching factor? Homogeneous vs heterogeneous granularity across branches? Does any theory or empirical work optimise topology for routing accuracy under token budgets?
5. **How should the tree be maintained as content changes?** Su's knowledge base grows over time. Full reconstruction is expensive. Incremental insertion (add new content to closest existing branch), lazy rebalancing (reconstruct subtrees that exceed quality thresholds), online clustering — what methods exist? How do they affect tree quality over time? RB-001 confirmed this is essentially unaddressed in the literature.
6. **What role should LLMs play in tree construction?** RAPTOR uses LLMs for summarisation but not for clustering. GraphRAG uses LLMs for entity/relationship extraction before community detection. LATTICE builds trees with LLM-generated summaries at each level. Could LLMs also guide the partitioning itself — deciding what belongs together based on semantic relationships rather than embedding distance? What's the cost/quality tradeoff?
7. **How do you evaluate tree quality independently of retrieval performance?** If you have a tree and a query workload, how do you measure whether the tree is well-constructed? Cluster purity, silhouette scores, and Davies-Bouldin are generic metrics that don't predict retrieval quality (noted in RB-002). Are there routing-specific metrics? Information-theoretic measures (mutual information between node membership and query relevance)? Per-level routing accuracy on held-out queries?
8. **How should HCR handle its unique constraint of leaves as external source pointers?** In RAPTOR/LATTICE, leaf content is directly available for summarisation. In HCR, leaves point to external sources (APIs, databases, repos). This means: (a) the tree is built from metadata and fetched content, not always from full text; (b) summaries must be constructable from partial or structured data; (c) some leaves may have content that changes. How does this affect construction strategy?

## Scope

**In scope:**

- All clustering/partitioning methods applicable to tree construction for retrieval
- Summary generation strategies optimised for routing quality (not reading comprehension)
- Multi-topic document handling (soft assignment, duplication, linking)
- Tree topology optimisation (depth, breadth, balance) for routing under token budgets
- Dynamic tree maintenance (incremental updates, rebalancing, quality monitoring)
- LLM-assisted construction (for clustering, summarisation, or both)
- Tree quality evaluation metrics that predict retrieval performance
- Handling external source pointers as leaves

**Out of scope:**

- Scoring mechanics (RB-003 — complete)
- End-to-end retrieval pipeline design (future brief)
- Specific embedding model selection (implementation detail)
- Benchmark design (RB-006)


## What We Already Know

From RB-001 (prior art):

- **RAPTOR:** Bottom-up clustering (GMM soft-clustering) + LLM summarisation at each level. Produces unbalanced trees. Collapsed tree (flat over all nodes) outperforms strict traversal — suggesting the tree's value is in creating multi-granularity representations, not in enforcing a navigation path.
- **GraphRAG:** Leiden community detection on entity-relationship graphs. Produces hierarchical community structure. Extremely expensive (\$650/100 queries for LLM entity extraction). Graph structure captures relationships that flat clustering misses.
- **HIRO:** Builds on RAPTOR trees, adds DFS + delta-threshold pruning. Does not innovate on construction.
- **LATTICE:** LLM-generated tree with summaries at each level. Beam search traversal. Contextual calibration via anchor nodes. Achieves Recall@100=74.8% on BRIGHT.
- **LlamaIndex TreeIndex:** Simple document-level chunking + recursive summarisation. Production framework, not research-optimised.
- **All sources:** Tree construction is brittle and dataset-dependent. Clustering algorithm choice dramatically affects performance. No principled method for automatic selection.

From RB-002 (theoretical basis):

- **Shallow + wide is strongly preferred.** (1-ε)^d penalises depth exponentially. d=2–3 with b=8–12 is the target regime.
- **The cluster hypothesis is necessary but not sufficient.** Holds for narrow, structured domains; fails for broad, multi-topic collections (Voorhees: 8% failure narrow vs 46% broad).
- **Overlapping clusters may be necessary.** Hard partitions are brittle when documents are multi-topic. But overlapping clusters contradict single-path hierarchies.
- **Tree quality determines whether safe elimination conditions are met.** Cluster alignment with typical query relevance patterns is the key metric.

From RB-003 (scoring mechanics):

- **Summary quality is the \#1 upstream factor for scoring accuracy.** No amount of scoring sophistication compensates for poorly differentiated summaries.
- **The DPI bottleneck means summaries lose detail.** Detail-query-against-thematic-summary is the structural failure case. Summaries must preserve "detail hooks."
- **Path-relevance EMA partially compensates.** `p(v) = α · p(parent) + (1-α) · calibrated_score(v)` smooths scores across depth. But it cannot recover information that was never in the summary.
- **ColBERT/late-interaction preserves detail hooks.** Multi-vector representations keep rare terms and specific identifiers that single-vector embeddings wash out. Relevant to summary representation, not just scoring.


## Prompt for Sources

> I am designing the **tree construction strategy** for a hierarchical context retrieval system (HCR) that retrieves context for LLMs under a hard token budget (<400 tokens). The system uses a shallow tree (depth 2–3, branching factor 8–12) where internal nodes hold summaries and leaf nodes point to external data sources. Queries enter at the root and are routed through the tree via a cascade scorer (hybrid BM25+dense → cross-encoder rerank, achieving per-level error ε ≈ 0.01–0.02).
>
> Our prior research established critical constraints:
> - **Summary quality is the \#1 upstream factor** for scoring accuracy. Poorly differentiated summaries structurally cap routing performance regardless of scorer sophistication. (RB-003)
> - **Error compounds as (1-ε)^d** across depth, making shallow wide trees essential. (RB-002)
> - **Summaries are lossy channels** (Data Processing Inequality) — they systematically lose detail. Detail queries against thematic summaries is the structural failure case. (RB-002, RB-003)
> - **Cross-branch queries are the \#1 failure mode** — when relevant content spans multiple branches, top-down routing misses evidence. (RB-001, RB-002)
> - **The cluster hypothesis holds for narrow structured domains but fails for broad collections** — 8% vs 46% failure rates (Voorhees 1985). (RB-002)
> - **Leaves are external source pointers**, not content stores. The tree is a pure routing index.
>
> I need a comprehensive analysis of tree construction. Specifically:
>
> 1. **Landscape of tree construction methods.** What methods partition a corpus into a tree suitable for hierarchical retrieval? Bottom-up agglomerative (RAPTOR/GMM), top-down divisive (bisecting k-means), community detection (Leiden/Louvain — GraphRAG), spectral methods, LLM-guided clustering, topic models (LDA/BERTopic), and any others. For each: (a) what signal does it partition on, (b) how does it handle multi-topic content, (c) what tree shape does it produce, (d) computational cost for 10K–100K chunks, (e) empirical quality where reported.
>
> 2. **Summary generation for routing quality.** What makes a node summary effective for *routing* (deciding "does my answer lie below this node?") as opposed to *reading comprehension* (understanding a topic)? Specific questions: Does contrastive summarisation ("this branch covers X, NOT Y") help? Should summaries preserve rare entities and identifiers ("detail hooks")? Does structured format (keywords + entities + narrative) outperform pure prose? Is there evidence on summary length vs routing accuracy? What about multi-vector representations (ColBERT-style) at the summary level — do they preserve detail hooks better than single embeddings?
>
> 3. **Handling multi-topic and cross-cutting content.** Content that belongs in multiple branches is the \#1 structural failure mode. Options include: soft clustering (content appears in multiple branches), link structures between related nodes, query-time multi-path expansion, content decomposition (split multi-topic documents into single-topic chunks before clustering), and redundant leaf placement. What works? What are the storage and consistency tradeoffs? Does any system solve this convincingly?
>
> 4. **Optimal tree topology.** Within d=2–3 and b=8–12: balanced vs unbalanced? Fixed vs variable branching? How should granularity vary across the tree (some branches deep, others flat)? Is there theory or empirical work on topology optimisation for routing accuracy or information density? What about non-tree structures (DAGs, forests) that relax the single-parent constraint?
>
> 5. **Dynamic tree maintenance.** The knowledge base grows over time. Full reconstruction is impractical for production. How can trees be updated incrementally? Incremental insertion into existing branches? Lazy subtree reconstruction when quality degrades? Online/streaming clustering methods? Split/merge operations when branches grow too large or too small? What are the quality degradation patterns over time, and how do you detect when reconstruction is needed?
>
> 6. **LLM-assisted construction.** Where in the construction pipeline do LLMs add the most value? Just summarisation (RAPTOR)? Entity/relationship extraction (GraphRAG)? Semantic partitioning decisions? Contrastive summary refinement? Quality validation? What's the cost profile for LLM-assisted construction at 10K–100K chunks, and what's the quality lift over purely embedding-based approaches?
>
> 7. **Tree quality evaluation.** How do you measure whether a tree is well-constructed for routing, independent of end-to-end retrieval metrics? Generic cluster metrics (silhouette, Davies-Bouldin) don't predict retrieval quality. Routing-specific metrics: per-level routing accuracy on held-out queries, sibling distinctiveness scores, summary-to-descendant information coverage, cross-branch query detection rate — do any of these exist in the literature? What would a principled tree quality metric look like?
>
> 8. **Construction with external source pointers.** HCR's leaves point to external sources (APIs, databases, document stores) rather than holding content directly. This means: summaries may need to be built from metadata or partial content, leaf content may change independently, and some sources may not be fully available at construction time. How does this constraint affect construction strategy? Are there precedents in federated search or meta-search that handle indexing over external collections?
>
> Be rigorous. Cite specific papers and systems where they exist. Distinguish between proven results, strong empirical evidence, and speculation. If a question doesn't have established answers, say so explicitly — knowing where the frontier is matters as much as knowing what's been solved.

## Success Criteria

A good response will:

- Map at least 5 distinct tree construction approaches with tradeoff analysis
- Address summary generation for routing specifically (not just generic summarisation)
- Provide concrete strategies for multi-topic content handling with tradeoff analysis
- Cover tree topology optimisation within the d=2–3, b=8–12 regime
- Address dynamic maintenance with at least 2 concrete approaches
- Analyse where LLMs add value in construction vs where embedding-based methods suffice
- Propose or cite at least one tree quality metric that predicts routing accuracy
- Address the external source pointer constraint specifically
- Distinguish clearly between established results and speculation
- Surface any construction approaches we haven't considered

Below is a synthesis of what the literature actually supports plus a concrete construction strategy for HCR under your constraints. Where evidence is thin, that is called out and separated from design speculation.

***

## 0. High‑level design stance for HCR

Given HCR’s constraints (shallow tree, 400‑token budget, external leaves, strong reliance on node summaries), the most defensible architecture is:

- **Topology**: shallow, almost-balanced, degree‑bounded tree (depth 2–3, average branching 8–12) with limited overlap at the leaves and a small number of cross-links (DAG flavor rather than pure tree).
- **Partitioning**: primarily **embedding-based divisive clustering** (top‑down) with:
    - pre‑decomposition of multi-topic content into finer units, and
    - constrained **soft assignment / duplication** for genuinely cross-cutting units.
- **Summaries**: each node has a **structured, contrastive summary** that:
    - preserves rare entities and schema identifiers,
    - enumerates coverage and explicit non‑coverage for sibling differentiation,
    - is backed by **multi-vector representations** (or at least keyword/entity bags) in addition to a single dense embedding.
- **Maintenance**: incremental insertion into existing branches plus **lazy subtree rebuilding** when routing metrics or cluster compactness drift.
- **LLMs**: used heavily for **summaries, labels, and multi-aspect encodings**, but not for all clustering decisions; clustering remains mostly classical with LLMs used at ambiguity boundaries.

The rest of this answer drills into each question and ends with a concrete, step‑by‑step HCR construction recipe.

***

## 1. Landscape of tree construction methods

Below are at least five distinct families of methods used to build hierarchies for retrieval or related tasks, with the requested characterization.

### 1.1 Bottom‑up agglomerative clustering (RAPTOR, HIRO-index, generic HAC)

**Signal.**

- RAPTOR starts from chunk embeddings (SBERT) and uses UMAP + Gaussian Mixture Models (GMMs) to soft‑cluster chunks; each cluster is summarized by an LLM and becomes a parent node, then the process repeats upward.[^1_1][^1_2]
- HIRO for opinion summarization learns a discrete hierarchy (paths in a codebook) for sentence encodings, but the core is still learning a structured embedding space that induces a hierarchy.[^1_3][^1_4]

**Multi-topic handling.**

- RAPTOR explicitly uses **soft clustering**: chunks can belong to multiple clusters so they may appear in multiple parent summaries.[^1_2]
- HIRO’s index is a **single path per sentence** (hard hierarchical code), so multi-topic content is handled by the representation learning rather than overlapping cluster assignments.[^1_3]

**Tree shape.**

- RAPTOR’s tree is **unbalanced** because recursive clustering continues only while cluster context exceeds an LLM token limit; deep where content is large/diverse, shallow where small/homogeneous.[^1_1]
- RAPTOR’s experiments show that **“collapsed tree” retrieval (flat search over all nodes) often outperforms strict top‑down traversal**, suggesting the tree is more a multi‑granularity representation than a reliable routing structure.[^1_1]
- HIRO-index yields relatively **balanced, fixed-depth hierarchies** because the path length (code depth) is fixed by the quantization scheme.[^1_3]

**Computational cost (10K–100K chunks).**

- Classical HAC (single/complete/average linkage) is $O(n^2)$, often prohibitive above ~50K without approximation.[^1_5]
- RAPTOR mitigates via UMAP for dimensionality reduction and local clustering stages, but cost is still on the order of many $n \log n$ / $n^2$-ish operations plus repeated summarization; in practice used on per‑document or medium‑scale corpora, not web‑scale.[^1_1]
- HIRO-index learns the hierarchy jointly with the encoder; building the codebook is more akin to training a model once, then assigning sentences cheaply.

**Empirical quality.**

- RAPTOR shows substantial QA gains over BM25/DPR on NarrativeQA, QASPER, QuALITY; but the collapsed-tree variant outperforms strict traversal, undercutting pure routing tree value.[^1_1]
- HIRO-index shows more structured encoding spaces and better opinion summarization quality than baselines, but evaluation is about **opinion representativeness**, not routing for arbitrary queries.[^1_6][^1_3]

**Implication for HCR.**
Bottom‑up HAC/GMM is attractive when you start from a single long document or coherent corpus, but it gives you **uncontrolled depth and branching** and is expensive; it also does not directly align with query patterns. For HCR’s global KB and strict depth limit, pure bottom‑up is not a good fit as the primary driver.

***

### 1.2 Top‑down divisive clustering (k‑means, bisecting k‑means, spectral, LATTICE)

**Signal.**

- Classical **bisecting k‑means** and other divisive methods start from all points and recursively split clusters to meet a target number of leaves or purity threshold.[^1_7][^1_5]
- LATTICE offers **two tree construction strategies**:
    - bottom‑up clustering+summarization, and
    - **top‑down divisive clustering** that recursively partitions documents using embeddings and multi‑level summaries.[^1_8]

**Multi-topic handling.**

- Standard divisive clustering is **hard partitioning**: each chunk goes to exactly one child.
- Multi-topic content will be forced into the “closest” cluster; LATTICE relies on the traversal LLM and cross‑branch scoring calibration (beam search across siblings) to partially mitigate cross‑branch failures at query time.[^1_8]
- There is no explicit multi‑cluster membership.

**Tree shape.**

- Divisive methods allow direct control over **branching factor and depth**; LATTICE explicitly constructs semantic trees suitable for BRIGHT with controlled depth and branching.[^1_8]
- With appropriate stopping rules, the trees can be **almost balanced**, especially if you target a fixed branching factor at each internal node.

**Computational cost.**

- k‑means on 10K–100K vectors is practical; bisecting k‑means yields approximately $O(k n t)$ where $t$ is iterations. Spectral methods are costlier (eigen decomposition).
- LATTICE reports offline tree construction as feasible for BRIGHT-scale corpora and emphasizes that online cost is dominated by LLM traversal, not clustering.[^1_8]

**Empirical quality.**

- On BRIGHT, LATTICE’s LLM-guided traversal over its semantic tree achieves **up to 9% Recall@100 improvements** over the next best zero‑shot baseline, and comparable to a fine-tuned SOTA model.[^1_9][^1_8]
- Their analysis section shows **non-trivial sensitivity to tree construction strategy**: some tree variants degrade recall, implying construction choices matter for routing, not just scoring.[^1_8]

**Implication for HCR.**
Top‑down divisive clustering with explicit control of branching is strongly aligned with your d=2–3, b=8–12 constraints. It is the most natural backbone for HCR, with additional mechanisms to handle multi-topic and cross-cutting content.

***

### 1.3 Community detection on graphs (GraphRAG, hierarchical Leiden/Louvain)

**Signal.**

- GraphRAG converts documents into a **knowledge graph** of entities and relationships via LLM extraction, then runs **hierarchical community detection (Leiden or Louvain)** on this graph.[^1_10][^1_11][^1_12][^1_13][^1_14][^1_15]
- Communities at each level are summarized by an LLM into “community summaries,” which become nodes in a hierarchy.[^1_11][^1_10]

**Multi-topic handling.**

- Graph communities are **naturally overlapping** at the entity level: a document or chunk can participate in multiple entity nodes, and entities can occur in multiple communities across levels.[^1_15]
- However, the **communities themselves are disjoint** per level in standard Leiden/Louvain; overlapping communities require modified algorithms.[^1_12][^1_16][^1_17]

**Tree shape.**

- Leiden/Louvain produce **multi-level community hierarchies** by repeatedly aggregating communities and re-running modularity optimization.[^1_13][^1_18][^1_12]
- The “tree” is often **irregular and unbalanced**; branching factors are determined by graph structure, not a user-specified b.

**Computational cost.**

- The dominating cost is **LLM-based entity and relation extraction**. Anecdotal reports from GraphRAG deployments mention costs on the order of hundreds of dollars per ~100 queries for sizable corpora.[^1_19][^1_15]
- Community detection itself (Leiden) is near‑linear in the number of edges and scales well.[^1_12][^1_13]
- Dynamic updates to Leiden have been studied; there are dynamic variants that update communities given batched graph changes rather than re-running from scratch.[^1_20]

**Empirical quality.**

- GraphRAG shows strong anecdotal performance for **global, cross-document questions**, particularly where entity-level reasoning is key; but there is limited published benchmark comparison with RAPTOR/LATTICE.[^1_21][^1_15]
- Community summaries enable multi-level reasoning and explanation, but the emphasis is not on strict top‑down routing with per-level error guarantees; retrieval often involves scanning relevant communities at one or more levels.

**Implication for HCR.**
Community detection is best viewed as a **secondary index** for cross-cutting, entity-heavy queries rather than the primary routing tree. Good for global “tell me about X across the org” questions but too expensive and structurally unconstrained to be the main index under tight token budgets.

***

### 1.4 Topic models and topic-based hierarchies (LDA, BERTopic, hierarchical topic merges)

**Signal.**

- LDA is a **soft clustering** model: each document has a distribution over topics; each topic is a distribution over words.[^1_22][^1_23][^1_24]
- BERTopic uses transformer embeddings + UMAP + clustering, then **class-based TF-IDF** (c‑TF‑IDF) to generate interpretable topics.[^1_25][^1_26]
- BERTopic supports **hierarchical topics** by clustering topic-term vectors (c‑TF‑IDF rows) to form topic trees.[^1_27]

**Multi-topic handling.**

- LDA is inherently **multi-topic**; documents have mixtures.[^1_23][^1_22]
- BERTopic exposes **topic probabilities per document** and can assign documents to multiple topics—or use the highest-probability topic as a hard assignment.[^1_28][^1_29]

**Tree shape.**

- Hierarchies are either:
    - manually specified (e.g., choose K topics then hierarchically cluster topic-term vectors), or
    - data-driven via agglomerative clustering of topics.[^1_27]
- Depth and branching are tunable; typically shallow and coarse (e.g., a couple of levels over tens of topics), but not strongly optimized for IR routing.

**Computational cost.**

- LDA on 10K–100K docs is feasible but less competitive than embedding-based methods for semantic similarity.
- BERTopic relies on embeddings plus clustering and is used at this scale routinely.[^1_26][^1_25]

**Empirical quality.**

- Topic models are strong at **thematic organization and exploration**, but not state-of-the-art for ranking relevance at query time compared to dense retrieval.
- There is limited evidence that topic-based hierarchies alone yield strong IR performance; they are usually used as **side channels** (facets, exploratory navigation).

**Implication for HCR.**
Topic modeling is valuable as a **coarse thematic prior** (e.g., first-level partition: product docs vs. HR policies vs. infrastructure), or as a feature in clustering, but should not be the sole basis for routing.

***

### 1.5 LLM-guided hierarchical construction and taxonomies (LATTICE, HIRO-index, LLM-guided taxonomies)

**Signal.**

- LATTICE: tree nodes are **multi-level summaries**; construction can be bottom-up or top-down, and summaries themselves are generated by an LLM.[^1_9][^1_8]
- HIRO-index learns a **hierarchical code space** where sentences are mapped to paths; the hierarchy is discrete and optimized for grouping similar opinions; LLMs are used mainly to generate the final opinion summaries, not to guide clustering per se.[^1_6][^1_3]
- Recent work on **LLM-guided taxonomy generation** for scientific papers generates aspects using GPT‑4, then clusters within each aspect with GMMs to build a coherent, context-aware hierarchy.[^1_30][^1_31]
- Multi-view hierarchical clustering frameworks use an LLM to generate multiple “views” (paraphrases or facet summaries) of cluster content to refine cluster representations and improve hierarchical clustering quality.[^1_32]

**Multi-topic handling.**

- The taxonomy paper enforces **non-overlapping partitions**—each paper belongs to exactly one child at each split—but uses **multi-aspect representations** so that splitting is made on the most discriminative aspects; this improves separation of subtly different topics.[^1_30]
- HIRO-index still assigns each sentence to a single path but learns an encoding that strongly reflects popular opinion dimensions.[^1_3]
- LATTICE’s tree is semantic but again has hard assignment; cross-branch issues are handled mainly at traversal time (cross-branch calibration).[^1_8]

**Tree shape.**

- All of these methods allow **explicit control over depth and branching**; the taxonomy framework in particular chooses the number of child categories $k_v$ at each node as part of its optimization.[^1_30]
- Trees tend to be **semantically coherent and interpretable** because LLMs label facets and nodes.

**Computational cost.**

- Cost is dominated by:
    - Multi-aspect LLM summarization per document per node,[^1_30]
    - Cluster- and node-level LLM calls for labels and summaries,[^1_9][^1_3][^1_8]
    - For 10K–100K documents, full LLM-guided clustering is expensive but feasible offline if amortized over many queries.

**Empirical quality.**

- The taxonomy framework achieves strong alignment with expert-crafted taxonomies (NMI, ARI, purity) and high human-judged coherence.[^1_30]
- HIRO-index shows better opinion summarization quality than baselines, and ablations show that the learned hierarchy matters.[^1_6][^1_3]
- LATTICE shows tree construction choices significantly influence BRIGHT performance.[^1_8]

**Implication for HCR.**
LLM-guided construction is the **highest-quality but most expensive** route. For HCR, a hybrid is attractive: use **classical divisive clustering to propose splits**, then use LLMs to refine cluster representations, adjust assignments for ambiguous leaf sets, and generate summaries and labels.

***

### 1.6 Other relevant hierarchies (vector indices, database context trees)

- **Vector hierarchies** in ANN search (e.g., IVF trees, quantization trees, HNSW layers) build coarse‑to‑fine indices over embeddings; they are strong for nearest-neighbor search but lack semantic labels/summaries and multi-topic notions.
- ConStruM for databases builds a **two-stage context tree**: per-table hierarchies (column → within-table summary) and then a database-level hierarchy by clustering per-table summaries.[^1_33]
    - This is effectively a hierarchical routing tree for **external structured sources** and is a close analogue to HCR’s leaf-as-pointer constraint.

***

## 2. What makes a good node summary for routing?

The literature plus your RB‑003 analysis converges on several concrete properties.

### 2.1 Distinctiveness vs. siblings

Evidence:

- LATTICE explicitly calibrates relevance scores across **sibling branches and previously visited nodes** to make path scores globally comparable; this only works if sibling summaries are semantically distinct enough for the LLM to discriminate.[^1_34][^1_8]
- GraphRAG’s community summaries are meant to represent **different entity communities**; the utility of the hierarchy depends on those summaries being contrastive enough to support choosing which communities to consult.[^1_11][^1_15]
- HIRO-index evaluation shows that a more structured encoding space, where similar sentences cluster tightly and dissimilar ones are separated, yields better opinion retrieval and summarization.[^1_6][^1_3]

Conclusion:

- **Sibling contrast is essential.** A routing summary should maximize **between-sibling separation** (low inter-sibling similarity) while preserving within-branch coherence.

Design implications for summaries:

- Include explicit **facet headings** or bullet lists distinguishing major subtopics in the branch.
- Where possible, add brief negative qualifiers:
    - “Focuses on customer‑facing product docs (X, Y, Z), **excludes** infra logs and internal SRE runbooks.”


### 2.2 Preservation of “detail hooks”

Evidence:

- RAPTOR’s authors stress that **soft clustering** avoids losing multi-topic segments and that summaries at different levels provide both high-level and low-level detail.[^1_2][^1_1]
- RB‑003’s DPI analysis aligns with broader observations: single-vector embeddings of summaries tend to underweight rare entities or identifiers; multi-vector methods like ColBERT preserve these hooks better.[^1_35][^1_36][^1_37]
- Multi-vector retrieval and late interaction architectures were explicitly introduced to preserve token-level detail that single-vector pooling washes out; they significantly improve recall on entity-heavy queries.[^1_36][^1_38][^1_35]
- Multi-aspect taxonomies rely on **aspect‑specific summaries** that retain aspect-specific identifiers, improving separability of fine-grained categories.[^1_30]

Conclusion:

- A good routing summary **must explicitly surface rare entities, IDs, and structural markers** from its descendants.
- You should not rely on an LLM’s notion of “salience for reading”; you need “salience for routing.”

Design pattern:

- Summaries should have **structured sections**:
    - Short narrative: 1–3 sentences describing the main theme.
    - **Key entities \& identifiers**: extracted list of names, codes, API endpoints, schema/table names, repo names, feature flags, etc.
    - **Key query terms / keywords**: top TF‑IDF or BM25 terms across descendants.
    - Optional: “typical questions this branch answers.”


### 2.3 Contrastive or query-aware summarization

There is no direct paper on “contrastive summarization for hierarchical routing,” but related strands:

- Contrastive summarization in opinions (differences between two entities) has been explored and shown to help with comparative tasks.[^1_39][^1_40]
- Taxonomy generation uses an LLM with access to parent and sibling facets to ensure new child topics are **non-overlapping and collectively exhaustive**, effectively doing contrastive labeling.[^1_31][^1_30]
- Query-focused summarization literature shows that **query-conditioned summaries** better support downstream QA than generic summaries; cluster-based retrieve–cluster–summarize pipelines rely on this for high-quality answers.[^1_41][^1_42][^1_43]

Conclusion (partly extrapolated):

- Summaries built in a **hierarchical, contrastive prompt** (“Summarize the unique content of this cluster compared to its siblings; state what it covers and what it does not”) are likely superior for routing than generic “summarize this cluster” prompts.
- This is consistent with RB‑003: routing depends on differentiating siblings, not just describing each branch in isolation.


### 2.4 Structured vs. pure prose

Evidence:

- GraphRAG’s community summaries are defined in terms of **entities and relationships**, not just prose.[^1_10][^1_15][^1_11]
- BERTopic’s topic representations use **class-based TF‑IDF keyword lists**, which are easy to match at query time and map well to BM25-style scoring.[^1_25][^1_26]
- Multi-vector and hybrid dense+sparse retrievers benefit from having both a sequence of tokens (for dense) and an explicit bag of key terms (for sparse).[^1_44][^1_35][^1_36]

Conclusion:

- Routing summaries should be **semi-structured artifacts**, not only narrative text.
    - This supports hybrid BM25+dense scoring as in HCR’s cascade.
- A practical format might be JSON‑ish internally:
    - `{theme: "...", includes: [...], excludes: [...], key_entities: [...], key_terms: [...], typical_queries: [...]}`.


### 2.5 Summary length vs routing accuracy

Direct empirical curves are scarce:

- RAPTOR evaluates different layers’ contributions but not summary lengths per se.[^1_1]
- LATTICE uses multi-level summaries and focuses on ranking metrics, not summary length ablations.[^1_9][^1_8]
- HIRO-index’s “opinions represented” metric depends on cluster purity rather than summary length; summaries are generated post hoc.[^1_3][^1_6]

What can be safely inferred:

- Extremely brief summaries risk losing detail hooks and subtle distinctions; extremely long summaries violate your token budget and increase scoring noise.
- For HCR, with d=2–3 and b≈10, you can afford on the order of **~50–120 tokens per internal node summary** if only a small number of nodes are consulted per query. But since you also want multi-vector or keyword structures, the “prose” part can stay short while auxiliary fields hold more detail.


### 2.6 Multi-vector representations at the summary level

Evidence:

- ColBERT and successors show that multi-vector, late-interaction models preserve detail hooks and improve performance especially on entity-centric and rare term queries.[^1_37][^1_38][^1_35][^1_36]
- Multi-vector compression work (ConstBERT) shows that a **fixed small number of vectors per document** can retain most of ColBERT’s effectiveness, suggesting a feasible compromise for summaries.[^1_38]

Conclusion:

- Representing each node summary with a **small set of vectors (e.g., 8–16) derived from its structured fields** is a strong way to mitigate DPI losses.
- For HCR you can:
    - Use a single “summary text” vector for coarse similarity.
    - Use **token-level or phrase-level vectors** for entities/identifiers and critical terms to allow late-interaction reranking at the node level if needed.

***

## 3. Handling multi-topic and cross-cutting content

This is indeed the hardest open problem; there is no single “solved” approach, but there are several partially successful patterns.

### 3.1 Soft clustering and duplication

- RAPTOR uses **GMM soft clustering**, explicitly permitting chunks to belong to multiple clusters; parent summaries may include shared children.[^1_2]
- LDA and other topic models treat documents as **mixtures**; you can decide at indexing time whether to duplicate leaves across top‑k topics or not.[^1_24][^1_22][^1_23]
- Overlapping community detection algorithms (e.g., OClustR, label‑propagation-based methods) allow nodes to belong to multiple communities.[^1_16][^1_17]

Tradeoffs:

- **Pros**: directly addresses cross-branch queries; relevant leaves can be reached via multiple parents.
- **Cons**:
    - Storage blow‑up (leaf pointers replicated into multiple branches).
    - Summaries may become less distinctive if many siblings share children.
    - Consistency issues: when underlying content changes, all copies must be kept in sync.

For HCR:

- Allow **controlled duplication at the leaf level**:
    - Each leaf can have up to, say, **2–3 parents**.
    - Duplication is reserved for clearly multi-topic units (e.g., a design doc crucial for both “payments infra” and “fraud models”).


### 3.2 Query-time multi-path traversal

- LATTICE’s **beam search with cross-branch calibration** explicitly keeps multiple branches alive, calibrating scores across siblings and previously seen leaves.[^1_9][^1_8]
- HIRO (querying over RAPTOR) uses **DFS-based threshold pruning** (Selection threshold $S$, Delta threshold $\Delta$) to decide which branches to explore further.[^1_45][^1_46][^1_47]
- Hierarchical retrieval survey work highlights pruning with thresholds and multi-path expansion as core techniques.[^1_48]

Tradeoffs:

- **Pros**: Does not require structural changes or duplication; cross-branch relevance is modeled at inference time.
- **Cons**: Under very tight token budgets, exploring too many branches early can exceed budgets; also, if summaries fail to indicate relevance for a minor aspect, no traversal algorithm can save you (DPI).

For HCR:

- Beam search across siblings is mandatory. Under b~10, a beam of 3–4 nodes per level still keeps total candidate nodes manageable. Summaries must be good enough that cross-branch calibration can detect weak but real relevance signals.


### 3.3 Content decomposition

- GraphRAG’s build pipeline breaks documents down into **entity and fact nodes**; complex documents become many small, mono-topic units in a graph.[^1_21][^1_15]
- ConStruM builds per-table trees where leaves are **columns** and small within-table regions, not entire tables.[^1_33]
- HIRO-index operates at sentence level; each sentence is a unit in the hierarchy.[^1_3]

Tradeoffs:

- **Pros**: If multi-topic documents are decomposed into smaller **semantic units**, the clustering problem becomes easier and hard partitions are less harmful.
- **Cons**:
    - More leaves; more complex routing.
    - You need to maintain provenance so that multiple leaves belonging to the same original document can be recombined when necessary.

For HCR:

- This should be **the primary defense**:
    - Normalize complex leaves into **atomic units aligned with query grain** (e.g., sections, API endpoints, tickets).
    - Only truly irreducible multi-topic units then need soft assignment.


### 3.4 Link structures and DAGs

- GraphRAG’s communities form a **graph structure**; queries can follow edges between related entities and communities.[^1_15][^1_10][^1_11]
- Overlapping community detection and multi-resolution clustering often effectively produce a **forest or DAG** rather than a strict tree.[^1_17][^1_49]
- Federated search systems often maintain **cross-collection mappings and verticals**; a query can be sent to multiple collections simultaneously.[^1_50][^1_51]

Tradeoffs:

- **Pros**: DAGs allow a node to have multiple parents or cross-links, relaxing the single‑path constraint while still giving hierarchical structure.
- **Cons**: Traversal logic becomes more complex; scoring must avoid double counting.

For HCR:

- A pragmatic compromise: maintain a **tree backbone** plus:
    - **Cross-links** between siblings for strongly related branches (e.g., “billing systems” ↔ “revenue analytics”).
    - Allow a limited **multi-parent relationship** for certain leaf sets (effectively a forest+ DAG).


### 3.5 Does any system “solve” cross-branch queries?

No. The literature overwhelmingly reports:

- Tree-based and cluster-based IR systems gain efficiency and sometimes effectiveness in narrow domains, but cross-topic queries remain a dominant failure mode when cluster hypothesis fails.[^1_52][^1_53]
- RAPTOR’s collapsed-tree retrieval outperforming strict hierarchical traversal is itself evidence that the tree is not a fully reliable routing structure.[^1_1]
- LATTICE and HIRO‑query mitigate issues via beam search, cross-branch calibration, and thresholds, but do not guarantee correctness.[^1_46][^1_8]

So multi-topic handling requires **combining decomposition, controlled overlap, and multi-path traversal**; no single mechanism is sufficient.

***

## 4. Tree topology under HCR’s constraints

You already adopted d=2–3, b=8–12 from RB‑002; here is what literature and theory say about more detailed topology choices.

### 4.1 Balanced vs unbalanced

Evidence:

- RAPTOR’s tree is unbalanced; its own ablations suggest the traversal path is less critical than the availability of multi-granularity summaries, since collapsed-tree retrieval often wins.[^1_1]
- Hierarchical clustering literature notes that unbalanced trees (particularly from single‑linkage) can be pathological; balanced trees often yield better search performance and **lower expected routing depth**.[^1_5][^1_7]
- The **online PERCH algorithm** for hierarchical clustering explicitly optimizes for **balancedness and subtree purity** via tree rotations and proves that under separability assumptions, it achieves perfect dendrogram purity with balanced structures.[^1_54]

Conclusion:

- For routing with error compounding, **near-balanced trees are preferred**: they minimize average depth and spread misrouting risk more evenly.


### 4.2 Fixed vs variable branching factor

There is limited IR-specific work, but:

- In practice, LATTICE and HIRO-index allow **variable branching per node**, but both use heuristics or hyperparameters to keep branching reasonable per layer.[^1_3][^1_8]
- Community detection hierarchies (Leiden/Louvain) have highly variable branching factors determined by graph structure.[^1_13][^1_12]
- Theory: for a given budget of internal nodes and leaves, **uniform branching minimizes average path length**; but in real data, forcing uniformity can increase semantic heterogeneity within nodes.

Conclusion:

- For HCR, target a **bounded branching range per level** (e.g., 6–12 children) but allow moderate variability where cluster quality demands it.
- Enforce **max-children constraints**; if a node would have >b_max children at reasonable purity, consider splitting via another dimension or introducing an intermediate layer.


### 4.3 Heterogeneous granularity across branches

Evidence:

- RAPTOR naturally yields deeper trees for parts of the corpus that are large/diverse, shallower ones where small/homogeneous.[^1_1]
- ConStruM’s database context tree has very different granularities for wide vs narrow tables; per-table trees adapt depth to table complexity.[^1_33]

Conclusion:

- Some heterogeneity is beneficial: complex subdomains merit more granular branching; trivial ones stay shallow.
- However, with your d≤3 constraint, this heterogeneity is limited: most variation will be in **branching factor per node**, not depth per branch.


### 4.4 Non-tree structures (DAGs, forests)

- GraphRAG plus overlapping communities clearly demonstrates the utility of **non-tree hierarchies** for global retrieval.[^1_17][^1_21][^1_15]
- Federated search effectively uses a **two-level hierarchy over collections** (verticals and sources) plus possibly cross-vertical strategies; this is more like a forest than a single tree.[^1_51][^1_50]

Conclusion:

- For HCR, a **forest of trees** per major domain (e.g., product, infrastructure, org processes) with a thin root layer that routes between forests may be superior to a monolithic tree.
- DAG links can be reserved for critical cross-domain connections.

***

## 5. Dynamic maintenance as content changes

The literature recognizes dynamic maintenance as hard and underexplored.

### 5.1 Incremental hierarchical clustering

- **Online HAC approximations** and **incremental hierarchical clustering** methods (OHAC, etc.) update trees with split–merge operations, aiming to approximate offline HAC trees.[^1_55][^1_56][^1_57][^1_58]
    - Strategy: when a new point arrives, find its closest place in the tree, insert it, and then locally restructure the hierarchy to maintain quality.
- The **PERCH** algorithm builds trees online and performs **tree rotations** to improve cluster purity and balance as new points arrive.[^1_54]

These methods show:

- It is possible to maintain **approximate high-quality hierarchies online** with local updates, at least for metric data.


### 5.2 Dynamic community detection

- Recent work extends Leiden to **dynamic graphs**, updating communities after batches of edge insertions/deletions; only affected vertices and communities are re‑examined.[^1_20]
- This reduces recomputation cost versus static re‑runs, suggesting a similar strategy can be applied to HCR if it ever uses graph-based clustering.


### 5.3 Topic modeling and incremental updates

- BERTopic explicitly supports **online/incremental topic updates**; topics can be merged and refined as new documents arrive.[^1_29][^1_28]


### 5.4 Quality degradation patterns and triggers

There is no systematic study for hierarchical retrieval trees, but:

- Cluster analysis notes that **internal evaluation metrics** (silhouette, Davies–Bouldin) can detect cluster drift but do not necessarily predict IR performance.[^1_59][^1_60]
- IR work on cluster-based retrieval (e.g., Tombros) shows that **query-sensitive clustering** can outperform static clustering, but also that static clusters can become misaligned with query distributions over time.[^1_53]

For HCR, a practical strategy is:

- Maintain **per-node quality monitors**:
    - Cluster compactness (average intra-cluster distance, silhouette).
    - Routing statistics: how often queries routed through this node end up with relevant leaves (see Section 7).
    - Drift in leaf embeddings or metadata.
- When metrics cross thresholds:
    - **Rebuild the subtree** rooted at that node offline (re-cluster and re-summarize children).
    - Optionally re-map leaf assignments from scratch within that subtree.


### 5.5 Concrete maintenance scheme for HCR

1. **Incremental insertion**:
    - When a new leaf appears:
        - Compute its embedding and metadata-derived “topic” features.
        - Route it through the current tree using the same scoring cascade you use for queries.
        - Attach it to the best-matching leaf-level cluster(s) (allowing multi-parent if multi-topic).
2. **Periodic local rebalancing**:
    - Periodically scan internal nodes whose:
        - Child count > b_max, or
        - Intra-cluster variance > threshold, or
        - Routing accuracy (see Section 7) has dropped.
    - For those nodes, **re-cluster children** (or even grandchildren) and regenerate summaries.
3. **Occasional global rebuild**:
    - At large scale changes (e.g., order-of-magnitude KB growth), schedule a **full rebuild** of the tree offline and swap in the new version.

This matches patterns from OHAC and PERCH (local restructuring plus occasional full recomputation) adapted to your IR context.[^1_58][^1_55][^1_54]

***

## 6. Where LLMs add value in construction

Based on RAPTOR, GraphRAG, LATTICE, HIRO-index, and taxonomy work, the most defensible roles for LLMs are:

### 6.1 Summarization and labeling (strong evidence)

- RAPTOR uses an LLM (GPT‑3.5) to generate summaries at each cluster level; this is central to its performance.[^1_2][^1_1]
- GraphRAG uses LLMs to summarize each community into a textual description used in retrieval.[^1_10][^1_11][^1_15]
- LATTICE relies on multi-level node summaries; better summaries improve the LLM’s traversal accuracy.[^1_9][^1_8]
- HIRO-index uses LLMs to generate coherent opinion summaries grounded in evidence clusters.[^1_6][^1_3]

Conclusion:

- LLM-based summarization is **indispensable** for high-quality node summaries, especially for contrastive, structured routing summaries.


### 6.2 Entity and relationship extraction (GraphRAG)

- GraphRAG depends on LLMs to extract entities and relations; this is what enables graph/community-based clustering.[^1_11][^1_21][^1_15][^1_10]
- Cost is substantial but yields a higher-level structural representation that is not easily captured by embeddings alone.

Conclusion:

- For HCR, full GraphRAG-style extraction is likely overkill except for high-value verticals, but **lightweight entity extraction** (names, IDs, schemas) is valuable for summary detail hooks.


### 6.3 Semantic partitioning and aspect generation

- LLM-guided taxonomy generation uses GPT‑4o to generate **aspects** and facet labels for each node, then clusters documents in each aspect subspace; this improves structural alignment with expert taxonomies.[^1_31][^1_30]
- Multi-view hierarchical clustering uses LLMs to create **multi-view representations** of cluster content that better guide agglomerative clustering.[^1_61][^1_32]

Conclusion:

- LLMs can significantly improve **where to split** and **how to describe splits** by:
    - Proposing **candidate facets** for partitions (e.g., “region,” “product line,” “infrastructure vs. application”).
    - Giving human-interpretable labels and constraints that classical clustering then respects.


### 6.4 Quality validation and refinement

- Taxonomy frameworks and HIRO-index both evaluate quality at multiple stages (encoding, clustering, summarization), often with human/LLM judgment in the loop.[^1_6][^1_30][^1_3]
- It is plausible to have an LLM act as a **critic**:
    - Given candidate child clusters and their summaries, ask: “Are these children semantically distinct and jointly cover the parent’s scope?” and adjust splits accordingly.


### 6.5 Cost profile (10K–100K chunks)

Rough order-of-magnitude reasoning from the papers:

- **Clustering** alone (k‑means, GMM, Leiden) is cheap compared to LLM calls.
- Summarizing 10K–100K chunks across multiple hierarchy levels naively can mean **tens to hundreds of thousands of LLM calls**, but:
    - You only need to summarize **internal nodes** (O(n/b) per level).
    - Summaries can be cached and updated only on changed nodes.

Recommendation:

- Use LLMs for:
    - Node summaries / labels.
    - Aspect suggestion at major splits.
    - Occasional quality audits and refinement of borderline assignments.
- Use embeddings/graph methods for:
    - Bulk clustering and distance computations.
    - Online incremental updates.

***

## 7. Evaluating tree quality for routing (beyond end-to-end retrieval)

There is no widely accepted “routing metric,” but there are building blocks and some relevant proposals.

### 7.1 Generic cluster metrics (limited relevance)

- Silhouette, Davies–Bouldin, within/between-cluster variance are standard but correlate poorly with IR effectiveness.[^1_60][^1_59]
- Cluster analysis literature notes explicitly that **internal criteria do not necessarily produce clusters that are useful for retrieval**.[^1_60]

Use only as **auxiliary signals**, not primary routing metrics.

### 7.2 Hierarchical clustering cost functions (Dasgupta cost)

- Dasgupta’s cost function measures how well a hierarchical clustering reflects pairwise similarities in a graph; low cost means similar items are merged lower in the tree.[^1_62]
- It evaluates the **entire hierarchy** rather than a single cut, which is closer to your need.

You could adapt this:

- Build a similarity graph over leaves (e.g., using relevance or co-click data).
- Compute Dasgupta cost for your tree relative to this graph.
- Lower cost suggests a better alignment of tree structure with similarity relationships.


### 7.3 Cluster hypothesis and query-based measures

- Voorhees-style tests compute “local precision”: for each relevant document, how many of its nearest neighbors (in some space) are also relevant; high local precision indicates strong clustering of relevance.[^1_52]
- Tombros’ work on **query-sensitive clustering** examines how well clusters align with **query-specific** relevance patterns; query-based clustering improves over static clustering in IR performance.[^1_53]

You can define:

- **Per-level routing accuracy**:
    - For a query with known relevant leaves:
        - At each internal node, ask: **Is the path containing a relevant leaf among the top‑k children according to your scorer?**
    - Report success rates per level and overall (product over levels).
- **Sibling distinctiveness score**:
    - For each internal node:
        - Compute average similarity between summaries of its children vs. similarity between each child and the rest of the corpus.
    - You want **low inter-sibling similarity relative to global**.


### 7.4 Summary-to-descendant information coverage

No direct paper, but you can define:

- **Coverage@k**:
    - For each rare entity or identifier that appears in many leaves of a branch:
        - Check whether it appears in the node’s structured summary (entity list / key terms).
    - High coverage means summaries preserve detail hooks.
- **Mutual information**:
    - Treat node membership as a variable, and relevance labels for queries as another.
    - Estimate mutual information between node and relevance; higher MI suggests node boundaries align with query-relevance patterns.


### 7.5 What exists vs what is new

- LATTICE and HIRO-index both evaluate **variants of tree construction** by their impact on retrieval metrics (nDCG, Recall), but do not report standalone tree-quality metrics.[^1_8][^1_3]
- The IR community has not yet standardized routing-specific metrics; your proposed metrics (per-level routing accuracy, sibling distinctiveness, coverage of descendant detail) would be at the research frontier.

For HCR, a practical evaluation protocol:

1. Build a held-out **query → relevant leaf** set.
2. Measure:
    - Per-level routing accuracy (top‑k children contains the gold subtree).
    - Overall routing success (does any path leading to relevant leaves survive down to leaves).
    - Dasgupta-like cost on a similarity graph defined from these queries.
    - Summary detail coverage for known-important entities (e.g., APIs, services).
3. Use these metrics **offline** to choose clustering/summarization hyperparameters and to trigger subtree rebuilds.

***

## 8. External source pointers at leaves

HCR’s unique constraint is that leaves are **pointers to external systems**, not local content. Analogies:

- **Federated search**: collection selection relies on **representations of external collections** built from samples, metadata, or query logs rather than full content.[^1_50][^1_51]
- **Tanium Reveal** and similar federated enterprise search engines build **lightweight per-host/per-collection indexes** and route queries across them.[^1_63]
- ConStruM’s database context tree builds summaries from **schemas and metadata**, not the underlying row data.[^1_33]

Implications:

### 8.1 Building summaries from metadata and partial content

- Collection selection work constructs **collection representations** from:
    - Sampled documents,
    - Metadata fields,
    - Query logs.[^1_51][^1_50]

For HCR:

- For each external source (API, DB, repo, document store), construct leaves based on:
    - **Metadata**: name, description, owner, data schema, endpoint paths, table names.
    - **Sampled content**: a small, periodically refreshed sample of records/documents.
    - **Historical queries** hitting that source (if available).
- Node summaries higher up in the tree should then:
    - Reflect **what kinds of questions this subtree can answer** based on metadata and samples.
    - Enumerate key entities/IDs that appear in that source.


### 8.2 Content that changes independently

- In federated search, result merging and collection selection must account for **drift in collection content**; representations need periodic refresh.[^1_50][^1_51]
- Dynamic community detection and topic modeling show that incremental updates can keep the index structure roughly aligned with the data.[^1_28][^1_29][^1_20]

For HCR:

- Recompute **leaf-level embeddings and metadata summaries** on a schedule or upon change signals (e.g., schema evolution, major codebase changes).
- Use those updates to **update parent summaries** via incremental summarization without full tree rebuild, unless drift beyond a threshold is detected.


### 8.3 Leaves that are not fully available at construction time

- Federated search often relies on **sparse, partial representations** for some collections, only accessing full content at query time.[^1_51][^1_50]

For HCR:

- Allow **placeholder leaves**:
    - Represent an external system with only metadata yet.
    - Summaries for such branches explicitly state uncertainty and offer coarse routing only (“misc external source X”).
    - As more content is sampled, refine both leaf representations and parent summaries.

***

## 9. Concrete construction strategy for HCR

Given all of the above, here is a concrete, end‑to‑end proposal tailored to your constraints.

### 9.1 Units and preprocessing

1. **Decompose content**:
    - Split large documents/repos into **semantic units**:
        - Sections, functions, API endpoints, tables, tickets, etc.
    - For external sources, define units as:
        - APIs: endpoint + resource.
        - DBs: tables/views; maybe major column groups (as in ConStruM).[^1_33]
        - Repos: modules/packages.
2. **Represent each unit** with:
    - Dense embedding (for semantic similarity).
    - Sparse representation (BM25 indices over descriptive fields).
    - Metadata: type, owner, system, timestamps.
3. **Tag multi-topic candidates**:
    - Use LDA/BERTopic or simple cluster variance heuristics to detect units that span multiple themes (e.g., very high entropy topic distributions).[^1_22][^1_26][^1_23]

### 9.2 Tree backbone: top‑down divisive clustering

1. **First-level partition (depth 1)**:
    - Use a combination of:
        - Coarse BERTopic-like thematic clustering over unit embeddings.[^1_26][^1_25]
        - LLM‑suggested **facets** for the corpus (e.g., “product area,” “infrastructure vs application,” “org/process vs code”).[^1_31][^1_30]
    - Implement as **k‑means or bisecting k‑means** in embedding space, but:
        - Use facet information as additional features or guidance.
        - Choose branching factor 8–12.
2. **Second-level partition (depth 2 or 3)**:
    - For each internal node:
        - Cluster its children (units or subclusters) again with k‑means/GMM, targeting 6–12 children.
        - Stop when:
            - Node’s descendants fit in your downstream retrieval budget, or
            - Cluster compactness (internal metrics) is high enough, or
            - Depth limit (3) reached.
3. **Multi-topic handling at construction**:
    - For units flagged multi-topic:
        - Allow assignment to up to 2 parents at each level (controlled duplication).
        - Let an LLM review a small sample of ambiguous units and their nearest candidate clusters to make final assignment decisions where scores are close.

### 9.3 Summaries and representations

For each internal node:

1. **Gather child evidence**:
    - Sample child units and their metadata (or summarized proxies for external leaves).
    - Extract:
        - Frequent terms (TF‑IDF / c‑TF‑IDF as in BERTopic).
        - Entities and identifiers (names, IDs, endpoints, tables) via a lightweight NER/regex pipeline, optionally LLM-verified.
2. **Generate a structured, contrastive summary** with an LLM prompt that includes:
    - Parent context (its own summary if existing).
    - Brief descriptions of sibling nodes (for contrast).
    - Instructions to:
        - Describe what the branch **covers** and what it explicitly **does not** (relative to siblings).
        - Enumerate key entities/identifiers and typical queries.
        - Keep narrative concise (e.g., ≤60 tokens).
3. **Store both**:
    - Prose text (for semantic embeddings).
    - Structured fields: `key_entities`, `key_terms`, `includes`, `excludes`, etc.
4. **Represent summaries** as:
    - A single dense embedding for coarse matching.
    - A small set (e.g., 8–16) of **multi-vectors** from:
        - Entity names, schema identifiers, and rare terms.
    - A sparse term index (BM25) over `key_terms` and `key_entities`.

This directly supports your hybrid BM25+dense scoring with better preservation of detail hooks.

### 9.4 Traversal and cross‑branch mitigation

- Use a **beam search** similar to LATTICE:
    - At each level, expand the top‑k nodes by hybrid score (BM25 + dense + multi-vector-late-interaction if used).
    - Apply **cross-sibling calibration** by comparing children across siblings and previously visited nodes as in LATTICE’s path relevance estimation.[^1_8]
- Use **HIRO‑style thresholds** to prune obviously irrelevant branches, with care not to prune early under uncertainty.[^1_45][^1_46]
- Allow explicit **multi-path expansion**:
    - For ambiguous queries or those with broad/bimodal similarity, keep multiple branch candidates to the leaf level if token budget allows.


### 9.5 Maintenance

- **Incremental insertion** using existing scoring cascade to find insertion branches.
- **Local subtree rebuild** when:
    - Child count of a node > b_max.
    - Summary coverage metrics or routing accuracy fall below thresholds.
    - Underlying external source schemas change significantly.
- For graph-based secondary indices (e.g., entity graph for global queries), use **dynamic Leiden** to update communities over time.[^1_20]


### 9.6 Evaluation loop

- Maintain a held-out **routing test set** of queries with known relevant leaves.
- For each tree version, compute:
    - **Per-level routing accuracy**: fraction of queries where relevant path survives each level.
    - Overall routing success (before leaf-level reranking).
    - **Sibling distinctiveness** metrics and summary coverage of rare entities.
    - Dasgupta-like cost over a similarity graph built from query–leaf co-relevance.[^1_62][^1_52]
- Use these metrics to:
    - Select clustering hyperparameters (k per level, thresholds).
    - Compare alternative tree-construction pipelines (pure k‑means vs. LLM-guided facets, degree of overlap, etc.).

***

## 10. Established vs speculative elements

To make the frontier explicit:

- **Well-supported by literature**:
    - Shallow+wide hierarchies to limit error compounding.
    - Importance of summary quality and multi-granularity representations (RAPTOR, LATTICE, HIRO-index).[^1_9][^1_3][^1_1]
    - Benefits of soft clustering and overlapping communities for multi-topic data.[^1_22][^1_17][^1_2]
    - Multi-vector/ColBERT representations preserving detail hooks.[^1_35][^1_36][^1_38]
    - Utility of LLMs for summarization, labeling, and multi-aspect encodings.[^1_10][^1_30][^1_9][^1_1]
    - Dynamic clustering and community detection techniques (OHAC, PERCH, dynamic Leiden).[^1_55][^1_54][^1_20]
    - Federated search patterns for indexing external collections via metadata/sample-based representations.[^1_50][^1_51]
- **Partially supported / extrapolated**:
    - Contrastive summarization for routing (supported in spirit by taxonomy generation and contrastive summarization work but not tested for hierarchical retrieval).[^1_39][^1_30]
    - Specific structured summary schema (includes/excludes, entities, typical queries).
    - Precise multi-parent constraints (e.g., 2–3 parents per leaf).
    - Using Dasgupta cost and mutual information as tree-quality metrics in IR.
- **Speculative but principled**:
    - Exact target summary lengths and multi-vector counts per node for HCR’s 400‑token budget.
    - Optimal balance between duplication and multi-path traversal under your workload; this will require HCR-specific experiments.
    - Forest+ DAG hybrid as the globally optimal topology; it is a reasonable design hypothesis but not yet a validated pattern for hierarchical RAG.

***

If you’d like, the next step can be to sketch a concrete **implementation plan** for HCR (data structures, build pipeline, and evaluation suite) mapped to your RB‑00x hypotheses, including prompt templates for routing-oriented summaries and test protocols for per-level routing error.
<span style="display:none">[^1_64][^1_65][^1_66][^1_67][^1_68][^1_69][^1_70][^1_71][^1_72][^1_73][^1_74][^1_75][^1_76][^1_77][^1_78][^1_79][^1_80][^1_81][^1_82][^1_83][^1_84][^1_85][^1_86][^1_87][^1_88][^1_89][^1_90]</span>

<div align="center">⁂</div>

[^1_1]: https://arxiv.org/html/2401.18059v1

[^1_2]: https://proceedings.iclr.cc/paper_files/paper/2024/file/8a2acd174940dbca361a6398a4f9df91-Paper-Conference.pdf

[^1_3]: https://arxiv.org/abs/2403.00435

[^1_4]: https://arxiv.org/html/2403.00435v1

[^1_5]: https://www.cl.cam.ac.uk/teaching/1314/InfoRtrv/lecture6.pdf

[^1_6]: https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00703/125483/Hierarchical-Indexing-for-Retrieval-Augmented

[^1_7]: https://nlp.stanford.edu/IR-book/pdf/16flat.pdf

[^1_8]: https://arxiv.org/html/2510.13217v1

[^1_9]: https://arxiv.org/abs/2510.13217

[^1_10]: https://microsoft.github.io/graphrag/index/default_dataflow/

[^1_11]: https://graphrag.com/reference/graphrag/global-community-summary-retriever/

[^1_12]: https://en.wikipedia.org/wiki/Leiden_algorithm

[^1_13]: https://memgraph.com/docs/advanced-algorithms/available-algorithms/leiden_community_detection

[^1_14]: https://en.wikipedia.org/wiki/Louvain_method

[^1_15]: https://www.datacamp.com/tutorial/graphrag

[^1_16]: https://vjs.ac.vn/jcc/article/view/16537

[^1_17]: https://inaoe.repositorioinstitucional.mx/jspui/bitstream/1009/2388/1/205. OClustR- A new graph-based algorithm for overlapping clustering.pdf

[^1_18]: http://www.pertanika.upm.edu.my/resources/files/Pertanika PAPERS/JST Vol. 32 (3) Apr. 2024/16 JST-4622-2023.pdf

[^1_19]: https://aiexpjourney.substack.com/p/graph-rag-an-approach-to-answering

[^1_20]: https://arxiv.org/html/2405.11658v4

[^1_21]: https://arxiv.org/abs/2404.16130

[^1_22]: https://arxiv.org/pdf/1808.08098.pdf

[^1_23]: https://liu-nlp.ai/text-mining/documents/l4_clustering.handout.pdf

[^1_24]: https://www.geeksforgeeks.org/nlp/topic-modeling-using-latent-dirichlet-allocation-lda/

[^1_25]: https://bertopic.com

[^1_26]: https://arxiv.org/abs/2203.05794

[^1_27]: https://maartengr.github.io/BERTopic/getting_started/hierarchicaltopics/hierarchicaltopics.html

[^1_28]: https://bertopic.readthedocs.io/en/latest/

[^1_29]: https://bertopic.readthedocs.io

[^1_30]: https://www.themoonlight.io/fr/review/context-aware-hierarchical-taxonomy-generation-for-scientific-papers-via-llm-guided-multi-aspect-clustering

[^1_31]: https://www.themoonlight.io/en/review/context-aware-hierarchical-taxonomy-generation-for-scientific-papers-via-llm-guided-multi-aspect-clustering

[^1_32]: https://aclanthology.org/2024.emnlp-industry.54.pdf

[^1_33]: https://arxiv.org/html/2601.20482v1

[^1_34]: https://liner.com/review/llmguided-hierarchical-retrieval

[^1_35]: https://mbrenndoerfer.com/writing/multi-vector-retrievers-fine-grained-token-level-matching-for-neural-information-retrieval

[^1_36]: https://www.answer.ai/posts/colbert-pooling.html

[^1_37]: https://www.linkedin.com/pulse/multi-vector-revolution-how-muvera-transforming-retrieval-geraci-fv2sc

[^1_38]: https://arxiv.org/html/2504.01818v1

[^1_39]: https://github.com/raphsilva/contrastive-summarization

[^1_40]: https://www.flyriver.com/l/contrastive-summarization

[^1_41]: http://arxiv.org/pdf/2310.12361.pdf

[^1_42]: https://aclanthology.org/Y10-1063.pdf

[^1_43]: https://pmc.ncbi.nlm.nih.gov/articles/PMC11222522/

[^1_44]: https://apxml.com/courses/large-scale-distributed-rag/chapter-2-advanced-distributed-retrieval-strategies/multi-vector-colbert-scale-rag

[^1_45]: https://arxiv.org/pdf/2406.09979.pdf

[^1_46]: https://arxiv.org/abs/2406.09979

[^1_47]: https://github.com/krishgoel/hiro

[^1_48]: https://www.emergentmind.com/topics/hierarchical-retrieval-hr

[^1_49]: http://snap.stanford.edu/soma2010/papers/soma2010_3.pdf

[^1_50]: https://www.microsoft.com/en-us/research/wp-content/uploads/2011/01/now.pdf

[^1_51]: https://dl.acm.org/doi/10.1561/1500000010

[^1_52]: https://841.io/doc/diazf-thesis.pdf

[^1_53]: https://theses.gla.ac.uk/76214/1/13833931.pdf

[^1_54]: https://arxiv.org/pdf/1704.01858.pdf

[^1_55]: https://www.arxiv.org/pdf/1909.09667.pdf

[^1_56]: https://people.iith.ac.in/ckm/assets/pdfs/con48.pdf

[^1_57]: https://www.vldb.org/conf/1998/p323.pdf

[^1_58]: https://orca2.tamu.edu/tom/pdfs/icdm02.pdf

[^1_59]: https://towardsdatascience.com/7-evaluation-metrics-for-clustering-algorithms-bdc537ff54d2/

[^1_60]: https://en.wikipedia.org/wiki/Cluster_analysis

[^1_61]: https://aclanthology.org/2025.findings-emnlp.1283.pdf

[^1_62]: https://yonatanlou.github.io/blog/Evaluating-Hierarchical-Clustering/hierarchical-clustering-eval/

[^1_63]: http://vldb.org/pvldb/vol14/p3096-stoddard.pdf

[^1_64]: https://www.themoonlight.io/tw/review/raptor-recursive-abstractive-processing-for-tree-organized-retrieval

[^1_65]: https://chatpaper.com/paper/200267

[^1_66]: https://www.themoonlight.io/en/review/raptor-recursive-abstractive-processing-for-tree-organized-retrieval

[^1_67]: https://huggingface.co/papers/2510.13217

[^1_68]: https://memgraph.com/blog/how-microsoft-graphrag-works-with-graph-databases

[^1_69]: https://www.facebook.com/groups/DeepNetGroup/posts/2593903191002547/

[^1_70]: https://dl.acm.org/doi/pdf/10.1145/72910.73351

[^1_71]: https://arxiv.org/html/2510.24402v1

[^1_72]: http://sigir.hosting.acm.org/wp-content/uploads/2017/06/p0351.pdf

[^1_73]: https://ui.adsabs.harvard.edu/abs/2024arXiv240609979G/abstract

[^1_74]: https://www.themoonlight.io/fr/review/hiro-hierarchical-information-retrieval-optimization

[^1_75]: https://blog.milvus.io/ai-quick-reference/what-is-hierarchical-image-retrieval

[^1_76]: https://webscraping.blog/raptor-rag/

[^1_77]: https://swirlaiconnect.com/unified-vs-federated-vs-metasearch/

[^1_78]: https://www.semanticscholar.org/paper/894d7eeb47e3bce415137f680ba29e9fa9c98b32

[^1_79]: https://arxiv.org/html/2406.09979v1

[^1_80]: https://aclanthology.org/2024.tacl-1.84.pdf

[^1_81]: https://docs.exploratory.io/analytics/topic_model

[^1_82]: https://github.com/LaurentVeyssier/Topic-Modeling-and-Document-Categorization-using-Latent-Dirichlet-Allocation

[^1_83]: https://www.sciencedirect.com/science/article/abs/pii/S002002552300525X

[^1_84]: https://developers.llamaindex.ai/python/framework-api-reference/response_synthesizers/tree_summarize/

[^1_85]: http://sujitpal.blogspot.com/2024/03/hierarchical-and-other-indexes-using.html

[^1_86]: https://paperswithcode.com/paper/hierarchical-indexing-for-retrieval-augmented

[^1_87]: https://llamaindexxx.readthedocs.io/en/latest/module_guides/indexing/index_guide.html

[^1_88]: https://linnk.ai/insight/natural-language-processing/Hierarchical-Indexing-for-Retrieval-Augmented-Opinion-Summarization-by-Tom-Hosking-Hao-Tang-and-Mirella-Lapata-oeQ5QvSZ/

[^1_89]: https://developers.llamaindex.ai/python/framework/module_guides/indexing/index_guide/

[^1_90]: https://github.com/run-llama/llama_index/blob/main/docs/docs/module_guides/indexing/index_guide.md


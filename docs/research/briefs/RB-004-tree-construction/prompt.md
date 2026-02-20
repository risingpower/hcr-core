# RB-004: Tree Construction for Hierarchical Retrieval

**Date:** 2026-02-13
**Status:** Open
**Decision Required:** Yes — tree construction strategy is a core architectural decision
**Related:** H1a (token efficiency), H1b (hybrid superiority), H1c (scoring lever), RB-001 (prior art), RB-002 (theoretical basis), RB-003 (scoring mechanics)

## Context

RB-003 established that **summary quality is the #1 upstream factor** for scoring accuracy in hierarchical retrieval. The cascade scoring architecture (hybrid BM25+dense → cross-encoder rerank) can achieve per-level error rates ε ≈ 0.01–0.02, but only if node summaries clearly differentiate sibling branches and preserve "detail hooks" — rare identifiers, specific terms, and structural markers that enable routing decisions.

This makes tree construction the critical enabler for everything downstream. A poorly constructed tree — with overlapping siblings, vague summaries, or unnatural partitions — structurally caps scoring accuracy regardless of how sophisticated the scorer is. Conversely, a well-constructed tree with clearly differentiated branches makes even simple scoring methods effective.

Previous briefs established:

- **RB-001:** Tree construction is "brittle and dataset-dependent" — clustering algorithm choice dramatically affects performance. No principled method exists for automatically selecting clustering algorithms and parameters. All sources flagged this as an open problem.
- **RB-002:** Shallow wide trees (d=2–3, b=8–12) are strongly preferred over deep narrow trees due to (1-ε)^d error compounding. The tree should be designed for coarse routing reliability, not fine-grained discrimination. Overlapping clusters may be necessary for multi-topic documents.
- **RB-003:** The DPI (Data Processing Inequality) bottleneck means summaries that are "too abstract" are structurally worse for routing than summaries that preserve key details. Summary embeddings systematically underestimate descendant relevance for detail queries. Path-relevance EMA smoothing partially compensates but cannot fix fundamentally poor summaries.

HCR's unique constraints add further requirements:
- **Leaves are external source pointers**, not content stores. The tree is a pure routing index.
- **Hard token budget (<400 tokens)** means the tree must produce candidate sets that are compact and information-dense.
- **The consumer is an agentic system** with an organisational knowledge base that grows over time — dynamic maintenance matters.

## Research Question

How should HCR's tree be constructed to maximise routing accuracy, and what makes a "good" node summary for hierarchical retrieval?

Specifically:

1. **What clustering/partitioning methods produce trees that align well with query-relevance patterns?** Bottom-up agglomerative (RAPTOR), top-down divisive (k-means, bisecting k-means), community detection (Leiden, Louvain — GraphRAG), spectral clustering, LLM-guided clustering — what does the landscape look like? For each, characterise: (a) what signal it uses, (b) how it handles multi-topic documents, (c) resulting tree shape (depth, branching factor, balance), (d) computational cost, (e) empirical performance where available.

2. **What makes a good node summary for routing?** RB-003 identified summary quality as the #1 upstream factor. But what specific properties make a summary "good" for routing decisions? Distinctiveness from siblings? Preservation of rare entities and detail hooks? Explicit boundary descriptions ("this branch covers X but NOT Y")? Structured format (keywords + narrative)? What does the evidence say about summary generation strategies that optimise for routing rather than reading comprehension?

3. **How should multi-topic and cross-cutting content be handled?** RB-001 and RB-002 identified cross-branch queries as the #1 failure mode. Documents or content that spans multiple topics violate the assumption that each piece belongs in one branch. Soft clustering (topic models, mixed membership), content duplication across branches, link structures between siblings — what are the options and their tradeoffs? Does any system solve this well?

4. **What tree topology is optimal for HCR's parameters?** RB-002 established shallow+wide (d=2–3, b=8–12). But within those bounds: balanced vs unbalanced trees? Fixed vs variable branching factor? Homogeneous vs heterogeneous granularity across branches? Does any theory or empirical work optimise topology for routing accuracy under token budgets?

5. **How should the tree be maintained as content changes?** The knowledge base grows over time. Full reconstruction is expensive. Incremental insertion (add new content to closest existing branch), lazy rebalancing (reconstruct subtrees that exceed quality thresholds), online clustering — what methods exist? How do they affect tree quality over time? RB-001 confirmed this is essentially unaddressed in the literature.

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
- **GraphRAG:** Leiden community detection on entity-relationship graphs. Produces hierarchical community structure. Extremely expensive ($650/100 queries for LLM entity extraction). Graph structure captures relationships that flat clustering misses.
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
- **Summary quality is the #1 upstream factor for scoring accuracy.** No amount of scoring sophistication compensates for poorly differentiated summaries.
- **The DPI bottleneck means summaries lose detail.** Detail-query-against-thematic-summary is the structural failure case. Summaries must preserve "detail hooks."
- **Path-relevance EMA partially compensates.** `p(v) = α · p(parent) + (1-α) · calibrated_score(v)` smooths scores across depth. But it cannot recover information that was never in the summary.
- **ColBERT/late-interaction preserves detail hooks.** Multi-vector representations keep rare terms and specific identifiers that single-vector embeddings wash out. Relevant to summary representation, not just scoring.

## Prompt for Sources

> I am designing the **tree construction strategy** for a hierarchical context retrieval system (HCR) that retrieves context for LLMs under a hard token budget (<400 tokens). The system uses a shallow tree (depth 2–3, branching factor 8–12) where internal nodes hold summaries and leaf nodes point to external data sources. Queries enter at the root and are routed through the tree via a cascade scorer (hybrid BM25+dense → cross-encoder rerank, achieving per-level error ε ≈ 0.01–0.02).
>
> Our prior research established critical constraints:
> - **Summary quality is the #1 upstream factor** for scoring accuracy. Poorly differentiated summaries structurally cap routing performance regardless of scorer sophistication. (RB-003)
> - **Error compounds as (1-ε)^d** across depth, making shallow wide trees essential. (RB-002)
> - **Summaries are lossy channels** (Data Processing Inequality) — they systematically lose detail. Detail queries against thematic summaries is the structural failure case. (RB-002, RB-003)
> - **Cross-branch queries are the #1 failure mode** — when relevant content spans multiple branches, top-down routing misses evidence. (RB-001, RB-002)
> - **The cluster hypothesis holds for narrow structured domains but fails for broad collections** — 8% vs 46% failure rates (Voorhees 1985). (RB-002)
> - **Leaves are external source pointers**, not content stores. The tree is a pure routing index.
>
> I need a comprehensive analysis of tree construction. Specifically:
>
> 1. **Landscape of tree construction methods.** What methods partition a corpus into a tree suitable for hierarchical retrieval? Bottom-up agglomerative (RAPTOR/GMM), top-down divisive (bisecting k-means), community detection (Leiden/Louvain — GraphRAG), spectral methods, LLM-guided clustering, topic models (LDA/BERTopic), and any others. For each: (a) what signal does it partition on, (b) how does it handle multi-topic content, (c) what tree shape does it produce, (d) computational cost for 10K–100K chunks, (e) empirical quality where reported.
>
> 2. **Summary generation for routing quality.** What makes a node summary effective for *routing* (deciding "does my answer lie below this node?") as opposed to *reading comprehension* (understanding a topic)? Specific questions: Does contrastive summarisation ("this branch covers X, NOT Y") help? Should summaries preserve rare entities and identifiers ("detail hooks")? Does structured format (keywords + entities + narrative) outperform pure prose? Is there evidence on summary length vs routing accuracy? What about multi-vector representations (ColBERT-style) at the summary level — do they preserve detail hooks better than single embeddings?
>
> 3. **Handling multi-topic and cross-cutting content.** Content that belongs in multiple branches is the #1 structural failure mode. Options include: soft clustering (content appears in multiple branches), link structures between related nodes, query-time multi-path expansion, content decomposition (split multi-topic documents into single-topic chunks before clustering), and redundant leaf placement. What works? What are the storage and consistency tradeoffs? Does any system solve this convincingly?
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

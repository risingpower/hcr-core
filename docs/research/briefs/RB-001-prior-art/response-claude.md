# RB-001: Prior Art Survey — Claude Response

# Hierarchical retrieval for LLMs: a prior art survey

**Tree-based retrieval is an active and rapidly growing subfield of RAG, with at least 12 distinct systems published since early 2024 — but no existing system matches HCR's specific combination of elimination-based pruning, parallel branch traversal, and hard token budgeting.** The closest analog is LATTICE (UT Austin, October 2025), which shares the philosophy of LLM-scored tree navigation with logarithmic complexity but differs in traversal strategy (best-first sequential vs. parallel elimination) and lacks a fixed token target. RAPTOR (Stanford, ICLR 2024) established the foundational approach of recursive clustering-and-summarization trees, while Microsoft's GraphRAG spawned a family of graph-hierarchy methods. Pre-LLM precedents run deep — from B-trees and hierarchical softmax to the cluster hypothesis of 1971 — providing strong theoretical grounding for the approach. The field's most significant gap: **no comprehensive head-to-head evaluation exists** comparing hierarchical vs. flat retrieval across all metrics on shared benchmarks.

---

## The twelve systems that define the space

The table below maps the landscape. Systems range from peer-reviewed conference papers to recent preprints, covering tree-structured, graph-hierarchical, and agentic approaches.

| System | Year / Venue | Hierarchy type | Construction | Traversal | Pruning mechanism |
|--------|-------------|---------------|-------------|-----------|-------------------|
| **RAPTOR** | 2024 / ICLR | Summary tree | Bottom-up: GMM+UMAP clustering → LLM summarization | Collapsed (all-level) or top-down | Token budget on collapsed; top-k per layer on traversal |
| **LATTICE** | Oct 2025 / arXiv | Semantic tree | Bottom-up agglomerative or top-down divisive, LLM summaries | Top-down best-first beam search | Calibrated path relevance scores |
| **HIRO** | Jun 2024 / arXiv | Uses RAPTOR tree | Same as RAPTOR | Top-down DFS | Selection threshold + delta threshold |
| **GraphRAG** | Apr 2024 / arXiv | Community hierarchy | LLM entity extraction → Leiden clustering → community summaries | Global (map-reduce) / Local (entity fan-out) | Community-level filtering |
| **HiRAG** | Mar 2025 / EMNLP 2025 | Hierarchical KG | Multi-layer KG with bridge entities | Hybrid: local + global + bridge | Bridge path pruning |
| **ArchRAG** | Feb 2025 / arXiv | Attributed community graph | Semantic+structural community detection → C-HNSW index | Hierarchical index search | Adaptive filtering |
| **TreeRAG** | 2025 / ACL 2025 | Document tree | Tree-chunking preserving document structure | Root-guided top-down | Branch selection |
| **CFT-RAG** | Jan 2025 / arXiv | Entity forest | Entity hierarchical trees + Cuckoo Filter | Entity matching via Cuckoo Filter | Filter-based elimination |
| **HAT** | Jun 2024 / arXiv | Dialogue aggregate tree | Recursive aggregation of dialogue turns | GPT-based conditional top-down traversal | Conditional path selection |
| **T-Retriever** | Jan 2026 / arXiv | Encoding tree (graphs) | Semantic-structural entropy optimization | Hierarchical partition traversal | Adaptive compression |
| **A-RAG** | Feb 2026 / arXiv | Multi-granularity index | Lightweight chunk+embed | Agent-driven multi-tool | Agent autonomously decides |
| **LeanRAG** | Aug 2025 / arXiv | Bottom-up graph | Fine-grained seed retrieval → LCA traversal | Bottom-up to lowest common ancestor | Inter-cluster path pruning |

Three of these are peer-reviewed (RAPTOR at ICLR 2024, HiRAG at EMNLP 2025, TreeRAG at ACL 2025). The rest are preprints or under review. Commercial implementations exist in LlamaIndex (Tree Index, Auto-Merging Retriever, HierarchicalNodeParser) and LangChain (ParentDocumentRetriever), though these are framework features rather than novel research systems.

---

## How each major system actually works

**RAPTOR** (Sarthi, Abdullah, Tuli, Khanna, Goldie, Manning — Stanford, January 2024, ICLR 2024) builds its tree bottom-up. Text is chunked into ~100-token segments, embedded with SBERT, then clustered using Gaussian Mixture Models after UMAP dimensionality reduction. The Bayesian Information Criterion determines optimal cluster count. Clustered chunks are summarized by an LLM (GPT-3.5-turbo), achieving **72% compression per level**. Summaries are re-embedded, and the cycle repeats until clustering is infeasible. Critically, RAPTOR uses **soft clustering** — nodes can belong to multiple clusters, preventing premature information loss. The paper defines two retrieval modes: tree traversal (top-down, selecting top-k nodes per layer) and collapsed tree (flattening all nodes across all levels into a single pool and retrieving by cosine similarity). **The collapsed tree outperforms tree traversal in most experiments**, which is a significant finding — it suggests that strict top-down navigation may sacrifice relevant information at unexpected abstraction levels. On QuALITY, RAPTOR + GPT-4 achieved **82.6% accuracy**, a 20-point absolute gain over prior state-of-the-art. On QASPER, it reached **55.7% F-1** with GPT-4, beating DPR by 2.7 points and BM25 by 5.5 points.

**LATTICE** (Gupta, Chang, Bui, Hsieh, Dhillon — UT Austin and UCLA, October 2025, arXiv 2510.13217) represents the most significant advance and is the **closest existing work to HCR**. A critical correction: LATTICE is **not from MIT** as initially reported — lead author Nilesh Gupta is a PhD student at UT Austin advised by Inderjit Dhillon. LATTICE organizes a corpus into a semantic tree offline using either bottom-up agglomerative or top-down divisive clustering, with LLM-generated summaries at internal nodes (branching factor ~10–20). The key innovation is making the **LLM the core search mechanism**: at query time, the LLM acts as an active traversal agent, performing listwise relevance judgments at each node via in-context reasoning. It uses a greedy best-first beam search (beam width B=2), evaluating approximately **250 documents per query**. The most important technical contribution is **calibrated latent relevance scoring**: raw LLM relevance judgments are noisy and context-dependent, so LATTICE calibrates scores across branches using sibling comparisons and aggregates them via an exponentially weighted moving average along the path from root. Ablations show this calibration is essential — without it, performance degrades drastically. On the BRIGHT benchmark (12 reasoning-intensive tasks, corpora up to 420K documents), LATTICE achieved **74.8% Recall@100** zero-shot, outperforming BM25 by +9.5 points and fine-tuned ReasonIR-8B by +4.0 points. It achieves **logarithmic search complexity** — the same theoretical property targeted by HCR.

**HIRO** (Goel & Chandak, June 2024, arXiv 2406.09979) is a querying method built on RAPTOR's tree, not a new tree construction approach. It replaces RAPTOR's collapsed tree with DFS-based recursive traversal using two thresholds: a **Selection Threshold (S ≈ 0.6)** governing which branches to explore, and a **Delta Threshold (Δ ≈ 0.08)** measuring whether a child node adds sufficient relevance improvement over its parent. If the child doesn't sufficiently improve, the parent's text is returned and the branch is pruned. This is the **closest published analog to HCR's elimination principle** — it explicitly prunes branches based on scoring — though it uses embedding similarity rather than LLM-based scoring and traverses via DFS rather than parallel execution.

**GraphRAG** (Edge et al. — Microsoft Research, April 2024, arXiv 2404.16130) takes a fundamentally different approach by building an entity-relationship knowledge graph from the corpus via LLM extraction, then applying the **Leiden algorithm** for hierarchical community detection. Communities at each level receive LLM-generated summaries. Global queries use a map-reduce pattern over community summaries; local queries fan out from matched entities. GraphRAG excels at holistic sensemaking but suffers from extreme cost: processing 100 questions on MultiHop-RAG costs approximately **$650 and 106M tokens** with GPT-4o. This cost problem spawned ArchRAG (achieving **250× token savings**) and LightRAG.

**HiRAG** (Huang et al., March 2025, EMNLP 2025 Findings) addresses a key limitation of graph-based hierarchies: the gap between local entity-level knowledge and global community-level knowledge. It introduces **bridge entities** that connect these levels, enabling retrieval that spans abstraction layers. Ablation studies confirm the bridge level is essential — removing it causes significant performance drops. HiRAG outperforms GraphRAG, LightRAG, and naive RAG across all tested datasets.

---

## Deep roots: pre-LLM hierarchical retrieval

The theoretical foundations for hierarchical retrieval predate LLMs by decades. Understanding these precedents clarifies what is genuinely novel in the current wave.

**The cluster hypothesis** (Jardine & van Rijsbergen, 1971) provides the theoretical justification for the entire approach: "closely associated documents tend to be relevant to the same requests." If relevant documents cluster in representation space, hierarchical structures that capture these clusters enable efficient navigation. This hypothesis has been empirically validated for modern embedding spaces.

**Hierarchical softmax** (Morin & Bengio, 2005; adopted in word2vec by Mikolov et al., 2013) is the most direct computational precursor. It converts an O(|V|) vocabulary search into O(log|V|) by arranging words as leaves of a binary Huffman tree, with learned sigmoid classifiers at each internal node routing predictions left or right. This is precisely the principle HCR applies to document retrieval: a large corpus navigated via a tree of routing decisions, each powered by a learned model.

**HNSW** (Malkov & Yashunin, 2016/2020) — the dominant algorithm in production vector databases (Pinecone, Weaviate, Qdrant) — already uses hierarchy. It builds a multi-layer proximity graph where the top layer contains a sparse subset of elements for coarse navigation, and each lower layer adds more elements for finer resolution. Search starts at the top layer's entry point and greedily descends. This achieves logarithmic complexity and is, conceptually, hierarchical retrieval — though it operates on raw embeddings rather than semantic abstractions. A cautionary finding: Dobson et al. (2024) showed HNSW's hierarchy primarily benefits low-dimensional data (d < 32) and may be unnecessary in high dimensions (d > 32), where hub nodes in flat graphs provide equivalent navigational efficiency.

**Multi-stage retrieval pipelines** (BM25 → neural reranker → fine retrieval) represent the practical realization of coarse-to-fine search in production IR. Bing web search fans out to 1000+ shards, merges ~15,000 candidates, reranks top 1,000 with a learned model in 30–50ms, then applies neural reranking on the top 50. This cascade is elimination-based retrieval without explicit tree structure — each stage narrows the candidate set using progressively more expensive scoring.

Other significant precedents include **B-trees** (Bayer & McCreight, 1972) demonstrating logarithmic search with high-fanout balanced trees; **cover trees** (Beygelzimer et al., 2006) achieving O(c¹² log n) query time based on intrinsic rather than ambient dimensionality; **hierarchical text classification** (Dumais & Chen, 2000) routing documents through a taxonomy via cascaded classifiers; and **faceted classification** (Ranganathan, 1933) demonstrating that real-world queries require multi-dimensional organization, not single-inheritance hierarchies. The **Dewey Decimal Classification** (1876) and **Library of Congress Classification** proved that hierarchical knowledge organization scales to millions of items, while their limitations — rigidity, single-inheritance, inability to handle cross-cutting topics — foreshadow the open problems in modern hierarchical retrieval.

---

## What the benchmarks actually show

Empirical evidence consistently favors hierarchical retrieval over flat approaches for complex queries, but with important caveats. **No single comprehensive evaluation compares hierarchical vs. flat retrieval across all metrics on shared benchmarks** — evidence is fragmented across papers with different experimental setups.

The strongest evidence comes from RAPTOR's evaluations on three benchmarks. On **QuALITY** (multiple-choice QA over ~5000-token passages), RAPTOR + GPT-4 achieved **82.6% accuracy** vs. DPR's 60.4% and BM25's 57.3% with GPT-3. On **QuALITY-HARD**, it outperformed the previous best (CoLISA) by **21.5 points**. On **QASPER** (F-1 on NLP papers), RAPTOR + GPT-4 reached **55.7%** vs. DPR's 53.0% and BM25's 50.2%. These are peer-reviewed results from ICLR 2024. A follow-up study (Frontiers, 2025) found that replacing RAPTOR's GMM clustering with Adaptive Graph Clustering (Leiden algorithm) improved QASPER LLM Score from **3.08 → 3.23** and Token F1 from **6.45 → 7.45%**, demonstrating that clustering quality critically affects tree quality.

LATTICE's evaluation on BRIGHT provides the clearest evidence for logarithmic-complexity hierarchical retrieval. Its **74.8% Recall@100** zero-shot is competitive with fine-tuned state-of-the-art (DIVER-v2 at 52.2 nDCG@10 vs. LATTICE's 51.6 on StackExchange subsets). Crucially, LATTICE shows that hierarchical traversal **continues improving with more compute** while flat reranking plateaus — a scaling property that favors tree-based approaches for large corpora.

Token efficiency gains are substantial. **ArchRAG achieves 250× token reduction** compared to GraphRAG (from 1,394M to 5.1M tokens on HotpotQA). **LeanRAG produces context 46% smaller** than baselines while achieving state-of-the-art on most metrics. **CFT-RAG delivers 100–138× speedup** over naive tree retrieval while maintaining generation quality. These numbers suggest that the efficiency thesis underlying HCR — precise context in under 400 tokens — is achievable, though no published system explicitly targets a fixed token budget.

**Where hierarchical retrieval struggles:** HopRAG (2025) found that RAPTOR "mainly focuses on hierarchical logical relations among passages but cannot capture other kinds of relevance," achieving 9.94% lower accuracy than HopRAG on multi-hop QA. A-RAG's analysis showed **40% failure rate on MuSiQue** and **71% on 2WikiMultiHopQA** due to entity confusion when information about the same entity spans multiple branches. RAPTOR's own ablation revealed its collapsed tree (which effectively reverts to augmented flat retrieval) outperforms strict tree traversal — a result that should give pause to purely top-down designs.

---

## Five open problems the field has not solved

**1. Tree construction remains brittle and dataset-dependent.** Performance varies dramatically with clustering algorithm choice — the Frontiers RAPTOR study found Adaptive Graph Clustering significantly outperformed GMM, which outperformed agglomerative clustering (47.50%) and HDBSCAN (49.00%). Optimal semantic chunking thresholds are dataset-specific (τ=0.7 for QuALITY). LLM-generated summaries at internal nodes lose granular details (specific entities, relationships), making tree structures less effective for fact-intensive retrieval. No principled method exists for automatically selecting clustering algorithms and parameters for a given corpus.

**2. Cross-branch queries cause systematic failures.** LATTICE explicitly identifies this: "LLM's relevance judgments are noisy, context-dependent, and unaware of the hierarchy, making cross-branch and cross-level comparisons difficult." When a query requires information from multiple tree branches (common in multi-hop reasoning), top-down traversal can miss relevant information that sits in a branch pruned early. LeanRAG's "semantic islanding" diagnosis is apt — hierarchical methods create isolated communities that inhibit cross-community reasoning. No system fully solves this without falling back to flat retrieval.

**3. Dynamic hierarchy maintenance is essentially unaddressed.** LATTICE's key limitation is that pre-computed summaries don't update when documents change — parent nodes become misleading. CFT-RAG's Cuckoo Filters support dynamic element insertion/deletion, but the tree structure itself requires rebuilding. **No published work systematically addresses incremental hierarchy maintenance** (insertions, deletions, updates) without full reconstruction. Most systems treat indexing as a one-time offline process, which is untenable for corpora that change frequently.

**4. Scoring accuracy at internal nodes degrades with abstraction.** Summary embeddings may not inhabit the same embedding space as original text. RAPTOR uses identical SBERT embeddings across all levels, creating potential semantic drift at higher abstraction layers. LATTICE sidesteps this by using LLM reasoning rather than embedding similarity, but at higher computational cost. **No published work systematically studies embedding model behavior on summary nodes vs. original text** or proposes specialized embedding models for hierarchical structures.

**5. Optimal tree topology is unexplored.** No systematic study examines how tree depth, branching factor, and compression ratio interact across different corpus sizes, domains, and query types. LATTICE uses branching factor ~10–20. EcphoryRAG found performance peaks at depth=2 for HotpotQA. HiRAG observed cluster sparsity increasing with more layers. These are isolated data points, not a coherent understanding of the design space.

---

## Where HCR diverges from existing work

HCR's specific combination of design choices — elimination-based pruning, parallel branch traversal, hard token budgeting (~400 tokens), and leaf nodes resolving to external data sources — does not appear in any published system. The closest analogs and key differences:

- **vs. LATTICE** (closest overall): LATTICE uses sequential best-first beam search; HCR proposes parallel traversal of surviving branches. LATTICE has variable token output; HCR targets a hard budget. LATTICE uses calibrated LLM reasoning for scoring; HCR's scoring mechanism (as described) focuses on branch elimination rather than path relevance accumulation. LATTICE's tree contains document text at leaves; HCR's leaves resolve to external data sources — a meaningful architectural difference that makes HCR more of a routing/indexing layer than a self-contained retrieval system.

- **vs. HIRO** (closest on pruning): HIRO uses delta-threshold pruning on RAPTOR's tree via DFS — conceptually similar to elimination, but sequential rather than parallel, and uses embedding similarity rather than potentially richer scoring.

- **vs. RAPTOR** (foundational): RAPTOR's best mode (collapsed tree) abandons tree traversal entirely in favor of all-level flat retrieval. HCR commits to tree traversal, betting that well-designed elimination can outperform RAPTOR's pragmatic retreat to flatness.

- **vs. A-RAG** (agentic): A-RAG gives the LLM agent hierarchical tools but lets it decide strategy autonomously. HCR prescribes the traversal algorithm, using the tree structure as a hard constraint rather than a suggestion.

Three aspects of HCR appear genuinely novel in the literature:

1. **Elimination semantics rather than selection semantics.** Existing systems select the top-k most relevant branches (positive selection). HCR eliminates branches that fail to meet a relevance threshold (negative selection). This is a subtle but meaningful difference — elimination is more conservative and may prevent the "winner-take-all" failure mode where a dominant but wrong branch captures all attention.

2. **Hard token budget targeting.** No published system explicitly optimizes traversal to produce context within a specific token bound. HIRO reduces tokens but doesn't target a number. LATTICE evaluates ~250 documents per query with variable output. A hard budget of ~400 tokens is a significantly tighter constraint that would require the tree to function as a precision instrument.

3. **Leaves as external source pointers.** In RAPTOR, LATTICE, and all other systems, leaf nodes contain document text directly. HCR's leaves resolving to external data sources makes the tree a pure routing index rather than a content store — closer to a B-tree's separation of keys from data than to a self-contained document tree.

---

## Conclusion: the opportunity is real but nuanced

The evidence is clear that hierarchical retrieval outperforms flat RAG for complex, thematic, and multi-hop queries — gains of **2–20 percentage points** on standard QA benchmarks are reproducible across multiple independent systems. The theoretical grounding is strong, with the cluster hypothesis, logarithmic search complexity, and multi-resolution representation all well-established. HCR's independent derivation from first principles converges on a design space that the academic community has been actively exploring since early 2024, which validates the intuition.

The nuanced reality is that **strict top-down tree traversal has not yet convincingly outperformed augmented flat retrieval** in all cases — RAPTOR's own experiments show its collapsed tree (which abandons strict traversal) beats its tree traversal mode. This suggests the key challenge for HCR is not whether tree structure helps organize knowledge, but whether elimination-based top-down traversal can be made reliable enough that it doesn't sacrifice relevant information sitting in prematurely pruned branches. LATTICE's calibration mechanism and HIRO's delta thresholds are both attempts to solve this problem; HCR's parallel traversal of surviving branches may offer a third approach. The field's biggest open problems — brittle tree construction, cross-branch queries, dynamic maintenance, and internal-node scoring accuracy — will also be HCR's challenges. The absence of a comprehensive benchmark comparing hierarchical approaches on shared metrics represents both a gap in the field and an opportunity for HCR to establish evaluation standards alongside its system contribution.
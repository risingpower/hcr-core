# RB-002: Theoretical Basis — Elimination vs Similarity Retrieval

**Date:** 2026-02-13
**Status:** Open
**Decision Required:** No — but findings directly affect H1 confidence and may reshape HCR's design
**Related:** H1 (core hypothesis), RB-001 (prior art survey), RB-003 (scoring mechanics)

## Context

RB-001 (prior art survey) established that hierarchical retrieval consistently outperforms flat RAG on complex, long-document, multi-hop reasoning tasks — with accuracy gains of 2–20 percentage points across multiple independent systems. However, a critical finding emerged: **RAPTOR's collapsed tree mode (flat retrieval over all nodes including multi-level summaries) outperforms its own strict tree traversal mode.** This means the tree structure helps as an enrichment mechanism (creating useful multi-level representations), but top-down traversal through the tree may actually lose relevant information compared to just searching broadly across all enriched representations.

This directly challenges HCR's core bet: that elimination-based top-down traversal through a tree is the right retrieval strategy. The question is no longer "does hierarchy help?" (it does) — it's "does navigating the hierarchy top-down outperform simply using the hierarchy to enrich a flat search?"

HCR proposes retrieval by elimination: a query enters at the root, branches are scored and pruned at each level, surviving branches are traversed in parallel, and only leaf nodes that survive all pruning stages contribute to the final context. This is fundamentally different from retrieval by similarity (nearest-neighbour search over a flat pool of vectors). But it's also different from RAPTOR's collapsed tree (flat similarity search over multi-level representations). We need to understand the theoretical conditions under which each approach wins.

## Research Question

Under what conditions does elimination-based top-down traversal through a hierarchy outperform:
1. **Flat similarity retrieval** (standard RAG — nearest-neighbour over chunk embeddings)?
2. **Enriched flat retrieval** (RAPTOR collapsed tree — flat similarity over multi-level representations)?

Specifically:
1. What does information theory, decision theory, or search theory say about when hierarchical elimination is optimal vs suboptimal?
2. What are the formal conditions (properties of the corpus, query distribution, tree structure) that determine whether top-down elimination preserves recall or loses it?
3. Is there a theoretical framework for reasoning about the recall/precision/token-efficiency tradeoff in tree-based elimination?
4. What is the relationship between tree quality (summary fidelity, clustering tightness, balanced branching) and elimination reliability?
5. Can the RAPTOR collapsed-tree result be explained theoretically — and can the conditions where it holds be precisely characterised?

## Scope

**In scope:**
- Information-theoretic analysis of hierarchical vs flat search (entropy, mutual information, channel capacity)
- Decision-theoretic frameworks for sequential elimination (optimal stopping, sequential hypothesis testing)
- Search theory: when does branch-and-bound outperform exhaustive search?
- Formal analysis of recall loss under pruning — error propagation in tree traversal
- The cluster hypothesis and its conditions — when does it hold, when does it break?
- Conditions under which RAPTOR's collapsed tree should theoretically outperform tree traversal
- Any formal proofs or bounds on hierarchical retrieval error

**Out of scope:**
- Specific implementation details of existing systems (covered in RB-001)
- Scoring mechanism specifics (deferred to RB-003)
- Tree construction algorithms (deferred to RB-004)
- Benchmarking methodology (deferred to RB-006)

## What We Already Know

From RB-001:
- **RAPTOR's collapsed tree outperforms its tree traversal mode** — the strongest counter-evidence to strict top-down elimination. The collapsed tree searches all nodes (leaves + summaries at all levels) by flat similarity, effectively using the tree only for enrichment.
- **LATTICE addresses scoring noise** via calibrated latent relevance scoring. Raw LLM relevance judgments are noisy and context-dependent, requiring cross-branch calibration. This suggests scoring quality is critical to elimination reliability.
- **HIRO's delta threshold** prunes branches only when children don't sufficiently improve over parents — a form of conditional elimination that avoids aggressive pruning.
- **The cluster hypothesis** (Jardine & van Rijsbergen, 1971): closely associated documents tend to be relevant to the same requests. This is the theoretical foundation for hierarchical retrieval, but its conditions and limits are poorly characterised.
- **Cross-branch queries** are the #1 failure mode: when relevant information spans multiple tree branches, top-down elimination systematically misses some of it.
- **Hierarchical softmax** (Morin & Bengio, 2005) is a direct computational precursor — converting O(|V|) search to O(log|V|) via learned binary classifiers at internal nodes.
- **Multi-stage retrieval pipelines** (BM25 → reranker → fine retrieval) are elimination-based retrieval without explicit tree structure — each stage narrows the candidate set using progressively more expensive scoring.
- **No formal bounds exist** on recall loss from tree pruning in the LLM retrieval context. All thresholds are empirically tuned.

## Prompt for Sources

> I am investigating the theoretical foundations of **retrieval by elimination** (top-down traversal through a hierarchical tree, scoring and pruning branches at each level) vs **retrieval by similarity** (nearest-neighbour search over a flat vector pool) for delivering context to LLMs.
>
> A key empirical finding motivates this: RAPTOR (ICLR 2024) builds a tree of recursive summaries over document chunks, but its "collapsed tree" mode — which flattens all nodes across all levels and performs standard similarity search over them — **outperforms its own strict tree traversal mode.** This suggests that the tree structure helps as enrichment (creating multi-level representations) but navigating it top-down may lose relevant information.
>
> I need a rigorous theoretical analysis. Specifically:
>
> 1. **Information-theoretic perspective**: When does hierarchical elimination preserve or lose information compared to flat search? What role does mutual information between query and tree nodes play? Is there a formal characterisation of when a tree structure enables lossless (or bounded-loss) search vs when it introduces irrecoverable errors?
>
> 2. **Decision-theoretic perspective**: Model tree traversal as sequential decision-making. Under what conditions is sequential elimination (branch-and-bound, alpha-beta pruning) optimal? When does it fail? What do optimal stopping theory and sequential hypothesis testing say about when to commit to a branch vs continue exploring?
>
> 3. **The cluster hypothesis — conditions and limits**: The cluster hypothesis (Jardine & van Rijsbergen, 1971) states that relevant documents cluster together. Under what conditions does this hold in modern embedding spaces? When does it break (e.g., cross-cutting topics, multi-hop queries, adversarial cases)? What is the relationship between cluster tightness and elimination reliability?
>
> 4. **Error propagation in tree pruning**: If a scoring function at level k has error rate ε, how does this compound across d levels of a tree? What are the theoretical recall bounds for a tree of depth d, branching factor b, with per-level error ε? Is there a formal framework for reasoning about this?
>
> 5. **Explaining the RAPTOR collapsed-tree result**: Can you provide a theoretical explanation for why flat retrieval over enriched multi-level representations outperforms strict tree traversal? Under what specific conditions would this reversal occur? Under what conditions would strict traversal win instead?
>
> 6. **Hybrid strategies**: Is there a theoretical basis for strategies that combine elimination and similarity — e.g., using the tree for coarse-grained filtering then flat search within surviving subtrees? What about parallel traversal of multiple branches (keeping more paths open) vs sequential beam search?
>
> 7. **Token efficiency as a constraint**: If we add a hard constraint (e.g., retrieved context must be under 400 tokens), how does this change the optimality conditions? Does a tight token budget make elimination more or less advantageous compared to flat retrieval?
>
> Be rigorous. Cite formal results where they exist. Distinguish between proven theorems, well-supported conjectures, and speculation. If a question lacks formal treatment in the literature, say so — and indicate what a formal treatment would need to establish.

## Success Criteria

A good response will:
- Provide at least one formal framework (information-theoretic, decision-theoretic, or search-theoretic) for reasoning about elimination vs similarity
- Characterise the conditions under which elimination outperforms flat search — not just assert that it does or doesn't
- Provide a theoretical explanation for the RAPTOR collapsed-tree result, with conditions for when it holds
- Address error propagation in tree pruning with at least a sketch of formal bounds
- Distinguish between proven results and conjectures
- Be honest about where formal theory is missing (this is itself a valuable finding)
- Offer at least one insight about how token budget constraints change the analysis

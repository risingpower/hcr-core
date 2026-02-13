# RB-003: Scoring Mechanics for Hierarchical Retrieval

**Date:** 2026-02-13
**Status:** Open
**Decision Required:** Yes — scoring approach is a core architectural decision
**Related:** H1c (scoring as exponential lever), RB-002 (theoretical basis), RB-004 (tree construction)

## Context

RB-002 established that per-level scoring quality is the exponential lever in hierarchical retrieval. Error at each level compounds as (1-ε)^d, where ε is per-level error rate and d is tree depth. At ε=0.10 and d=5, overall recall drops to ~59%. At ε=0.01 and d=5, it stays at ~95%.

This makes scoring the single highest-leverage component in HCR's architecture. Small improvements in per-level accuracy yield exponential gains in end-to-end retrieval quality. Conversely, mediocre scoring renders the entire hierarchy pointless — you'd be better off with flat search.

RB-002 also established that HCR should use a **coarse-to-fine hybrid** strategy: shallow hierarchy (1-2 levels) for coarse routing with very high recall, then flat similarity search within surviving branches. This means scoring serves two distinct roles:

1. **Coarse routing (levels 1-2):** Score must achieve near-perfect recall (≥99%). False negatives are catastrophic — they permanently eliminate correct branches. False positives are cheap — they just widen the search space for the next stage.
2. **Fine selection (within survivors):** Score must achieve high precision under a token budget (<400 tokens). False positives are expensive — they waste irreplaceable token slots. This is closer to standard reranking.

These two roles may require different scoring mechanisms. RB-003 needs to determine what those mechanisms are, whether they're feasible, and at what cost.

## Research Question

What scoring mechanisms can achieve the per-level accuracy required for hierarchical retrieval to outperform flat search, and at what cost in latency, tokens, and dollars?

Specifically:

1. **What scoring methods exist for determining query-to-node relevance in a hierarchy?** Embeddings (dense, sparse, hybrid), LLM-as-judge, cross-encoder reranking, geometric bounds (ball trees, metric trees), learned routing functions, calibrated classifiers — what is the landscape?

2. **What per-level accuracy is achievable with each method?** Not general retrieval accuracy — specifically, can a method reliably determine whether a query's answer lies within a subtree? This is a routing decision, not a ranking decision.

3. **What does "admissible" scoring look like in practice?** RB-002 established that safe pruning requires admissible bounds (a score that never underestimates true descendant relevance). Is this achievable? Metric trees use triangle inequality for exact bounds. Can anything analogous work with embeddings or LLM-generated node descriptions?

4. **How should scoring differ between abstraction levels?** Root-level nodes are high-abstraction summaries. Leaf nodes are concrete content. A query about a specific detail may score low against a thematic summary but high against the leaf chunk. How do existing systems handle cross-level scoring calibration?

5. **What is the cost profile of each method?** For a tree with branching factor b and depth d, scoring all nodes at one level requires b^k evaluations. What does this cost in latency and tokens for embeddings vs cross-encoders vs LLM-as-judge? At what tree size does each method become impractical?

6. **Can scoring be calibrated to produce reliable confidence estimates?** SPRT-style optimal stopping (from RB-002) requires scores that approximate likelihood ratios. Platt scaling, isotonic regression, temperature scaling — do these work for retrieval scoring? Can we get calibrated probabilities that "the answer is in this subtree"?

7. **What about hybrid/cascaded scoring?** Fast cheap method (embeddings) for initial filtering, expensive accurate method (cross-encoder or LLM) for borderline cases. What does the literature say about cascaded scoring for hierarchical retrieval? What are the recall/latency tradeoffs?

8. **How does LATTICE handle scoring?** LATTICE (UT Austin, Oct 2025) is the closest system to HCR in the prior art. It uses LLM-as-judge with calibrated latent relevance scoring. What specifically does it do, how well does it work, and what are its limitations?

## Scope

**In scope:**
- All scoring methods applicable to query-node relevance in a tree structure
- Per-level accuracy benchmarks and theoretical bounds
- Admissibility analysis — can any scoring method guarantee no false negatives?
- Cross-level calibration — scoring at different abstraction levels
- Cost analysis (latency, token spend, dollar cost) for each method
- Cascaded/hybrid scoring strategies
- LATTICE's scoring approach in detail
- Calibration methods for converting scores to reliable probabilities
- The relationship between node representation quality and scoring accuracy

**Out of scope:**
- Tree construction (RB-004) — we take the tree as given
- End-to-end system design — we're focused on the scoring component
- Specific embedding model benchmarks (we want the landscape, not a product comparison)
- Implementation details (code, APIs) — we want the conceptual framework

## What We Already Know

From RB-001 (prior art):
- **LATTICE** uses LLM-as-judge with calibrated latent relevance scoring. Raw LLM relevance judgments are noisy and context-dependent, requiring cross-branch calibration. Achieves strong results.
- **RAPTOR** uses standard cosine similarity against summary embeddings at each level. This is the simplest approach — and it's the one whose strict traversal mode loses to collapsed tree.
- **HIRO** uses a delta threshold — prunes only when children don't sufficiently improve over parent scores. This is a form of conditional elimination that avoids aggressive pruning.
- **Multi-stage retrieval pipelines** (BM25 → reranker → LLM) are cascaded scoring in practice — each stage narrows candidates using progressively more expensive scoring.

From RB-002 (theoretical basis):
- **(1-ε)^d governs everything.** For d=3 at 95% recall: ε ≤ 1.7% per level. For d=2 at 95% recall: ε ≤ 2.5%. For d=2 at 99% recall: ε ≤ 0.5%.
- **Summaries are lossy channels (DPI).** Summary embeddings systematically lose information about specific descendant content. This is not a bug in the embeddings — it's structural.
- **Admissible bounds require provable upper bounds on descendant relevance.** Cosine similarity to summary embeddings trivially violates this — a detail query can score low against a thematic summary but high against a leaf.
- **Calibration is the missing piece for SPRT-style optimal stopping.** If scores were calibrated likelihood ratios with known distributions, optimal routing would be a solved problem.
- **Embedding anisotropy** (Ethayarajh 2019) degrades cosine similarity as a routing signal — embeddings cluster in narrow cones, making similarity scores compress into a small range.
- **Perplexity framed the token budget as a knapsack optimisation** — selecting the highest-information-density nodes within the budget. This requires scores that approximate information density, not just relevance.

From the theoretical gaps (RB-002):
- No formal characterisation of when LLM summarisation produces approximate sufficient statistics for retrieval
- No recall bounds accounting for correlated errors across tree levels
- No theory for optimal cascade parameters (when to escalate from cheap to expensive scoring)

## Prompt for Sources

> I am designing the **scoring component** for a hierarchical context retrieval system (HCR) that retrieves context for LLMs under a hard token budget (<400 tokens). The system uses a tree of nodes where internal nodes hold descriptions/summaries and leaf nodes point to external data sources. Queries enter at the root, and scoring at each level determines which branches to explore further.
>
> Prior theoretical analysis (our RB-002) established that:
> - Per-level scoring error compounds as **(1-ε)^d** across tree depth d — this makes scoring the exponential lever for the whole system
> - Summaries are lossy channels (Data Processing Inequality) — information about query relevance decreases ascending the tree
> - Safe pruning requires **admissible bounds** (scores that never underestimate true descendant relevance), which standard cosine similarity over summary embeddings does not provide
> - **Calibrated scoring** is necessary for optimal routing decisions (SPRT framework)
> - Embedding anisotropy compresses similarity scores into narrow ranges, degrading discriminative power
> - The system uses a **coarse-to-fine hybrid**: shallow hierarchy (1-2 levels) for high-recall routing, then flat similarity within survivors for precision under token budget
>
> I need a comprehensive analysis of scoring mechanisms. Specifically:
>
> 1. **Landscape of scoring methods for hierarchical routing.** What methods can score query-to-node relevance in a tree? I need the full landscape: dense embeddings, sparse retrieval (BM25), cross-encoders, LLM-as-judge, learned routing classifiers, geometric/metric-tree bounds, ColBERT-style late interaction, Matryoshka embeddings, and anything else. For each, characterise: (a) what signal it captures, (b) achievable accuracy for routing decisions, (c) cost profile (latency, compute, token spend), (d) whether it can provide admissible bounds.
>
> 2. **Admissibility analysis.** Can any scoring method guarantee no false negatives (never prune a branch containing the correct answer)? Metric trees use triangle inequality for exact bounds. Is anything analogous possible with embeddings or text representations? What about conservative thresholding — setting scores so high that false negatives are negligible, at the cost of more false positives? What are the theoretical limits?
>
> 3. **Cross-level calibration.** A query about a specific detail may score low against a high-level thematic summary but high against the leaf chunk containing the answer. How should scoring handle different abstraction levels? Does any existing system calibrate scores across tree levels? What techniques exist (level-specific models, normalisation, relative scoring)?
>
> 4. **Calibration for probabilistic routing.** Can retrieval scores be converted to reliable probability estimates ("80% chance the answer is in this subtree")? Platt scaling, isotonic regression, temperature scaling — do these work for retrieval? Has anyone applied calibration techniques specifically to hierarchical routing decisions?
>
> 5. **Cascaded/hybrid scoring.** Fast cheap pass (embeddings) to eliminate obvious non-matches, then expensive accurate pass (cross-encoder or LLM) for borderline cases. What does the literature say about cascaded scoring? What recall/latency tradeoffs are achievable? How should the cascade threshold be set — is there theory for optimal cascade design?
>
> 6. **LATTICE's scoring approach.** LATTICE (UT Austin, ~Oct 2025) uses LLM-as-judge with calibrated latent relevance scoring and is the closest existing system to what we're building. What specifically does it do for scoring? How does it calibrate? What accuracy does it achieve? What are its costs and limitations?
>
> 7. **The knapsack dimension.** Under a hard token budget, scoring should capture not just relevance but **information density** — how much unique, non-redundant information a node contributes per token. Is anyone scoring for information density rather than just relevance? What would this look like formally?
>
> 8. **Practical feasibility.** For a tree with branching factor 8-12 and depth 2-3, what scoring strategy achieves ε ≤ 0.02 (per-level error rate) at reasonable cost? Is this target realistic? What's the state of the art for routing accuracy in hierarchical systems?
>
> Be rigorous. Cite specific papers and systems where they exist. Distinguish between proven results, strong empirical evidence, and speculation. If a question doesn't have established answers, say so explicitly — knowing where the frontier is matters as much as knowing what's been solved.

## Success Criteria

A good response will:
- Map the full landscape of scoring methods applicable to hierarchical routing (at least 5 distinct approaches)
- Provide concrete accuracy figures or bounds for at least some methods (not just "good" or "better")
- Address admissibility seriously — either show how to achieve it or prove why it's impractical and what the alternatives are
- Cover the cross-level calibration problem with at least one concrete technique
- Analyse cascaded scoring with recall/cost tradeoffs
- Address LATTICE's approach specifically (or honestly state if information is limited)
- Provide a cost analysis for at least 2-3 methods at the specified tree size (branching factor 8-12, depth 2-3)
- Distinguish clearly between established results and speculation
- Surface any scoring approaches we haven't considered

# RB-001: Prior Art Survey — Consolidation

**Date:** 2026-02-13
**Status:** Complete (3/4 sources — Gemini pending)
**Brief:** [RB-001 Prompt](./prompt.md)
**Sources:** Claude, GPT, Perplexity

## Summary

Three independent sources surveyed the landscape of hierarchical and tree-based retrieval for LLMs. The field is active and growing rapidly — at least 12 distinct systems have been published since early 2024, spanning tree-structured indices, graph-hierarchy methods, and agentic approaches. All three sources converge on the same core finding: **hierarchical retrieval consistently outperforms flat RAG on long-document, structured, and multi-hop reasoning tasks**, with accuracy gains of 2–20 percentage points depending on benchmark. However, strict top-down tree traversal has not yet convincingly beaten augmented flat retrieval in all cases — RAPTOR's own experiments show its collapsed tree (which abandons strict traversal) outperforms its tree traversal mode.

No existing system matches HCR's specific combination of elimination-based pruning, parallel branch traversal, hard token budgeting (~400 tokens), and leaf nodes resolving to external data sources. The closest analog is LATTICE (UT Austin, October 2025), which shares the philosophy of LLM-scored tree navigation with logarithmic complexity but differs in traversal strategy and lacks a fixed token target.

---

## Consensus

All three sources agree on the following findings. Confidence is rated by the strength and independence of corroboration.

| # | Finding | GPT | Perplexity | Claude | Confidence |
|---|---------|-----|------------|--------|------------|
| 1 | RAPTOR (ICLR 2024) is the foundational system — bottom-up clustering + LLM summarisation, multi-level tree | Yes | Yes | Yes | **Very High** |
| 2 | RAPTOR's collapsed tree (flat retrieval over all nodes) outperforms its own tree traversal mode | Yes | Implied | Yes | **High** |
| 3 | LATTICE (UT Austin, Oct 2025) is the closest existing work to HCR — LLM-guided tree navigation with logarithmic complexity | Yes | Yes | Yes | **Very High** |
| 4 | LATTICE is from UT Austin (not MIT as initially assumed) | Yes | — | Yes | **High** |
| 5 | HIRO adds DFS + delta-threshold pruning on RAPTOR's tree — closest to elimination-based pruning | Yes | Yes | Yes | **Very High** |
| 6 | GraphRAG (Microsoft) uses hierarchical community detection but is graph-based, not tree-based; extreme cost ($650/100 questions) | Yes | Yes | Yes | **Very High** |
| 7 | Hierarchical retrieval outperforms flat RAG on long-document, multi-hop, and reasoning-heavy benchmarks | Yes | Yes | Yes | **Very High** |
| 8 | No comprehensive head-to-head benchmark exists comparing hierarchical vs flat across all metrics on shared benchmarks | Yes | Yes | Yes | **Very High** |
| 9 | Tree construction is brittle and dataset-dependent — clustering algorithm choice dramatically affects performance | Yes | Yes | Yes | **Very High** |
| 10 | Cross-branch queries cause systematic failures in top-down traversal | Yes | Yes | Yes | **Very High** |
| 11 | Dynamic hierarchy maintenance is essentially unaddressed — most systems treat indexing as offline/static | Yes | Yes | Yes | **Very High** |
| 12 | No existing system explicitly targets a hard token budget as a first-class constraint | Yes | Yes | Yes | **Very High** |
| 13 | Pre-LLM precedents (B-trees, HNSW, cluster hypothesis, hierarchical softmax) provide strong theoretical grounding | Yes | Yes | Yes | **Very High** |
| 14 | LlamaIndex TreeIndex/RecursiveRetriever is the primary production framework implementing hierarchical traversal | Yes | Yes | Yes | **High** |
| 15 | Scoring accuracy at internal nodes degrades with abstraction level — summary embeddings may not inhabit the same space as original text | Yes | Yes | Yes | **High** |

---

## Conflicts

| # | Point of Conflict | Position A | Position B | Assessment |
|---|-------------------|-----------|-----------|------------|
| 1 | **HIRO identity** | Claude identifies a separate "HIRO" (Goel & Chandak, 2024) as a DFS querying method on RAPTOR trees | GPT identifies "HIRO" (Hosking, Tang & Lapata, TACL 2024) as a learned hierarchical index for opinion summarisation | **Two different papers share the HIRO name.** Claude's HIRO (arXiv 2406.09979) is the one relevant to HCR — it implements elimination-style traversal. GPT's HIRO (TACL 2024) is about learned hierarchical indexing for opinion summarisation, a different system. Perplexity aligns with Claude's HIRO. Both are valid prior art but serve different purposes. |
| 2 | **RAPTOR performance numbers** | Claude cites QuALITY accuracy as 82.6% (GPT-4) | GPT cites "+20 percentage points" improvement | **Not a real conflict** — both are from the same paper. 82.6% absolute accuracy represents a ~20pp gain over prior SOTA. Numbers are consistent. |
| 3 | **Scope of "hierarchical retrieval beats flat"** | Claude and GPT note important caveats — collapsed tree beats tree traversal, results are benchmark-specific | Perplexity's framing is somewhat more bullish on hierarchical approaches | **Claude/GPT are more precise.** The evidence is strong for long-document/reasoning tasks but not universal. RAPTOR's collapsed tree result is a genuine caution for strictly top-down designs like HCR. |

---

## Gaps

### Between sources
- **Gemini response still pending** — may surface additional systems or contradictory findings
- **GPT uniquely surfaced** HiREC (ACL Findings 2025) — a hierarchical retrieval system for financial QA on SEC filings, demonstrating elimination-style cascading in a production-relevant domain. Neither Claude nor Perplexity mentioned this.
- **Claude uniquely surfaced** CFT-RAG (Cuckoo Filter-based elimination, 100–138x speedup) and LeanRAG (46% smaller context). Neither GPT nor Perplexity covered these.
- **Perplexity uniquely surfaced** BookRAG (hybrid tree-graph index for complex documents) and provided the most structured treatment of opportunities for novel contribution.

### In the literature
1. **No fixed-token-budget retrieval system exists.** Every source confirms this gap. Systems report token efficiency improvements but none optimise for a hard bound.
2. **No standardised benchmark** for hierarchical vs flat retrieval across shared corpora, metrics, and token budgets.
3. **Dynamic maintenance** is universally identified as unaddressed — no system handles incremental updates without full reconstruction.
4. **Leaves as external source pointers** (HCR's design) has no academic precedent. Only LlamaIndex's RecursiveRetriever approximates this in production, and it's not formally evaluated.
5. **Theoretical analysis of elimination error** — no work provides formal bounds on recall loss from tree pruning. All thresholds are empirically tuned.
6. **Multi-hierarchy ensembles** — no system traverses multiple complementary trees simultaneously.

---

## Key Takeaways

### 1. The core hypothesis has empirical support — but with a critical caveat

All sources confirm that hierarchical retrieval outperforms flat RAG on complex, long-document, reasoning-heavy tasks. This validates HCR's direction. **However**, RAPTOR's finding that its collapsed tree (effectively reverting to flat retrieval over enriched representations) outperforms strict tree traversal is a direct challenge to HCR's bet on top-down elimination. HCR must demonstrate that its elimination mechanism is good enough to not sacrifice relevant information — or the optimal strategy may be to use the tree for enrichment while still retrieving broadly.

### 2. LATTICE is the primary competitor

LATTICE is the system most aligned with HCR's philosophy. Key differences to exploit:
- LATTICE uses sequential best-first beam search; HCR proposes parallel traversal
- LATTICE has variable token output; HCR targets a hard ~400 token budget
- LATTICE's tree contains document text at leaves; HCR's leaves resolve to external sources
- LATTICE requires calibrated LLM calls at each traversal step (expensive); HCR could use lightweight embedding-based scoring

### 3. Five open problems are now HCR's challenges

All sources converge on the same five unsolved problems. These aren't just risks — they're the research agenda:
1. **Tree construction** — no principled method exists for automatically selecting clustering algorithms and parameters
2. **Cross-branch queries** — top-down traversal systematically misses information in pruned branches
3. **Dynamic maintenance** — no incremental update mechanism without full reconstruction
4. **Internal node scoring** — summary embeddings drift from original text embedding space
5. **Optimal tree topology** — no systematic study of depth × branching factor × compression ratio

### 4. Three aspects of HCR appear genuinely novel

1. **Elimination semantics** (negative selection) vs selection semantics (positive selection, top-k)
2. **Hard token budget** (~400 tokens) as a first-class optimisation constraint
3. **Leaves as external source pointers** — making the tree a pure routing index, not a content store

### 5. The benchmark gap is an opportunity

No standardised evaluation exists for hierarchical retrieval. HCR could establish evaluation standards alongside its system contribution — measuring accuracy as a function of context length, which no current benchmark does.

---

## Recommendation

**Decision required:** No — informational only. Findings feed into RB-002 through RB-006.

### For RB-002 (Theoretical basis: elimination vs similarity)
The evidence supports elimination-based retrieval in principle, but the RAPTOR collapsed-tree result is the strongest counter-evidence. RB-002 must directly address: **under what conditions does strict top-down elimination outperform enriched flat retrieval?** This is now the central theoretical question.

### For RB-003 (Scoring mechanics)
Three scoring approaches are on the table:
- **Embedding similarity** (HIRO, RAPTOR) — cheap, fast, but degrades at higher abstraction levels
- **LLM-as-judge** (LATTICE) — accurate, but expensive and requires calibration
- **Hybrid** — no existing system has tried a lightweight learned router that combines signals

RB-003 should evaluate all three against HCR's hard token budget constraint.

### For RB-004 (Tree construction)
All sources agree this is the most brittle component. RB-004 should investigate:
- Whether HCR can be **tree-construction-agnostic** (generic traversal over any hierarchy)
- The impact of clustering algorithm choice (GMM vs Leiden vs agglomerative)
- How to handle HCR's unique requirement: leaves as pointers, not content

### For RB-005 (Failure modes)
Cross-branch queries are the #1 failure mode. RB-005 should catalogue:
- When top-down elimination fails (multi-hop, cross-domain, entity-spanning)
- Whether parallel traversal mitigates this vs sequential beam search
- What the recall floor is when operating under a 400-token budget

### For RB-006 (Benchmark design)
The absence of standardised benchmarks is confirmed by all sources. RB-006 should design a benchmark that measures **accuracy × token efficiency** — the metric no one is currently evaluating. This positions HCR to set the evaluation standard, not just compete on existing ones.

---

## Next Steps

1. **RB-002: Theoretical basis** — "Under what conditions does elimination outperform similarity?" Directly address the RAPTOR collapsed-tree challenge.
2. If Gemini responds, add to this consolidation — unlikely to change findings but may surface additional systems.
3. Update hypothesis H1 confidence based on this evidence.

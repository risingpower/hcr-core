# RB-005: Failure Modes of Hierarchical Coarse-to-Fine Retrieval

**Date:** 2026-02-13
**Status:** Open
**Decision Required:** Yes — go/no-go confidence for Phase 1 depends on whether failure modes are bounded
**Related:** H1a (token efficiency), H1b (hybrid superiority), H1c (scoring lever), RB-001 (prior art), RB-002 (theoretical basis), RB-003 (scoring mechanics), RB-004 (tree construction)

## Context

Four prior research briefs have established the theoretical basis, scoring architecture, and construction strategy for HCR — a hierarchical coarse-to-fine retrieval system operating under hard token budgets (<400 tokens). The design is now well-specified:

- **Tree:** Top-down divisive clustering (bisecting k-means), depth 2–3, branching factor 6–15, with LLM-generated structured contrastive routing summaries at internal nodes and external source pointers at leaves.
- **Scoring:** Per-level cascade (hybrid BM25+dense pre-filter → cross-encoder rerank), path-relevance EMA, beam search (k=3–5).
- **Cross-branch defense:** Five layers — content decomposition, soft assignment (1–3 parents per leaf), entity cross-links, beam search, collapsed-tree fallback.
- **Token budget selection:** AdaGReS-style submodular knapsack (relevance − redundancy under token constraint).

Every prior brief has flagged the same concern: **cross-branch queries are the #1 structural risk.** RB-001 identified them as systematic failures. RB-002 proved the error compounding equation ((1-ε)^d) and showed cross-branch queries violate the cluster hypothesis by construction. RB-003 confirmed scoring alone cannot solve the problem. RB-004 proposed a five-layer defense but noted no single method solves cross-branch queries.

But cross-branch queries are not the only failure mode. Before committing to Phase 1 implementation, we need a comprehensive failure catalogue — not just the known #1 risk, but all the ways this system can fail, how likely each is, and whether our mitigations are sufficient or whether there are showstoppers we haven't considered.

## Research Question

**What are the complete failure modes of hierarchical coarse-to-fine retrieval under HCR's design, how severe is each, and what is the residual risk after our planned mitigations?**

Specifically:

1. **Comprehensive failure taxonomy.** Enumerate all failure modes of hierarchical coarse-to-fine retrieval — not just cross-branch queries. Consider failures at every stage: tree construction, summary generation, scoring/routing, beam search traversal, leaf resolution, token-budget selection, and maintenance/drift. For each failure mode: (a) describe the mechanism, (b) characterise the query types or corpus conditions that trigger it, (c) estimate severity (how much accuracy is lost when it occurs), (d) estimate frequency (what fraction of queries in a typical organisational knowledge base trigger this mode).

2. **Cross-branch query analysis in depth.** Cross-branch queries are the known #1 risk. But "cross-branch" is a broad category. Break it down:
   - **Multi-hop queries** (answer requires combining facts from different branches)
   - **Entity-spanning queries** (an entity appears in multiple branches; query asks about the entity)
   - **Comparative queries** ("how does X differ from Y?" where X and Y are in different branches)
   - **Aggregation queries** ("how many...", "list all...", "what's the total...")
   - **Temporal queries** ("what changed between..." where history spans branches)
   - For each sub-type: how common is it in organisational knowledge bases (like the target consumer Su)? How effective is each of our five defense layers against it? What is the expected recall after all mitigations?

3. **Query distribution analysis.** The severity of failure modes depends on what queries actually look like in practice. For an organisational knowledge base (policies, procedures, projects, people, tools, communications):
   - What fraction of queries are single-branch (answer exists entirely within one subtree)?
   - What fraction are cross-branch (answer requires evidence from multiple subtrees)?
   - What fraction are detail queries (specific identifiers, dates, numbers) vs thematic queries (broad topics)?
   - What fraction are entity-centric (about a person, project, or tool) vs concept-centric (about a process or idea)?
   - Is there empirical data from real-world RAG deployments or enterprise search systems on these distributions?

4. **The DPI failure cascade.** RB-002 and RB-003 established that summaries are lossy channels (Data Processing Inequality). When does this cause retrieval failure vs merely degraded ranking?
   - What types of information are most likely to be lost in summarisation?
   - How does the structured routing summary format (theme, includes, excludes, key_entities, key_terms) mitigate this vs generic summaries?
   - At what point does accumulated information loss make coarse-to-fine routing worse than flat similarity?
   - What is the relationship between corpus heterogeneity and DPI failure rate?

5. **Beam search failure analysis.** Beam search (k=3–5) is the primary query-time mitigation. When does it fail?
   - **Beam collapse:** All k beams converge to the same region, missing other relevant branches. How common is this? What causes it?
   - **Score plateau:** Top children all score similarly, making beam selection effectively random. Under what conditions does this occur?
   - **Depth interaction:** Does beam width k=3 at depth d=2 provide adequate coverage? At d=3?
   - What is the theoretical recall floor for beam search (k=3) on a tree with branching factor b=10 and depth d=2, assuming per-level ε=0.02?
   - Are there query types where beam search systematically underperforms flat retrieval regardless of beam width?

6. **Maintenance and drift failures.** The knowledge base grows and changes over time. What can go wrong?
   - **Summary staleness:** How quickly do routing summaries become inaccurate as content changes?
   - **Distribution shift:** New content changes the topic distribution; existing partitions no longer reflect the corpus.
   - **Incremental insertion degradation:** How does routing quality degrade as more content is inserted without full reconstruction?
   - **Orphaned cross-links:** Entity cross-links become stale as content is removed or updated.
   - At what rate of change does the incremental maintenance approach break down?

7. **Token budget interaction with failures.** How does the 400-token budget amplify or mitigate each failure mode?
   - When routing fails, what fraction of the budget is wasted on irrelevant context?
   - Does the submodular knapsack selection (relevance − redundancy) provide any resilience against partial routing failures?
   - Is 400 tokens enough to be useful even with perfect routing? What's the minimum viable context size for different query types?
   - Are there query types where no amount of routing can produce a useful answer under 400 tokens?

8. **Adversarial and edge-case failures.** What about:
   - **Queries that don't match any branch** (truly novel topics, out-of-distribution queries)?
   - **Ambiguous queries** (multiple valid interpretations leading to different branches)?
   - **Negation queries** ("what is NOT covered by policy X?")?
   - **Meta-queries** ("what do we know about topic Y?" requiring awareness of the tree structure itself)?
   - **Rapidly evolving content** (the correct answer changed since the last summary update)?

## Scope

**In scope:**
- All failure modes at every stage of the HCR pipeline
- Quantitative or semi-quantitative severity/frequency estimates where possible
- Assessment of HCR's planned mitigations against each failure mode
- Residual risk after mitigations — what remains unsolved?
- Comparison to flat retrieval failure modes — is HCR strictly worse on any dimension?
- Empirical data on query distributions from real-world knowledge bases and enterprise search

**Out of scope:**
- Scoring architecture alternatives (RB-003 — complete)
- Tree construction alternatives (RB-004 — complete)
- Benchmark design (RB-006 — next)
- Implementation-level failure modes (bugs, latency spikes, infrastructure — these are engineering, not architectural)

## What We Already Know

From RB-001 (prior art):
- Cross-branch queries cause systematic failures in top-down traversal (consensus, very high confidence)
- RAPTOR's collapsed tree outperforms its own tree traversal — structural evidence that forced routing loses information
- No existing system reports per-level routing accuracy; failure rates are not quantified in the literature

From RB-002 (theoretical basis):
- Error compounds at (1-ε)^d — the central fragility equation
- The cluster hypothesis holds for narrow domains (8% failure) but not broad collections (46% failure, Voorhees 1985)
- Cross-branch failure is structural to any tree-partitioned search when relevance crosses partition boundaries
- Token budgets amplify both upside and downside: correct routing → excellent context, misrouting → total waste
- Beam search transforms recall from (1-ε)^d to approximately (1-(1-p)^k)^d — dramatic improvement for modest k
- Tight budgets shift the objective from recall to precision/utility per token

From RB-003 (scoring mechanics):
- Per-level ε ≈ 0.01–0.02 is achievable with cascade architecture
- Summary quality is the #1 upstream factor — no scoring method compensates for poor summaries
- Path-relevance EMA is higher leverage than per-node scoring sophistication
- ColBERT/multi-vector representations preserve detail hooks that single-vector embeddings lose
- Detail queries against thematic summaries is the structural DPI failure case

From RB-004 (tree construction):
- Content decomposition into atomic units is the primary defense against cross-branch failure (PropRAG: 94% Recall@5)
- Soft assignment (1–3 parents) is cheap because leaves are pointers
- Entity cross-links provide cross-branch query support
- No single method solves cross-branch queries — five-layer defense is the emerging best practice
- Summary hallucination risk (~4% in RAPTOR) — hallucinated hook terms are more dangerous than hallucinated narrative
- Incremental maintenance follows "insert locally, repair locally, rebuild periodically" — but no one has measured quality degradation rates

## Prompt for Sources

> I am conducting a **failure mode analysis** for a hierarchical coarse-to-fine retrieval system (HCR) designed to retrieve context for LLMs under a hard token budget (<400 tokens). The system is fully designed but not yet built — this is the pre-implementation risk assessment. The system uses:
>
> - **Tree structure:** Top-down divisive clustering (bisecting k-means), depth 2–3, branching factor 6–15. Internal nodes hold structured contrastive routing summaries (`{theme, includes, excludes, key_entities, key_terms}`). Leaf nodes are pointers to external data sources (APIs, databases, document stores).
> - **Scoring cascade:** Per level: hybrid BM25+dense pre-filter (all children) → top-3 → cross-encoder rerank → top-1–2. Path-relevance EMA across depth (α=0.5). Per-level error rate ε ≈ 0.01–0.02.
> - **Beam search traversal:** Width k=3–5 over frontier nodes. Best-first expansion using path relevance scores.
> - **Five-layer cross-branch defense:** (1) Content decomposition into atomic semantic units before clustering, (2) Soft assignment — leaves can have 1–3 parents, (3) Entity cross-links across branches, (4) Beam search at query time, (5) Collapsed-tree fallback when beam confidence is low.
> - **Token budget selection:** AdaGReS-style submodular knapsack — greedy selection of retrieved chunks under 400-token constraint, scoring relevance − redundancy.
> - **Maintenance:** Incremental insertion via scoring cascade, local split/merge repairs, dirty-flag summary staleness with lazy regeneration, periodic full rebuild at 20–30% new content threshold.
>
> Our prior research has established that:
> - Error compounds at (1-ε)^d across tree depth (RB-002) — with ε=0.02 and d=2, end-to-end recall ≈ 96%
> - The cluster hypothesis holds weakly for broad collections (46% failure rate, Voorhees 1985) (RB-002)
> - Summaries are lossy channels (DPI) — detail queries against thematic summaries is the structural failure case (RB-002, RB-003)
> - Cross-branch queries are the #1 known failure mode — no single mitigation solves them (all briefs)
> - No system in the literature reports per-level routing accuracy — failure rates are unquantified (RB-001, RB-003)
>
> **The target domain is an organisational knowledge base** — a personal/team knowledge system containing: policies, procedures, project documentation, meeting notes, tool configurations, people directories, communications history, technical documentation, and reference materials. The consumer (Su) is an agentic command centre that needs precise retrieval from this growing knowledge base.
>
> I need a **comprehensive failure mode analysis**. Specifically:
>
> 1. **Complete failure taxonomy.** Enumerate all failure modes of this architecture — not just the known cross-branch risk. Consider failures at every stage: tree construction, summary generation, scoring/routing, beam search traversal, leaf resolution, token-budget packing, and maintenance/drift. For each failure mode: (a) mechanism, (b) triggering conditions, (c) severity (accuracy impact when triggered), (d) estimated frequency in the target domain (organisational knowledge base), (e) which of our planned mitigations address it, and (f) residual risk after mitigation. Organise into a structured taxonomy.
>
> 2. **Cross-branch query decomposition.** Break "cross-branch queries" into specific sub-types: multi-hop, entity-spanning, comparative, aggregation, temporal, and any others. For each: (a) concrete example in an organisational knowledge base, (b) estimated frequency as a fraction of all queries, (c) effectiveness of each of the five defense layers against it, (d) expected recall after all five layers. Be quantitative where possible, even if approximate.
>
> 3. **Query distribution in organisational knowledge bases.** What do queries actually look like in the target domain? Specifically:
>    - What fraction are single-branch vs cross-branch?
>    - What fraction are detail (specific facts, identifiers) vs thematic (broad topics)?
>    - What fraction are entity-centric vs concept-centric?
>    - Is there empirical data from enterprise search, knowledge management, or RAG deployment studies?
>    - How does the Su use case (agentic, precision-focused, growing knowledge base) differ from academic retrieval benchmarks?
>
> 4. **DPI (Data Processing Inequality) failure analysis.** Summaries lose information. When does this cause routing failure vs merely degraded ranking? What types of information are most likely to be lost? How does the structured routing summary format mitigate this? At what corpus heterogeneity does DPI failure dominate?
>
> 5. **Beam search failure modes.** When does beam search (k=3–5) fail? Beam collapse (all beams converge), score plateaus (random selection), depth interaction, and systematic underperformance vs flat retrieval. Calculate the theoretical recall floor for beam k=3, b=10, d=2, ε=0.02.
>
> 6. **Maintenance and drift failures.** How quickly do trees degrade with incremental updates? What causes the fastest degradation? When does incremental maintenance fail and full reconstruction become necessary? Any empirical data on degradation rates?
>
> 7. **Token budget interaction.** How does the 400-token constraint interact with each failure mode? When does it amplify failures? When does it provide resilience? What query types can never be answered under 400 tokens regardless of routing quality?
>
> 8. **Comparison to flat retrieval failures.** Is HCR strictly worse than flat retrieval on any failure dimension? Where does flat retrieval fail that HCR handles better? Where does HCR introduce new failure modes that flat retrieval doesn't have? What is the overall failure-mode risk profile of HCR vs flat similarity + reranking?
>
> 9. **Residual risk assessment.** After all planned mitigations, what is the expected overall failure rate for the target domain? What is the single biggest remaining risk? Is there any showstopper — a failure mode so severe or frequent that it invalidates the architecture?
>
> Be rigorous and adversarial. The goal is to find problems before building, not to confirm the design is sound. Cite specific papers, systems, and empirical data where they exist. Distinguish between proven failure modes, theoretically predicted failures, and speculative concerns. If quantitative estimates are uncertain, state the uncertainty range.

## Success Criteria

A good response will:
- Identify at least 10 distinct failure modes across all pipeline stages (not just routing failures)
- Decompose cross-branch queries into at least 4 sub-types with per-sub-type analysis
- Provide quantitative or semi-quantitative frequency/severity estimates for the target domain
- Cite empirical data on query distributions from real-world knowledge bases or enterprise search (not just academic benchmarks)
- Calculate the theoretical recall floor for the specified beam search parameters
- Assess each of the five defense layers against each cross-branch sub-type
- Identify at least one failure mode we haven't previously considered
- Provide an honest residual risk assessment — including whether any failure mode is a potential showstopper
- Compare HCR's failure profile to flat retrieval on the same failure dimensions
- Distinguish between architectural failures (unfixable by design) and engineering failures (fixable by implementation quality)

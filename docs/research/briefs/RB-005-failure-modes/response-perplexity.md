# RB-005: Failure Modes — Perplexity Response

# \# RB-005: Failure Modes of Hierarchical Coarse-to-Fine Retrieval

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

Every prior brief has flagged the same concern: **cross-branch queries are the \#1 structural risk.** RB-001 identified them as systematic failures. RB-002 proved the error compounding equation ((1-ε)^d) and showed cross-branch queries violate the cluster hypothesis by construction. RB-003 confirmed scoring alone cannot solve the problem. RB-004 proposed a five-layer defense but noted no single method solves cross-branch queries.

But cross-branch queries are not the only failure mode. Before committing to Phase 1 implementation, we need a comprehensive failure catalogue — not just the known \#1 risk, but all the ways this system can fail, how likely each is, and whether our mitigations are sufficient or whether there are showstoppers we haven't considered.

## Research Question

**What are the complete failure modes of hierarchical coarse-to-fine retrieval under HCR's design, how severe is each, and what is the residual risk after our planned mitigations?**

Specifically:

1. **Comprehensive failure taxonomy.** Enumerate all failure modes of hierarchical coarse-to-fine retrieval — not just cross-branch queries. Consider failures at every stage: tree construction, summary generation, scoring/routing, beam search traversal, leaf resolution, token-budget selection, and maintenance/drift. For each failure mode: (a) describe the mechanism, (b) characterise the query types or corpus conditions that trigger it, (c) estimate severity (how much accuracy is lost when it occurs), (d) estimate frequency (what fraction of queries in a typical organisational knowledge base trigger this mode).
2. **Cross-branch query analysis in depth.** Cross-branch queries are the known \#1 risk. But "cross-branch" is a broad category. Break it down:
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
- Summary quality is the \#1 upstream factor — no scoring method compensates for poor summaries
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
> - Cross-branch queries are the \#1 known failure mode — no single mitigation solves them (all briefs)
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

**Executive summary / Phase‑1 decision**

- Hierarchical coarse‑to‑fine retrieval (HCR) introduces *new* structural failure modes on top of the usual RAG and enterprise‑search failures. The dominant architectural risk is still cross‑branch queries, especially aggregation/temporal and high‑fan‑out entity queries.
- With your five‑layer cross‑branch defense, shallow trees (d=2–3), strong summaries, and beam search $k=3–5$, the *overall* failure rate for an organisational KB appears bounded: a plausible band for “answerable but missed due to retrieval” is on the order of 10–20% of queries, with single‑branch factual/thematic queries above 95% recall and complex cross‑branch queries often in the 70–90% band, depending on subtype. These numbers are approximate and based on analogues, not direct HCR measurements.
- There is **no clear architectural showstopper** for your Phase‑1 scope (agentic assistant over an internal KB under ~400 tokens). The design is fragile in exactly the ways RB‑001–RB‑004 already flagged, but the risks are *bounded and diagnosable* rather than fatal.
- The single biggest remaining risk is **high‑fan‑out cross‑branch queries that require global aggregation or change‑over‑time comparisons** (e.g., “list all incidents of X across all projects last year; what changed vs the year before?”). For these, HCR will systematically underperform graph‑based RAG and some flavors of flat retrieval plus downstream aggregation.

The rest of this answer:

1. Gives a structured failure taxonomy across all pipeline stages.
2. Decomposes cross‑branch queries and scores each defense layer.
3. Summarizes what is known about real‑world query distributions.
4. Analyses DPI/summarisation failures.
5. Analyses beam search failure modes and computes the theoretical recall floor.
6. Discusses maintenance/drift failure.
7. Discusses interaction with the 400‑token budget.
8. Compares HCR vs flat retrieval.
9. Ends with a residual‑risk and go/no‑go assessment.

***

## 1. Failure taxonomy for HCR

Below is a compact taxonomy by stage. For each, “severity” is the impact *conditional on the failure being triggered* (low: re‑ranking/quality only; medium: partial answer; high: answer‑killing). Frequency estimates are for a reasonably curated organisational KB like Su’s, based on enterprise‑search studies and RAG practice, but are necessarily approximate and partly speculative.

### 1.1 Tree construction \& representation

**F1. Top‑level partition violates cluster hypothesis**

- **Mechanism:** Bisecting k‑means creates high‑level partitions that mix many topical dimensions (e.g., policy vs product vs time vs team). Relevant items for many queries are scattered across branches. This is the classic failure in Voorhees’ cluster‑based retrieval: retrieving whole clusters tends to underperform document‑level retrieval on heterogeneous corpora.[^1_1][^1_2]
- **Triggers:** Broad, heterogeneous corpora (mixed domains, long multi‑topic docs); queries that cut across orthogonal facets (e.g., “incident reports involving contractor X in Europe since 2023”) rather than along a single topical dimension.
- **Severity:** High when it hits: routing can systematically exclude necessary subtrees; beam search explores the wrong “axes of variation.”
- **Frequency:** For a heterogeneous enterprise corpus, empirical work suggests cluster‑hypothesis failures approaching 40–50% on broad collections vs <10% on narrow domains. For Su‑style KBs, expect this to affect maybe 20–40% of queries that are not cleanly topical (multi‑facet, multi‑entity, time‑sliced).[^1_3][^1_1]
- **Mitigations:**
– Content decomposition to atomic units (reduces multi‑topic contamination).
– Soft assignment and entity cross‑links (let content live under multiple parents).
– Collapsed‑tree fallback (flat retrieval when routing is low‑confidence).
- **Residual risk:** Still substantial for global queries that need many branches even with perfect atomic units; *structural* to any tree partition.

***

**F2. Over‑fragmentation or under‑fragmentation of atomic units**

- **Mechanism:** Decomposition produces units that are too small (losing context needed by embeddings) or too large (mixing unrelated facts so that routing reflects the majority topic).
- **Triggers:** Highly structured documents (tables, configs, code) or messy notes where sentence boundaries don’t track semantic units; automatic proposition extraction that misses implicit dependencies.
- **Severity:**
– Over‑fragmentation: medium (detail queries may still match; reasoning chains break).
– Under‑fragmentation: high for cross‑branch/exception queries (minority facts are entangled with unrelated majority topics).
- **Frequency:** On naive chunking, this is pervasive; PropRAG shows that moving to proposition‑level units can boost Recall@5 to the high‑80s/90s on multi‑hop benchmarks vs standard passage retrieval. With an explicit atomic‑unit pipeline, residual mis‑segmentation might affect perhaps 10–20% of documents.[^1_4][^1_5]
- **Mitigations:** LLM‑based proposition extraction (PropRAG‑style); alignment to document structure (headings, bullets, issue IDs).
- **Residual risk:** Medium. Some knowledge is inherently contextual (e.g., “except as noted above”), and atomicization will sometimes break it.

***

**F3. Unbalanced or degenerate tree**

- **Mechanism:** Some branches end up shallow or extremely dense; others sparse, leading to uneven branching factors and depth, which hurts scoring calibration and beam allocation.
- **Triggers:** Skewed corpora (e.g., thousands of tickets vs a handful of strategy docs), poor clustering hyperparameters, incremental splits without global rebalancing.
- **Severity:** Medium; it can starve some regions of beam budget and over‑allocate to others.
- **Frequency:** Common without explicit balancing; but with bisecting k‑means + branch‑factor caps, likely limited to a minority (<10%) of the tree.
- **Mitigations:** Branching‑factor constraints; periodic rebalancing/rebuild; depth‑aware beam allocation.
- **Residual risk:** Low–medium.

***

### 1.2 Summary generation (DPI, hallucinations, contrastive errors)

**F4. Loss of discriminative details (DPI failure)**

- **Mechanism:** Summaries are lossy; low‑salience but query‑critical details (IDs, dates, rare entities, negations, counts) are dropped. Hierarchical and compression‑based summarization pipelines are empirically worse than full‑context approaches for content selection, especially at deeper layers.[^1_6][^1_7]
- **Triggers:**
– Detail queries (ticket numbers, version numbers, specific clauses).
– Exception clauses (“except for contractors in region X”), negative duties, corner cases.
– Heterogeneous clusters where no single “theme” captures all query‑relevant content.
- **Severity:**
– Routing: high when the only hooks that signal relevance are exactly the details that were dropped → catastrophic miss.
– Ranking within leaf pool: medium; the right leaf may still be present but demoted.
- **Frequency:** For generic abstractive summaries over long inputs, coverage errors and hallucinations are common; recent work reports detectable coverage errors at non‑trivial rates in LLM outputs. RAPTOR’s own analysis finds ~4% of hierarchical summaries contain hallucinations, though they judged little impact on their benchmarks. For *routing* in an enterprise KB with careful prompts and structured fields, a reasonable expectation is DPI‑driven routing failure in perhaps 5–15% of queries, concentrated in detail / exception queries.[^1_8][^1_9]
- **Mitigations:**
– Structured routing summaries with `{theme, includes, excludes, key_entities, key_terms}` (forces explicit mention of details and exceptions).
– Using extractive elements (key sentences, IDs) alongside abstractive text.
– Summarization QA / self‑critique to check that IDs, counts, exceptions are preserved.
- **Residual risk:** Medium and irreducible: any compression under DPI will sometimes throw away the only discriminative feature.

***

**F5. Hallucinated routing hooks**

- **Mechanism:** Summaries introduce entities or key terms not grounded in the underlying content. In RAPTOR about 4% of node summaries showed minor hallucinations. In a *routing* context, these invented hooks can attract unrelated queries into the wrong subtree.[^1_9]
- **Triggers:** Summarizing long, noisy, or partially relevant documents; generic prompts that invite abstraction beyond the text.
- **Severity:** High when hallucinated hooks collide with real high‑traffic query terms (e.g., hallucinating “GDPR” or “Kubernetes”).
- **Frequency:** With cautious prompts and moderately short input spans, probably low single digits of nodes and a much smaller fraction of *queries* (only those that happen to hit the hallucinated term).
- **Mitigations:**
– Constraining summaries to be *conservative* and grounded (“do not introduce entities or terms not present in these chunks”).
– Spot‑checking high‑traffic nodes; heuristic checks against source text.
- **Residual risk:** Low but high‑impact for certain topics; needs monitoring.

***

**F6. Over‑broad or non‑contrastive summaries**

- **Mechanism:** Internal node summaries become generic (“misc project notes”) or fail to state what is *excluded*, so multiple siblings look similar under scoring and routing becomes near‑random.
- **Triggers:** Noisy clusters; k‑means that groups together items lacking a clear shared theme; poor prompt design for contrastive “includes/excludes.”
- **Severity:** Medium–high; it inflates effective ε at that level.
- **Frequency:** Likely significant in early iterations until prompts and clustering are tuned; afterwards maybe ~10% of internal nodes show weak contrast.
- **Mitigations:** Contrastive summarization prompts, cluster‑quality heuristics (intra/inter similarity thresholds), re‑clustering of “miscellaneous” buckets.
- **Residual risk:** Medium, but largely engineering‑tunable.

***

### 1.3 Scoring and routing

**F7. Lexical–semantic mismatch / vocabulary gap**

- **Mechanism:** Hybrid BM25+dense scoring still fails when query uses different terminology than both the underlying leaves and the routing summaries (e.g., internal jargon vs user‑facing terms).
- **Triggers:** New tools whose user names differ from internal names; legacy jargon; abbreviations; multilingual content.
- **Severity:** Medium–high; the right branch may sit outside the top‑k children at some level.
- **Frequency:** Enterprise search studies emphasize vocabulary mismatch as a top cause of failure. In practice, expect a few to low‑double‑digit percent of queries unless you actively model synonyms.[^1_10]
- **Mitigations:** Synonym/alias dictionaries; entity linking; query expansion; multi‑vector encoders that capture synonyms better than BM25 alone.
- **Residual risk:** Medium but not unique to HCR.

***

**F8. Path‑relevance EMA “rich‑get‑richer”**

- **Mechanism:** Early small scoring differences at upper levels get smoothed into a path EMA (α=0.5). Once a path is slightly ahead, later evidence has reduced marginal impact, so beams tend to keep following early winners even if a sibling becomes more relevant deeper down.
- **Triggers:** Ambiguous or multi‑facet queries where several top‑level branches are moderately relevant; noisy or low‑contrast summaries early in the path.
- **Severity:** Medium for multi‑topic queries; for single‑branch queries EMA is mostly beneficial as a stabilizer.
- **Frequency:** Likely affects a non‑trivial portion of cross‑branch and exploratory queries (say 10–20%).
- **Mitigations:** Depth‑dependent α (higher weight on deeper evidence); occasional beam “resets” that allow late‑emerging branches back in; collapsed‑tree fallback when score deltas are small.
- **Residual risk:** Medium; this is a subtle but structural effect of cumulative routing.

***

**F9. Training–testing discrepancy under beam search**

- **Mechanism:** Even if node‑wise scorers are Bayes‑optimal, limited‑width beam search can systematically retrieve suboptimal leaves; there is an intrinsic “beam regret” that cannot be eliminated by improving local scorers alone.[^1_11][^1_12]
- **Triggers:** Trees with many near‑tie children; skewed class priors; node scorers trained without modeling beam‑search behavior.
- **Severity:** Medium: it sets a hard ceiling on achievable recall for any finite k.
- **Frequency:** Structural; present for all queries but most visible where true‑relevant branches are slightly less probable at many levels (long‑tail topics).
- **Mitigations:** Beam‑aware training (as in Zhuo et al.); modestly wider beams; exploration heuristics.
- **Residual risk:** Low for d≤2 and k≥3 under your ε; higher for deeper trees or more aggressive pruning.

***

### 1.4 Beam search traversal

These are partially consequences of F8/F9 but worth isolating.

**F10. Beam collapse (all beams converge to same region)**

- **Mechanism:** Due to EMA and correlated scores, the top‑k beams at each level all follow the same or very similar paths; effectively k=1.
- **Triggers:** Strong top‑level theme match; lack of diversity encouragement; highly skewed score distributions.
- **Severity:** High for cross‑branch queries; negligible for single‑branch ones.
- **Frequency:** Likely common on sharply topical queries (~half of informational queries in many logs), where collapse is actually correct; harmful collapse maybe in 10–20% of genuinely cross‑branch queries.
- **Mitigations:** Diversity‑aware beam heuristics; explicitly preventing all k beams from sharing the same parent at every step; entity‑based diversification.
- **Residual risk:** Medium for multi‑facet queries.

***

**F11. Score plateaus (near‑random branching)**

- **Mechanism:** Children of a node get very similar scores; selection among them is effectively noise. With small k and depth>1, error compounds as in RB‑002.
- **Triggers:** Over‑broad or generic summaries; queries that are only weakly related to the tree’s top‑level axes; very heterogeneous branches.
- **Severity:** High when it happens; plateau behaves like high ε.
- **Frequency:** Expect plateaus at some rate in any large KB; empirically, cluster‑based retrieval gains vanish or reverse when cluster similarity is low. For Su, perhaps 10–20% of queries at some node in the path.[^1_2][^1_1]
- **Mitigations:** Confidence measures on per‑node scores; switching to collapsed‑tree retrieval when margins are small; better contrastive summaries.
- **Residual risk:** Medium.

***

### 1.5 Leaf resolution and external pointers

**F12. Pointer staleness / broken or partial external references**

- **Mechanism:** Leaf nodes point to external systems (tickets, repos, wikis). Items are moved, access‑controlled, or deleted, leaving the pointer stale or incomplete.
- **Triggers:** System migrations; renames; permission changes.
- **Severity:** High when it happens: user sees missing or truncated context.
- **Frequency:** Proportional to churn in external systems; often low per month but accumulative over years.
- **Mitigations:** Regular pointer validation; “dirty” flags and automatic repair; reliance on stable IDs rather than URLs.
- **Residual risk:** Engineering‑dominant rather than architectural, but important.

***

**F13. Granularity mismatch at leaves**

- **Mechanism:** Leaf chunks are too large or too small relative to query needs. Too large → many irrelevant tokens wasted; too small → important supporting context omitted from selection.
- **Triggers:** Uniform chunk sizes across very different content types; ignoring document structure; not aligning to semantically atomic units.
- **Severity:** Medium; often degrades answer usefulness rather than making it impossible.
- **Frequency:** Common without careful design; with atomic propositions and AdaGReS, probably <10% of queries see serious granularity harm.
- **Mitigations:** Proposition‑level units; type‑specific chunking; adjacency heuristics for leaf selection.
- **Residual risk:** Low–medium.

***

### 1.6 Token‑budget packing (AdaGReS)

**F14. Redundancy‑only diversity that misses complementary evidence**

- **Mechanism:** AdaGReS optimizes relevance − redundancy under a budget. If all relevant chunks are moderately redundant (e.g., multiple mentions of a key fact) but differ in complementary details, the redundancy penalty can exclude chunks needed for full reasoning or aggregation.[^1_13][^1_14]
- **Triggers:** Multi‑hop/aggregation queries where different hops mention overlapping central entities or phrases.
- **Severity:** Medium–high; the model may get the core fact but miss important qualifiers, counts, or secondary facts.
- **Frequency:** Hard to quantify; in AdaGReS experiments redundancy control generally improves performance, *on average*. Failures are likely skewed toward complex multi‑fact queries.[^1_13]
- **Mitigations:** Task‑aware tuning of β (e.g., allow more redundancy for multi‑hop tasks); ensuring candidate pool already focuses on diverse aspects via cross‑branch defenses.
- **Residual risk:** Medium for aggregation/multi‑hop tasks.

***

**F15. Budget saturation for inherently large answers**

- **Mechanism:** Some queries cannot be adequately answered in 400 tokens, independent of routing (e.g., “summarize all architectural decisions for Project X across its history”).
- **Triggers:** Broad “summarize everything we know about Y,” exhaustive lists, large comparison sets, or dense multi‑hop research requests.
- **Severity:** High; user receives partial or shallow answers even with perfect retrieval.
- **Frequency:** For an internal assistant, probably a minority (maybe 5–15%) but often high‑value queries.
- **Mitigations:** Explicitly recognize and negotiate scope (“here is a high‑level summary; ask follow‑ups for drill‑down”); multi‑turn retrieval that allocates budget per sub‑question; task‑dependent budget increases.
- **Residual risk:** High but structural to the 400‑token constraint, not to HCR per se.

***

### 1.7 Maintenance \& drift

**F16. Summary staleness**

- **Mechanism:** Under incremental updates, internal node summaries lag behind; new topics or exceptions aren’t reflected, breaking routing and contrast.
- **Triggers:** Hot areas of the KB (rapidly updated policies, live projects); long rebuild cycles; failures in dirty‑flagging.
- **Severity:** Medium–high; summary staleness effectively increases ε for queries touching updated content.
- **Frequency:** Depends on refresh policy. In fast‑moving domains, studies of enterprise indexing show that without incremental updates, stale results and zero‑results grow quickly. With your dirty‑flag + periodic rebuild design, expect noticeable drift after ~20–30% of content changes.[^1_10]
- **Mitigations:** Aggressive dirty‑flagging; prioritizing re‑summarization of high‑traffic nodes; telemetry‑driven rebuild triggers.
- **Residual risk:** Medium.

***

**F17. Partition drift / distribution shift**

- **Mechanism:** Topic distribution shifts; historical partitions no longer align with how people query (e.g., new product lines, reorgs).
- **Triggers:** Major shifts in business focus, tools, or org structure; onboarding of large new corpora.
- **Severity:** High when shift is large; tree becomes misaligned with user mental models, inflating ε across many queries.
- **Frequency:** A few times per year in dynamic organizations; slow but inexorable drift otherwise.
- **Mitigations:** Monitoring query performance and “zero‑result” analytics; scheduled full rebuilds; adaptive branching at hot spots.
- **Residual risk:** Medium; requires active operations discipline.

***

**F18. Orphaned / stale cross‑links**

- **Mechanism:** Entity cross‑links and soft assignments refer to entities or leaves that move or disappear; cross‑branch defenses silently weaken.
- **Triggers:** Deletions, refactors, renames not propagated into the cross‑link graph.
- **Severity:** Medium for entity‑centric and multi‑branch entity queries.
- **Frequency:** Proportional to entity churn; moderate in active orgs.
- **Mitigations:** Periodic recomputation of entity graphs; deriving links from up‑to‑date NER rather than hand‑built lists.
- **Residual risk:** Low–medium.

***

### 1.8 Adversarial and edge‑case queries

**F19. Out‑of‑distribution (OOD) or content‑sparse queries**

- **Mechanism:** Queries on topics the KB does not cover, or that only appear in transient communications, match weakly or spuriously to existing branches.
- **Triggers:** Novel topics, future‑oriented hypotheticals, or external questions.
- **Severity:** High; either no relevant retrieval or misleading partial matches (hallucinated coverage).
- **Frequency:** For a well‑scoped KB assistant, perhaps low but non‑trivial (<10%).
- **Mitigations:** OOD detection; honest “I don’t know” behaviors; explicit routing to web tools when allowed.
- **Residual risk:** Inevitable; not specific to HCR.

***

**F20. Ambiguous queries**

- **Mechanism:** Queries with multiple plausible interpretations (e.g., “benefits policy” vs “benefits of policy X”) lead to arbitrary branch choices.
- **Triggers:** Short, context‑free queries; missing qualifiers.
- **Severity:** High if the system doesn’t clarify; recall is undefined because “answer” isn’t well‑posed.
- **Frequency:** Common in logs; many studies find 20–30% of web queries and a similar portion of enterprise queries are ambiguous or multi‑intent.[^1_15][^1_16]
- **Mitigations:** Clarification questions; multi‑intent retrieval (serve top interpretations in parallel); beam search helps only if you allow multiple distinct interpretations.
- **Residual risk:** Medium, but mostly UX/prompting.

***

**F21. Negation and complement queries**

- **Mechanism:** “What is *not* covered by policy X?”; “Which teams are *not* yet migrated?” require reasoning over *absence* across many branches. Hierarchical routing is optimized for positive topical similarity, not complements.
- **Triggers:** Compliance, coverage, gap analyses.
- **Severity:** High; routing finds where policy *is* discussed, not where it is missing; answers can be misleading (false sense of coverage).
- **Frequency:** Probably a small but important tail (<5%) in org KBs.
- **Mitigations:** Recognizing negation patterns and switching to specialized logic (e.g., structured data queries, explicit enumeration and subtraction); meta‑queries that ask the system about its own coverage.
- **Residual risk:** High for this niche; HCR is not a good fit without additional structured representations.

***

**F22. Meta‑queries over the tree itself**

- **Mechanism:** Questions like “what do we know about X?” or “how is the KB organized around Y?” require introspection over the index, not just the underlying documents.
- **Triggers:** Audits, knowledge‑gap analyses, schema introspection.
- **Severity:** Medium; the system may answer with content examples rather than structural overview or may miss gaps completely.
- **Frequency:** Rare for typical end‑users but important for KB admins.
- **Mitigations:** Dedicated tooling to query the tree and summary metadata directly.
- **Residual risk:** Low; orthogonal to core retrieval.

***

## 2. Cross‑branch queries in depth

### 2.1 Sub‑types, examples, and rough frequency

These are high‑level estimates for an enterprise KB used by an agentic assistant like Su:

- **Single‑branch queries (answer lives in one subtree):** Perhaps 60–80% of all queries. Typical examples: “What is our remote‑work policy?”; “How do I reset my VPN?”
- **Cross‑branch queries overall:** Roughly 20–40%, including:
– **Multi‑hop queries:** Need a chain of 2–3 facts across different documents/branches, e.g., “Which suppliers on Project Delta are over budget this quarter?”
    - Rough share: 5–15% in enterprise contexts, analogous to multi‑hop QA benchmarks where 2–4 supporting documents are required.[^1_17][^1_18]
– **Entity‑spanning queries:** Entity appears in multiple semantic contexts, e.g., “What projects is Alice involved in, and what incidents have been attributed to her code?”
    - Rough share: 10–20%.
– **Comparative queries:** “How does our UK parental‑leave policy differ from the US one?”
    - Rough share: 5–10%.
– **Aggregation queries:** “How many Sev‑1 incidents involved service X in 2025?”
    - Rough share: 5–10%.
– **Temporal/change queries:** “What changed in our promotion criteria between 2022 and 2025?”
    - Rough share: 5–10%.

Shares overlap (a query can be multi‑hop *and* comparative, etc.). Empirical work on multi‑hop RAG shows that purely single‑document questions dominate in standard QA benchmarks, but enterprise and agentic uses skew more multi‑hop and aggregative than web search.[^1_18]

### 2.2 Effectiveness of the five cross‑branch defenses

For each subtype, below is a qualitative assessment of each layer: 0=ineffective, 1=helps sometimes, 2=strong help but not sufficient alone, 3=near‑solve within HCR’s design.

**Legend:**
CD = content decomposition; SA = soft assignment; EX = entity cross‑links; BS = beam search; CT = collapsed‑tree fallback.

#### 2.2.1 Multi‑hop queries

- **Example:** “Which vendors used in Project Orion have unresolved security issues?”
Hop 1: find Orion vendors; Hop 2: find security issues about those vendors elsewhere.
- **Layer effectiveness:**
– CD: **2** — atomic propositions make it easier for both hops to be seen and matched separately.[^1_4]
– SA: **1–2** — helps if propositions legitimately belong under both “Project Orion” and “Vendor Security.”
– EX: **1** — entity links between vendors and incidents help some hops but not all.
– BS: **2** — allows exploration of multiple branches per hop, increasing chance of covering both sides. Beam‑based methods for multi‑hop retrieval show clear benefits over simple top‑k retrieval.[^1_18]
– CT: **2–3** — falling back to flat retrieval can approximate baseline multi‑hop top‑k RAG, which is competitive but not SOTA.[^1_17]
- **Expected recall after all defenses:** On multi‑hop QA benchmarks, graph‑ and proposition‑based systems reach Recall@5 in the high‑80s/90s. A tree‑structured HCR without explicit graph edges but with CD, SA, EX, and BS probably lands in the 75–90% range for 2–3‑hop queries where all hops live inside the KB. The long‑tail of more complex chains will be worse.[^1_19][^1_4]

***

#### 2.2.2 Entity‑spanning queries

- **Example:** “Show me everything on Alice’s role in the data‑migration project and any performance concerns raised about her.”
- **Layer effectiveness:**
– CD: **2** — ensures each mention of Alice is in a small, distinct unit.
– SA: **2–3** — leaves about Alice can be attached to multiple parents (people directory, projects, incidents).
– EX: **3** — this is the natural use case: cross‑branch entity graphs (Alice ↔ projects ↔ tickets). HippoRAG‑style KG indexing shows large gains on entity‑centric and multi‑hop queries vs vanilla vector RAG.[^1_20][^1_19]
– BS: **1–2** — helps discover different branches where Alice appears, especially when combined with entity‑aware scoring.
– CT: **1–2** — flat retrieval over entity mentions is strong but often swamped by high‑frequency names without graph structure.
- **Expected recall:** With decent entity extraction and cross‑links, entity‑centric recall can plausibly sit in the 85–95% range for well‑known entities; long‑tail names, ambiguous entities, and permissions issues pull this down.

***

#### 2.2.3 Comparative queries

- **Example:** “How does our on‑call compensation differ between SREs and support engineers?” (two distinct subtrees: SRE policies vs support policies.)
- **Layer effectiveness:**
– CD: **1–2** — makes each comparator’s policy slice explicit.
– SA: **1** — mild help if shared chunks are attached to both comparators; usually the policies are separate.
– EX: **1** — entity links (e.g., job families) can help, but not always present.
– BS: **2–3** — crucial: beams should straddle different branches (SRE vs Support). If routing is decent, beams can bring back both policy documents.
– CT: **2** — flat retrieval over both comparators often works well, provided the query mentions both names.
- **Expected recall:** 80–95% when both comparators are explicitly named and appear in reasonably distinct policy docs; much worse if the comparison is implicit (“current on‑call vs old system”).

***

#### 2.2.4 Aggregation queries

- **Example:** “How many Sev‑1 incidents involved the payments service in 2025?” (may require pulling many tickets scattered under different projects/teams, then aggregating.)
- **Layer effectiveness:**
– CD: **2** — each incident → proposition; easier counting.
– SA: **1–2** — incidents belong to both “payments” and “incident management” trees.
– EX: **2** — entity links between service and incidents help.
– BS: **1–2** — can pick up multiple incident clusters, but token budget will limit how many.
– CT: **1–2** — flat retrieval can find many incidents but still limited by top‑k and budget.
- **Expected recall:** For modest aggregations (tens of items), recall on *whether relevant items are seen at all* can be high (>90%), but recall on *complete aggregation* is inherently limited by budget. For enterprise analytics, graph or database queries outperform HCR or flat RAG here. This is one of the key residual risks.

***

#### 2.2.5 Temporal/change queries

- **Example:** “What changed in the remote‑work policy between 2021 and 2024?”
- **Layer effectiveness:**
– CD: **2** — each historical policy version and change note is its own unit.
– SA: **2** — policies can hang under both “remote‑work” and “policy history.”
– EX: **1–2** — entity links to policy IDs and version numbers help.
– BS: **2** — can retrieve multiple versions across time.
– CT: **2** — flat retrieval over policy names and dates is solid.
- **Expected recall:** If versioning is explicit and summaries mention dates/versions in key_terms, recall of *both old and new* policies for comparison can be 80–95%. More diffuse temporal questions (“how has incident rate changed over time?”) degrade toward aggregation‑query behavior.

***

### 2.3 Overall cross‑branch risk

- Cross‑branch queries are **not rare** in enterprise KBs, especially for an agentic system tasked with analysis and comparison. A working band of 20–40% of queries is reasonable.
- Your five‑layer defense is well aligned with best practices: PropRAG shows that proposition‑level decomposition plus beam search and graph‑like structure can reach Recall@5 of 87–94% on multi‑hop benchmarks.[^1_5][^1_4]
- However, HCR’s *tree‑only* structure lacks the fully general connectivity of a KG. Even with SA and EX, there will remain a material segment (particularly aggregation and global temporal queries) where recall is significantly below graph‑based or specialized analytic methods.

***

## 3. Query distribution in organisational knowledge bases

There is limited public data on *enterprise* log distributions for privacy reasons; Hawking explicitly notes that organizations rarely release query logs. Nonetheless:[^1_10]

### 3.1 Intent and structural categories

- **Informational vs navigational vs transactional:**
– Jansen et al. and related studies on web logs find ~80% informational, ~10% navigational, ~10% transactional queries.[^1_16]
– Hawking argues that the same taxonomy broadly applies to enterprise search, with examples:
    - Navigational: “HR”, “library”;
    - Transactional: “claim expenses”;
    - Informational: “IP policy”, “product xyz error 57”.[^1_10]
– For Su, focus is heavily on informational and some transactional (“file X”, “trigger workflow Y”); navigational is often abstracted away.
- **Single‑branch vs cross‑branch:**
– There is no direct measurement. Based on case studies of tasks (call‑center knowledge, proposal writing, expertise finding), many queries are “local” (single domain), but high‑value tasks like troubleshooting and analytics are inherently cross‑branch.[^1_10]
– A plausible band is:
    - Single‑branch: 60–80%.
    - Cross‑branch: 20–40%.
– For an *agentic* assistant tasked with cross‑cutting analysis, the cross‑branch share is likely toward the high end of this band.
- **Detail vs thematic:**
– In support and diagnostic contexts, a substantial fraction of queries include IDs, error codes, or entity names (detail‑heavy). Studies on technical search and software engineers’ logs suggest that 30–50% of queries include such specific identifiers.[^1_10]
– Thematic queries (“how do we handle customer data retention?”) remain the majority but detail queries are *over‑represented* in failure and high‑value cases.
- **Entity‑centric vs concept‑centric:**
– Enterprise scenarios Hawking describes (expertise finding, CRM, call‑center tasks) are often entity‑centric: people, customers, products, or systems.[^1_10]
– A rough split: 40–60% entity‑centric, 40–60% concept‑centric, varying by organization. Su’s workload (projects, tools, incidents, people) likely skews slightly entity‑heavy.


### 3.2 Differences vs academic benchmarks

- Multi‑hop QA benchmarks (HotpotQA, 2Wiki, MuSiQue, MultiHop‑RAG) assume cross‑document evidence is *the norm* (100% of queries). That overstates cross‑branch prevalence vs a typical KB, but is a good stress‑test distribution.[^1_17][^1_18]
- Enterprise queries are less carefully worded, more ambiguous, and more task‑driven; they also include many navigational and transactional intents largely absent from QA benchmarks.[^1_10]
- For Su, design and evaluation should therefore:
– Treat cross‑branch/multi‑hop queries as a *minority of all traffic but a majority of “hard” cases*;
– Weight evaluation toward these harder cases, since they are where HCR differs most from flat retrieval.

***

## 4. DPI and summarisation failure analysis

### 4.1 What gets lost

Evidence from hierarchical and multi‑document summarization shows that multi‑stage compression:

- Performs well on salient high‑level content but loses low‑frequency, local details, leading to lower recall of reference facts vs full‑context systems.[^1_7][^1_6]
- Is particularly prone to dropping:
– Rare entities and synonyms;
– Numbers, counts, and ranges;
– Exceptions and negations;
– Cross‑references (“see section 4.2 above”).

In HCR, this manifests as:

- **Routing failure** when the *only* discriminative cues live in these details and never make it into key_terms or includes.
- **Ranking degradation** when details matter only for final answer quality but not to decide which leaf to retrieve.


### 4.2 Effect of structured routing summaries

Your format `{theme, includes, excludes, key_entities, key_terms}` partially mitigates DPI:

- It forces the summarizer to surface:
– Entities and terms explicitly;
– Exclusions and exceptions;
– Multiple aspects beyond a single “theme.”
- This is conceptually similar to structured hierarchical summaries proposed in recent work, where multi‑aspect or facet‑driven clustering improves coverage.[^1_21][^1_22]

However:

- The channel is still narrow: a handful of fields vs the underlying text.
- If cluster heterogeneity is high (F1), the summarizer must decide which minority details to elevate; DPI guarantees that some potentially query‑critical ones are dropped.


### 4.3 When HCR becomes worse than flat similarity

HCR becomes strictly worse than flat retrieval when:

1. **Cluster heterogeneity is high** (cluster hypothesis not holding), so internal summaries cannot faithfully represent all relevant variants; experiments by Voorhees and others show cluster‑based retrieval can underperform sequential search in such settings.[^1_1][^1_2]
2. **Relevant evidence is weakly similar to any single cluster theme** (e.g., a rare combination of facets), so routing is noisy while flat retrieval can still retrieve relevant leaf chunks based on fine‑grained lexical/embedding similarity.
3. **Multiple routing layers compound noise** (F8/F9/F11), even though at leaf level your hybrid + cross‑encoder scoring is as strong as in the flat case.

Empirical analogues from summarization work show that compression‑based, hierarchical pipelines underperform full‑context methods in end‑to‑end accuracy once inputs can fit into a long‑context model, precisely because of multi‑stage information loss.[^1_6]

### 4.4 Relationship to corpus heterogeneity

- On narrow, homogeneous corpora (e.g., support tickets for a single product line), the cluster hypothesis roughly holds and HCR’s summaries mostly reinforce useful structure.[^1_1]
- On broad organisational KBs (policies + people + projects + code + configs), heterogeneity is high; cluster‑hypothesis failures can approach 40–50%.[^1_3][^1_1]
- In such settings, DPI failures are more frequent and more damaging; routing error ε will concentrate on these broad, cross‑facet queries.

***

## 5. Beam search failure analysis

### 5.1 Failure modes

**Beam collapse and plateaus (F10/F11)** have already been described: they effectively raise ε by either:

- Making k>1 behave like k=1 (collapse), or
- Making branch choice effectively random (plateau).

**Training–testing discrepancy:** Zhuo et al. show that optimizing node‑wise scorers for per‑node accuracy does *not* yield optimal retrieval under beam search; there is an intrinsic regret due to limited beam width even with Bayes‑optimal scores. This maps directly onto HCR: improving per‑node ε from, say, 0.02 to 0.01 doesn’t linearly translate to end‑to‑end recall because of beam truncation.[^1_12][^1_11]

### 5.2 Theoretical recall floor for your parameters

Using the approximation from RB‑002:

- Let ε be per‑level probability that the correct child *is not* selected when k=1; you assume ε≈0.02, so per‑level success p≈0.98.
- With beam width k and assuming independence, per‑level success becomes approximately:

$$
p_k = 1 - (1-p)^k
$$
- For p=0.98 and k=3:

$$
p_3 = 1 - (0.02)^3 = 1 - 8 \times 10^{-6} = 0.999992
$$
- Over depth d=2, assuming independent levels:

$$
\text{Recall} \approx p_3^2 \approx 0.999984
$$

So under optimistic assumptions (independent errors, correct child always among top‑3 per‑node scores with probability ~0.999992), the *theoretical* floor is ~99.998% recall. In practice:

- Errors are not independent across levels.
- ε=0.02 likely already *includes* some effect of ambiguity and plateaus.
- Beam collapse and miscalibration reduce the effective p_k.

A more realistic stance is:

- With d=2, b≈10, k=3–5, and well‑behaved summaries, overall end‑to‑end routing error for *single‑branch*, well‑clustered queries can plausibly be pushed below 2–3%.
- For cross‑branch and heterogeneous cases, effective ε is higher and p lower; beam search still substantially improves recall relative to single‑path (as also observed in multi‑hop QA beam‑retrieval work) but will not achieve the near‑100% theoretical bound.[^1_18]


### 5.3 Cases where beam search underperforms flat retrieval regardless of k

- **Globally rare branches:** If the relevant leaves live on paths that look weakly relevant at *all* levels (long‑tail topics, rare combinations of facets), then p is small at each node; even large k cannot compensate because those branches rarely enter the beam. Flat retrieval, which scores all leaves at once, may still surface them.
- **Adversarial or noisy scores:** If summaries or scorers are miscalibrated in ways that consistently downweight a topic (e.g., missing critical terms in key_terms), beam search will systematically ignore those branches.
- **Severe plateaus:** When score distributions are flat across many branches, branch selection is essentially random; then HCR reduces to sampling a small subset of leaves, which will be inferior to a well‑tuned flat top‑k.

***

## 6. Maintenance and drift failures

There is limited *quantitative* data on hierarchical retrieval drift, but enterprise indexing experience is instructive.[^1_10]

- **Summary staleness:** Without regular refresh, internal metadata (topics, dates, owners) diverge from reality, leading to increased zero‑result queries and user dissatisfaction. Similar dynamics will apply to LLM summaries.
- **Incremental index degradation:** Hawking notes that incremental updates can fragment indexes and slow queries; content churn without reorganization leads to growing inefficiency and stale results. For HCR, incremental insertion without global reclustering leads to:[^1_10]
– Overcrowded or misaligned clusters as new topics appear;
– Pathological branch factors at hot nodes;
– Growing mismatch between user query patterns and the tree structure.

Your plan—incremental “insert/repair” with periodic full rebuild after 20–30% new content—is aligned with standard practice in large intranets. Nevertheless:[^1_10]

- **Fastest degradation** will occur in:
– Hot policy areas with frequent small changes;
– Fast‑moving project spaces;
– People and org structures after reorgs.
- **Breakdown point:** While not empirically pinned down, a reasonable operational rule would be:
– If >30–40% of leaves have been touched (inserted/updated) since last build in a given subtree, expect noticeable routing degradation (effective ε rising significantly) and schedule local or global rebuild.
– Telemetry (drop in hit‑rate, rise in user reformulations) should drive these thresholds.

***

## 7. Interaction with the 400‑token budget

### 7.1 Failure amplification

- As RB‑002 noted, budgeted RAG amplifies both upside and downside: with correct routing, 400 tokens of highly relevant content is more than enough for most single‑branch and many cross‑branch queries; with misrouting, the same 400 tokens are almost entirely wasted.
- In enterprise settings, a large fraction of answerable queries can be handled with even less; some event‑summarization work shows that retrieval‑based or light compression methods can match or exceed full‑context models for many tasks when selection is good.[^1_6]

**When routing fails:**

- If routing completely misses the relevant subtree, AdaGReS cannot recover; it only optimizes over the *candidate pool*. All 400 tokens are allocated among irrelevant leaves.
- For partial routing failures (some relevant, some irrelevant leaves in the pool), AdaGReS’s redundancy penalty tends to *prioritize the few relevant chunks*, which gives some resilience: even if half the candidate pool is noise, AdaGReS will devote most of the 400 tokens to the genuinely high‑relevance chunks.[^1_14][^1_13]


### 7.2 Minimum viable context by query type

Approximate guidance:

- **Simple factual/thematic queries:** 100–200 tokens is often enough if the relevant clause is present verbatim. 400 tokens is ample; routing dominates.
- **Multi‑hop 2‑step queries:** 200–300 tokens typically suffice to include both hops plus a little framing; 400 tokens are comfortable.
- **Comparative queries between 2–3 items:** 300–400 tokens is acceptable if you select only the differential parts of each policy or doc; naive chunk selection that repeats irrelevant boilerplate will hit the limit.
- **Aggregations and large lists:** 400 tokens are often *not* enough for full enumeration; at best you can surface representative examples and summary statistics if they exist.
- **Temporal/change‑over‑time:** Comparing two or three versions of a policy is fine within 400 tokens; full‑history “what changed over 10 years?” is not.

So:

- There **are** query types where no amount of routing can produce a fully satisfactory answer under 400 tokens (global aggregation, exhaustive lists, long histories, some rich multi‑hop research questions). For these, you need either multi‑turn workflows or separate analytic subsystems.

***

## 8. HCR vs flat retrieval: failure‑mode comparison

### 8.1 Where HCR introduces new failure modes

Compared to flat similarity + reranking (on which RAPTOR, PropRAG, etc. are built):

- **Structural routing errors (F1, F8–F11):** Mispartitioned clusters, beam‑regret, and EMA “lock‑in” are unique to hierarchical traversal; flat retrieval evaluates all candidates at once.
- **Summary‑induced failures (F4–F6):** DPI and hallucinated hooks directly affect *routing* in HCR, whereas in flat RAG summaries are usually post‑hoc or purely for compression, not gating.
- **Maintenance drift of the index structure (F16/F17):** Flat retrieval still suffers staleness, but there is no global structure whose misalignment systematically prevents certain paths from ever being explored.
- **Beam‑search specific artifacts:** Beam collapse and plateaus matter far more in a tree than in flat retrieval, where beam is used only for re‑ranking at the tail.


### 8.2 Where HCR is strictly better than flat retrieval

Empirically:

- **Long documents and hierarchical reasoning:** RAPTOR’s recursive tree‑organised retrieval significantly outperforms traditional flat RAG on long‑document QA and multi‑step reasoning tasks, including a 20‑point absolute improvement on QuALITY when combined with GPT‑4.[^1_23][^1_24][^1_25]
- **Proposition‑level retrieval and multi‑hop:** PropRAG and similar proposition/graph approaches, which your design echoes through CD+EX+BS, achieve SOTA Recall@5 and F1 on multi‑hop datasets, beating flat passage retrieval by several points.[^1_5][^1_19][^1_4]
- **Token efficiency:** Hierarchical index retrieval with summaries demonstrates that starting with high‑level summaries and drilling down can “significantly narrow the search space” and improve both efficiency and quality when documents are long and multi‑section.[^1_26]

Architecturally:

- HCR allows *scale‑sensitive* retrieval: the system can choose between abstract summaries and raw leaves depending on budget and question, something flat retrieval cannot do naturally.
- HCR plus AdaGReS is better positioned to maximize utility per token than flat top‑k, which wastes budget on redundant near‑neighbors.[^1_14][^1_13]


### 8.3 Net failure‑mode risk profile

- On **single‑branch**, well‑clustered queries over long documents, HCR is strictly better: fewer failures and higher utility per token than flat retrieval, as RAPTOR‑style results show.[^1_24][^1_23]
- On **cross‑branch and highly heterogeneous queries**, HCR introduces new sources of failure (routing, beam, DPI), making it sometimes strictly worse than a strong flat retriever + reranker, especially for long‑tail, global, or aggregative queries.
- On **maintenance and drift**, both approaches degrade if not maintained, but HCR’s failures can be sharper (entire subtrees effectively “fall off the map”).

Overall, HCR is not dominated by flat retrieval: it trades *localized, diagnosable* structural risks for better performance on long‑context, multi‑level reasoning and token efficiency.

***

## 9. Residual risk assessment and Phase‑1 go/no‑go

### 9.1 Expected overall failure rate (answerable but missed due to retrieval)

Given all the above, a reasonable ballpark for Su’s target domain:

- **Single‑branch, informational and detail queries (≈60–80% of load):**
– With ε≈0.01–0.02, d=2, k=3–5, strong summaries, and AdaGReS, end‑to‑end retrieval recall in the **95–99%** range is plausible. Most residual failures come from vocabulary mismatch and DPI on extreme detail queries.
- **Cross‑branch / multi‑hop / comparative / temporal queries (≈20–40%):**
– With your five‑layer defense, expected recall is highly subtype‑dependent:
    - Entity‑centric multi‑branch queries: perhaps **85–95%**.
    - Simple 2‑hop queries: **75–90%**.
    - Comparisons between 2–3 clearly named entities/policies: **80–95%**.
    - Aggregation and broad temporal analytics: often **<70–80%** effective for full coverage under 400 tokens, though many will still yield partially useful answers.
- **Additional failures from maintenance/drift, ambiguity, and OOD:** add perhaps another few percent.

Putting this together:

- A rough *overall* band for “answerable but materially mishandled by retrieval” is on the order of **10–20%** of queries, with:
– Lower end (~10%) achievable under good maintenance, narrowish scope, and strong operational monitoring;
– Higher end (~20%) likely for larger, more heterogeneous, fast‑changing KBs.

These numbers are **uncertain** and extrapolated from adjacent literature; actual HCR performance will require empirical validation.

### 9.2 Biggest remaining risks

1. **High‑fan‑out aggregation and temporal comparison queries (structural):**
– HCR (and flat RAG) are ill‑suited for “exhaustive list” or “global stat” questions under 400 tokens. These should eventually be routed to specialized analytic pipelines (SQL/OLAP + summarization) or graph engines.
2. **Cluster‑hypothesis violations in a broad KB (architectural):**
– If top‑level partitions don’t align with how users think and query, routing ε will be higher than assumed, especially for cross‑facet questions. This risk can only be reduced, not eliminated, by CD/SA/EX.
3. **Maintenance and drift (operational but impactful):**
– Without disciplined rebuilds and summary refresh, HCR quality will silently decay, and structural errors will dominate.
4. **DPI on detail and exception queries (architectural):**
– No summarization scheme can be lossless; there will always be a tail of queries for which routing fails because the necessary detail never appears in summaries.

### 9.3 Is there a showstopper?

For the **Phase‑1 goal**—token‑efficient retrieval for an internal agent over a mixed organisational KB under ~400 tokens—there is **no evidence of an architectural showstopper**:

- Tree‑organised retrieval with summaries has been shown to outperform flat RAG on relevant tasks (complex QA, long documents).[^1_23][^1_24]
- Multi‑hop and cross‑branch challenges can be substantially mitigated with proposition‑level units, beam search, and entity/soft‑assignment structures, as PropRAG and graph‑based systems demonstrate.[^1_19][^1_20][^1_4]
- The primary failure modes are *bounded* and *well‑understood* from both classical IR (cluster hypothesis, DPI) and modern RAG literature.

However, HCR is **not sufficient on its own** for:

- Enterprise‑scale analytics, global aggregations, and strict coverage/negation questions.
- Long‑term operation without careful monitoring and periodic tree reconstruction.


### 9.4 Recommendation for Phase‑1

A reasonable stance is:

- **Go for Phase‑1**, with explicit acknowledgement that:
– Cross‑branch and aggregative queries are the main structural risk and must be over‑represented in your evaluation (RB‑006).
– Success criteria for Phase‑1 should be asymmetrical: very high reliability on single‑branch/detail/thematic queries, and “good but not perfect” performance on cross‑branch queries, with a roadmap toward graph/analytic augmentations for the hardest cases.
– Operational metrics (per‑query retrieval diagnostics, “zero‑result” or “low‑evidence” detection, user reformulation rates) are critical to catch drift and structural blind spots early.

If Phase‑1 experiments reveal significantly worse performance on cross‑branch queries than this analysis suggests (e.g., recall <60–70% even with all defenses), that would be a signal to introduce *graph‑based* or *multi‑index* retrieval alongside HCR, rather than abandon the architecture outright.
<span style="display:none">[^1_27][^1_28][^1_29][^1_30][^1_31][^1_32][^1_33][^1_34][^1_35][^1_36][^1_37][^1_38][^1_39][^1_40][^1_41][^1_42][^1_43][^1_44][^1_45][^1_46][^1_47][^1_48][^1_49][^1_50][^1_51][^1_52][^1_53][^1_54][^1_55][^1_56][^1_57][^1_58][^1_59][^1_60][^1_61][^1_62][^1_63][^1_64][^1_65][^1_66][^1_67][^1_68][^1_69][^1_70][^1_71][^1_72][^1_73][^1_74][^1_75][^1_76][^1_77][^1_78][^1_79][^1_80][^1_81][^1_82][^1_83][^1_84][^1_85][^1_86][^1_87][^1_88]</span>

<div align="center">⁂</div>

[^1_1]: https://dl.acm.org/doi/pdf/10.1145/253495.253524

[^1_2]: https://people.ischool.berkeley.edu/~hearst/papers/sigir96.pdf

[^1_3]: http://sigir.hosting.acm.org/wp-content/uploads/2017/06/p0351.pdf

[^1_4]: https://arxiv.org/pdf/2504.18070v2.pdf

[^1_5]: https://www.ideals.illinois.edu/items/136262/bitstreams/445380/data.pdf

[^1_6]: https://arxiv.org/pdf/2502.06617.pdf

[^1_7]: https://www.cse.iitd.ac.in/~mausam/papers/acl14.pdf

[^1_8]: https://aclanthology.org/2024.lrec-main.423.pdf

[^1_9]: https://arxiv.org/html/2401.18059v1

[^1_10]: http://david-hawking.net/pubs/ModernIR2_Hawking_chapter.pdf

[^1_11]: http://proceedings.mlr.press/v119/zhuo20a/zhuo20a.pdf

[^1_12]: https://arxiv.org/pdf/2006.15408.pdf

[^1_13]: https://arxiv.org/abs/2512.25052

[^1_14]: https://arxiv.org/html/2512.25052v1

[^1_15]: https://faculty.ist.psu.edu/jjansen/academic/pubs/jansen_search_log_analysis.pdf

[^1_16]: https://researchportal.hbku.edu.qa/en/publications/determining-the-informational-navigational-and-transactional-inte

[^1_17]: https://github.com/yixuantt/MultiHop-RAG

[^1_18]: https://arxiv.org/html/2601.00536v1

[^1_19]: https://graphwise.ai/blog/from-retrieval-to-reasoning-enhancing-hipporag-with-graph-based-semantics/

[^1_20]: https://arxiv.org/html/2405.14831v1

[^1_21]: https://www.emergentmind.com/topics/hierarchical-nl-summaries

[^1_22]: https://www.emergentmind.com/topics/hierarchical-summarization

[^1_23]: https://arxiv.org/abs/2401.18059

[^1_24]: https://www.deeplearning.ai/the-batch/raptor-a-recursive-summarizer-captures-more-relevant-context-for-llm-inputs/

[^1_25]: https://openreview.net/forum?id=GN921JHCRw\&noteId=rquBHNygEX

[^1_26]: https://pixion.co/blog/rag-strategies-hierarchical-index-retrieval

[^1_27]: https://mirasvit.com/blog/three-types-of-search-queries-navigational-informational-transactional.html

[^1_28]: https://www.cs.cmu.edu/~callan/Papers/tois15-akulkarni.pdf

[^1_29]: https://moz.com/blog/revisiting-navigational-informational-transactional-search-post-pagerank

[^1_30]: https://liner.com/review/learning-optimal-tree-models-under-beam-search

[^1_31]: https://enterprise-knowledge.com/the-4-steps-to-designing-an-effective-taxonomy-1-design-a-user-centric-taxonomy/

[^1_32]: https://aclanthology.org/2025.emnlp-main.222.pdf

[^1_33]: https://i656e74657270726973652d6b6e6f776c65646765o636f6dz.oszar.com/the-4-steps-to-designing-an-effective-taxonomy-1-design-a-user-centric-taxonomy/

[^1_34]: https://arxiv.org/html/2508.14515v1

[^1_35]: https://www.kminstitute.org/blog/design-a-user-centric-taxonomy

[^1_36]: https://pmc.ncbi.nlm.nih.gov/articles/PMC2730439/

[^1_37]: https://huggingface.co/papers/2401.18059

[^1_38]: https://www.themoonlight.io/en/review/adagresadaptive-greedy-context-selection-via-redundancy-aware-scoring-for-token-budgeted-rag

[^1_39]: https://arxiv.org/pdf/2504.18070.pdf

[^1_40]: https://github.com/parthsarthi03/raptor

[^1_41]: https://www.studocu.com/tw/document/national-taiwan-university/machine-learning-techniques/adaptive-greedy-context-selection-for-rag-2512/149971406

[^1_42]: https://github.com/profintegra/raptor-rag

[^1_43]: https://arxiv.org/html/2601.20055v1

[^1_44]: https://www.linkedin.com/posts/nishantha-ruwan-15b301b2_adagresadaptive-greedy-context-selection-activity-7413291979989561344-UUXk

[^1_45]: https://www.youtube.com/watch?v=bg0WX7Ewe6I

[^1_46]: https://pubs.rsc.org/en/content/articlehtml/2023/dd/d3dd00112a

[^1_47]: https://chenli.ics.uci.edu/files/instant-search-log-analysis-webdb12.pdf

[^1_48]: https://xenoss.io/blog/enterprise-knowledge-base-llm-rag-architecture

[^1_49]: https://www.marketinginasia.com/types-of-searches-navigational-informational-transactional/

[^1_50]: https://www.kore.ai/blog/enterprise-search-how-ai-powered-search-boosts-work-productivity

[^1_51]: https://smartdev.com/de/rag-implement-enterprise-kb-with-ai-qa/

[^1_52]: https://tmd.com.au/search-query-types

[^1_53]: https://www.moveworks.com/us/en/resources/blog/enterprise-search-analytics-for-optimized-search-performance

[^1_54]: https://coralogix.com/ai-blog/rag-in-production-deployment-strategies-and-practical-considerations/

[^1_55]: https://searchxpro.com/4-types-of-keyword-intent-explained/

[^1_56]: https://www.unily.com/resources/guides/ultimate-guide-to-intranet-search

[^1_57]: https://aws.amazon.com/bedrock/knowledge-bases/

[^1_58]: https://www.semrush.com/blog/types-of-keywords-commercial-informational-navigational-transactional/

[^1_59]: https://www.informatica.com/resources/articles/enterprise-rag-data-ingestion.html

[^1_60]: https://www.webpro.in/understanding-different-types-of-search-queries-in-traditional-and-ai-powered-search/

[^1_61]: https://powell-software.com/solutions/knowledge-management/

[^1_62]: https://website-chamaeleon.de/content-management/what-are-the-different-types-of-search-queries/

[^1_63]: https://www.seo-theory.com/how-web-marketers-should-classify-search-queries/

[^1_64]: https://www.hubengage.com/employee-intranet/intranet-search-engine/

[^1_65]: https://www.linkedin.com/pulse/3-types-search-queries-how-approach-them-impress-bss

[^1_66]: https://www.scoutos.com/blog/ai-intranet-search-streamlined-knowledge-access

[^1_67]: https://ajw.design/blog/classificiation-of-search-queries/

[^1_68]: https://www.3kites.com/single-post/leveraging-intranets-as-a-knowledge-management-tool-within-the-legal-sector-part-ii-know

[^1_69]: https://www.webfx.com/blog/seo/types-of-search-queries/

[^1_70]: https://www.immwit.com/wiki/query-classification/

[^1_71]: https://www.tricension.com/news/harnessing-enterprise-search-to-boost-knowledge-management-tricension-2

[^1_72]: https://en.wikipedia.org/wiki/Lossy_compression

[^1_73]: https://www.linkedin.com/pulse/feed-raptor-pigeon-how-hierarchical-chunking-turns-rag-ercin-dedeoglu-io88f

[^1_74]: https://pmc.ncbi.nlm.nih.gov/articles/PMC8907274/

[^1_75]: https://pmc.ncbi.nlm.nih.gov/articles/PMC7065005/

[^1_76]: https://arxiv.org/html/2502.00977v2

[^1_77]: https://www.dc.fi.udc.es/~roi/publications/rblanco-phd.pdf

[^1_78]: https://memgraph.com/blog/how-microsoft-graphrag-works-with-graph-databases

[^1_79]: https://shrsv.github.io/p/about-hipporag/

[^1_80]: https://www.youtube.com/watch?v=LV0jRVXtx80

[^1_81]: https://dev.to/shrsv/about-hipporag-3mf6

[^1_82]: https://learnwithparam.com/blog/multi-hop-rag-query-decomposition

[^1_83]: https://microsoft.github.io/graphrag/

[^1_84]: https://www.microsoft.com/en-us/research/project/graphrag/

[^1_85]: https://www.zyphra.com/post/understanding-graph-based-rag-and-multi-hop-question-answering

[^1_86]: https://aiexpjourney.substack.com/p/a-rag-solution-for-multi-hop-question

[^1_87]: https://graphrag.openml.io

[^1_88]: https://aclanthology.org/2025.emnlp-main.1328.pdf


# RB-005: Failure Modes — Claude Response

# Comprehensive failure mode analysis for hierarchical coarse-to-fine retrieval

**The HCR architecture's deepest vulnerability is not cross-branch queries — it is the interaction between DPI-induced information loss in routing summaries and the tight 400-token budget, which together create a failure envelope affecting an estimated 15–25% of organizational queries.** No single failure mode is a clear showstopper, but the compounding of routing errors, summary lossiness, and budget constraints produces residual risk substantially higher than the headline 96% recall figure suggests. The five-layer cross-branch defense is well-designed but cannot overcome information-theoretic limits: when thematic summaries lack the detail a query targets, no amount of beam search or soft assignment recovers the lost routing signal. This analysis identifies 21 distinct failure modes across all pipeline stages, decomposes cross-branch queries into 6 sub-types, and provides quantitative risk estimates grounded in empirical data where available.

---

## 1. Complete failure taxonomy across all pipeline stages

The following taxonomy organizes failure modes by the pipeline stage where they originate. Each failure mode is classified as **architectural** (inherent to the design, not fixable by implementation quality) or **engineering** (reducible through careful implementation). Severity is rated on impact when triggered; frequency is estimated for an organizational knowledge base.

### Tree construction failures

**FM-01: Cluster boundary misplacement.** Bisecting k-means optimizes geometric separation in embedding space, which does not necessarily align with query-relevant topical boundaries. Documents about "remote work policy" and "remote work tooling" may be semantically close but serve entirely different query intents. When relevant documents are split across sibling clusters, routing must discover both branches — converting a single-branch query into an artificial cross-branch query. **Severity: High** (the correct leaf becomes unreachable via any single path). **Frequency: ~10–20%** of documents sit near cluster boundaries based on IVF index research showing multi-probe retrieval is routinely needed. **Mitigations: Soft assignment (Layer 2) directly addresses this; beam search (Layer 4) provides secondary coverage.** Residual risk after mitigation: Low for documents with 2–3 parent assignments; moderate for documents with only 1 parent near a boundary. **Type: Architectural** — bisecting k-means will always produce some misaligned boundaries.

**FM-02: Heterogeneity-induced shallow cluster separation.** Organizational knowledge bases are among the most heterogeneous corpora in existence — mixing policies, meeting notes, technical docs, people directories, and communications across radically different vocabularies and structures. Voorhees (1985) found that **46% of relevant documents had zero relevant neighbors among their 5 nearest neighbors** in the broad INSPEC collection (12,684 documents). The cluster hypothesis fails most dramatically on exactly the type of broad, heterogeneous collection that characterizes an organizational knowledge base. At depth 2–3 with branching factor 6–15, the top-level split must separate perhaps 8–12 fundamentally different content types, but cross-cutting concerns (e.g., a project that touches policy, technology, and people) defy clean separation. **Severity: High.** **Frequency: Persistent** — affects the global tree structure. **Mitigations: Content decomposition (Layer 1) helps by splitting multi-topic documents into atomic units; entity cross-links (Layer 3) bridge the gaps.** Residual risk: Moderate-high. Raiber & Kurland (2014) showed that cluster hypothesis test scores can be **negatively correlated** with actual retrieval effectiveness, meaning the tree may look well-structured by internal metrics while performing poorly on real queries. **Type: Architectural.**

**FM-03: Branching factor mismatch.** With branching factor 6–15, the system must balance discrimination (more branches = more specific routing summaries) against scoring reliability (more branches = harder to rank correctly). At b=15 with beam k=3, the system evaluates 15 children and keeps 3 — a 5:1 rejection ratio. If the scorer's discrimination ability degrades for similar-scoring siblings, the effective error rate rises. **Severity: Moderate.** **Frequency: Depends on corpus structure; worst for homogeneous sub-topics.** **Mitigations: The scoring cascade (BM25+dense → cross-encoder rerank) is specifically designed to maximize discrimination. Beam width k=3–5 provides margin.** Residual risk: Low at b=6–10, moderate at b=15. **Type: Engineering** — tunable.

### Summary generation failures

**FM-04: DPI information loss — the structural failure case.** This is the most theoretically grounded failure mode. By the Data Processing Inequality, the Markov chain Documents → Summaries → Query-Summary Match guarantees that **I(Documents; Match) ≤ I(Documents; Summary)**. Information is provably and irreversibly lost. The FRANK benchmark (Pagnoni et al., NAACL 2021) quantified factual errors in abstractive summaries: **35.85% predicate errors, 33.75% entity errors, 10.55% circumstance errors** (time, location, manner). Even the structured routing summary format (`{theme, includes, excludes, key_entities, key_terms}`) cannot preserve all queryable details — specific dates, version numbers, conditional logic, procedural steps, and quantitative thresholds are systematically dropped. When a query targets these lost details ("What is the expense reimbursement deadline for Q3?" where the summary captures "expense policy" but not "Q3 deadline"), routing becomes near-random at that level. **Severity: Critical** — converts a good scorer into a near-random one for affected queries. **Frequency: Estimated 20–35%** of organizational queries target specific facts or identifiers (see Section 3). **Mitigations: The structured summary format partially addresses this by explicitly listing key_entities and key_terms, preserving more routing-relevant signals than free-text summaries. Entity cross-links (Layer 3) help for entity-centric detail queries. Collapsed-tree fallback (Layer 5) is the true safety net.** Residual risk: **High** — this is the single largest residual risk. When the fallback triggers, the system effectively abandons hierarchical routing. **Type: Architectural** — fundamental information-theoretic limit.

**FM-05: Summary hallucination.** LLM-generated summaries can introduce fabricated content. RAPTOR's hallucination analysis (Sarthi et al., ICLR 2024, Appendix E) found hallucinated content in sampled summary nodes from GPT-3.5 generation, though impact on downstream QA was limited. Williams et al. (2024) found **42% of GPT-4 emergency department summaries contained hallucinated details**. For routing summaries, hallucinated entities in `key_entities` or fabricated themes would misdirect queries to wrong branches. An `excludes` field that incorrectly excludes a topic that IS present would cause systematic routing failure for that topic. **Severity: High when triggered** (systematic misdirection). **Frequency: Low-moderate** (~5–15% of summaries may contain some hallucinated detail, based on RAPTOR findings, but most won't affect routing decisions). **Mitigations: Validation during summary generation (cross-checking entities against actual cluster contents); periodic summary audit.** Residual risk: Low if validation is implemented. **Type: Engineering.**

**FM-06: Summary staleness.** When documents are added, updated, or removed, parent summaries become stale. The dirty-flag lazy regeneration system addresses this, but there is a latency window where stale summaries route queries incorrectly. In an organizational knowledge base, policies change quarterly, project docs change continuously, and people information changes with **15–20% annual turnover**. A stale routing summary that still lists a departed team member as a key entity, or describes a superseded policy as current, will misdirect queries during the staleness window. Research on HNSW indexes shows that after ~3,000 update operations, **3–4% of data points become unreachable** and **recall drops ~3%** (Xiao et al., 2024). Hierarchical indexes degrade faster than flat indexes because leaf changes invalidate parent summaries up the tree. **Severity: Moderate.** **Frequency: Proportional to content churn** — in an active organizational KB, some summaries will always be stale. **Mitigations: Dirty-flag system with lazy regeneration; periodic full rebuild at 20–30% threshold.** Residual risk: Low-moderate during normal operations; high during periods of rapid organizational change (reorgs, policy overhauls). **Type: Engineering.**

### Scoring and routing failures

**FM-07: Hybrid scorer blind spots.** The BM25+dense pre-filter combines lexical and semantic signals, but each component has documented failure modes. BM25 fails on vocabulary mismatch (paraphrased queries, synonyms) — its top-1 passage recall on Natural Questions is only **22.1%** vs. DPR's 48.7%. Dense retrieval fails on domain-specific terminology, rare entities, and out-of-domain queries — on BEIR, DPR underperformed BM25 on 17 of 18 out-of-domain datasets (Thakur et al., NeurIPS 2021). The hybrid partially compensates, but neither component handles negation well, and both struggle with multi-condition queries. **Severity: Moderate.** **Frequency: ~5–10%** of queries hit blind spots in both components simultaneously. **Mitigations: Cross-encoder reranking as second stage catches many pre-filter errors. The ExcluIR benchmark shows cross-encoders handle exclusionary queries better than bi-encoders.** Residual risk: Low for simple queries; moderate for negation/multi-condition queries. **Type: Engineering.**

**FM-08: Cross-encoder truncation and multi-condition degradation.** Most cross-encoder models truncate input at **512 tokens**. If a routing summary exceeds this limit (plausible for rich structured summaries of large clusters), discriminative content in the `excludes` or `key_terms` fields may be truncated. More critically, the MultiConIR benchmark demonstrates that cross-encoder rerankers suffer **"severe performance degradation as query complexity increases"** — multi-condition organizational queries ("meeting notes from the engineering team about the Q3 deadline for the migration project") compound multiple constraints that stress the cross-encoder's discriminative capacity. Jacob et al. (2024) showed that cross-encoders can assign high scores to documents with **no lexical or semantic overlap** with the query when scoring too many candidates. **Severity: Moderate-high for complex queries.** **Frequency: ~10–20%** of organizational queries have 3+ conditions. **Mitigations: Limiting reranking to top-3 candidates (per the cascade design) avoids the over-scoring failure. Keeping summaries under 512 tokens avoids truncation.** Residual risk: Moderate for complex queries. **Type: Engineering** (partially) / **Architectural** (the multi-condition degradation is inherent to pointwise scoring).

**FM-09: Score plateau — near-random selection among similar siblings.** When sibling cluster summaries are too similar (common at deeper levels where sub-topics converge), all children score within a narrow band. The top-3 selection becomes effectively random. In the extreme, if 10 siblings all score within ±0.01, the probability of selecting the correct child drops from 0.98 toward the random baseline of **3/10 = 0.30**. Score plateaus are most likely when the query is broad and matches the parent's theme without discriminating between children, or when sibling clusters have significant content overlap. **Severity: High** (converts to near-random routing at that level). **Frequency: ~5–15%** of query-node combinations, concentrated at deeper tree levels where clusters are more fine-grained. **Mitigations: Contrastive routing summaries with explicit `excludes` fields are specifically designed to maximize inter-sibling discrimination. Beam search provides resilience (3 beams at a plateau level gives ~1-(7/10)^3 ≈ 66% chance of including the correct child, vs. 30% with greedy).** Residual risk: Moderate. **Type: Architectural** — some queries will always match multiple siblings equally.

### Beam search failures

**FM-10: Beam collapse.** All k beams converge to the same branch or highly overlapping branches, providing no diversity benefit. This occurs when one branch dominates scoring by a large margin for a given query, or when the path-relevance EMA (α=0.5) amplifies an early advantage. As noted in beam search literature: "the branches will often converge to k states that are all very similar to each other. If this happens, we pay the expense of maintaining k branches but effectively only gain the benefits of one." **Severity: High** (reduces effective beam width to 1, eliminating cross-branch coverage). **Frequency: ~15–25%** of queries, particularly focused queries with a single clearly dominant topic. **Mitigations: Diversity penalties could be applied to beam selection, but are not currently in the design. The entity cross-links (Layer 3) partially compensate by providing alternative discovery paths.** Residual risk: Moderate-high. This is a **gap in the current design** — no explicit diversity mechanism prevents beam collapse. **Type: Engineering** (addressable with diversity-aware beam selection).

**FM-11: Compounding error across depth.** With ε=0.02 per level and d=2, the expected recall is (0.98)² = **96.04%**. At d=3, this drops to (0.98)³ = 94.12%. But ε=0.02 is an average — for detail queries where DPI degrades the scorer, ε may rise to 0.05–0.15 at the affected level. A single degraded level with ε=0.10 combined with a normal level (ε=0.02) yields 0.90 × 0.98 = **88.2%** recall. For queries that degrade scoring at both levels: 0.90² = **81%**. The compounding is multiplicative and unforgiving. **Severity: Moderate in expectation, high for DPI-affected queries.** **Frequency: Universal** — affects every query proportionally to per-level error rate. **Mitigations: Keeping depth to 2 limits compounding. Soft assignment (m=2) with independent paths raises recall from 96% to 99.84% in the normal case.** Residual risk: Low for d=2 with soft assignment; concerning if depth increases to 3+. **Type: Architectural.**

**FM-12: Training-testing discrepancy.** Zhuo et al. (ICML 2020) proved formally that tree models trained with standard node-wise losses are **not Bayes optimal under beam search**. The scorer is optimized to rank the correct child highest at each node independently, but beam search operates over paths — a node that is individually well-scored may be on a path that beam search never explores. This means the effective ε may be higher than what is measured by per-node evaluation. **Severity: Moderate.** **Frequency: Persistent** — structural mismatch between training and inference. **Mitigations: Not explicitly addressed in the current design. Could be mitigated by training scorers with beam-search-aware losses.** Residual risk: Moderate. **Type: Engineering** (addressable with specialized training).

### Leaf resolution failures

**FM-13: External source unavailability.** This is a failure mode **not addressed by any of the five defense layers**. Leaf nodes are pointers to external APIs, databases, and document stores. These external sources can be unavailable (API downtime, network failures, authentication expiration), rate-limited, or slow (database timeouts). If the routing correctly identifies the relevant leaf but the external source is unreachable, the system returns no context despite successful retrieval. This is particularly concerning for an agentic system that may issue many concurrent queries. **Severity: Critical when triggered** (complete retrieval failure despite correct routing). **Frequency: ~1–5%** of queries in a system with multiple external data sources, based on typical API reliability (99.9% uptime per source, but with multiple sources and concurrent queries, aggregate failure probability rises). **Mitigations: Not currently addressed.** This is a **novel failure mode** that the five-layer defense completely ignores. Residual risk: Moderate. Needs fallback/retry logic, cached snapshots, or redundant source paths. **Type: Engineering** (fully addressable with standard reliability patterns).

**FM-14: Stale leaf pointers.** Leaves point to external resources that may have been moved, restructured, or deleted. A document store reorganization, API version change, or database schema migration could invalidate leaf pointers silently. The system would route correctly to a leaf that points to a non-existent or changed resource. **Severity: High when triggered.** **Frequency: Low** (~1–3% annually with good operational practices) but spiky during migrations. **Mitigations: Periodic full rebuild catches these; dirty-flag system does not address external changes.** Residual risk: Low with monitoring. **Type: Engineering.**

### Token budget packing failures

**FM-15: Budget-coverage impossibility.** Some queries structurally cannot be answered within 400 tokens (~300 words, ~1–2 typical chunks). The Databricks Long Context RAG Study (2024) showed that retrieval recall saturates at different points per dataset — NQ saturates at ~8K tokens, while FinanceBench requires 96K+. At 400 tokens, only single-fact queries from single sources are reliably answerable. Aggregation queries ("average processing time across all departments"), comparative queries ("how does Policy A differ from Policy B"), timeline queries ("sequence of changes to the remote work policy 2020–2024"), and exhaustive queries ("list all attendees of the Q3 offsite") all require more context than the budget allows. **Severity: Critical for affected query types** (structurally unanswerable regardless of retrieval quality). **Frequency: Estimated 20–35%** of organizational queries — see Section 3 for the breakdown of query types. **Mitigations: The AdaGReS-style selection maximizes information density within the budget. An agentic consumer could decompose queries into multiple retrieval calls, effectively circumventing the per-call budget.** Residual risk: **High if using single-shot retrieval; low-moderate if the consumer implements multi-turn retrieval.** This is a critical design dependency. **Type: Architectural** for single-shot retrieval; **Engineering** if the consumer decomposes queries.

**FM-16: Greedy knapsack suboptimality.** For monotone submodular maximization under a knapsack constraint (variable-cost elements, like variable-length chunks), the standard greedy algorithm has an **unbounded approximation ratio** — it can miss the optimal solution entirely when a single high-value item consumes most of the budget (Horel, notes on submodular maximization). The modified greedy (taking the better of cost-benefit greedy and single-best-element) achieves only a **0.316 approximation** for general knapsack, compared to the (1-1/e) ≈ 0.632 guarantee for cardinality constraints (Nemhauser et al., 1978). AdaGReS achieves ε-approximate submodularity, but under very tight budgets (400 tokens), the greedy may select 2–3 short, moderately relevant chunks over one long, highly relevant chunk that doesn't fit alongside anything else. **Severity: Moderate.** **Frequency: ~10–15%** of cases where chunk lengths vary significantly. **Mitigations: AdaGReS's adaptive λ calibration adjusts for candidate pool statistics. Pre-segmenting content into roughly equal-length atomic units (from Layer 1 content decomposition) reduces variance.** Residual risk: Low-moderate. **Type: Engineering.**

**FM-17: Redundancy misjudgment.** The relevance − redundancy scoring must correctly identify when two chunks are redundant vs. complementary. Embedding similarity is an imperfect proxy for content redundancy: two chunks describing the same policy from different angles may have high embedding similarity (flagged as redundant) but contain complementary information. Conversely, chunks with low similarity may contain overlapping facts in different phrasings (missed redundancy). **Severity: Moderate.** **Frequency: ~10–20%** of multi-chunk selections. **Mitigations: AdaGReS's adaptive λ calibration is instance-specific, adjusting the redundancy threshold per query.** Residual risk: Low-moderate. **Type: Engineering.**

### Maintenance and drift failures

**FM-18: Tree topology drift under incremental updates.** Incremental insertion via the scoring cascade places new documents by routing them through the existing tree and inserting at the best-scoring leaf. This is fundamentally different from globally optimal clustering. Over time, the tree's cluster structure diverges from what a fresh build would produce. Singh et al. (FreshDiskANN, Microsoft Research) showed that over 20 cycles of 5% insertion/deletion, **all graph-based indexes show consistently deteriorating search performance**. Local split/merge repairs mitigate individual nodes but cannot fix global topology drift. The 20–30% threshold for full rebuild means the system tolerates significant degradation between rebuilds. **Severity: Moderate** (gradual degradation, not sudden failure). **Frequency: Continuous** — every incremental update slightly degrades optimality. **Mitigations: Local split/merge repairs; periodic full rebuild at 20–30% threshold.** Residual risk: Low-moderate during normal growth; high during rapid content expansion. **Type: Engineering.**

**FM-19: Concept drift outpacing summary regeneration.** The lazy regeneration approach (dirty-flag + regenerate on next access) means stale summaries persist until a query triggers regeneration. In a rapidly evolving knowledge base, infrequently queried branches may accumulate severe staleness. If a new project creates 50 documents in a branch that was previously about a different project, the routing summary may not be regenerated until someone queries that branch — by which point queries about the new project have been systematically misdirected. **Severity: Moderate-high for affected branches.** **Frequency: Proportional to content velocity** — high for active organizational KBs. **Mitigations: Dirty-flag system; full rebuild threshold.** Residual risk: Moderate. A proactive regeneration schedule (rather than purely lazy) would reduce this. **Type: Engineering.**

---

## 2. Cross-branch queries decomposed into specific sub-types

Cross-branch queries are not monolithic. Each sub-type interacts differently with the five defense layers.

### Sub-type 1: Multi-hop queries

**Mechanism:** The answer requires chaining facts across documents in different branches. Example: "Who approved the budget for the project that caused the most support tickets last quarter?" — requires finding (a) support ticket counts by project, (b) linking the top project to its budget approval, which lives in a different branch (financial records).

**Estimated frequency:** 10–15% of agentic queries. Min et al. (2019) found that even in the multi-hop HotpotQA benchmark, ~46% of questions were solvable with single-hop reasoning, suggesting true multi-hop is less frequent than assumed. In enterprise settings, agentic decomposition (Microsoft Azure AI Search, 2025) converts many apparent multi-hop queries into sequential single-hop queries.

**Defense layer effectiveness:** Layer 1 (content decomposition): **Low** — atomic units don't help because the chain crosses documents, not units within a document. Layer 2 (soft assignment): **Low** — the intermediate documents may not share parents. Layer 3 (entity cross-links): **High** — entity links provide exactly the bridge multi-hop needs (project name links support tickets to budget records). Layer 4 (beam search): **Low-moderate** — beams are unlikely to discover both branches independently. Layer 5 (collapsed fallback): **Moderate** — helps find individual hops but doesn't chain them.

**Expected recall after all five layers:** ~70–80% for 2-hop queries where entities bridge the gap; ~40–55% for 3+ hop queries. Under the 400-token budget, even successful retrieval may fail to provide enough context for both hops.

### Sub-type 2: Entity-spanning queries

**Mechanism:** A query about a specific entity (person, project, tool) whose information is distributed across multiple branches. Example: "What is Sarah Chen's role, which projects is she on, and what policies apply to her remote work arrangement?" — Sarah Chen appears in people directory, project docs, and HR policies.

**Estimated frequency:** 15–25% of organizational queries. Enterprise search studies (Hawking, 2004; Balog, 2008) confirm entity-centric queries are a dominant query type, and organizational entities naturally span multiple contexts. **This is likely the single most common cross-branch sub-type** in an organizational knowledge base.

**Defense layer effectiveness:** Layer 1: **Moderate** — decomposition ensures Sarah's name is preserved as an atomic fact in each unit. Layer 2: **Low** — Sarah's documents are likely in genuinely different clusters (HR vs. projects vs. directory). Layer 3: **Very High** — entity cross-links are specifically designed for this case, directly connecting all mentions of "Sarah Chen" across branches. Layer 4: **Moderate** — beams may discover the people-directory branch, and cross-links redirect to other branches. Layer 5: **Moderate** — collapsed tree finds Sarah-related documents across levels.

**Expected recall after all five layers:** ~85–92%. Entity cross-links are highly effective here, but coverage depends on entity extraction quality. Rare entities, misspellings, and entity disambiguation ("Sarah Chen" vs. "S. Chen") degrade cross-link effectiveness.

### Sub-type 3: Comparative queries

**Mechanism:** Query requires side-by-side comparison of items in different branches. Example: "How does the engineering team's code review process differ from the data science team's?"

**Estimated frequency:** 5–10% of organizational queries. Common in decision-making and policy analysis contexts.

**Defense layer effectiveness:** Layer 1: **Low** — decomposition doesn't help because both sides are needed. Layer 2: **Low** — the two processes are genuinely in different clusters. Layer 3: **Low-Moderate** — entity links might connect "code review" across branches, but only if "code review" is extracted as a cross-linked entity in both. Layer 4: **Moderate** — beam search might discover both branches if the query equally activates both, but beam collapse (FM-10) is a risk if one team dominates scoring. Layer 5: **High** — collapsed-tree fallback searches all nodes and can find both items.

**Expected recall after all five layers:** ~65–80%. Comparative queries are one of the hardest types for tree-structured retrieval because they require equal coverage of two branches, and scoring naturally favors one. The 400-token budget further constrains comparison because both sides must fit within the budget.

### Sub-type 4: Aggregation queries

**Mechanism:** Query requires collecting data across many branches and computing a summary. Example: "How many active projects does the organization have, and what is the total headcount allocated?"

**Estimated frequency:** 5–10% of agentic queries. Less common in human search but natural for agentic systems performing analytics.

**Defense layer effectiveness:** Layer 1: **Very Low** — decomposition is irrelevant; the problem is coverage breadth. Layer 2: **Very Low** — aggregation inherently spans all branches. Layer 3: **Low** — cross-links help for entity-based aggregation but not for statistical aggregation. Layer 4: **Very Low** — beam width 3–5 cannot cover dozens of relevant leaves. Layer 5: **Moderate** — collapsed-tree can find many relevant nodes but is limited by how many the token budget can accommodate.

**Expected recall after all five layers:** ~30–50% of required data points. Aggregation queries are **structurally incompatible** with tree-based retrieval under tight token budgets. This is not a routing failure — it is a coverage impossibility. Even flat retrieval would struggle under a 400-token constraint.

### Sub-type 5: Temporal queries

**Mechanism:** Query targets the evolution of something over time, where different time periods are in different branches or documents. Example: "How has the company's remote work policy evolved since 2020?"

**Estimated frequency:** 5–10% of organizational queries. Temporal reasoning is common for policy tracking, project history, and audit trails.

**Defense layer effectiveness:** Layer 1: **Moderate** — temporal markers (dates) preserved in atomic units. Layer 2: **Low** — different time periods may cluster separately. Layer 3: **Moderate** — entity links for "remote work policy" connect versions across time. Layer 4: **Low-Moderate** — beam search may find the most recent version but miss historical ones. Layer 5: **High** — collapsed fallback can find multiple temporal versions.

**Expected recall after all five layers:** ~55–75%. The system will reliably find the current version but may miss intermediate historical states. The 400-token budget severely limits how many temporal snapshots can be included.

### Sub-type 6: Compositional constraint queries

**Mechanism:** Query combines constraints from different semantic dimensions that map to different branches. Example: "What are the security requirements for contractor access to the production database?" — combines security policies, contractor policies, and database administration, potentially three different branches.

**Estimated frequency:** 10–15% of organizational queries. Common when organizational knowledge is siloed by function.

**Defense layer effectiveness:** Layer 1: **Moderate** — decomposition may create units that capture individual constraints. Layer 2: **Moderate** — if a document covering this intersection exists, soft assignment helps it appear in multiple branches. Layer 3: **Moderate** — entity cross-links for "production database" or "contractor" help. Layer 4: **Moderate** — beam search may cover 2 of 3 constraint branches. Layer 5: **High** — collapsed fallback effective for finding documents at the intersection.

**Expected recall after all five layers:** ~60–80% for 2-constraint queries; ~40–60% for 3+ constraints. Each additional constraint that maps to a different branch reduces the probability of full coverage.

### Summary table: Cross-branch sub-types

| Sub-type | Frequency | Best defense layer | Expected recall | 400-token feasible? |
|---|---|---|---|---|
| Multi-hop | 10–15% | Entity cross-links (L3) | 70–80% (2-hop) | Marginal |
| Entity-spanning | 15–25% | Entity cross-links (L3) | 85–92% | Yes (summary) |
| Comparative | 5–10% | Collapsed fallback (L5) | 65–80% | Marginal |
| Aggregation | 5–10% | Collapsed fallback (L5) | 30–50% | No |
| Temporal | 5–10% | Collapsed fallback (L5) | 55–75% | No (for full history) |
| Compositional | 10–15% | Beam + cross-links (L3+L4) | 60–80% | Yes (2-constraint) |

---

## 3. What queries actually look like in organizational knowledge bases

Empirical data on organizational query distributions is **remarkably scarce**. Multiple researchers (Hawking, 2004; Griesbaum et al., 2015; Freund & Toms, 2006) note that enterprise search is "under-investigated" academically. The estimates below synthesize the best available evidence with explicit uncertainty.

### Single-branch vs. cross-branch distribution

Estimating from the cross-branch sub-type frequencies above (summing the non-overlapping ranges): approximately **40–60% of organizational queries are single-branch** (targeting a specific document, policy, or fact within one topical area) and **25–40% are cross-branch** to some degree. The remaining ~15–20% are navigational queries ("where is the expense form?") that are trivially routable. The fraction of truly complex cross-branch queries (3+ branches) is smaller, estimated at **10–20%**. For an agentic consumer, the cross-branch fraction is likely higher than for human searchers because agents issue more analytically complex queries and are less likely to self-decompose before querying.

### Detail vs. thematic query distribution

Enterprise search behavior research consistently shows a heavy emphasis on entity-centric, fact-finding queries. Hawking (2004) characterized enterprise search as having "a heavier emphasis on entity-centric queries (people search, project search) and task-integrated search." The TREC Enterprise Track (2005–2008) focused on expert/people finding as a core enterprise task. Based on this evidence: **detail queries (specific facts, identifiers, dates, names) constitute an estimated 50–65%** of organizational queries, while **thematic queries (broad topics, process overviews, best practices) constitute 25–35%**. The remaining ~10–15% are navigational. This distribution is unfavorable for the HCR architecture because thematic summaries are optimized for thematic queries — the minority of the workload — while the majority of queries target the specific details that summaries systematically lose.

### Entity-centric vs. concept-centric

Based on Balog (2008), Freund & Toms (2006), and the TREC Enterprise Track: **entity-centric queries constitute an estimated 40–55%** of organizational queries (people, projects, tools, systems, documents by name), while **concept-centric queries constitute 30–40%** (processes, approaches, best practices, policies by topic). Entity-centric queries are better served by entity cross-links (Layer 3) than by thematic routing summaries, suggesting that the entity cross-link layer is a critical component, not just a secondary defense.

### How the agentic use case differs from academic benchmarks

The differences are substantial and systematically disadvantage the HCR architecture relative to academic evaluations.

Academic benchmarks (MS MARCO, Natural Questions, BEIR) operate on clean, well-structured corpora with general English vocabulary, static content, and human-annotated relevance labels. Organizational knowledge bases feature heterogeneous formats (emails, PDFs, wikis, chat logs, databases), domain-specific jargon and acronyms, constantly updated content, internal entities with no external training data, and no gold-standard relevance labels. BEIR results show that **in-domain performance is not a good indicator of out-of-domain generalization** (Thakur et al., NeurIPS 2021), and organizational KBs represent an extreme out-of-domain shift from standard training corpora. Performance on enterprise retrieval tasks is "substantially lower than on common retrieval evaluation datasets such as BEIR and TREC DL" (arxiv:2509.07253).

An agentic consumer adds further challenges: agents issue longer, more specific, multi-condition queries; they decompose complex questions into parallel sub-queries (Microsoft Azure AI Search, 2025); and they demand structured, citable responses rather than ranked lists. This means the query distribution facing HCR will be more complex, more precise, and more demanding than what academic benchmarks test.

---

## 4. When summary-based routing fails — the DPI analysis

The Data Processing Inequality provides the theoretical foundation for understanding when and why summary-based routing fails. The key question is not whether information is lost — it provably is — but whether the lost information was routing-relevant for a given query.

### Routing failure vs. degraded ranking

**Routing failure** occurs when the information needed to rank the correct child highest is entirely absent from the summary. Example: a query for "reimbursement form version 3.2" where the summary captures "expense policies and procedures" but no version numbers. The scorer has zero signal and routes randomly. **Degraded ranking** occurs when the summary retains partial signal — enough to rank the correct child in the top-5 but not reliably in the top-1. Example: a query for "Python deployment guidelines" where the summary mentions "technical documentation" and "deployment" but not "Python" specifically. The scorer has weak signal; beam search (k=3–5) provides resilience.

The critical distinction is whether the query's discriminative terms appear anywhere in the routing summary's fields. The structured format helps significantly: `key_entities` preserves named entities, `key_terms` preserves domain vocabulary, and `includes/excludes` preserves topical scope. But these fields have finite capacity. A cluster containing 500 documents cannot list all entities and terms from all 500 documents in a routing summary of reasonable length. The coverage ratio (fraction of queryable terms preserved in the summary) determines whether a given query experiences routing failure vs. degraded ranking.

### What the structured format preserves and loses

The structured routing summary format (`{theme, includes, excludes, key_entities, key_terms}`) preserves thematic scope (what the cluster is about), explicit entity lists (limited by summary length), contrastive information (what the cluster is NOT about), and key vocabulary. It systematically loses specific quantitative values (dates, amounts, thresholds, version numbers), conditional logic ("if X then Y, unless Z"), procedural details (step-by-step instructions), relationships between entities (who reports to whom), and content that is unique to individual documents rather than cluster-level themes. The FRANK benchmark data confirms this hierarchy of information vulnerability: circumstance errors (time, location, manner) at 10.55% and predicate errors (actions, relations) at 35.85% represent exactly the types of detail most likely to be routing-relevant for organizational queries.

### The heterogeneity threshold

No quantitative threshold exists in the literature for when DPI-induced information loss dominates retrieval quality. However, the theoretical argument is clear: as corpus heterogeneity increases, clusters must compress more diverse content into summaries, reducing the coverage ratio for any specific query term. Organizational knowledge bases, with their mix of policies, technical docs, meeting notes, and communications, represent near-maximal heterogeneity for a single-domain corpus. The structured summary format partially compensates by offering multiple fields for capturing different types of routing-relevant information, but it cannot overcome the fundamental limit: **a routing summary that must represent hundreds of diverse documents will inevitably lose most document-specific details**.

The practical implication is that DPI failure is not a cliff but a gradient. For thematic queries (matching `theme` and `includes`), routing is highly reliable. For entity-centric queries (matching `key_entities`), routing is reliable if the entity is listed. For detail queries targeting information not preserved in any field, routing degrades toward random. In an organizational KB where an estimated 50–65% of queries are detail-oriented, the fraction experiencing meaningful DPI degradation is likely **20–35%** — those queries whose discriminative terms fall outside the summary's coverage.

---

## 5. When beam search fails — modes, math, and the recall floor

### Theoretical recall calculation

For the specified parameters (beam width k=3, branching factor b=10, depth d=2, per-level error rate ε=0.02):

**Expected recall:** (1 − ε)^d = (0.98)² = **96.04%**

**Random scoring floor (absolute worst case):** At level 1, top-3 of 10 with no signal → P = 3/10. At level 2, top-3 of 30 (3 parents × 10 children) → P = 3/30. Combined: 0.3 × 0.1 = **3.0%**. This is the floor if the scorer provides zero information.

**DPI-degraded scenario:** If DPI raises ε to 0.10 at one level and 0.05 at the other (a plausible scenario for a detail query against thematic summaries): 0.90 × 0.95 = **85.5%** recall.

**With soft assignment (m=2 parents, independent paths):** P(at least one path found) = 1 − (1 − 0.9604)² = **99.84%**. Soft assignment with m=2 provides a **25× reduction in miss rate** (from 3.96% to 0.16%) at the cost of 2× leaf storage.

**With soft assignment under DPI degradation (m=2, ε=0.10 both levels):** 1 − (1 − 0.81)² = **96.39%**. Even with significantly degraded scoring, soft assignment m=2 recovers most losses.

**Depth sensitivity:** The compounding formula (1−ε)^d means that moving from d=2 to d=3 at ε=0.02 reduces recall from 96.04% to 94.12% — each additional level costs ~2 percentage points. At ε=0.05, the cost per level is ~5 points (90.25% at d=2, 85.74% at d=3). **Keeping depth at 2 is a strong design choice.**

### Beam collapse analysis

Beam collapse occurs when all k beams converge to children of the same parent, providing no cross-branch exploration. The risk is highest when one branch dominates relevance scores for the query. With path-relevance EMA (α=0.5), a beam that scored well at level 1 carries forward 50% of that advantage, biasing level-2 expansion toward that branch's children. For a focused query with one clearly dominant branch, all 3 beams may select children of that branch at level 1, producing beam collapse at level 2 where all 30 candidates come from the same subtree.

The current design includes **no explicit diversity mechanism** to prevent collapse. Adding a diversity penalty (similar to MMR's redundancy penalty) to beam selection would directly address this — e.g., penalizing beam candidates whose parent shares a sibling with already-selected beams. This is a clear **design gap** that could be addressed before implementation.

### Score plateau interaction

When sibling scores fall within a narrow band (plateau), the effective ε approaches the random baseline. The probability that the correct child is in top-3 of 10 under a plateau is 3/10 = 0.30, giving two-level recall of only 0.30 × 0.98 = 29.4% (if plateau at level 1) or 0.98 × 0.10 = 9.8% (if plateau at level 2 with 30 candidates). Score plateaus are most dangerous at deeper levels where there are more candidates and finer distinctions to make. The contrastive `excludes` field in routing summaries is specifically designed to break plateaus by providing negative discrimination, but its effectiveness is limited when the query genuinely spans sibling topics.

### When flat retrieval beats beam search

RAPTOR (Sarthi et al., ICLR 2024) found that **collapsed-tree retrieval consistently outperformed tree traversal** across all tested datasets. The collapsed approach — evaluating all nodes at all levels simultaneously — is effectively flat retrieval over the augmented node set. This empirical finding suggests that tree traversal (which beam search implements) is inherently inferior to approaches that can access any node at any level. The HCR design addresses this partially through the collapsed-tree fallback (Layer 5), but this is positioned as a fallback rather than the primary retrieval mode. The RAPTOR result raises a deeper question: **if collapsed retrieval is consistently better, why not use it as the primary approach?** The answer is latency — collapsed search over all nodes is O(N) while beam search is O(k·b·d) — but this tradeoff should be explicitly quantified for the target corpus size.

---

## 6. How fast trees degrade with incremental updates

### Empirical degradation rates

Index degradation under updates is well-studied for graph-based indexes (HNSW, Vamana, NSG) and the findings are directly applicable by analogy to tree-structured indexes.

Xiao et al. (2024) demonstrated that after ~3,000 delete-and-reinsert operations on HNSW, **3–4% of data points become unreachable** and recall drops ~3%. This degradation is monotonic — it only gets worse with continued operations — and **cannot be mitigated by adjusting search parameters**. Singh et al. (FreshDiskANN, Microsoft Research) showed that over 20 cycles of 5% insertion/deletion, all graph-based indexes show consistently deteriorating search performance. These findings apply to the HCR tree structure: incremental insertions route new documents via the existing tree, which places them based on the current (possibly suboptimal) clustering rather than globally optimal assignment.

### What causes the fastest degradation

Three factors accelerate tree degradation: **topic drift** (new content introduces topics not represented in the original tree structure, forcing documents into ill-fitting clusters), **asymmetric growth** (some branches grow much faster than others, creating imbalanced trees where some leaves have 10 documents and others have 1,000), and **summary staleness** (parent summaries increasingly misrepresent their children's content as incremental insertions shift the topical distribution). The local split/merge repair mechanism addresses asymmetric growth but not topic drift — a new topic that doesn't fit any existing branch will be forced into the least-bad cluster, degrading that cluster's coherence without triggering a split.

### When full reconstruction becomes necessary

The 20–30% new content threshold for full rebuild is reasonable based on the empirical data. At 20% new content, the tree's global structure is still largely valid, with local distortions. At 30%, cumulative distortions likely degrade recall by **2–5 percentage points** based on extrapolation from the HNSW degradation data. Beyond 30%, the tree increasingly reflects historical rather than current content organization, and the routing summaries diverge from reality. For an active organizational knowledge base growing at 5–10% per month (a reasonable estimate for a team knowledge system with active documentation), the full rebuild threshold is reached every **2–6 months**. This is operationally significant — full rebuilds require recomputing all summaries (many LLM API calls) and reconstructing the tree, which may take hours for a large corpus.

---

## 7. How the 400-token constraint interacts with every failure mode

The 400-token budget acts as both an amplifier and a filter on upstream failures. Its interaction with each major failure category is distinct.

### When the budget amplifies failures

The budget **amplifies routing failures** because there is no room for error. If 2 of 3 retrieved chunks are irrelevant (a partial routing failure), the remaining 1 relevant chunk provides only ~130–200 tokens of useful context — often insufficient for a complete answer. In contrast, a system with a 4,000-token budget could absorb 5 irrelevant chunks and still have room for the relevant ones. The budget also **amplifies cross-branch failures**: if a query requires information from two branches, the budget can accommodate at most one chunk from each branch (~200 tokens each), which may be insufficient for either to provide a complete answer. Liu et al. (TACL, 2024) showed **30%+ performance degradation** when relevant information is in the wrong position within context — at 400 tokens, every token's position matters.

### When the budget provides resilience

Paradoxically, the tight budget provides a form of resilience against noise. The "Lost in the Middle" effect (Liu et al., 2024) — where LLMs fail to use information buried in long contexts — is minimized at 400 tokens because there is no "middle" to get lost in. With only 1–2 chunks, the LLM sees all retrieved content with roughly equal attention. The budget also forces the AdaGReS selector to be highly discriminating, reducing the chance of including irrelevant but superficially relevant chunks that would confuse the LLM.

### Query types structurally unanswerable under 400 tokens

Regardless of routing quality, several query types cannot be adequately answered: **aggregation queries** requiring data from many sources (only 1–2 chunks can fit), **comprehensive comparative queries** requiring substantial text from both items, **full timeline reconstructions** spanning many events, **exhaustive list queries** ("all employees in department X"), and **multi-hop chains** requiring intermediate reasoning context. The LlamaIndex agentic retrieval guide (2025) identifies that different query types demand fundamentally different retrieval strategies — the 400-token budget constrains the system to the simplest strategy (chunk retrieval) and makes file-level or multi-document retrieval infeasible in a single call. **This is the most significant constraint on the system's utility**, and it places a heavy burden on the consumer to decompose complex queries into multiple simple retrieval calls.

---

## 8. HCR vs. flat retrieval — where each fails

### Where HCR is strictly worse

**HCR introduces failure modes that flat retrieval does not have.** Routing errors (FM-04, FM-09, FM-10, FM-11, FM-12) are entirely absent in flat retrieval — every document is a candidate for every query. Summary hallucination (FM-05) and staleness (FM-06) don't exist when there are no summaries. Tree topology drift (FM-18) doesn't exist without a tree. These are the architectural taxes of hierarchy.

Willett (1988) found that hierarchical cluster-based retrieval "does not outperform non-cluster searches, except on the Cranfield collection" — a small, focused test collection. Voorhees (1985) found that retrieving entire clusters almost always performed worse than retrieving individual documents. And RAPTOR (Sarthi et al., 2024) found collapsed-tree retrieval (effectively flat over augmented nodes) consistently outperformed tree traversal. The empirical evidence consistently favors flat or collapsed approaches over tree-traversal approaches for retrieval accuracy.

### Where HCR outperforms flat retrieval

HCR's advantages are in **efficiency, scalability, and multi-granularity reasoning**. Flat dense retrieval's recall drops 10%+ as the database grows from 50K to 200K vectors (TDS analysis). HCR's O(k·b·d) scoring cost is independent of corpus size, making it scalable to arbitrarily large collections. The tree structure also enables multi-granularity retrieval — a query can be answered by a summary node rather than a leaf, providing broader context. RAPTOR showed +20% absolute accuracy on QuALITY (GPT-4) compared to flat retrieval, with gains most pronounced on complex, multi-step reasoning tasks. ArchRAG achieved up to **250-fold token cost reduction** compared to flat RAG. HCR also provides better diversity: flat retrieval tends to return semantically similar documents, while tree-based retrieval can return documents from different clusters.

### Overall failure-mode risk profile

Flat retrieval has fewer failure modes (no routing, no summaries, no tree drift) but fails gradually under scale, lacks multi-granularity reasoning, and provides poor diversity. HCR has more failure modes but provides better efficiency, scalability, and structured navigation. The critical question is whether the organizational knowledge base will grow large enough for HCR's scalability advantages to outweigh its routing risks. For a small KB (<10K documents), flat retrieval with cross-encoder reranking is likely superior — the routing overhead buys little and introduces real risk. For a large, growing KB (>50K documents), HCR's scalability becomes essential, but the routing risks must be actively managed through the defense layers and, critically, through the collapsed-tree fallback.

The collapsed-tree fallback (Layer 5) is the linchpin of the design. When it triggers, the system effectively becomes flat retrieval over the augmented tree, providing the safety of flat retrieval with the scalability of hierarchy. The key design question is: **how aggressively should the fallback trigger?** If it triggers too rarely, routing failures accumulate. If it triggers too often, the hierarchy provides no benefit.

---

## 9. Residual risk after all mitigations

### Expected overall failure rate

Synthesizing the frequency and severity estimates across all failure modes, and accounting for the five defense layers plus the scoring cascade:

For the target domain (organizational knowledge base, agentic consumer), the estimated failure rates by query type are: **simple factoid queries routable by theme** (~35% of queries): 2–4% failure rate — well-served by the architecture. **Entity-centric queries** (~25% of queries): 5–10% failure rate — entity cross-links (Layer 3) are effective but imperfect. **Detail queries targeting specific facts** (~20% of queries): 15–30% failure rate — DPI information loss is the dominant risk, partially mitigated by `key_entities` and `key_terms` but fundamentally limited. **Cross-branch complex queries** (~15% of queries): 20–40% failure rate — defense layers help but cannot fully compensate. **Aggregation/exhaustive queries** (~5% of queries): 50–70% failure rate — structurally incompatible with tree routing under tight token budgets.

**Weighted overall expected failure rate: approximately 10–18%**, with a central estimate of **~14%**. This means roughly 1 in 7 queries will receive materially degraded or absent context. For comparison, flat retrieval with cross-encoder reranking on the same corpus would likely produce a 6–12% failure rate (lower routing risk but higher scale/diversity risk), suggesting HCR's net failure rate is **2–8 percentage points higher** than flat retrieval at small-to-medium corpus sizes, converging as corpus grows.

### The single biggest remaining risk

**DPI information loss for detail queries is the single biggest residual risk.** It is architectural (unfixable by implementation quality), affects the most common query type in the target domain (detail/fact-finding queries constitute 50–65% of organizational queries), and is only partially mitigated by the structured summary format. When DPI causes a routing failure, the error is silent — the system confidently returns irrelevant context — and the 400-token budget provides no buffer for partial failures. The collapsed-tree fallback is the safety net, but it requires accurate confidence estimation to trigger, and overconfident routing (high scores on wrong branches) can prevent fallback triggering.

### Potential showstoppers

**No single failure mode is a clear showstopper**, but two interactions approach showstopper territory:

The **DPI × token budget interaction** is the most concerning. If 20–35% of queries are detail-oriented, and DPI degrades routing for these queries, and the 400-token budget leaves no room for error in the selected context, then the system may produce confidently wrong answers for a substantial fraction of the workload. Whether this is acceptable depends on the consumer's error tolerance and whether it implements multi-turn retrieval to compensate.

The **absent leaf resolution failure handling** (FM-13) is a design gap. The five defense layers address routing quality but not source availability. If a consumer depends on HCR for critical operational decisions and an external data source is unavailable, the system has no documented fallback. This is an engineering gap, not an architectural showstopper, but it needs to be addressed before deployment.

### Previously unconsidered failure modes

This analysis surfaces several failure modes beyond the cross-branch risk identified in prior research: **leaf resolution failures** (FM-13, FM-14) from external source unavailability and pointer staleness; **cross-encoder multi-condition degradation** (FM-08) that specifically affects the complex, multi-constraint queries an agentic consumer issues; **beam collapse without diversity enforcement** (FM-10) where all beams converge, negating the cross-branch exploration that beam search is supposed to provide; and the **training-testing discrepancy** (FM-12, from Zhuo et al., ICML 2020) where node-wise scorer training is provably suboptimal for beam-search inference. The most impactful of these is beam collapse — it directly undermines the fourth defense layer, and no existing mitigation addresses it.

---

## Conclusion: what this analysis changes about the design

Three findings should alter implementation priorities. First, the **collapsed-tree fallback (Layer 5) is more important than the tree traversal itself** — RAPTOR's empirical finding that collapsed retrieval beats tree traversal, combined with this analysis showing ~14% expected failure rate for tree routing, suggests the fallback should be the co-primary retrieval path with aggressive triggering, not a last resort. Consider making every query attempt both tree traversal and collapsed retrieval, returning the higher-confidence result.

Second, **beam diversity enforcement is a missing defense layer**. Beam collapse (FM-10) undermines cross-branch exploration for ~15–25% of queries, and no existing mitigation addresses it. Adding an MMR-style diversity penalty to beam selection — penalizing beams that explore the same branch as already-selected beams — would directly address the gap at minimal implementation cost.

Third, the **entity cross-link layer (Layer 3) is more critical than the analysis initially framed it** — in an organizational knowledge base where 40–55% of queries are entity-centric, this layer is the primary defense for the largest query category. Investment in high-quality entity extraction, disambiguation, and cross-linking will yield higher returns than optimizing the routing summaries.

The architecture is defensible but not dominant. It trades flat retrieval's simplicity and robustness for scalability and multi-granularity reasoning, at a cost of ~2–8 percentage points in failure rate at small-to-medium scale. The design is sound for a growing knowledge base that will eventually outscale flat retrieval — but the transition period, where the corpus is small enough for flat retrieval to be feasible but the tree introduces routing risk, represents the highest-risk deployment phase. During this phase, the collapsed-tree fallback and multi-turn agentic decomposition by the consumer are the primary risk controls.
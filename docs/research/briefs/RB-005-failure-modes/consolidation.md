# RB-005: Failure Modes — Consolidation

**Date:** 2026-02-13
**Status:** Complete (3/4 sources — Gemini unavailable)
**Brief:** [RB-005 Prompt](./prompt.md)
**Sources:** GPT, Claude, Perplexity

## Summary

Three sources independently conducted failure mode analysis of the HCR architecture. The convergence is strong on structural conclusions, with complementary analytical depth. The headline finding: **no architectural showstopper exists for Phase 1, but failure modes are bounded only if the design explicitly handles "budget-impossible" query classes (aggregation, exhaustive listing, temporal diffs) through multi-turn agentic decomposition rather than single-shot retrieval.** The overall expected failure rate for Su-like usage is **10–20%** (three-source consensus on this range), with the dominant residual risks being: (1) DPI information loss for detail queries against thematic summaries, (2) token-budget impossibility for aggregation/global queries, and (3) beam collapse without explicit diversity enforcement. A critical new insight across all three sources: **the collapsed-tree fallback (Layer 5) is more important than previously framed** — RAPTOR's collapsed-tree superiority over strict traversal means this is a co-primary retrieval path, not an emergency-only fallback.

---

## Consensus

All three sources agree on the following. Confidence reflects strength and independence of corroboration.

| # | Finding | GPT | Perplexity | Claude | Confidence |
|---|---------|-----|------------|--------|------------|
| 1 | **No architectural showstopper for Phase 1.** Failure modes are bounded and diagnosable. The architecture is defensible for the target domain (organisational KB, agentic consumer). | Yes — "Go, with the caveat that failure modes are bounded only if aggregation/meta tasks are excluded or reformulated" | Yes — "no evidence of an architectural showstopper for Phase 1 scope"; "risks are bounded and diagnosable rather than fatal" | Yes — "no single failure mode is a clear showstopper"; architecture "defensible but not dominant" | **Very High** |
| 2 | **Overall expected failure rate: 10–20%.** Weighted across query types, roughly 1 in 5–10 queries will receive materially degraded or absent context. Lower end achievable with good maintenance and narrower scope; higher end likely for larger, heterogeneous, fast-changing KBs. | Yes — "low teens" if Su is lookup-heavy, "20–35%" if agentic ops with aggregation | Yes — "10–20% of queries" as the plausible band for "answerable but missed" | Yes — "approximately 10–18%, with a central estimate of ~14%"; "roughly 1 in 7 queries" | **High** |
| 3 | **Token-budget impossibility is a distinct, orthogonal failure class.** Aggregation, exhaustive listing, temporal diffs, and meta-queries often cannot be answered within 400 tokens regardless of routing quality. This is not a retrieval failure — it is a context-size constraint. | Yes — "Important new failure mode not emphasised in prior briefs"; "unanswerable by design under a strict 400-token cap" | Yes — budget saturation for "inherently large answers" is "structural to the 400-token constraint, not to HCR per se" | Yes — FM-15 "budget-coverage impossibility"; "structurally unanswerable regardless of retrieval quality"; frequency ~20–35% of queries | **Very High** |
| 4 | **DPI information loss for detail queries is the #1 residual architectural risk.** Summaries systematically lose specific facts (dates, version numbers, conditional logic, quantities) that are the discriminative features for the majority of enterprise queries. The structured routing summary format partially mitigates but cannot overcome this fundamental limit. | Yes — detail/identifier queries "plausibly 40–70%"; "residual remains for rare-but-critical details" | Yes — DPI failure in "5–15% of queries, concentrated in detail/exception queries"; "medium and irreducible" | Yes — "single biggest residual risk"; affects "50–65% of organisational queries" which are detail-oriented; "20–35% experiencing meaningful DPI degradation" | **Very High** |
| 5 | **Cross-branch queries are not rare in the target domain (~20–40% of queries).** Agentic use cases increase the proportion further because agents issue connective, analytical queries that compress multiple human search steps. | Yes — "20–45% cross-branch, higher if Su is used for planning, audits, project coordination" | Yes — "20–40% cross-branch, including multi-hop, entity-spanning, comparative, aggregation, temporal" | Yes — "25–40% cross-branch to some degree"; "10–20% truly complex (3+ branches)" | **Very High** |
| 6 | **Entity-spanning queries are the most common cross-branch sub-type and entity cross-links (Layer 3) are the primary defense.** Enterprise queries are entity-dominated (people, projects, tools); entity cross-links directly address this. | Yes — "entities dominate many enterprise query categories"; entity-spanning recall ~90–97% with cross-links | Yes — "entity-spanning: 10–20%"; entity cross-links rated 3 (near-solve) | Yes — entity-spanning "15–25%"; "likely the single most common cross-branch sub-type"; entity cross-links are "very high" effectiveness | **Very High** |
| 7 | **Beam collapse is a design gap — no explicit diversity mechanism exists.** All beams can converge to the same branch, negating cross-branch exploration. This is addressable (MMR-style diversity penalty) but is currently missing from the design. | Yes — identified as a distinct failure mode; "5–15% of ambiguous/underspecified queries" | Yes — "10–20% of genuinely cross-branch queries"; recommends "diversity-aware beam heuristics" | Yes — FM-10; "~15–25% of queries"; "gap in the current design"; "no explicit diversity mechanism prevents beam collapse" | **Very High** |
| 8 | **Collapsed-tree fallback is more important than previously framed.** RAPTOR's collapsed-tree consistently outperforming strict traversal means this should be a co-primary retrieval path, not emergency-only. The key design question is how aggressively it should trigger. | Yes — "collapsed-tree fallback is not optional; it is the mechanism that prevents DPI loss from becoming an unrecoverable routing cliff" | Yes — collapsed-tree fallback rated high effectiveness for comparative, aggregation, temporal sub-types | Yes — "Layer 5 is more important than the tree traversal itself"; "consider making every query attempt both tree traversal and collapsed retrieval" | **Very High** |
| 9 | **HCR introduces failure modes that flat retrieval does not have.** Routing errors, summary hallucination/staleness, tree topology drift, and beam artifacts are unique to hierarchical retrieval. The trade-off is scalability and multi-granularity reasoning vs. robustness at small-to-medium corpus sizes. | Yes — "flat retrieval does not have an early hard gate"; lists specific new failure modes | Yes — "structural routing errors, summary-induced failures, maintenance drift, beam-search artifacts are unique to hierarchical traversal" | Yes — "HCR introduces failure modes that flat retrieval does not have"; routing errors, summary hallucination, tree drift all absent in flat retrieval | **Very High** |
| 10 | **Maintenance/drift is a real but engineering-solvable risk.** Trees degrade with incremental updates. The 20–30% rebuild threshold is directionally correct but must be empirically tuned. No quantitative degradation rate exists in the literature for semantic trees. | Yes — "latent decay: without continuous quality telemetry, degradation is silent until users complain" | Yes — "breakdown point not empirically pinned down"; recommends telemetry-driven thresholds | Yes — FM-18/FM-19; "gradual degradation, not sudden failure"; 20–30% threshold "reasonable based on empirical data" from HNSW studies | **High** |
| 11 | **Summary hallucination is low-frequency but high-impact.** Hallucinated entities in routing summaries cause systematic misrouting until repaired. RAPTOR reports ~4% hallucination rate. | Yes — "catastrophic when it happens"; "0.5–3% query-triggered"; "a single bad summary can poison many queries" | Yes — "low single digits of nodes"; "high-impact for certain topics; needs monitoring" | Yes — FM-05; "~5–15% of summaries may contain some hallucinated detail"; "low-moderate frequency" | **High** |
| 12 | **Score plateaus make beam selection near-random for generic queries.** When sibling summaries score similarly, top-3 selection becomes effectively random. This is worst for short, vague enterprise queries. | Yes — "10–30% depending on UI prompting quality"; drops to recall floor of 0.09 in worst case | Yes — "10–20% of queries at some node in the path"; "score distributions flat across many branches" | Yes — FM-09; "~5–15% of query-node combinations"; "contrastive excludes field specifically designed to break plateaus" | **High** |

---

## Conflicts

| # | Point of Conflict | Position A | Position B | Assessment |
|---|-------------------|-----------|-----------|------------|
| 1 | **Severity of DPI for detail queries — frequency estimates** | GPT estimates detail/identifier queries at "40–70%", citing enterprise people search at 59.5%. Claude estimates "50–65%" of queries are detail-oriented, with "20–35%" experiencing meaningful DPI degradation. | Perplexity estimates DPI-driven routing failure at "5–15% of queries", a more conservative figure focused on when summaries actually cause routing failure (not just theoretical information loss). | **Both are correct at different levels.** The majority of enterprise queries ARE detail/identifier-oriented (GPT/Claude are right about query distribution). But structured routing summaries with `key_entities` and `key_terms` do capture many of these detail hooks, so the fraction where DPI causes actual routing failure is lower than the fraction of detail queries (Perplexity's estimate). A defensible estimate: **30–50% of queries are detail-oriented, of which 20–40% experience meaningful DPI degradation in routing, yielding 6–20% of total queries affected by DPI routing failure.** The wide range reflects genuine uncertainty. |
| 2 | **Whether HCR is "defensible" or merely "not a showstopper"** | GPT frames HCR as a conditional go — "Go with the caveat that failure modes are bounded only if aggregation/meta tasks are excluded." Perplexity is the most positive: "Go for Phase 1 with explicit acknowledgement." | Claude is the most adversarial: HCR is "defensible but not dominant"; "2–8 percentage points higher failure rate than flat retrieval at small-to-medium corpus sizes"; the transition period is "highest-risk deployment phase." | **Claude's framing is the most honest.** HCR trades robustness for scalability. At small corpus sizes, flat retrieval with cross-encoder reranking is likely superior. HCR's advantages only manifest at scale. Phase 1 needs to demonstrate that the routing overhead is worth it even at initial corpus sizes — or accept that the initial deployment is "investing in scale" before the payoff. This is a critical design expectation to set correctly. |
| 3 | **Beam search recall floor calculation** | GPT provides three bounds: optimistic independence (0.999984), realistic (between 0.96 and 0.999984), and worst-case plateau (0.09). | Perplexity calculates the same optimistic figure (~0.999984) but frames the realistic bound differently, noting that "ε=0.02 likely already includes some effect of ambiguity and plateaus." Claude provides DPI-degraded scenarios: ε=0.10/0.05 → 85.5% recall; ε=0.10/0.10 → 81% recall. | **All three are consistent.** The key insight is that the recall floor has two regimes: (1) when scoring is informative, beam search is extremely effective (~99.9%+); (2) when scoring degrades (DPI, plateaus), recall drops dramatically. The practical recall floor for HCR is NOT the optimistic 99.998% — it is the weighted average across query types, including the substantial fraction where ε is elevated. This is why soft assignment (m=2, reducing miss rate by 25×) is so critical. |
| 4 | **Frequency of aggregation/meta queries** | GPT: "5–20% depending on how Su is used (agentic ops tends to ask more of these)." Perplexity: "5–15% but often high-value queries." | Claude: "5–10% of agentic queries" for aggregation; "5–10%" for temporal; separately noting 20–35% of queries are structurally unanswerable under 400 tokens. | **The distinction between "aggregation queries" and "queries unanswerable under 400 tokens" is important.** Pure aggregation is ~5–15%, but the budget-impossible class is broader — it includes any query requiring more context than 400 tokens can hold (comparisons needing both sides, multi-hop chains needing intermediate context, exhaustive listings). Claude's 20–35% for budget-impossible queries is the more relevant figure for design decisions. |

---

## Gaps

### Between sources
- **Gemini unavailable** — unlikely to change conclusions given strong three-source convergence.
- **Claude uniquely surfaced** 19 individually numbered failure modes (FM-01 through FM-19) with severity/frequency estimates for each, the training-testing discrepancy (Zhuo et al., ICML 2020) as a distinct failure mode, external source unavailability (FM-13) as a novel failure mode not addressed by the five defense layers, cross-encoder multi-condition degradation from MultiConIR, FRANK benchmark hallucination rates (35.85% predicate errors, 33.75% entity errors), and the concept of "highest-risk deployment phase" during the small-corpus transition period.
- **GPT uniquely surfaced** enterprise search log data (288K queries, 77.2% workforce usage, 59.5% people search, 1.40 terms/query average), RAPTOR's 400-token context experiments, detailed enterprise orienteering/tracing behaviour from Hawking and Marchionini, AdaGReS greedy knapsack approximation guarantees (0.316 for knapsack vs 0.632 for cardinality), and the "redundancy penalty removes necessary corroboration" failure mode.
- **Perplexity uniquely surfaced** path-relevance EMA "rich-get-richer" as a distinct failure mode, over-fragmentation/under-fragmentation as a bilateral failure, granularity mismatch at leaves, and the most complete bibliography with 88 references including operational enterprise search studies (Hawking's Modern IR chapter), PropRAG beam search results, and the Zhuo et al. beam-aware training paper.

### In the theory
1. **No empirical measurement of per-level routing accuracy exists in any system.** All three sources flag this. The ε=0.01–0.02 estimate is derived from cascade scoring benchmarks, not measured on actual routing trees. This is the single most important metric to validate in Phase 1.
2. **No quantitative degradation rate for semantic trees under incremental updates.** HNSW data (3–4% unreachable after ~3K ops) provides an analog but is not directly applicable to tree-structured retrieval with summaries.
3. **No empirical data on enterprise query distributions for "single-branch vs cross-branch" fractions.** The 20–40% cross-branch estimate is derived from intent categories and work-task studies, not direct measurement.
4. **No study of collapsed-tree fallback trigger calibration.** When should the system fall back from beam search to collapsed-tree retrieval? GPT flags this as "poorly calibrated: either too eager (cost) or too conservative (misses)." No principled method exists.
5. **No empirical study of beam diversity mechanisms for hierarchical retrieval.** All three sources recommend diversity-aware beam selection but none cite a system that has implemented it for tree-structured retrieval.

---

## Failure Taxonomy (Consolidated)

### By pipeline stage — severity and frequency in the target domain

The following synthesises all three sources' failure modes into a unified taxonomy. Where sources disagree on frequency, ranges are merged.

| # | Stage | Failure Mode | Severity | Frequency (org KB) | Mitigations | Residual Risk | Type |
|---|-------|-------------|----------|-------------------|-------------|---------------|------|
| 1 | Construction | **Cluster boundary misplacement** — k-means splits don't align with query-relevant boundaries | High | 10–20% of documents near boundaries | Soft assignment (L2), beam search (L4) | Low-moderate with soft assignment | Architectural |
| 2 | Construction | **Heterogeneity-induced weak clustering** — cluster hypothesis fails for broad org KBs (Voorhees: 46% failure) | High | Persistent structural effect | Content decomposition (L1), entity cross-links (L3), collapsed fallback (L5) | Moderate-high — structural to tree partition | Architectural |
| 3 | Construction | **Branch imbalance / gravity wells** — some branches dominate, creating "misc" buckets with weak summaries | Moderate | 5–20% of tree | Branching factor constraints, periodic rebuild | Low-moderate | Engineering |
| 4 | Construction | **Over/under-fragmentation** — atomic units too small (losing context) or too large (mixing topics) | Medium-high | 10–20% of documents | LLM proposition extraction, structure-aware chunking | Medium — contextual knowledge resists atomization | Engineering |
| 5 | Summaries | **DPI information loss** — summaries drop discriminative details (dates, IDs, conditions, quantities) | Critical | 6–20% of queries experience routing failure from DPI | Structured `{key_entities, key_terms}`, hybrid BM25, multi-vector | **High — #1 residual risk.** Irreducible for rare details | Architectural |
| 6 | Summaries | **Hallucinated routing hooks** — summaries introduce false entities/terms causing systematic misrouting | High when triggered | 0.5–3% of queries; ~4% of summaries (RAPTOR) | Grounded prompts, validation pass, dirty-flag regeneration | Low with validation; high-impact without | Engineering |
| 7 | Summaries | **Summary staleness** — summaries lag behind content changes | Moderate-high | Proportional to churn; 5–25% over a quarter | Dirty-flag, lazy regen, periodic rebuild | Low-moderate normally; high during rapid change | Engineering |
| 8 | Summaries | **Non-contrastive / over-broad summaries** — siblings look similar, inflating effective ε | Medium-high | ~10% of internal nodes in early iterations | Contrastive prompts with sibling context, re-clustering | Medium, largely tunable | Engineering |
| 9 | Scoring | **Lexical-semantic mismatch** — query terms don't appear in summaries (jargon, acronyms, new tools) | Major | 10–25% | Hybrid BM25+dense, entity linking, synonym dicts | Medium — not unique to HCR | Engineering |
| 10 | Scoring | **Cross-encoder multi-condition degradation** — rerankers lose accuracy on complex multi-constraint queries | Moderate-high | 10–20% of queries with 3+ conditions | Limit reranking to top-3 candidates; keep summaries <512 tokens | Moderate for complex queries | Partially architectural |
| 11 | Traversal | **Beam collapse** — all k beams converge to same region, no diversity | High | 10–25% of queries | **Currently missing:** needs MMR-style diversity penalty | **Moderate-high — design gap** | Engineering (addressable) |
| 12 | Traversal | **Score plateau** — children score similarly, selection near-random | High when triggered | 5–20% of query-node combinations | Contrastive `excludes`, collapsed fallback on low margin | Medium | Architectural |
| 13 | Traversal | **Path-relevance EMA "rich-get-richer"** — early winners amplified, late-emerging branches suppressed | Medium | 10–20% of cross-branch queries | Depth-dependent α, beam resets | Medium — subtle but structural | Engineering |
| 14 | Traversal | **Training-testing discrepancy** — node-wise scorers not Bayes-optimal under beam search (Zhuo et al., 2020) | Moderate | Persistent structural effect | Beam-aware training, wider beams | Low-moderate for d≤2, k≥3 | Engineering |
| 15 | Traversal | **Error compounding across depth** — (1-ε)^d multiplicative, worse when DPI raises ε | Moderate (avg), High (DPI-affected) | Universal | Depth ≤ 2, soft assignment (m=2 → 25× miss reduction) | Low for d=2 with soft assignment | Architectural |
| 16 | Leaf resolution | **External source unavailability** — APIs down, databases unreachable, auth expired | Critical when triggered | 1–5% of queries | **Not addressed by five-layer defense** — needs retry/cache/fallback | Moderate — engineering gap | Engineering |
| 17 | Leaf resolution | **Stale leaf pointers** — external resources moved, deleted, restructured | High when triggered | 1–3% annually, spiky during migrations | Periodic validation, stable IDs | Low with monitoring | Engineering |
| 18 | Token selection | **Budget-coverage impossibility** — answer requires more context than 400 tokens | Critical | 5–20% of queries (broader budget-impossible: 20–35%) | Multi-turn agentic decomposition by Su | **High — structural constraint, not routing failure** | Architectural |
| 19 | Token selection | **Redundancy misjudgment** — relevance−redundancy incorrectly discards complementary evidence | Moderate-major | 5–15% of multi-chunk selections | AdaGReS adaptive λ, evidence diversity constraints | Low-moderate | Engineering |
| 20 | Maintenance | **Tree topology drift** — incremental insertions diverge from global optimum | Moderate | Continuous; noticeable after 20–30% churn | Local repairs, periodic full rebuild | Low-moderate | Engineering |
| 21 | Maintenance | **Concept drift outpacing regeneration** — infrequently queried branches accumulate severe staleness | Moderate-high | Proportional to content velocity | Proactive regen schedule (not purely lazy) | Moderate | Engineering |
| 22 | Maintenance | **Orphaned cross-links** — entity references to deleted/moved content | Medium | Proportional to entity churn | Periodic recomputation of entity graph | Low-medium | Engineering |
| 23 | Edge case | **OOD queries** — topics not in KB match spuriously | High | <10% | OOD detection, "I don't know" behaviour | Inevitable; not HCR-specific | Engineering |
| 24 | Edge case | **Ambiguous queries** — multiple interpretations lead to arbitrary branch choice | High | 20–30% (enterprise queries) | Clarification, multi-intent retrieval | Medium — mostly UX/prompting | Engineering |
| 25 | Edge case | **Negation/complement queries** — "what is NOT covered" requires reasoning about absence | Major | 2–10% | Structured `excludes` field, specialised logic | **High for this niche** — HCR is poorly suited | Architectural |
| 26 | Edge case | **Meta-queries** — "what do we know about X?" requires tree introspection | Moderate-critical | 5–15% in agentic use | High-level node summaries, dedicated tooling | Medium — orthogonal to core retrieval | Engineering |

**Total: 26 distinct failure modes** across all pipeline stages.

**Architectural (unfixable by implementation):** #1, #2, #5, #10 (partial), #12, #15, #18, #25 — these define the irreducible failure envelope.

**Engineering (addressable with implementation quality):** #3, #4, #6, #7, #8, #9, #11, #13, #14, #16, #17, #19, #20, #21, #22, #23, #24, #26 — these can be reduced through careful design.

---

## Cross-Branch Query Analysis (Consolidated)

### Sub-type frequency and expected recall after all five defense layers

| Sub-type | Frequency in org KB | Best defense layer(s) | Expected recall (all layers) | 400-token feasible? | Key residual risk |
|----------|-------------------:|----------------------|----------------------------:|:-------------------:|-------------------|
| **Entity-spanning** | 15–25% | Entity cross-links (L3) | **85–95%** | Yes (summary sufficient) | Entity aliasing, stale cross-links |
| **Multi-hop (2-hop)** | 10–15% | Entity cross-links (L3) + Beam (L4) | **75–90%** | Marginal (both hops must fit) | Missing connector facts in summaries, beam collapse |
| **Multi-hop (3+ hop)** | 2–5% | Collapsed fallback (L5) | **40–55%** | No | Structural — too many hops for tree routing |
| **Comparative** | 5–10% | Beam (L4) + Collapsed fallback (L5) | **65–80%** (named entities) | Marginal (both sides must fit) | Beam collapse favours one comparator; budget for both sides |
| **Compositional (2+ constraints)** | 10–15% | Beam (L4) + Cross-links (L3) | **60–80%** (2 constraints) | Yes (2 constraints) | Each additional constraint degrades recall |
| **Aggregation / listing** | 5–10% | Collapsed fallback (L5) | **30–50%** (of data points) | **No** — structurally impossible | Budget impossibility; evidence set > context cap |
| **Temporal / versioned** | 5–10% | Cross-links (L3) + Collapsed (L5) | **55–75%** (finding versions) | **No** (for full history) | Version linkage absent; "latest vs historical" ambiguity |

### Defense layer effectiveness summary

| Layer | Strongest against | Weakest against |
|-------|-------------------|-----------------|
| L1: Content decomposition | Multi-topic documents, heterogeneous chunks | Contextual knowledge ("except as noted above"), implicit dependencies |
| L2: Soft assignment | Boundary documents, multi-topic leaves | Genuinely distinct branches (HR vs Engineering) |
| L3: Entity cross-links | Entity-spanning, 2-hop entity-bridged queries | Statistical aggregation, concept-centric queries |
| L4: Beam search | Comparative (named), multi-facet queries | Beam collapse; aggregation requiring broad coverage |
| L5: Collapsed fallback | Comparative, aggregation, temporal, meta-queries | Cost; needs calibrated trigger threshold; defeats hierarchy's purpose |

---

## Query Distribution (Consolidated)

### Empirical evidence from enterprise search

Three sources converge on the following characterisation, drawing on Hawking (2004), enterprise search log studies, and TREC Enterprise Track data:

| Dimension | Estimate | Source evidence |
|-----------|---------|-----------------|
| **Single-branch queries** | 55–75% | Entity/identifier lookups dominate; people search alone can be 59.5% (GPT, citing enterprise log study) |
| **Cross-branch queries** | 20–40% | Higher for agentic use (analytical, connective queries); work-task studies show "tracing" behaviour across contexts |
| **Detail/identifier queries** | 50–65% | Enterprise queries are short (~1.4 terms avg), ID-heavy, entity-centric; people search dominates |
| **Thematic/broad queries** | 25–35% | Process, policy, concept queries; often become multi-step through orienteering |
| **Entity-centric** | 40–55% | People, projects, tools, systems dominate enterprise search; TREC Enterprise Track focused on expert finding |
| **Concept-centric** | 30–40% | Processes, approaches, policies by topic |

### Critical insight for HCR

The query distribution is **structurally unfavourable** for thematic-summary-based routing:

- **Majority of queries are detail/identifier-oriented** — targeting the specific facts that summaries systematically lose (DPI).
- **Minority of queries are thematic** — matching the kind of broad topic queries that routing summaries handle well.
- **Entity cross-links (Layer 3) are therefore more critical than routing summaries** for the most common query type.

This reframes the architectural priority: entity extraction and cross-linking quality is at least as important as summary generation quality.

### How Su differs from academic benchmarks

All three sources agree that enterprise retrieval is a substantially harder evaluation context:

- Heterogeneous formats (emails, PDFs, wikis, chat, databases) vs clean academic corpora
- Domain-specific jargon and acronyms vs general English
- Constantly updated content vs static benchmarks
- No gold-standard relevance labels vs annotated datasets
- BEIR results show in-domain performance is NOT a good indicator of OOD generalisation (Thakur et al., NeurIPS 2021)
- Enterprise retrieval performance is "substantially lower than on common retrieval evaluation datasets" (arxiv:2509.07253)

---

## HCR vs Flat Retrieval (Consolidated)

### Where HCR is strictly worse

| Dimension | HCR failure mode | Flat retrieval |
|-----------|-----------------|----------------|
| Routing errors | FM-5, 9, 11, 12, 14, 15 — early routing gates can exclude correct leaves | No hard gate — every document is a candidate |
| Summary-induced failures | DPI, hallucination, staleness directly affect routing | No summaries → no summary failures |
| Maintenance complexity | Tree structure + summaries + cross-links all need maintenance | Single flat index, simpler updates |
| Beam artifacts | Collapse, plateaus, EMA lock-in | No beam search needed |
| Error compounding | (1-ε)^d multiplicative across depth | No depth → no compounding |

### Where HCR is strictly better

| Dimension | HCR advantage | Flat retrieval weakness |
|-----------|--------------|----------------------|
| Token efficiency | O(k·b·d) scoring, independent of corpus size; RAPTOR: +20% on QuALITY; ArchRAG: 250× fewer tokens | Recall drops 10%+ as database grows from 50K to 200K vectors |
| Multi-granularity | Summary nodes provide "right abstraction level" for thematic queries | Only raw chunks — no abstraction |
| Scale | Sublinear scoring cost | Linear scoring cost |
| Diversity | Tree structure returns documents from different clusters | Flat retrieval tends toward semantic near-duplicates |
| Context density | AdaGReS under tight budget maximises information per token | Flat top-k wastes budget on redundant neighbours |

### Net assessment

**At small corpus sizes (<10K documents):** flat retrieval with cross-encoder reranking is likely superior. HCR introduces routing overhead with minimal scalability benefit. The "transition period" is the highest-risk deployment phase.

**At large corpus sizes (>50K documents):** HCR's scalability becomes essential. Routing overhead is amortised, and multi-granularity retrieval provides real advantages on complex reasoning tasks.

**The collapsed-tree fallback bridges the gap:** when it triggers, HCR becomes flat retrieval over augmented nodes, providing the safety of flat retrieval with the enrichment of hierarchy.

---

## Key Takeaways

### 1. The failure envelope is bounded but not small

Three-source consensus: **10–20% overall failure rate** for Su-like usage. This breaks down as:

- **Single-branch, thematic queries (~35% of workload):** 2–5% failure rate — well-served
- **Entity-centric queries (~25% of workload):** 5–10% failure rate — entity cross-links are effective
- **Detail queries targeting specific facts (~20% of workload):** 15–30% failure rate — DPI is the dominant risk
- **Cross-branch complex queries (~15% of workload):** 20–40% failure rate — defense layers help but can't fully compensate
- **Aggregation/exhaustive queries (~5% of workload):** 50–70% failure rate — budget impossibility

### 2. Three design changes should be made before Phase 1

**a) Beam diversity enforcement.** All three sources identify beam collapse as a design gap. Adding an MMR-style diversity penalty to beam selection — penalising beams that explore the same branch as already-selected beams — is a low-cost, high-impact addition.

**b) Collapsed-tree as co-primary, not fallback.** RAPTOR's collapsed-tree superiority is structural evidence. Consider a "race" design: every query attempts both beam-search traversal and collapsed retrieval, returning the higher-confidence result. This eliminates the fallback calibration problem (when to trigger) at the cost of increased scoring compute.

**c) External source availability handling.** The five defense layers are entirely silent on what happens when leaf pointers resolve to unavailable external sources. Retry logic, cached snapshots, or redundant source paths are needed.

### 3. Budget-impossible queries must be handled architecturally

The 400-token constraint is not just a design parameter — it creates a class of queries that are structurally unanswerable regardless of routing quality. For Phase 1, this means:

- **Su must implement multi-turn retrieval** for aggregation, temporal diff, and exhaustive listing queries
- **Or** the system must recognise these query types and respond with "here's a high-level summary; ask follow-ups for details" rather than attempting a single-shot answer
- **Or** precomputed artefacts (diffs, indexes, rollups) must exist for common aggregation patterns

This is not an HCR limitation — flat retrieval under 400 tokens has the same constraint. But it must be explicitly designed for.

### 4. Entity cross-links are more critical than previously understood

Given that 40–55% of enterprise queries are entity-centric, and entity cross-links are the primary defense for the most common cross-branch sub-type (entity-spanning), **investment in entity extraction, disambiguation, and cross-linking quality will yield higher returns than optimising routing summaries.** The entity cross-link layer is not a secondary defense — it is a primary retrieval mechanism for the dominant query type.

### 5. The "transition period" is the highest-risk phase

Claude's insight deserves emphasis: at small corpus sizes where flat retrieval is feasible, HCR introduces routing overhead and new failure modes without sufficient scalability benefit. Phase 1 must either:

- Demonstrate value even at small scale (via multi-granularity reasoning, not just scalability)
- Accept that early deployment is "investing in architecture" before the payoff at scale
- Use collapsed-tree as the primary retrieval path initially, transitioning to beam-search traversal as corpus grows

---

## Recommendation

### Go/No-Go for Phase 1

**Go** — with three explicit conditions:

1. **Budget-impossible queries are out of scope for single-shot retrieval.** Phase 1 success criteria must not require high reliability on aggregation, exhaustive listing, or temporal diff queries in a single 400-token retrieval call. Su must implement multi-turn decomposition for these.

2. **Beam diversity enforcement is added to the design.** This is a low-cost fix for a high-impact gap.

3. **The collapsed-tree fallback is promoted to co-primary.** The Phase 1 benchmark (RB-006) must measure both beam-search traversal and collapsed retrieval, and the system should use whichever produces higher-confidence results per query.

### What This Means for Hypotheses

**H1a (token efficiency, 65%):** The failure analysis shows the 400-token constraint creates a hard impossibility class (~5–20% of queries). For queries within the feasible class, token efficiency is achievable. H1a should be scoped to "single-branch and entity-spanning queries" (which are ~75% of the workload). No confidence change yet — RB-006 is needed.

**H1b (hybrid superiority, 80%):** Unchanged. All three sources confirm that neither pure hierarchy nor pure flat retrieval is optimal. The hybrid architecture (coarse routing + fine similarity + collapsed fallback) is the theoretically and empirically supported approach. The failure analysis reinforces this.

**H1c (scoring quality as primary determinant, 75%):** Partially challenged. The failure analysis shows that **entity cross-link quality** is at least as important as per-level scoring quality for the dominant query type (entity-spanning). Scoring quality matters most for thematic routing; entity cross-links matter most for entity-centric routing. Both are primary determinants, for different query classes. No confidence change, but the mechanism is broader than initially framed.

### What Remains Open

1. **Empirical per-level routing accuracy (ε).** No system has ever measured this. Phase 1 must instrument it as a first-class metric.
2. **Collapsed-tree fallback trigger calibration.** When should the system switch from beam search to collapsed retrieval? No principled method exists.
3. **Beam diversity mechanism design.** What diversity penalty function and strength provides the best trade-off between exploration and exploitation?
4. **Entity extraction and disambiguation quality.** How good must the entity cross-link layer be to achieve the ~85–95% entity-spanning recall estimated here?
5. **Degradation rate under incremental updates.** When does tree quality cross the threshold where full rebuild is needed?

---

## Next Steps

1. **Update CLAUDE.md** — RB-005 complete, three design changes identified (beam diversity, collapsed co-primary, external source handling)
2. **Update hypotheses.md** — note H1c mechanism broadening (entity cross-links as co-primary determinant)
3. **RB-006 (Benchmark design)** — the final brief before go/no-go. Must include:
   - Per-level routing accuracy as a first-class metric
   - Cross-branch sub-type coverage in the evaluation suite
   - Beam-search vs collapsed-tree comparison
   - Budget-impossible query detection
   - Entity cross-link quality metrics
4. **After RB-006: Go/no-go decision** on Phase 1 implementation

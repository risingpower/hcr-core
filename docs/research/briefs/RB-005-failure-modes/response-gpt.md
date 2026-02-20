# RB-005: Failure Modes — GPT Response

# RB-005: Failure Modes of Hierarchical Coarse-to-Fine Retrieval

## What the literature already implies about HCR’s core fragility

Hierarchical coarse-to-fine retrieval (tree traversal with progressively narrower candidate sets) introduces a **structural dependency**: early routing decisions constrain everything that follows. The classic IR clustering literature already observed that **cluster structure is not a safe proxy for relevance** across heterogeneous collections, even when “cluster hypothesis” indicators look healthy. In *The Cluster Hypothesis Revisited*, Table 2 shows that in the INSPEC collection **46% of relevant documents have zero relevant nearest neighbours among the top-5 neighbours**, i.e., “co-relevance” is often *not* locally clustered. citeturn22view0

Modern RAG-specific hierarchical systems show the same pattern from the opposite direction: hierarchy can help (by offering multi-granularity summaries), but **forced top-down traversal can underperform “flat over all nodes”**. RAPTOR explicitly compared **tree traversal vs a “collapsed tree”** that retrieves from *all* nodes (across levels) and found the collapsed approach “consistently performs better” on a QASPER subset, attributing this to flexibility in retrieving the “correct level of granularity” per question. citeturn23view0

Graph/path-based multi-hop retrieval systems reinforce the same point: when relevance is *path-like* (multi-step association), traversal needs either (a) explicit cross-links, or (b) exploration breadth. PropRAG’s proposition-graph + beam search is a direct demonstration that **multi-hop recall can be high when the structure supports cross-branch connectivity and multi-step exploration**, reaching Recall@5 values in the 90s on multi-hop benchmarks and showing measurable drops when removing graph guidance. citeturn33view0

Those three results triangulate HCR’s central risk profile:

- **HCR is advantaged** when questions benefit from multi-granularity context (summary nodes can supply “the right abstraction level”). citeturn23view0  
- **HCR is disadvantaged** when relevance is multi-region (cross-branch) or when local clustering is weak in the corpus (heterogeneous enterprise KBs are exactly this). citeturn22view0turn26view0  
- **HCR can recover** if it adds cross-links + exploration (beam, soft assignment, fallback to collapsed-tree / flat-over-nodes). citeturn33view0turn23view0  

The remainder of this brief treats HCR as a pipeline and enumerates failure modes beyond cross-branch routing, then quantifies residual risk *after* your five-layer defence.

## Failure mode taxonomy across the HCR pipeline

Severity is defined as expected degradation in end-to-end answer quality under a hard ~400-token context budget (catastrophic = answer wrong/unanswerable; major = large miss/partial; moderate = noticeable but recoverable; minor = mostly ranking/efficiency). Frequency estimates are **domain-conditional** (organisational KB: policies/procedures/projects/people/tools/comms) and therefore given as ranges with explicit uncertainty, anchored where possible in enterprise search log evidence (notably: heavy tail usage; people/entity lookups dominating many enterprise search workloads). citeturn26view0turn13view1turn17view1

### Taxonomy (at least 10 distinct architectural failure modes)

| Pipeline stage | Failure mode (mechanism) | Triggers (query/corpus conditions) | Severity if triggered | Frequency estimate in org KB | Planned mitigations that help | Residual risk after mitigations |
|---|---|---|---|---|---|---|
| Corpus preparation | **Over-coarse content units** (atomicity failure): chunks contain multiple topics/entities, causing mixed routing signals | Long policy pages, meeting notes, “everything in one doc”, email threads; multi-topic pages typical in enterprise content citeturn26view0turn27search5 | Major–catastrophic (wrong subtree; wasted budget) | 10–30% of corpora; query-triggered 5–15% | Content decomposition; redundancy-aware selection | Still vulnerable when decomposition misses implicit scope/exception structure (policies) or when “atomic” units still require surrounding context for meaning |
| Tree construction | **Partition boundary pathology**: bisecting k-means yields semantically arbitrary splits; relevance crosses boundary | Heterogeneous corpora; weak cluster hypothesis regimes (large share of relevant docs not locally clustered) citeturn22view0 | Major | Cross-branch queries: 15–35% (see distribution section); boundary-sensitive single-hop: 5–10% | Soft assignment; entity cross-links; beam search; collapsed-tree fallback | Residual is structural: partitioned routing cannot be perfect when relevance is multi-region citeturn22view0turn23view0 |
| Tree structure | **Branch imbalance / topical “gravity wells”**: some branches dominate size/entropy, collapsing diversity | One branch becomes “misc/other”; enterprise “no top category” content is common citeturn26view0 | Moderate–major | 5–20% corpora | Beam search; collapsed-tree fallback | If imbalance becomes stable, traversal turns into near-linear scan on that branch, removing HCR’s benefits under tight budgets |
| Summary generation | **DPI information loss (detail elision)**: summaries omit discriminative detail needed for routing | Detail/identifier queries (codes, dates, exact clause, “which version”), common in enterprise and email refinding; average enterprise/intranet queries are short and identifier-like citeturn13view1turn26view0turn27search6 | Major–catastrophic for detail queries | Detail-heavy queries plausibly 40–70% depending on KB (people search alone 59.5% in one enterprise study) citeturn26view0 | Structured routing summaries (key_entities/key_terms); hybrid BM25 component; multi-vector storage at leaves | Residual remains for **rare-but-critical details** (numbers, negated exceptions, edge-case clauses), which summarisation is known to mishandle even in dedicated summarisation research citeturn34search8turn34search5 |
| Summary generation | **Hallucinated routing hooks**: summaries introduce spurious key_terms/entities → systematic misrouting | Abstractive generation is prone to unfaithfulness/hallucination; entity/quantity spans are frequent error sites in summarisation studies citeturn34search8turn34search12 | Catastrophic when it happens (wrong branch with high confidence) | Low per-summary, but persistent over time; expected query-triggered 0.5–3% unless heavily constrained | Contrastive structured format; regeneration/dirty flags; collapsed-tree fallback on low confidence | Still a top residual because a single bad internal-node summary can poison many queries until repaired |
| Scoring/routing | **Lexical–semantic mismatch at internal nodes**: query terms don’t appear in summaries; BM25 underfires, dense under-separates | Acronyms, names, multilingual terms; enterprise intranet terms often indeterminable/acronym/system names; operators rarely used citeturn17view3turn17view4 | Major | 10–25% | Hybrid BM25+dense; key_terms; entity cross-links | Residual mainly in OOD vocabulary and “internal jargon drift” (new project names) |
| Traversal | **Beam collapse**: beams converge into same region due to correlated scores, losing intended breadth | Ambiguous queries; dominant cluster; score correlations; shallow trees amplify this | Major | 5–15% of ambiguous/underspecified queries | Beam width 3–5; EMA path relevance smoothing | Still happens when top children score similarly or share same theme wording (see score plateau) |
| Traversal | **Score plateau / tie-like frontier**: child scores nearly equal; beam selection becomes pseudo-random | Generic thematic queries (“policy”, “onboarding”), or high-entropy branches; enterprise users often use short, vague queries and then “orienteer” citeturn27search1turn25view1 | Moderate–major | 10–30% depending on UI prompting quality | Beam search; collapsed-tree fallback when confidence low | Residual risk is high if “fallback trigger” is poorly calibrated: either too eager (cost) or too conservative (misses) |
| Leaf resolution | **Pointer-level incompleteness**: leaves are pointers; relevant evidence exists but is inaccessible/unindexed/unregistered → retrieval blind spot | Enterprise search failures often involve access, inadequate metadata, missing registration into the system citeturn25view3turn26view0 | Catastrophic for affected queries | 5–20% (high variance by org governance) | Collapsed-tree fallback does *not* fix; cross-links don’t fix | Architectural residual: HCR cannot retrieve what is not in the reachable leaf addressing space |
| Token selection | **Budget packing fails on “need-many-pieces” questions**: sub-400 tokens cannot support aggregation/listing tasks even with perfect retrieval | “List all exceptions / all projects / all vendors”; “what changed between versions”; these require broad evidence | Catastrophic (cannot answer) | 5–20% depending on usage patterns (agentic ops tends to ask more of these) | Submodular relevance–redundancy selection helps avoid wasted redundancy citeturn36search4turn36search0 | Residual is fundamental: if the answer requires many distinct facts, a 400-token cap sets a hard ceiling regardless of routing |
| Token selection | **Redundancy penalty removes necessary corroboration**: “relevance − redundancy” discards duplicate-looking snippets that are actually independent evidence (policy vs comms vs ticket) | Compliance/decision audit queries; multi-source corroboration | Moderate–major | 5–15% | Knapsack/submodular approximations are principled but still heuristic under complex objectives citeturn36search1turn36search4 | Residual needs explicit “evidence diversity” constraints by source type, not just semantic redundancy |
| Maintenance/drift | **Summary staleness + concept drift**: partitions reflect old corpus; incremental insertion warps cluster boundaries | Rapid KB growth; renames; re-orgs; policy versioning; enterprise content is dynamic and heavy-tail queried citeturn26view0turn25view0 | Major | Depends on change rate; practical risk 5–25% over a quarter without rebuild | Dirty-flag summaries; local repair; periodic rebuild | Residual is “latent decay”: without continuous quality telemetry, degradation is silent until users complain |
| Maintenance/drift | **Incremental maintenance degradation**: local updates in hierarchical clustering drift from global optimum | Known in streaming/incremental clustering: localised graph maintenance can preserve speed but quality depends on drift regime citeturn36search2turn36search6 | Moderate–major | Likely in any “insert locally” regime; 5–15% query impact between rebuilds | Periodic rebuild threshold | Residual: threshold choice is not literature-grounded for text semantics; it must be empirically tuned on your KB |
| Query class edge cases | **Negation / exclusion / “NOT covered” queries**: summaries and scorers are biased toward presence not absence | Queries that ask for exclusions, constraints, prohibitions; policies are rich in these | Major | 2–10% | Structured “excludes” field; cross-encoder rerank | Residual is high if “excludes” is incomplete or hallucinated; also conflicts with summary lossy nature citeturn34search8 |
| Query class edge cases | **Meta-queries requiring global awareness**: “what do we know about X?” / “show coverage gaps” | Requires broad scan; enterprise “orienteering” behaviour suggests users explore by successive narrowing rather than single query citeturn27search1turn25view1 | Moderate–catastrophic under 400 tokens | 5–15% in agentic command-centre usage | Collapsed-tree fallback; high-level node summaries | Residual: these tasks are intrinsically multi-context; HCR helps structure discovery but 400 tokens blocks completeness |

**Important new failure mode not emphasised in prior briefs:** **token-budget impossibility classes** for aggregation/meta queries. These are not just “hard”; they are often **unanswerable by design** under a strict 400-token cap, even with perfect retrieval, because the required evidence set is too large. This failure is *orthogonal* to routing accuracy and is therefore a true architectural limiter.

## Cross-branch query analysis and effectiveness of the five-layer defence

“Cross-branch” is not a monolith. In enterprise environments, search behaviour studies show (a) many queries are entity/people lookups and identifier-heavy, but (b) non-trivial work tasks involve “tracing” through contextual/historical relations and navigating multiple sources. citeturn26view0turn25view3turn27search1 This implies cross-branch queries exist both as explicit multi-hop questions and as “orienteering / tracing” interactions spread across multiple retrieval steps.

### Cross-branch subtypes in an organisational KB

The examples below are framed as single-shot questions, but enterprise search research suggests users often approximate these via iterative “orienteering” even when they start with short queries. citeturn27search1turn25view1

**Multi-hop (needs a reasoning chain across subtrees)**  
Example: “Which customer commitments are affected by the new IT access policy change, and which projects must update their runbooks?” (policy subtree + customer commitments + projects/runbooks).  
PropRAG exists largely because multi-hop retrieval is hard under independent passage retrieval and benefits from explicit path discovery with beam search. citeturn33view0

**Entity-spanning (same entity appears in multiple branches)**  
Example: “What systems does ‘Project Atlas’ touch, who owns each, and where are the latest configs?” (project + people + tools/config + comms).  
Enterprise logs often show entity lookup dominance (e.g., people search as a majority category in one large enterprise study). citeturn26view0

**Comparative (contrast across branches)**  
Example: “How does contractor onboarding differ from employee onboarding, and what’s the security policy delta?” (HR + security policy + regional variants).

**Aggregation/listing (requires coverage across many leaves)**  
Example: “List all exceptions to policy X across departments” or “How many services are non-compliant with standard Y?”  
This is where token budget becomes a hard limiter (often cannot fit even if retrieved). citeturn36search4turn26view0

**Temporal/versioned (requires evidence across time slices that may be stored separately)**  
Example: “What changed in the incident response process between v2 and v3 and why?” (policy versions + comms + postmortems).

### Defence-layer effectiveness by subtype (qualitative + recall estimates)

The table below estimates “retrieval recall for necessary evidence” under HCR with your five defences. Where possible, ranges are anchored by empirical points: RAPTOR shows collapsed-tree > traversal (meaning forced routing is risky), and PropRAG demonstrates that proposition-level units plus beam/path discovery can deliver high Recall@5 on multi-hop tasks. citeturn23view0turn33view0  
Because no enterprise paper reports “cross-branch fraction” or “per-level routing accuracy” directly, frequency and recall are necessarily uncertain.

| Cross-branch subtype | Likely frequency in agentic org KB | Layer 1: decomposition | Layer 2: soft assignment | Layer 3: entity cross-links | Layer 4: beam search | Layer 5: collapsed-tree fallback | Expected recall after all layers (best estimate) | Key residual risk |
|---|---:|---|---|---|---|---|---:|---|
| Multi-hop | 10–25% (higher in agentic workflows) citeturn25view3turn33view0 | High impact (reduces entangled chunks) citeturn33view0turn31search22 | Medium (boundary bridging) | Medium (helps if hops are entity-linked) | High (explicit breadth) citeturn33view0 | High but compute-heavy citeturn23view0 | ~0.80–0.92 (2–3 hop), assuming good links and beam diversity | Beam collapse/plateau; missing links; summaries omitting “connector” facts |
| Entity-spanning | 15–35% (entities dominate many enterprise query categories) citeturn26view0 | Medium | Medium–high | High (direct) | Medium | Medium (if cross-links fail) | ~0.90–0.97 | Stale/incorrect cross-links; entity aliasing/jargon drift |
| Comparative | 5–15% | Medium | Medium | Medium | Medium–high | High (retrieves both sides) | ~0.80–0.92 | Token budget: cannot include both sides + supporting detail in 400 tokens |
| Aggregation/listing | 5–20% | Medium (helps atomise) | Medium | Low–medium | Medium | High (global scan) | **Retrieval** may be high, but **answer utility** often low under 400 tokens | Hard impossibility class: the evidence set is larger than the context cap |
| Temporal/versioned | 5–15% | Medium | Medium | Medium | Medium | Medium–high | ~0.70–0.88 | Version linkage absent; stale summaries; “latest vs historical” ambiguity; requires multiple versions in context |

**Most important implication:** after all five layers, **entity-spanning and many 2-hop queries can plausibly be bounded**, but **aggregation and temporal diff** remain the highest residual risk under a strict 400-token cap because they are dominated by *context size*, not *retrieval correctness*. citeturn26view0turn36search4

## Query distribution in organisational knowledge bases

Direct enterprise evidence about “single-branch vs cross-branch” proportions is scarce; what exists is indirect: category distributions, query lengths, reformulation behaviour, and prevalence of people/entity search plus “tracing/orienteering” behaviour across work tasks. citeturn26view0turn25view1turn27search1

### What enterprise search logs show reliably

In one operational enterprise search study (international biotech company), log analysis reports:  
- **77.2% of the workforce used enterprise search** during the study period, producing 288,363 queries (heavy tail: 8.2% of users generated 39.9% of searches). citeturn26view0  
- **People search was the most frequent subject category (59.5% of queries)**, dominated by initials/name-like lookups. citeturn26view0  
- Users primarily searched “All” sources (73.4%), with people directory as the most used specific filter (20.0%). citeturn26view0  
- When search broke down, common responses were query reformulation (78.6%), asking colleagues (70.4%), and using personal archives (44.9%); ~33.7% sometimes give up. citeturn25view1  

Older but detailed intranet log studies show similarly “thin” queries and high uniqueness: one week of corporate search logs reported **~1.40 terms per query on average**, with most users active on only one monitored day. citeturn13view1  
A longitudinal intranet term analysis (2000/2002/2004) reports that top-100 terms account for ~23–24% of all terms and that “not repeated” terms are a majority of distinct terms, indicating long-tail, idiosyncratic needs; query operators appear in under 10% (dropping to ~3%). citeturn17view1turn17view4

### Implications for an agentic system's likely query mix (single-branch vs cross-branch)

From first principles plus the above evidence:

- The **dominant mass of queries in enterprise search logs is entity/identifier centric** (people, initials, product codes, system names). citeturn26view0turn17view3  
  These are *often single-branch answerable* if the tree has strong entity indexing and cross-links.

- However, enterprise work-task studies describe a “tracing” technique relying on **historical and contextual relationships as paths**, which is essentially cross-branch traversal behaviour even when the interface is a single search box. citeturn25view3turn25view1  
  An agentic command centre (not a passive search box) is likely to *increase* the proportion of multi-step queries because agents naturally ask "connective" questions that compress multiple human steps into one instruction.

A conservative, decision-relevant estimate for agentic usage therefore looks like:

- **Single-branch**: ~45–70% (higher if the system is used mostly for lookup/refinding). citeturn26view0turn27search6  
- **Cross-branch**: ~20–45% (higher if the system is used for planning, audits, project coordination, and “what changed / what’s impacted?”). citeturn25view3turn27search1  
- **Detail/identifier-heavy**: ~50–80% in many enterprise log regimes (people search alone can exceed half). citeturn26view0turn13view1  
- **Thematic/exploratory**: ~20–50%, but these often become multi-step via orienteering/tracing. citeturn27search1turn25view1  

Those ranges are wide because the literature reports **categories and behaviours**, not the “branch locality” of ground-truth evidence. But the key for Phase 1 is that **cross-branch is unlikely to be <10%** in an agentic ops setting, so it cannot be treated as an edge case.

## DPI and summarisation: when lossy routing becomes worse than flat retrieval

### Why the DPI framing is correct but incomplete in practice

The core information-theoretic claim is: if a routing summary is a (lossy) transformation of underlying content, it cannot increase mutual information about the original signal; this is the essence of the data-processing inequality as presented in information theory treatments. citeturn34search7turn34search3

In HCR terms: the internal-node summary is a channel; routing is a decision based on that channel output. Therefore, **there exist query intents that are separable in the raw content space but not separable after summarisation** (especially for rare details).

This is not speculative: summarisation systems are well documented to produce **unfaithful/hallucinated content** and to mishandle entities/quantities—exactly the features that drive enterprise “detail queries”. citeturn34search8turn34search5turn34search12

### What information is most likely to be lost (and why this matters for routing)

Empirically and mechanistically, lossy/hallucination risk concentrates in:

- **Named entities, identifiers, and quantities** (common hallucination loci; also central to enterprise lookup). citeturn34search12turn26view0  
- **Exceptions/conditions/negations** (the “only if”, “unless”, “not covered” clauses), which are high-information but low-salience; they often drop out of thematic summaries. citeturn33view0turn34search8  
- **Provenance and versioning** (which version said what, who approved, when changed): triples can collapse context; propositions preserve it, but any compression step risks eliding it. citeturn33view0turn34search7  

### Does your structured routing summary mitigate DPI failure?

Partially, and for reasons supported by older IR summarisation work:

- Query-biased summaries improve relevance judgement accuracy and speed over static summaries, suggesting that **summary structure and biasing toward discriminative cues matters**. citeturn35search0  
- Your format explicitly stores **includes/excludes** and **key_entities/key_terms**, which is a targeted attempt to retain exactly the discriminative features that generic summaries drop.

However, two residual problems remain:

1. **Coverage limit:** a summary can list only so many entities/terms under token constraints; long-tail entities (new project names) will be omitted, yet enterprise logs show long-tail query terms are substantial. citeturn17view1turn26view0  
2. **Factuality risk:** if the includes/excludes fields are wrong (hallucination or omission), the routing error becomes systematic until regeneration; summarisation factuality is a known barrier. citeturn34search8turn34search5  

### When accumulated loss makes coarse-to-fine worse than flat similarity

RAPTOR provides a concrete clue: even in a purpose-built hierarchical system with embeddings at all nodes, **collapsed-tree retrieval (flat over all nodes) beat tree traversal** on tested QASPER stories. citeturn23view0  
That result is consistent with the following failure condition for HCR:

- As **corpus heterogeneity increases**, the probability that relevant evidence spans multiple clusters rises (cluster hypothesis weakens), and the probability that any single thematic summary preserves the discriminative hook falls. citeturn22view0turn26view0  
- Once “connectors” (the small facts that link hops) are frequently absent from summaries, traversal becomes a brittle filter; at that point, a **flat pass over all nodes** (including summaries) becomes superior because it removes the “must choose a branch first” constraint. citeturn23view0turn33view0  

This is the clearest structural argument that **collapsed-tree fallback is not optional**; it is the mechanism that prevents DPI loss from becoming an unrecoverable routing cliff.

## Beam search failure analysis and theoretical recall floors

Beam search is your primary query-time hedge against early routing mistakes. PropRAG’s results show that beam/path exploration can materially improve multi-hop retrieval and that removing graph guidance reduces Recall@5 on at least some benchmarks (e.g., drops on 2Wiki). citeturn33view0  
But beam search is not a guarantee; it fails in identifiable ways.

### Failure mechanisms

**Beam collapse (lack of diversity):** beams converge into the same topical region because scores are correlated (shared summary wording, dominant cluster, or embeddings that over-represent frequent terms). This is particularly likely when enterprise users issue short, ambiguous queries and then rely on iterative navigation/orienteering. citeturn27search1turn17view4

**Score plateau:** multiple children are near-tied, making selection effectively random. Enterprise query logs suggest users frequently reformulate and use social/archival fallbacks when search fails, indicating that ambiguity and low-separability queries are common in practice. citeturn25view1turn26view0

**Depth interaction:** the value of beam width depends strongly on depth. A depth-3 tree multiplies the number of “decision points”; if each level has non-trivial plateau probability, the chance of losing the correct region increases faster than simplistic independence models predict. citeturn22view0turn33view0

### Theoretical recall floor for beam k=3, b=10, d=2, ε=0.02

Because “ε = 0.02” is specified as a per-level error rate, the “recall floor” depends on what ε means operationally. There are three useful bounds:

1. **Top-1 traversal (no beam)**: per-level success = 1 − ε = 0.98; depth-2 success = 0.98² = **0.9604**.  
2. **Optimistic independence model** (each beam is an independent chance to include the correct child at each level): per-level miss = ε³ = 0.02³ = 0.000008; depth-2 success = (1 − 0.02³)² ≈ **0.999984**.  
3. **Score-plateau/random-choice bound** (routing signal collapses; choose k of b uniformly): per-level success = k/b = 0.3; depth-2 success = 0.3² = **0.09**.

The second figure is a theoretical upper-style bound and is *not* realistic when beams are correlated (beam collapse), while the third is a “worst-case plateau” bound that becomes relevant precisely in the conditions where HCR is weakest (ambiguous queries, heterogeneous corpora). The existence of the 0.09 regime is the critical warning: **beam helps enormously when scoring is informative, but it collapses to near-useless when scoring is not separative**. citeturn22view0turn25view1

### Are there query types where beam systematically underperforms flat retrieval regardless of k?

Yes: when the query requires **global evidence coverage** or **multiple distinct regions** but the scoring function is dominated by a frequent-topic attractor, increasing k can still waste budget because beams remain correlated or because retrieved evidence cannot fit under the token cap. The RAPTOR collapsed-tree superiority result is a concrete example that flat-over-nodes can dominate traversal-based methods even within a hierarchical system. citeturn23view0

## Maintenance, token budget interaction, flat-vs-HCR comparison, and residual risk

### Maintenance and drift: what can go wrong and how fast

Enterprise search usage is heavy-tailed: a small fraction of users generate a large fraction of searches. citeturn26view0 In such regimes, **quality degradation is discovered via the heaviest users first**, and their behaviour tends to dominate perceived product quality.

Your maintenance strategy (“insert locally; repair locally; rebuild periodically”) is directionally consistent with incremental clustering practice in other domains, which uses localised updates to avoid full rebuild costs. citeturn36search2turn36search6 But text semantics add two accelerants:

- **Vocabulary drift (new project/tool names)** directly attacks routing summaries and BM25 signals; intranet logs show long-tail and multilingual/acronym-heavy terms. citeturn17view1turn17view3  
- **Policy/version churn** makes stale summaries actively misleading (not just incomplete), increasing the probability of confident misrouting.

Empirically, the literature does not provide a clean “X% new content → Y% retrieval degradation” rule for semantic trees; therefore the rebuild threshold must be treated as an **unknown to be learned**, not a known constant.

### Token budget interactions: how 400 tokens amplifies specific failures

RAPTOR’s own experiments explicitly used **400 tokens of context** for a reader model with a 512-token max context, highlighting that 400-token regimes are meaningful but also implying performance varies strongly with provided context length (collapsed-tree best result used far more tokens in that specific configuration). citeturn23view0

Under 400 tokens, HCR behaves like a high-gain system:

- **Correct routing → disproportionate upside:** you can pack a small number of highly relevant atoms, which is exactly what submodular budgeted selection is designed to do (monotone submodular coverage objectives have greedy approximation guarantees under budgets). citeturn36search4turn36search1turn36search0  
- **Misrouting → near-total waste:** if the selected leaves are irrelevant, the budget is consumed by wrong context and the model’s answer becomes confidently wrong or abstains.

Submodular “relevance − redundancy” selection provides resilience mainly against **redundant over-retrieval**, not against **systematic misrouting**, because the candidate set itself is already biased by routing. citeturn36search0turn36search4

Most importantly, some question types are **structurally incompatible** with 400 tokens:

- Aggregation/listing (“list all…”, “count all…”, “compare across all departments”) requires many distinct evidence items, and no routing scheme can compress the universe of required facts into 400 tokens without losing completeness. citeturn36search4turn26view0  
- Temporal diffs that require quoting multiple versions plus rationale similarly exceed budget (unless the KB already contains a precomputed diff artifact).

### HCR vs flat retrieval: where each is strictly worse or better

**Where HCR introduces new failure modes that flat retrieval does not:**
- **Error compounding via routing:** flat retrieval does not have an early hard gate. The RAPTOR evidence that collapsed-tree retrieval can beat traversal is an existence proof that gating can be harmful even in well-designed hierarchies. citeturn23view0  
- **Summary staleness/hallucination as a routing defect:** flat retrieval can ignore summaries entirely; HCR depends on them. Summarisation factuality issues are widely documented. citeturn34search8turn34search5  
- **Maintenance complexity:** a flat index can be updated incrementally with less semantic drift risk than a semantic partition tree with generated summaries (the latter needs monitoring and repair to remain meaningful). citeturn36search2turn36search6  

**Where HCR can be better than flat retrieval under tight budgets:**
- Multi-granularity retrieval can surface “right abstraction level” nodes; RAPTOR’s broader results show hierarchical summary nodes can improve QA over baselines in some datasets, and it motivates higher-level nodes as useful for thematic/multi-hop questions. citeturn24view4turn23view0  
- In workloads dominated by entity/identifier lookup, HCR can route quickly to a compact set of relevant atoms, which matches enterprise log reality (people/identifier queries are extremely common in some enterprises). citeturn26view0turn13view1  

### Residual risk assessment and Phase 1 go/no-go

**Expected overall failure rate after mitigations (order-of-magnitude):**  
Given (i) high prevalence of entity/identifier queries (good fit), citeturn26view0 (ii) non-trivial presence of tracing/multi-source tasks (cross-branch), citeturn25view3turn27search1 and (iii) summarisation/routing brittleness in heterogeneous corpora, citeturn22view0turn34search8 a defensible Phase 1 expectation is:

- **Single-branch, detail lookup:** low residual failure if entity indexing/cross-links are solid (likely <5–10% for the subset, dominated by OOD terms and pointer-level incompleteness). citeturn26view0turn17view3  
- **Cross-branch multi-hop/comparative:** moderate residual failure (plausibly 10–25% within this subset) driven by missing connectors, beam collapse, and budget limits. citeturn33view0turn23view0  
- **Aggregation/meta/temporal diffs:** high failure-to-be-useful under 400 tokens (often >30–60% for that subset), because the constraint is context size, not retrieval accuracy. citeturn36search4turn23view0  

Combined, if the workload resembles “enterprise search logs” (mostly lookup), overall failure might be bounded in the low teens. If the workload resembles “agentic ops copilot” (more aggregation/temporal/comparative), overall failure could drift into the 20–35% range unless the system is allowed to **multi-turn retrieve** or **call tools** (which is outside this architectural brief but affects feasibility). citeturn25view3turn27search1

**Single biggest remaining risk after all mitigations:**  
**Token-budget impossibility for aggregation/meta/temporal-diff questions.** This is the only failure mode here that is both (a) plausibly common in agentic command-centre use and (b) not solvable by better routing, scoring, or traversal. citeturn36search4turn25view3

**Second biggest risk:**  
**Summary correctness (hallucinated hooks / stale excludes) creating systematic misrouting.** Summarisation factuality issues are empirically real, and routing magnifies them. citeturn34search8turn34search5

**Go/no-go for Phase 1 (boundedness verdict):**  
**Go**, with the caveat that failure modes are bounded **only if Phase 1 explicitly excludes or reformulates “need-many-pieces” tasks** (aggregation/meta/large temporal diffs) into either (a) multi-turn retrieval plans or (b) precomputed artefacts (diffs, indexes, rollups). Under a strict single-shot <400-token regime, those classes are not bounded—they are structurally constrained. citeturn36search4turn23view0

If Phase 1 success criteria require high reliability on aggregation and temporal diff questions *in one shot*, the correct decision is **no-go**, because the dominant failure becomes the context cap, not the retrieval architecture. citeturn36search4
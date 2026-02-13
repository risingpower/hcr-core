# RB-006: Benchmark Design — GPT Response

**Date:** 2026-02-13
**Source:** GPT
**Status:** Awaiting response

---

*Paste GPT response below this line.*
# RB-006: Benchmark design for hierarchical coarse-to-fine retrieval

## Benchmark intent and hypothesis mapping

This benchmark is not a general-purpose leaderboard. It is a Phase 1 gate that must answer three binary questions with high confidence: whether hierarchical coarse-to-fine retrieval (HCR) is (a) materially more token-efficient than a strong flat baseline, (b) materially better as a *hybrid* than either hierarchy-only or flat-only, and (c) primarily governed by per-level routing/scoring quality (ε) and entity cross-links (for entity-spanning queries). The benchmark therefore needs two properties that most existing retrieval or RAG benchmarks do not: (i) it must measure *internal routing events per tree level*, and (ii) it must score *answer sufficiency under hard token budgets*, not just document relevance. Existing RAG evaluation frameworks (e.g., RAGAS, ARES, RAGChecker) provide useful primitives for context relevance/faithfulness diagnostics, but none directly measure hierarchical routing error or “budget-impossible” detection out of the box. citeturn0search15turn0search11turn5search0turn7search2

The benchmark should output three decision-grade artefacts:

1. **Token-efficiency curves**: answerability/accuracy vs budget at 200/400/800/1200/unconstrained, with an explicit “budget-at-parity” statistic. This is the decisive evidence for H1a. Long-context work shows that “more context” does not monotonically translate to better task performance; position and distractors matter, so measuring performance at controlled budgets is non-negotiable. citeturn7search3turn5search3  
2. **Hybrid decomposition**: Beam-only vs collapsed-tree-only vs hybrid-race. This is decisive for H1b and also tells you whether collapsed-tree is “co-primary” in practice. RAPTOR demonstrates the value of tree-organised retrieval, while LATTICE represents a more explicitly guided hierarchical traversal line; neither is designed around strict token budgets or parallel-path “race” evaluation, which is the gap you must close. citeturn1search0turn1search1  
3. **Internal diagnostics**: per-level ε, cross-link quality signals, and routing-specific tree metrics. These must be predictive of end-to-end outcomes, otherwise you will not have an engineering knob for Phase 1 iteration. Classical IR evaluation work also makes clear that query set size and variance matter; you need enough queries per stratum to make a go/no-go decision robust. citeturn4search9turn4search2turn4search4

## Corpus design

### What’s reusable and where existing benchmarks miss

**BEIR** is valuable as a sanity check baseline suite: it is explicitly designed to test robustness across heterogeneous retrieval tasks and domains and demonstrates that BM25 remains a strong baseline while rerankers can improve performance at higher compute cost. That supports your baseline design philosophy, but BEIR is not an organisational KB proxy: it does not embed enterprise-like heterogeneity (emails + policies + project docs), and it does not measure hierarchical routing or budgeted answer sufficiency. citeturn0search4turn0search8

**MTEB** is valuable for the embedding-model choice within the benchmark harness: it explicitly shows that no single embedding method dominates across tasks, which is a warning against overfitting your corpus to a single embedding leaderboard. But MTEB is not an enterprise KB benchmark and does not provide the hierarchical/routing measurements you need. citeturn0search5turn0search9

**Enterprise-oriented corpora exist but have practical access constraints.** The entity["organization","TREC","text retrieval conference"] Enterprise Track was explicitly framed around enterprise data (intranet pages, email archives, document repositories), and analyses of the entity["organization","W3C","web standards consortium"] collection used there describe a heterogeneous corpus including technical documents, mailing lists, source code, a wiki, and personal homepages, with on the order of 331k documents in at least one reported setup. However, entity["organization","NIST","us standards agency"] notes that some Enterprise Track test collections are no longer distributed, which makes “just use TREC Enterprise” a risky Phase 1 dependency. citeturn8search14turn3search18turn8search2

Conclusion: reuse BEIR/MTEB tooling as harness components, but build a domain-proxy corpus yourself (with a reproducible snapshot) for the go/no-go gate.

### Recommended Phase 1 corpus: hybrid real+synthetic with growth stages

A Phase 1 corpus must simultaneously (i) look like an organisational KB, (ii) be buildable by one person, (iii) allow ground-truth generation for budgeted answerability, and (iv) support a growth/transition experiment. The most pragmatic design is:

**Base real corpus (domain proxy):**

- **Policies / procedures / people ops**: the entity["company","GitLab","devops platform company"] public handbook includes controlled documents and policy-style content that is structurally close to the target domain (policies, procedures, People topics). Use a pinned snapshot (commit hash or dated scrape) to avoid drift. citeturn10search4turn10search12turn10search16  
- **Communications / decisions / entity-dense threads**: the entity["company","Enron","energy company"] email corpus is large (≈0.5M messages reported in the entity["organization","Carnegie Mellon University","pittsburgh, pa, us"] distribution) and provides real-world conversational and temporal structure, which is critical for DPI and ambiguity stress. Sample it rather than ingesting everything in Phase 1. citeturn3search1  
- **Technical docs with explicit versioning**: entity["organization","Kubernetes","container orchestration project"] release notes and contributor processes provide naturally versioned content and “what changed” semantics suitable for temporal query classes. citeturn10search5turn10search17turn10search9

**Synthetic augmentation (targeted failure-mode injectors):**

Augment the base corpus with *small, controlled synthetic documents* that are designed to trigger the known failure modes you already enumerated in RB-005: near-duplicate policies with single-token differences; contradictory versions; “buried” identifiers; cross-branch entity collisions (same name refers to multiple things); and long-tailed synonyms. The goal is not realism; it is diagnostic power.

**Corpus sizing and growth stages (to test the “transition period”):**

Use *passage/chunk units* as “documents” for retrieval (this aligns with modern RAG evaluation practice and lets you hit >50k retrieval units without an enormous raw corpus). Set three fixed corpus sizes:

- **Small**: 10k chunks (expected: hierarchy may underperform; this is the transition baseline).
- **Threshold**: 50k chunks (where RB-005 expects HCR advantage to start manifesting).
- **Large**: 200k chunks (stress test for cross-branch and budget pressure).

These stages should be constructed as strict supersets (10k ⊂ 50k ⊂ 200k) so you can attribute changes to scale rather than distribution drift.

### What to explicitly *exclude* from Phase 1

Extremely large web corpora (e.g., GOV2 at ~25M pages and hundreds of GB) are valuable for scalability research but are not Phase 1 practical and will swamp your iteration loop. They are also not an organisational KB proxy in the “people/policy/project artefact” sense. citeturn10search3turn10search7

## Query suite design

### Principles: stratified, label-rich, and mostly auto-generatable

You need queries that (i) match the organisational KB distribution you’ve estimated, (ii) produce ground truth for both routing and answerability under budget, and (iii) are numerous enough for stable comparisons. Classic IR stability work supports rules of thumb like “25 queries is a minimum; 50 is better” for reliable comparative evaluation, and significance testing guidance in IR recommends paired tests (randomisation/bootstrap/Wilcoxon) rather than naïve unpaired approaches. citeturn4search9turn4search4turn4search2

For Phase 1, the most efficient construction pipeline is **hybrid generation**: model-assisted query generation with *explicit evidence anchoring*, followed by lightweight human verification on a sample. RAG evaluation frameworks explicitly use synthetic or automated dataset construction in order to reduce labelling cost, which you can mirror for your custom corpus. citeturn0search15turn5search0

### Minimum viable query counts and category coverage

You do not need thousands of queries for a go/no-go decision, but you do need enough per stratum to avoid being fooled by variance.

**Minimum viable benchmark (MVB) query suite (Phase 1 gate): 300 queries total**

- 180 “budget-feasible” queries (answerable under 400 tokens by construction)
- 120 “budget-impossible” queries (not answerable under 400 tokens by construction)

Each query is multi-labelled (not exclusive categories). Ensure the *marginal distributions* match your target workload estimates by design.

**Required tagged strata (target counts within 300):**

- Single-branch thematic: 90  
- Entity-spanning cross-branch: 75  
- Detail/identifier (DPI): 120  
- Multi-hop 2-hop: 60  
- Multi-hop 3+ hop: 30  
- Comparative (“X vs Y”): 45 (HotpotQA explicitly includes comparison questions; use this as a template for what “comparative” looks like in QA evaluation.) citeturn1search6turn1search10  
- Aggregation/listing: 60 (mostly labelled budget-impossible)  
- Temporal (“what changed”, “as of version/date”): 45  
- Ambiguous/multi-intent: 30  
- Out-of-distribution (OOD, answer not in KB): 30 (budget-impossible by definition, but distinct from aggregation)

These numbers overlap because one query can be DPI + entity-spanning + temporal, etc. The enforcement mechanism is a query generator that *assigns tags first* and then generates/filters questions to reach target totals.

**If you can afford a larger suite** (recommended for stronger significance and fewer “false no-go” outcomes): 500 queries with the same label schema. The incremental cost is primarily evaluation, not query authoring, if you automate evidence anchoring.

### How to generate queries without contaminating evaluation

Use three sources of queries:

1. **Evidence-anchored synthetic queries (≈60%)**: sample a passage (or a small set of passages for multi-hop) and generate a question whose answer is fully contained within a minimal evidence set. This is exactly how multi-hop QA datasets operationalise “supporting evidence”, and it’s the only scalable way to label budget feasibility precisely. HotpotQA provides sentence-level supporting facts; QASPER provides supporting evidence annotations over papers; MultiHop-RAG includes supporting evidence alongside answers. Use these as design exemplars for your own annotation format. citeturn1search6turn2search1turn2search3  
2. **Adversarial synthetic queries (≈20%)**: generated specifically to hit the failure-mode injectors (near duplicates, collisions, etc.).  
3. **Human-written “business realistic” queries (≈20%)**: short set written manually to reflect how an org actually asks things (“What’s the policy for X?”, “Who owns Y?”, “When did Z change?”). These provide face validity and catch synthetic artefacts.

For *temporal* queries, explicitly include multiple versions of a policy/procedure page and ask “what changed between version A and B” (budget-impossible unless changes are tiny), or ask “as of date D, what is the rule?”. Long-context benchmarks (QuALITY, LongBench) demonstrate that difficulty increases when relevant information is distributed and cannot be skimmed; your temporal questions should exploit this by spreading evidence across sections/versions. citeturn2search0turn5search3

## Metrics and instrumentation design

### Metric stack: separate retrieval sufficiency from answer generation

To make the benchmark diagnostic (and not confounded by an answer generator), score three layers:

1. **Routing layer** (tree navigation quality): per-level ε and routing margins.  
2. **Retrieval layer** (context quality under budget): evidence recall/precision and answerability-from-context.  
3. **Generation layer** (optional for Phase 1 go/no-go): answer correctness and faithfulness to retrieved context, using established RAG evaluation metrics and judges.

RAG evaluation frameworks explicitly separate context relevance and answer faithfulness/relevance; use those ideas, but add the routing-specific layer that the literature lacks. citeturn0search11turn5search0turn7search2

### Per-level routing accuracy ε: definition and measurement

**Core idea:** routing is a *multi-label decision* at each level because multiple branches can legitimately contain relevant evidence (especially with soft assignment and entity cross-links). Therefore, “accuracy” should be defined as a *recall-of-relevant-branches* metric, not a single-label hit rate; hierarchical classification literature uses hierarchical precision/recall/F-type concepts to handle DAGs and multi-path labelling, which is conceptually aligned with soft assignment. citeturn7search4

Define the following objects for a query *q*:

- Gold evidence passages: **G(q)** (one or more passage IDs).
- For each evidence passage *g ∈ G(q)*, the set of valid tree paths to its leaf under soft assignment: **Paths(g)**.
- For a tree depth of *d*, define the set of “correct nodes” at level ℓ as:  
  **Cℓ(q) = { node at level ℓ that lies on any path in ⋃g Paths(g) }**.

Now measure the scoring cascade (BM25+dense → top-3 → cross-encoder → top-1/2 expansion) as it operates at each internal node:

- Let the system consider a parent node *p* at level ℓ and score its children. Let **Sℓ(q, p)** be the set of children selected for expansion from *p* (size 1–2 per your design).  
- Define **routing success at level ℓ** as:  
  **Rℓ(q) = 1** if for every beam element expanded at level ℓ, at least one selected child is in **Cℓ+1(q)** (i.e., you didn’t eliminate *all* correct continuations); otherwise **Rℓ(q) = 0**.  
- Then define **εℓ = 1 − meanq Rℓ(q)** over the evaluation set (and report ε by query tags: single-branch vs entity-spanning vs DPI).

Also report a softer, more informative version:

- **Child Recall@Mℓ** at each level: fraction of correct children included in the top-Mℓ list *before* cross-encoder rerank, where *Mℓ* equals your prefilter cut (e.g., 3). This isolates which stage of the cascade is failing.

This yields exactly the parameter your RB-002 theory uses, but in a form that respects multi-relevance and soft assignment.

**Instrumentation requirement:** the retrieval engine must log, per query, per level, per expanded node: candidate children, scores per scorer stage, and which children were selected. Without this log, ε cannot be computed.

### End-to-end retrieval quality under token constraint: “answerability-from-context”

You need a metric that answers: *did the returned ≤T-token context contain enough information to answer correctly?*

Use evidence-anchored ground truth and score:

- **Evidence Recall@T (ER@T):** fraction of gold evidence units present in the selected context within token budget T. Evidence units should be sentence-level for DPI and comparison queries (HotpotQA-style supporting facts), and paragraph-level for longer policy/procedure items (QASPER-style). citeturn1search6turn2search9  
- **Evidence Precision@T (EP@T):** fraction of context that is labelled evidence (or tightly overlapping evidence). This penalises “dumping” under budget.  
- **Answerability@T (A@T):** binary, judged as “a competent answerer could answer correctly using only this context”. This can be implemented as:
  - deterministic if your query generation includes a minimal evidence set whose token length ≤ T (then A@T is mechanically true if ER@T hits all required evidence); and/or
  - LLM-as-judge if you include semantically equivalent evidence variants and want robustness. For judge-based approaches, use established RAG evaluation judge dimensions (context relevance, groundedness/faithfulness, answer relevance) as guardrails; ARES and RAGChecker are explicitly designed for automated component-level evaluation and report correlation improvements over other automated methods, making them reasonable starting points for Phase 1 judge scaffolding. citeturn5search0turn7search6turn7search2

Critically, keep **A@T** separate from generation correctness: the first is a retrieval benchmark, the second mixes retrieval and generator failure modes.

### Token efficiency: curves and “budget at parity”

For each system *s* produce **A@T(s)** at T ∈ {200, 400, 800, 1200, ∞}. Then compute:

- **Budget-at-parity:** the smallest T such that A@T(HCR) ≥ A@∞(FlatStrong) − δ, where δ is a tolerance (recommended δ=0.02 absolute on budget-feasible queries; see Success Criteria).  
- **Area-under-curve (AUCbudget):** trapezoidal area under A@T for T up to 1200; higher means more accuracy per token.

Why curves matter: long-context studies show performance can degrade as contexts get longer or more cluttered (“lost in the middle”), which makes “unconstrained accuracy” a weak north star. Your design target is budgeted performance, so measure it directly. citeturn7search3turn5search3

### Beam vs collapsed-tree: race value and conditional wins

Compute for each query:

- **A@T(BeamOnly)**, **A@T(CollapsedOnly)**, **A@T(Race)** where Race chooses the path with higher confidence (must be a deterministic confidence function based on retrieval scores to avoid judge leakage).  
- **Race Gain@T:** A@T(Race) − max(A@T(BeamOnly), A@T(CollapsedOnly)).  
- **Win conditions:** stratify by tags (entity-spanning, DPI, multi-hop) and report which path dominates.

This directly answers whether running both paths is worth its added complexity and whether collapsed-tree is truly co-primary in your domain-proxy corpus (as RB-005 predicts).

### Entity cross-link quality: diagnostic metrics that matter in Phase 1

For Phase 1, do not overinvest in perfect entity-link labelling. Measure cross-links through *reachability and causal impact*:

- **Cross-branch Reachability (CBR):** for each entity-spanning query, measure whether at least one gold evidence passage lies outside the primary routed branch *and* is reachable within ≤1 cross-link hop from a visited node.  
- **Cross-link Utilisation Rate (CUR):** fraction of entity-spanning queries where the final selected context includes at least one passage retrieved via a cross-link traversal.  
- **Cross-link Ablation Drop (ΔXLink):** A@400(HCR) − A@400(HCR without cross-links) on entity-spanning queries.

Entity linking evaluation literature is large, but you do not need to replicate TAC-style linked-KB evaluation to make a Phase 1 decision; your question is whether cross-links *function as the dominant cross-branch mechanism* in practice for your architecture. citeturn7search5

### Routing-specific tree quality: what HCR should introduce

You need intrinsic and extrinsic metrics. Intrinsic metrics let you iterate without query labels; extrinsic metrics tie tree properties to outcomes.

**Intrinsic (query-free):**

- **Sibling Distinctiveness (SD):** average pairwise cosine distance between child routing-summary embeddings at each internal node (higher is better).  
- **Entity Overlap Ratio (EOR):** Jaccard overlap of `key_entities` across siblings (lower is better, except where cross-linking is intended).  
- **Coverage & reachability:** fraction of leaf passages reachable via at least one parent path; with soft assignment this should be near 1.0 by construction, but measure it to catch pipeline bugs.

**Extrinsic (query-conditioned):**

- **Routing Margin (RM):** at each level, difference between the best-scoring correct child and best-scoring incorrect child under the cross-encoder stage; low RM predicts beam collapse.  
- **ε-by-node heatmap:** which internal nodes contribute disproportionate routing error; this becomes your focused engineering backlog.

This creates a routing-specific “tree quality” concept aligned with operational decisions, rather than generic clustering scores.

### Budget-impossible detection: evaluation as a classifier under asymmetric costs

Label each query with **Feasible@400 ∈ {yes, no}** by construction where possible (e.g., if minimal evidence set token length ≤400 then yes; if the task requires enumerating >N items or diffing long versions then no). Then measure:

- **Precision/Recall/F1 for “impossible”** (treat “impossible” as the positive class).  
- **Expected Utility@400:** assign higher penalty to false negatives (attempting an impossible answer) than false positives (refusing when possible), because false negatives waste tokens and can mislead an agentic system.

Frameworks like RAGChecker explicitly motivate fine-grained diagnostics for modular RAG pipelines; “abstain/answerable” is one such module that should be evaluated explicitly rather than inferred from downstream answer accuracy. citeturn7search6turn7search2

## Baselines and ablations

### Baselines: what to compare against and why

A credible go/no-go needs baselines that are both strong and interpretable.

**Strong flat baseline (must-have):** BM25 + dense hybrid retrieval + cross-encoder reranking + the same token-budgeted selection (AdaGReS-style or your submodular knapsack) but *without hierarchy*. BM25 is a standard robust lexical baseline; two-stage neural reranking with BERT-style cross-encoders is a proven effectiveness pattern. citeturn6search2turn6search3turn0search8

**Weak flat baselines (must-have):** BM25-only; dense-only cosine (no rerank). These establish headroom and help interpret whether gains are coming from reranking or hierarchy.

**Academic baselines (should-have if reproducible):**

- **RAPTOR-style collapsed tree retrieval**: bottom-up clustered summaries and retrieval over the tree; use it as a reference architecture for your collapsed-tree path expectations. citeturn1search4  
- **LATTICE**: hierarchical traversal guided by LLM reasoning over a semantic tree. Treat it as a conceptual competitor; only include if you can reproduce it without GPU dependence because Phase 1 must run on modest hardware. citeturn1search1

**Commercial systems (optional, and usually not worth it in Phase 1):** products like entity["company","Pinecone","vector database company"] and entity["company","Weaviate","vector database company"] are not “systems” in the same sense—they are infrastructure components whose retrieval behaviour depends on your indexing, embedding, hybrid configuration, and reranking stack. Comparing against them will mostly test your configuration choices, not HCR’s architecture. Include them only if your go/no-go decision is explicitly “build vs buy”. citeturn8search1turn9search0

### Tooling for baseline implementation under Phase 1 constraints

Use established evaluation and retrieval tooling to minimise engineering load:

- **First-stage retrieval (BM25/dense)**: Pyserini provides reproducible sparse+dense retrieval and is designed for multi-stage ranking pipelines. citeturn8search5turn8search17  
- **Dataset plumbing**: ir_datasets standardises dataset access and formats for IR experiments, useful even if you load your custom corpus through the same interfaces. citeturn8search0turn8search8  
- **Metrics computation**: ir_measures standardises evaluation measure names/parameters and interfaces with common IR eval tools. citeturn4search7turn4search23  
- **Vector search**: FAISS is the standard reference library for similarity search trade-offs and can run in CPU mode. citeturn9search0

### Minimum viable ablation set for Phase 1

Ablations must map directly to hypotheses. The minimal set that still yields decision-grade evidence is:

- **Hybrid superiority (H1b):**
  - Beam-only (no collapsed-tree)
  - Collapsed-tree-only (no beam)
  - Race (both; choose higher confidence)  
- **Token efficiency (H1a):**
  - Selection method swap: submodular/greedy vs naïve top-k chunks (same retrieval scores)  
- **Scoring lever (H1c):**
  - Path-relevance EMA off vs on
  - Cross-encoder rerank off vs on (keep BM25+dense prefilter constant)

Then, as soon as possible (but can be second wave), add:

- Cross-links off vs on (entity-spanning impact)
- Soft assignment off vs on (cross-branch robustness)
- Contrastive routing summaries vs generic summaries (tree construction claim)

Diversity enforcement in beam search is grounded in classic MMR-style relevance–novelty trade-offs; if you include “diversity off vs on”, implement and cite MMR as the conceptual baseline for the diversity term. citeturn6search1

## Experimental protocol, reproducibility, and Phase 1 practicality

### Data splits and scale protocol

Use a **fixed corpus snapshot** and three evaluation scales (10k/50k/200k chunks) with identical query sets where possible. For each scale:

- Build tree and indexes on the corpus subset.
- Evaluate the same 300-query suite, but mark which queries are “in-scope” (evidence exists in that subset) vs “not yet present” (this naturally simulates KB growth).

This directly tests the transition-period concern: does HCR become superior only after a threshold, and if so, where?

### Controlling randomness and LLM variability

You have three sources of variance: clustering initialisation, LLM summarisation outputs, and optional LLM judging.

Protocol:

- **Clustering**: 5 random seeds per corpus scale; report mean and 95% CI for key metrics.  
- **Summaries**: temperature 0; cache outputs keyed by (node_id, prompt_version, model_id). Treat prompt changes as version bumps.  
- **LLM-as-judge** (if used for Answerability@T): run 3 judge samples per (query, system, budget) with deterministic temperature; use majority vote. ARES and RAGChecker both emphasise component-level evaluation and judge reliability concerns; caching and repeat-judging are your main levers to keep this stable in Phase 1. citeturn5search0turn7search6

### Significance testing and decision discipline

Because comparisons are paired by query, use paired tests. IR literature explicitly compares common significance tests and offers guidance on which are appropriate under typical IR metric distributions; randomisation/permutation or non-parametric paired tests are usually safer than assuming normality. citeturn4search4turn4search0

Minimum protocol:

- For the primary go/no-go metrics (A@400, budget-at-parity, ε), run **paired randomisation/permutation tests** between HCR and FlatStrong on the same query set, and between Race and max(BeamOnly, CollapsedOnly).  
- Report effect sizes (absolute deltas) alongside p-values; do not ship a “go” based on p-values alone.

### Fail-fast experiment order

To avoid wasting Phase 1 time, run experiments in this order:

1. **ε measurement on a tiny dev slice (50 queries, 10k corpus)**: if per-level ε is nowhere near the theoretical regime (e.g., >0.05 at level 1 even with cross-encoder), most of the architecture’s promise collapses; stop and fix scoring/summaries first. (This is justified because ε is the controlling parameter in your theory and the only metric that can invalidate H1c quickly.)  
2. **Token-efficiency curve on budget-feasible queries (10k → 50k corpus)**: if HCR cannot beat FlatStrong at 400 tokens even on feasible queries, H1a is likely false or the selection/scoring is broken.  
3. **Hybrid decomposition at 50k corpus**: BeamOnly vs CollapsedOnly vs Race, stratified by entity-spanning and DPI. This is the first decisive test of H1b.  
4. **Cross-link ablation on entity-spanning strata**: if ΔXLink is negligible, your cross-branch defence mechanism is not functioning and H1c’s “co-primary determinant” claim is likely false in practice.  
5. **Scale-up to 200k corpus**: only after the above passes; otherwise you are paying compute to confirm failure.

## Success criteria and kill criteria for the go/no-go gate

These thresholds are designed to be strict enough to prevent “optimism shipping” while still achievable in Phase 1.

### H1a token efficiency: go/no-go thresholds

Evaluate on **budget-feasible queries only** (because impossible queries should be handled by abstention/detection, not forced accuracy).

**Go (H1a):**

- **A@400(HCR Race) ≥ A@400(FlatStrong) + 0.08** absolute (≥8 percentage points), and  
- **A@400(HCR Race) ≥ A@∞(FlatStrong) − 0.02** absolute (within 2 points of FlatStrong unconstrained), and  
- **Budget-at-parity ≤ 400 tokens** (by definition above).

Rationale: BEIR-style results show strong baselines and the cost of reranking; modest deltas are easy to get with better rerankers alone, so +8pp at the same budget is a meaningful architecture-level gain rather than tuning noise. citeturn0search8turn6search3

**No-go (H1a kill):**

- **A@400(HCR Race) < A@400(FlatStrong) + 0.03** (less than 3pp gain) *and*  
- **A@800(HCR Race) < A@∞(FlatStrong) − 0.02** (cannot reach baseline even with 2× target budget).  
This indicates HCR is not buying meaningful token efficiency; you are paying complexity for little.

### H1b hybrid superiority: go/no-go thresholds

Evaluate on all queries, but especially stratify entity-spanning and multi-hop.

**Go (H1b):**

- **A@400(Race) ≥ max(A@400(BeamOnly), A@400(CollapsedOnly)) + 0.03**, and  
- Race wins are *not* confined to a trivial stratum: require **≥2 strata** (e.g., entity-spanning and DPI) where Race provides ≥3pp uplift over the better single path.  
- Additionally, at 50k and 200k corpus sizes, Race must not regress below FlatStrong@400.

**No-go (H1b kill):**

- Race provides **≤1pp** improvement over the best single path across the full set, implying the “race” complexity is unjustified; in that case you should simplify to the dominant path and reconsider the architecture.

### H1c scoring quality as lever: go/no-go thresholds

This requires both a *level-wise ε regime* and *predictiveness*.

**Go (H1c):**

- Measured ε at each level satisfies **εℓ ≤ 0.02** on single-branch queries and **εℓ ≤ 0.03** on cross-branch queries at 50k corpus scale (using your effective top-1/2 expansion definition).  
- ε is predictive: across queries, **Routing Survival Score = ∏ℓ (1 − εℓ(q))** (computed from logged routing events) must have **Spearman ρ ≥ 0.6** with A@400 on budget-feasible queries. (Spearman is chosen because the relationship need not be linear.)  
- Cross-link mechanism is validated as co-primary for entity-spanning queries: **ΔXLink ≥ 0.10** absolute drop in A@400 on entity-spanning queries when cross-links are removed.

Supporting rationale: hierarchical classification evaluation work formalises multi-path labelling/metrics; RAG diagnostics work (ARES/RAGChecker/RAGAS) emphasises component-level measurement as necessary for improving system understanding. Your ε metric operationalises this specifically for hierarchical routing. citeturn7search4turn5search0turn0search11turn7search6

**No-go (H1c kill):**

- Any of the following:
  - **ε1 > 0.05** at the first level on the dev slice even with cross-encoder reranking (this means your summaries/scoring are not separating siblings; compounding will dominate).
  - Spearman ρ < 0.3 between routing survival and A@400 (your supposed controlling lever does not control outcomes).
  - ΔXLink < 0.03 on entity-spanning queries (cross-links aren’t doing real work; either your workload assumptions are wrong or your cross-link construction is ineffective).

### Budget-impossible detection: acceptable operational performance in Phase 1

Because RB-005 estimates a large impossible fraction, you must not “hide” this with poor abstention.

**Go:**

- Impossible-detection **precision ≥ 0.80** and **recall ≥ 0.70** on the labelled impossible set, with clear separation between “aggregation/listing” and “OOD” (track them separately).

**No-go:**

- Precision < 0.65 (too many false alarms; the system refuses too often) or recall < 0.50 (system attempts impossible queries and wastes budget).

### Minimum viable benchmark deliverable for Phase 1

If you build only one version in Phase 1, build this:

- Corpus at 50k and 200k chunks (GitLab handbook snapshot + sampled Enron + Kubernetes release artefacts + targeted synthetic injectors). citeturn10search4turn3search1turn10search5  
- 300-query suite with tags and Feasible@400 labels, with evidence IDs.  
- Metrics: εℓ, A@T curves (T ∈ {200,400,800,1200,∞}), Race decomposition, ΔXLink, and impossible-detection F1.  
- Baselines: FlatStrong, BM25-only, dense-only, BeamOnly, CollapsedOnly.  
- Statistical protocol: 5 seeds, paired permutation tests on (A@400, AUCbudget, ε). citeturn4search4turn4search9
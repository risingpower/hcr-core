# RB-006: Benchmark Design — Perplexity Response

**Date:** 2026-02-13
**Source:** Perplexity
**Status:** Awaiting response

---

*Paste Perplexity response below this line.*
<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# \# RB-006: Benchmark Design for Hierarchical Coarse-to-Fine Retrieval

**Date:** 2026-02-13
**Status:** Open
**Decision Required:** Yes — this benchmark defines the success criteria for Phase 1 and the go/no-go gate
**Related:** H1a (token efficiency), H1b (hybrid superiority), H1c (scoring lever), RB-001 (prior art), RB-002 (theoretical basis), RB-003 (scoring mechanics), RB-004 (tree construction), RB-005 (failure modes)

## Context

Five prior research briefs have taken HCR from hypothesis to fully specified (but unbuilt) architecture. The findings are:

- **RB-001 (Prior art):** 12+ hierarchical retrieval systems exist. RAPTOR and LATTICE are closest. No system targets hard token budgets. RAPTOR's collapsed-tree outperforms strict traversal.
- **RB-002 (Theory):** Error compounds at (1-ε)^d. Strict elimination is fragile. Hybrid coarse-to-fine is theoretically optimal. Beam search transforms recall from (1-ε)^d to ~(1-(1-p)^k)^d.
- **RB-003 (Scoring):** Cascade architecture (BM25+dense → cross-encoder) achieves ε ≈ 0.01–0.02 per level. Path-relevance EMA is the highest-leverage component. Summary quality is the \#1 upstream factor.
- **RB-004 (Construction):** Top-down divisive clustering + LLM contrastive routing summaries + soft assignment. Structured summaries {theme, includes, excludes, key_entities, key_terms}. Entity cross-links for cross-branch support. No routing-specific tree quality metric exists — a genuine research gap.
- **RB-005 (Failure modes):** 26 failure modes, no showstopper. 10–20% expected overall failure rate. Top residual risks: DPI information loss, budget impossibility for aggregation queries, beam collapse. Entity cross-links are more critical than previously understood (primary mechanism for 40–55% of enterprise queries). Collapsed-tree should be co-primary, not fallback.

The architecture is now fully specified:

- **Tree:** Bisecting k-means, d=2–3, b∈[6,15], structured contrastive routing summaries, soft assignment (1–3 parents), entity cross-links, external source pointers at leaves
- **Traversal:** Dual-path — beam search (k=3–5 with MMR-style diversity enforcement) AND collapsed-tree retrieval in parallel; return higher-confidence result
- **Scoring:** Per-level cascade (hybrid BM25+dense pre-filter → top-3 → cross-encoder rerank → top-1–2), path-relevance EMA (α=0.5)
- **Selection:** AdaGReS-style submodular knapsack (relevance − redundancy under token constraint)
- **Budget:** 400 tokens as design aspiration, adaptive per query; success metric is "fraction answerable under 400 tokens"

**The question now is: how do we test it?**

RB-006 is the final research brief. After consolidation, we make the go/no-go decision on Phase 1 implementation. The benchmark design must be rigorous enough to definitively validate or invalidate the three sub-hypotheses (H1a, H1b, H1c), while being practical enough to build and run during Phase 1.

## Research Question

**What benchmark design — corpus, queries, metrics, baselines, and experimental protocol — will definitively validate or invalidate HCR's architecture for the target domain?**

Specifically:

1. **Corpus design.** What kind of test corpus captures the properties of an organisational knowledge base (heterogeneous formats, entity-dense, policy/procedure/project/people content, temporal evolution) while being small enough to build and iterate on during Phase 1? Should we use:
    - A synthetic corpus designed to stress-test specific failure modes?
    - A real-world dataset (or subset of one) that approximates organisational KB properties?
    - A hybrid — a real corpus augmented with synthetic elements targeting known weaknesses?
What existing datasets (BEIR, MTEB, enterprise search benchmarks, TREC Enterprise Track, organisational KB datasets) are closest to our needs? What are the gaps between available benchmarks and our target domain? What corpus size is sufficient to distinguish HCR from flat retrieval (given RB-005's finding that HCR's advantage manifests primarily at >50K documents)?
2. **Query design.** RB-005 identified the query distribution for organisational KBs: ~55–75% single-branch, ~20–40% cross-branch, ~50–65% detail/identifier, ~40–55% entity-centric. The benchmark must cover:
    - **Single-branch thematic queries** — the "easy" case where routing summaries work well
    - **Entity-spanning queries** (the most common cross-branch sub-type, 15–25%)
    - **Detail/identifier queries** — the DPI stress test (specific dates, version numbers, conditional logic)
    - **Multi-hop queries** (2-hop and 3+ hop)
    - **Comparative queries** ("how does X differ from Y?")
    - **Aggregation/listing queries** — the budget-impossible class
    - **Temporal queries** — versioned content, "what changed"
    - **Ambiguous queries** — multiple valid interpretations
    - **Out-of-distribution queries** — topics not in the KB

How many queries per category are needed for statistical significance? How should queries be generated — manually crafted, LLM-generated, derived from real search logs, or a combination? What query difficulty stratification is appropriate?
3. **Metrics design.** This is the most critical section. RB-005 and RB-003 identified several metrics that no existing system measures. HCR's benchmark must include:

**a) Per-level routing accuracy (ε).** The governing parameter. No system has ever measured this. How should it be defined and measured? What is the ground truth — human annotation of "correct branch at each level"? How do we handle cases where multiple branches are legitimately relevant (soft assignment)?

**b) End-to-end retrieval quality.** Standard metrics: Recall@k, NDCG@k, MRR. But under token budgets, these need adaptation — what matters is not "did the right document appear in top-k" but "did the returned context (under 400 tokens) contain the answer?" What metric captures this?

**c) Token efficiency.** The core H1a metric. Proposed: answer accuracy as a function of token budget. Measure at 200, 400, 800, 1200, unconstrained. The key comparison: at what budget does HCR match flat retrieval's unconstrained accuracy?

**d) Beam-search vs collapsed-tree comparison.** The system runs both in parallel. What metrics distinguish when each path wins? How do we measure the value of the "race" design?

**e) Entity cross-link quality.** Given RB-005's finding that entity cross-links are the primary mechanism for 40–55% of queries, how do we measure cross-link coverage, precision, and recall? What is the relationship between entity cross-link quality and end-to-end retrieval quality?

**f) Tree quality metrics.** RB-004 identified a research gap: no routing-specific tree quality metric exists. What should such a metric capture? Proposed candidates: per-level routing accuracy, sibling distinctiveness (do siblings have clearly different themes?), entity coverage (are all entities reachable via cross-links?), leaf coverage (what fraction of corpus is reachable by at least one traversal path?). Which of these are most diagnostic?

**g) Budget-impossible query detection.** The system needs to recognise when a query cannot be answered under the token budget. What metric measures the accuracy of this detection? False positives (giving up when an answer was possible) vs false negatives (attempting an answer that's inevitably incomplete)?

**h) Failure mode coverage.** RB-005 identified 26 failure modes. The benchmark should instrument as many as possible. Which of the 26 are measurable in a benchmark setting? Which require production telemetry instead?
4. **Baselines.** What systems should HCR be compared against? At minimum:
    - **Flat retrieval + cross-encoder reranking** — the strong "do nothing fancy" baseline
    - **RAPTOR** — collapsed-tree approach, the closest prior art that challenges strict hierarchy
    - **Naive top-k** — embedding similarity, no reranking, the weak baseline
    - **LATTICE** — if reproducible; closest architectural competitor

What other baselines are important? Should we compare against commercial systems (Pinecone, Weaviate) or only against reproducible academic baselines? What about BM25-only as a lexical baseline?
5. **Experimental protocol.** What experimental design ensures valid, reproducible results?
    - How many runs for variance estimation?
    - What statistical tests for significance?
    - Should we use held-out test queries, k-fold cross-validation, or a train/dev/test split?
    - How do we control for LLM variability (summary generation, scoring with LLM-as-judge)?
    - What is the right order of experiments — what should we test first to fail fast if the architecture is flawed?
    - How do we handle the "transition period" concern from RB-005 (HCR may be worse at small corpus sizes)?
6. **Ablation design.** Which components should be individually ablated to understand their contribution?
    - Beam search with/without diversity enforcement
    - Collapsed-tree path on/off
    - Entity cross-links on/off
    - Soft assignment on/off
    - Contrastive vs generic summaries
    - Different tree depths (d=1, d=2, d=3)
    - Different beam widths (k=1, k=3, k=5)
    - Different token budgets (200, 400, 800, 1200, unconstrained)

What is the minimum viable ablation set — what must we test, and what can be deferred?
7. **Practical constraints.** Phase 1 is a small team (one person + AI assistance). The benchmark must be:
    - Buildable incrementally (not all-or-nothing)
    - Runnable on reasonable hardware (no GPU cluster)
    - Iteratable — results should inform design changes without requiring full rebuild
    - Cost-aware — LLM calls for summary generation, cross-encoder scoring, and LLM-as-judge evaluation add up

What is the minimum viable benchmark that can provide a credible go/no-go signal? What can be deferred to later phases?
8. **Existing benchmark landscape.** What benchmarks and evaluation frameworks already exist that we can build on?
    - BEIR (Thakur et al., NeurIPS 2021) — multi-dataset retrieval benchmark
    - MTEB — massive text embedding benchmark
    - TREC Enterprise Track — enterprise search evaluation
    - RAGAS, ARES, or other RAG evaluation frameworks
    - LongBench, QuALITY — long-context QA benchmarks
    - Any benchmarks specifically designed for hierarchical retrieval?
    - Any benchmarks specifically designed for token-constrained retrieval?

What can we reuse vs what must we build from scratch?

## Scope

**In scope:**

- Complete benchmark specification: corpus, queries, metrics, baselines, protocol, ablations
- Mapping of benchmark components to hypothesis validation (H1a, H1b, H1c)
- Practical feasibility assessment for Phase 1 constraints
- Identification of what existing benchmarks/tools can be reused
- Minimum viable benchmark definition (what's essential vs nice-to-have)

**Out of scope:**

- Actually running the benchmark (that's Phase 1)
- Implementation details of the HCR system itself
- Scoring architecture alternatives (RB-003 — complete)
- Tree construction alternatives (RB-004 — complete)
- Failure mode analysis (RB-005 — complete)


## What We Already Know

From RB-001 (prior art):

- RAPTOR evaluates on QuALITY, NarrativeQA, QASPER — long-context QA benchmarks
- LATTICE evaluates on MultiHop-RAG, MuSiQue, HotpotQA — multi-hop reasoning benchmarks
- No system evaluates per-level routing accuracy — everyone reports end-to-end metrics only
- BEIR shows in-domain performance doesn't predict out-of-domain generalisation
- Enterprise retrieval performance is "substantially lower" than academic benchmarks

From RB-002 (theory):

- The key theoretical prediction to validate: hybrid coarse-to-fine should outperform both pure approaches
- Token budget creates a measurable advantage: at what budget does hierarchy match flat retrieval's unconstrained accuracy?
- The (1-ε)^d equation is the central prediction — if ε is measurably ≈0.01–0.02, the theory holds

From RB-003 (scoring):

- Per-level ε is the single most important metric to instrument
- The cascade architecture is specified: we know what to build, we need to measure if it works as predicted
- Path-relevance EMA is theoretically highest-leverage — needs A/B testing
- AdaGReS submodular knapsack has approximation guarantees (0.316 for knapsack constraint)

From RB-004 (construction):

- No routing-specific tree quality metric exists — this is a genuine research gap HCR can fill
- Contrastive vs generic summaries: no empirical evidence for routing improvement — highest-value experiment
- The construction recipe is convergent (three-source agreement) — we're testing a well-specified design

From RB-005 (failure modes):

- 26 failure modes to instrument/measure where possible
- Query distribution estimates: 55–75% single-branch, 20–40% cross-branch, 50–65% detail, 40–55% entity-centric
- Entity cross-link quality is a primary metric (not secondary)
- Budget-impossible queries (~20–35%) need detection, not retrieval
- Collapsed-tree vs beam-search comparison is a first-class experiment
- The "transition period" at small corpus sizes is the highest-risk phase


## Prompt for Sources

> I am designing a **benchmark** for a hierarchical coarse-to-fine retrieval system (HCR) that will serve as the **final validation gate before implementation**. The benchmark must definitively validate or invalidate three hypotheses about the architecture. The system is fully designed but not yet built — this benchmark defines what "success" looks like.
>
> **The system being benchmarked:**
> - **Tree structure:** Top-down divisive clustering (bisecting k-means), depth 2–3, branching factor 6–15. Internal nodes hold structured contrastive routing summaries (`{theme, includes, excludes, key_entities, key_terms}`). Leaf nodes are pointers to external data sources.
> - **Dual-path retrieval:** (1) Beam search (k=3–5, MMR-style diversity enforcement) over the tree, AND (2) collapsed-tree retrieval (RAPTOR-style, flat search over all nodes including summaries), run in parallel; return higher-confidence result.
> - **Scoring cascade:** Per level: hybrid BM25+dense pre-filter (all children) → top-3 → cross-encoder rerank → top-1–2. Path-relevance EMA across depth (α=0.5).
> - **Token budget:** 400 tokens as design aspiration (adaptive, not hard-capped). AdaGReS-style submodular knapsack for chunk selection (relevance − redundancy under token constraint).
> - **Cross-branch defense:** Content decomposition, soft assignment (1–3 parents), entity cross-links, beam diversity, collapsed-tree co-primary path.
> - **Target domain:** Organisational knowledge base — policies, procedures, projects, people, tools, communications, technical docs. Consumed by an agentic system that needs precise retrieval from a growing knowledge base.
>
> **The three hypotheses to validate:**
>
> **H1a (Token efficiency, 65% confidence):** HCR achieves equivalent or better answer accuracy than flat retrieval while using fewer tokens. Design target: 400 tokens. Success metric: "fraction of queries answerable under 400 tokens" should be significantly higher than flat retrieval at the same budget.
>
> **H1b (Hybrid superiority, 80% confidence):** Coarse elimination + fine similarity (the dual-path architecture) outperforms either pure hierarchy (beam search only) or pure flat retrieval (no hierarchy) on both precision and recall.
>
> **H1c (Scoring quality as lever, 75% confidence):** Per-level scoring quality (measured as ε, per-level error rate) is the primary determinant of end-to-end retrieval quality, with error compounding at (1-ε)^d. Additionally, entity cross-link quality is a co-primary determinant for entity-centric queries (~40–55% of workload).
>
> **What our prior research established:**
> - 26 failure modes identified, no showstopper. 10–20% expected overall failure rate.
> - Query distribution: ~55–75% single-branch, ~20–40% cross-branch, ~50–65% detail/identifier, ~40–55% entity-centric.
> - Per-level routing accuracy (ε ≈ 0.01–0.02) has NEVER been measured in any system — it is a theoretical estimate from cascade scoring benchmarks, not empirical.
> - No routing-specific tree quality metric exists in the literature — a genuine research gap.
> - Entity cross-links are the primary defense for the dominant query type (entity-spanning), more critical than routing summaries.
> - Budget-impossible queries (~20–35%: aggregation, exhaustive listing, temporal diffs) cannot be answered under 400 tokens regardless of retrieval quality.
> - HCR's advantage over flat retrieval manifests primarily at >50K documents; at small corpus sizes, flat retrieval may be superior.
> - Collapsed-tree retrieval should be co-primary with beam search, not a fallback.
>
> I need a **comprehensive benchmark design**. Specifically:
>
> 1. **Corpus design.** What test corpus captures organisational KB properties (heterogeneous, entity-dense, temporal, policy/procedure/project/people) while being practical for Phase 1 (one-person team, no GPU cluster)? Options: synthetic, real-world subset, hybrid? What existing datasets (BEIR, MTEB, TREC Enterprise, etc.) are closest? What size is needed to demonstrate HCR's advantage over flat retrieval? How should the corpus be structured to stress-test the 26 identified failure modes? Should the corpus include a "growth" dimension (start small, add content) to test the transition period?
>
> 2. **Query design.** Design a query suite that covers the identified distribution:
>    - Single-branch thematic, entity-spanning, detail/identifier (DPI stress test), multi-hop (2-hop and 3+), comparative, aggregation/listing, temporal, ambiguous, OOD
>    - How many queries per category for statistical significance?
>    - How should queries be generated — manual, LLM-generated, derived from real logs, or combination?
>    - How should query difficulty be stratified?
>    - Should queries include expected "budget feasibility" labels (answerable in 400 tokens yes/no)?
>
> 3. **Metrics design.** This is the most critical component. For each metric, specify: definition, measurement method, ground truth requirement, and which hypothesis it validates.
>    - **Per-level routing accuracy (ε):** How to define, measure, and establish ground truth for the metric no system has ever measured. How to handle multi-relevance (multiple correct branches)?
>    - **End-to-end retrieval under token constraint:** Not just Recall@k — what metric captures "did the 400-token context contain the answer?" Answer sufficiency, context precision, faithfulness?
>    - **Token efficiency curve:** Accuracy as f(token budget) at 200, 400, 800, 1200, unconstrained. What is the shape of this curve and what shape indicates success?
>    - **Beam vs collapsed comparison:** How to measure which path wins per query and under what conditions?
>    - **Entity cross-link quality:** Coverage, precision, recall. Relationship to end-to-end performance.
>    - **Tree quality metrics:** What routing-specific quality metric(s) should HCR introduce to fill the research gap? Sibling distinctiveness, routing accuracy, entity coverage, leaf reachability?
>    - **Budget-impossible detection:** Precision/recall of detecting unanswerable queries.
>    - **Failure mode instrumentation:** Which of the 26 identified failure modes are measurable in a benchmark? Which need production telemetry?
>
> 4. **Baselines.** What systems should HCR be compared against?
>    - Strong: flat retrieval + cross-encoder reranking (the "do nothing fancy" baseline)
>    - Academic: RAPTOR, LATTICE (if reproducible)
>    - Weak: naive top-k embedding similarity, BM25-only
>    - Are there other baselines that would strengthen the evaluation? Commercial systems?
>    - For each baseline, what is the implementation complexity and what do we learn from the comparison?
>
> 5. **Experimental protocol.** Design for validity and reproducibility:
>    - How many runs for variance estimation? What statistical tests?
>    - How to control for LLM variability (temperature, model version, prompt sensitivity)?
>    - What is the fail-fast experiment order — what should we test first to detect fatal flaws early?
>    - How to handle the transition period (small corpus) — should we test at multiple corpus sizes?
>    - Train/dev/test split or cross-validation? How to avoid overfitting the tree to the query set?
>    - How to ensure the benchmark is fair to baselines (same retrieval budget, same reranking, same LLM for evaluation)?
>
> 6. **Ablation design.** Which components must be individually ablated and in what priority order?
>    - Minimum viable ablation set for Phase 1
>    - What does each ablation tell us about which hypothesis?
>    - Which ablation would be the highest-value single experiment to run first?
>
> 7. **Evaluation framework.** How should answers be judged?
>    - LLM-as-judge for answer quality — which framework (RAGAS, ARES, custom)?
>    - Human evaluation — when is it needed, what scale is practical?
>    - How to measure "answer sufficiency" (did the context contain enough information?) separately from "answer accuracy" (was the generated answer correct)?
>    - How to handle queries with no single correct answer (thematic queries, opinion-dependent)?
>
> 8. **Practical constraints.** The benchmark must be buildable by one person with AI assistance:
>    - What is the minimum viable benchmark (MVB) that provides a credible go/no-go signal?
>    - What can be deferred to later phases without compromising the go/no-go decision?
>    - What is the estimated cost (LLM API calls for summary generation, scoring, evaluation)?
>    - What existing tools/frameworks can be reused (ir_measures, RAGAS, BEIR toolkit, etc.)?
>    - Should the benchmark be designed to also serve as a regression suite for ongoing development?
>
> 9. **Success criteria.** What specific numeric thresholds define "go" vs "no-go"?
>    - For H1a: at what token budget must HCR match flat retrieval's accuracy? What delta is meaningful?
>    - For H1b: what precision/recall improvement over the best single-path approach is required?
>    - For H1c: what correlation between ε and end-to-end quality confirms the compounding equation?
>    - What overall failure rate is acceptable? (Our estimate: 10–20%. Is that good enough?)
>    - At what corpus size must HCR demonstrate advantage?
>    - What is the "kill criterion" — what result would definitively invalidate the architecture?
>
> Be specific and practical. I want a benchmark I can actually build and run, not a theoretical wish list. Prioritise ruthlessly — what must be in the first version vs what can come later? Cite existing benchmarks, evaluation frameworks, and methodologies that HCR can build on. If there are trade-offs between rigour and practicality, state them explicitly and recommend which way to lean for a Phase 1 go/no-go decision.

## Success Criteria

A good response will:

1. **Specify a concrete, buildable corpus** — not just "use an organisational KB" but specific datasets, sizes, and augmentation strategies with justification
2. **Define a query suite with category counts** — how many queries per type, how to generate them, and why that count is sufficient for statistical significance
3. **Provide precise metric definitions** — especially for per-level routing accuracy (ε), which has never been measured, and for token-constrained answer sufficiency
4. **Include numeric success thresholds** — what specific numbers define "go" vs "no-go" for each hypothesis
5. **Propose a fail-fast experiment order** — what to test first to detect fatal flaws early, avoiding wasted effort
6. **Specify the minimum viable benchmark** — the smallest useful evaluation that provides a credible go/no-go signal
7. **Address the transition period** — how to evaluate HCR at small corpus sizes where flat retrieval may be superior
8. **Design ablations that map to hypotheses** — each ablation should directly test a specific claim
9. **Be practically feasible** — one person, no GPU cluster, reasonable LLM API costs, incremental buildability
10. **Cite reusable tools and frameworks** — what existing infrastructure (BEIR, RAGAS, ir_measures, etc.) can be leveraged

Below is a concrete, Phase‑1‑buildable benchmark design that hits your success criteria and maps cleanly to H1a–c.

***

## 0. Design principles

The benchmark is built to:

- Stress the specific advantages HCR claims (hierarchy, dual-path, token efficiency, cross-links) over strong flat baselines.
- Measure the unmeasured (ε, routing-specific tree quality, budget feasibility) using ideas from RAG evaluation frameworks like RAGAS/ARES and recent token‑budget RAG work.[^1_1][^1_2][^1_3][^1_4][^1_5]
- Stay within 1‑person / CPU‑only constraints by:
    - Reusing existing corpora and toolkits (BEIR/MTEB data format, RAG evaluation libraries, MultiHop‑RAG, LongBench/QuALITY).[^1_6][^1_7][^1_8][^1_9][^1_10][^1_11]
    - Starting with a minimal viable benchmark (MVB) and extending only if HCR survives fail‑fast checks.

The rest is organized by your numbered questions.

***

## 1. Corpus design

### 1.1 Overall strategy: hybrid corpus with growth slices

Use a **hybrid corpus** that approximates an organisational KB but is composed from public sources:

- **KB‑like structure**: policies, procedures, project docs, people/org info, temporal evolution.
- **Multi-source** to avoid overfitting to one style.
- **Growth slices** to test the transition period (small → medium → large) where HCR is predicted to overtake flat retrieval.

Proposed corpus layers (document counts are after chunking):

1. **C_small (~10k chunks)** – debugging + early fail‑fast:
    - A subset of one rich, structured “handbook-style” source (e.g., GitLab Handbook, Basecamp Handbook, or similar public engineering handbooks).
    - Chunk into 300–500 token passages (with overlap) to get ~10k chunks.
2. **C_mid (~40k–50k chunks)** – main go/no‑go corpus:
    - Add:
        - Public engineering / product manuals and runbooks (Kubernetes, Terraform, popular SaaS API docs).
        - 1–2 open company handbooks / policy repositories (engineering guidelines, HR policies, security policies).
        - A small, curated people/org layer: project READMEs, “team pages”, issue trackers or RFC collections with author metadata.
    - Target after chunking: 40–50k chunks (this keeps Phase 1 tractable but begins to cross the >50k cutoff where you expect HCR’s advantage).
3. **C_large (~80k–100k chunks)** – transition period \& scalability:
    - Extend C_mid with:
        - Additional doc categories: incident reports, changelogs / release notes, design docs from extra OSS projects.
        - Synthetic variants (see below) designed to embed more entities and temporal versions.
    - Target ~100k chunks. This is where HCR must show advantage over flat retrieval.

For **temporal evolution**, preferentially include sources with multiple versions (e.g., versioned docs, changelog entries) and keep version metadata. For “people/project” dimensions, exploit authorship, team labels, and repo metadata.

### 1.2 Synthetic augmentation for targeted failure modes

To stress the 26 failure modes without building a purely synthetic corpus:

- **Entity-spanning stressors**:
    - Take entities (products, teams, people) that appear in multiple corpora (e.g., project names, services).
    - Generate synthetic “linking” documents that mention them in different branches (e.g., a postmortem mentioning a product + team + infra component) to enforce cross-branch evidence paths.
- **Detail/identifier (DPI) stressors**:
    - Programmatically mutate copies of policy/procedure docs by:
        - Changing specific dates, thresholds, version numbers, conditionals.
        - Ensuring multiple near-duplicate versions exist.
    - Label queries so that only the correct version is acceptable.
- **Aggregation/listing / budget‑impossible**:
    - Create synthetic summary pages that list 50+ items (e.g., all open incidents, all features launched in a quarter).
    - Construct queries that require exhaustive lists or long diffs (“List all incidents involving X in 2024 and their resolutions”) where even ideal compression cannot fit in 400 tokens.
- **Temporal diffs**:
    - For docs with versions (v1, v2, v3), add synthetic “changelog” docs and queries like “What changed in the security policy for contractors between v2.1 and v3.0?”

This keeps annotation tractable: these synthetic elements have automatically knowable ground truth.

### 1.3 Existing datasets to reuse / adapt

Use external benchmarks **auxiliarily**, not as the main KB, to validate generality for specific query types:

- **Multi-hop \& news‑style aggregation**: MultiHop‑RAG (multi-hop queries with gold supporting evidence over a news corpus).[^1_7][^1_12]
- **Long-context QA**: QuALITY and NarrativeQA, which RAPTOR uses.[^1_13][^1_8]
- **Multi-hop QA**: HotpotQA, MuSiQue, 2WikiMultiHopQA (used in hierarchical RAG variants like HiRAG).[^1_14][^1_15]

These help check whether HCR’s advantages survive outside the synthetic org KB but do not need full tree construction in Phase 1.

### 1.4 Corpus size and structure vs hypotheses

- **Minimum**: C_mid (~50k chunks) is where HCR vs flat differences should become observable per RB‑005.
- **Transition test**: Explicitly run at:
    - C_small (~10k chunks)
    - C_mid (~50k)
    - C_large (~100k)
- Tree built per corpus slice with same depth/branching constraints (d=2–3, b∈) so routing depth d is controlled.[^1_16][^1_17]

***

## 2. Query design

### 2.1 Query categories and counts

Aim for **~400 test queries** on C_mid as the main evaluation set (plus ~100 dev queries), with each query tagged along several axes (branch type, entity-centric, DPI, multi-hop, temporal, etc.). Many queries will have multiple labels; numbers below are “primary” labels.

Target distribution (for test set):

- **Single-branch thematic**: 120
- **Entity-spanning** (cross-branch, entity-centric): 80
- **Detail/identifier (DPI)**: 80
- **Multi-hop**:
    - 2-hop: 40
    - 3+ hop: 20
- **Comparative**: 40
- **Aggregation/listing** (budget-impossible candidates): 40
- **Temporal “what changed”**: 40
- **Ambiguous**: 40
- **Out-of-distribution (OOD)**: 40

Total is >400 because of overlap; enforce at least:

- ≥200 single-branch,
- ≥120 cross-branch,
- ≥160 DPI,
- ≥100 multi-hop (tagged),
- ≥80 temporal,
- ≥80 aggregation/listing.

With 400 queries, a 5–7 point absolute accuracy difference is detectable at p<0.05 with paired tests.

### 2.2 Query generation process

Use a **three-way pipeline** for query generation:

1. **Seed from real docs**:
    - For each major document cluster (policy, procedure, project, incident, handbook section), have an LLM propose 5–10 candidate questions:
        - One-thematic
        - One DPI
        - One entity-centric
        - One temporal / versioning
        - One comparative or aggregation
    - Filter manually for realism and diversity.
2. **Programmatic queries for synthetic structures**:
    - For synthetic DPI/version docs: auto-generate queries that target specific IDs, thresholds, clauses.
    - For aggregation/listing docs: auto-generate list/diff queries known to be budget‑impossible under 400 tokens.
3. **Multi-hop and cross-entity queries**:
    - Use LLMs to explicitly construct 2-hop / 3-hop questions referencing 2–3 entities or documents across branches, in the style of MultiHop‑RAG and HotpotQA.[^1_15][^1_7]
    - Use a chain-of-thought prompt that enumerates supporting docs, then emit the final natural language question plus gold answer and evidence.

Use **LLM‑assisted annotation** to identify the minimal supporting chunks (see metrics section).

### 2.3 Difficulty stratification

For each query, define a **difficulty level (1–3)** based on:

- **Evidence span**:
    - Level 1: answer contained in a single chunk.
    - Level 2: 2–3 chunks; possibly in one branch.
    - Level 3: 3+ chunks and / or multi-branch.
- **Entity complexity**:
    - 
# of distinct entities involved and whether they cross branches.

- **Temporal complexity**:
    - Whether reasoning about “before vs after” or diff is required.

This allows stratified analysis (e.g., HCR may outperform flat retrieval mainly on Level 3, cross-branch).

### 2.4 Budget-feasibility labels

Add a binary label **“budget-feasible @400?”** for each query:

- **Feasible**: there exists some set of ≤400 tokens (including summarisation) that suffices to answer correctly and completely.
    - For evidence-based datasets (MultiHop‑RAG, HotpotQA), approximate by total tokens across gold supporting paragraphs; if ≤400, mark feasible, else manual check.
    - For synthetic aggregation \& diff queries, label most as **not feasible** by construction.
- **Not feasible**: exhaustive list / long diff / long chain of reasoning uncompressible into 400 tokens without losing required detail.

Ground truth built via:

- LLM proposals of minimal supporting snippets + manual spot checks on a 20–25% sample.

***

## 3. Metrics design

For each metric: definition, how to measure, ground truth, and link to hypotheses.

### 3.1 Per-level routing accuracy (ε) – core for H1c

**Definition**

For each query $q$ and tree depth level $l$:

- Let $C_l$ be the set of children of the current node(s) considered at level $l$ during beam traversal.
- Let $G_l \subseteq C_l$ be the set of **gold-relevant children**: children whose subtree contains at least one gold evidence chunk for $q$.
- Let $S_l \subseteq C_l$ be the set of children actually selected by the algorithm at that level (beam with width $k$).

Define level‑l routing success as:

$$
\text{succ}_l(q) = \mathbb{1}[S_l \cap G_l \neq \emptyset]
$$

and routing error:

$$
\varepsilon_l(q) = 1 - \text{succ}_l(q).
$$

Aggregate over queries to get:

- $\varepsilon_l = \mathbb{E}_q[\varepsilon_l(q)]$ per level.
- Global $\varepsilon = \frac{1}{d}\sum_{l=1}^d \varepsilon_l$ or route‑level success probability $\hat{P}_\text{route}(q) = \prod_{l=1}^d \text{succ}_l(q)$.

This handles **multi-relevance** naturally: if several branches are gold (soft assignment), any of them counts as success.

**Ground truth requirement**

- For each query, a set of **gold evidence leaves** (chunk IDs).
- Tree structure with ancestors for each leaf.
- From leaves, compute $G_l$ as the set of children on any path from root to a gold leaf.

Gold evidence is already provided in MultiHop‑RAG and many QA datasets, and can be annotated for the org KB with LLM‑assisted tools plus manual verification on a subset.[^1_12][^1_7]

**Measurement method**

- Instrument the beam traversal for each query to log $C_l$, $S_l$, and the path‑relevance scores.
- Compute $\varepsilon_l$ at each depth.

**Hypothesis link**

- **H1c**: Validate whether empirically $\varepsilon \approx 0.01–0.02$ is achievable with the BM25 + dense + cross‑encoder cascade.[^1_9][^1_10]
- Check correlation between per‑level error and end‑to‑end quality (see below). If $\varepsilon$ is significantly higher (e.g., >0.05) and correlates with failures as $(1 - \varepsilon)^d$, H1c holds but design may be insufficient; if errors do not correlate, the theory is suspect.


### 3.2 End-to-end retrieval under token constraint – H1a, H1b, H1c

End‑to‑end evaluation must separate:

1. **Context quality under budget**: did the retrieved context (≤B tokens) contain necessary information?
2. **Answer quality**: given that context, did the LLM answer correctly and faithfully?

Use two layers of metrics, borrowing from RAG evaluation practice:[^1_2][^1_4][^1_5][^1_18][^1_1]

1. **Contextual metrics** (per query and budget B):
    - **Context Recall@B**: fraction of gold evidence chunks whose content is present (or semantically paraphrased) in the retrieved ≤B-token context.
    - **Context Precision@B**: fraction of retrieved chunks that are relevant to the query.
    - Implement via RAGAS/ARES‑style LLM‑based context precision/recall metrics.[^1_5][^1_1][^1_2]
2. **Answer metrics**:
    - **Answer correctness**: binary / graded score from an LLM judge trained or configured as in ARES (faithfulness + relevance to gold answer).[^1_19][^1_1]
    - **Answer faithfulness**: does the answer stay within retrieved context (no hallucinations).
    - **Answer sufficiency**: LLM‑as‑judge decides whether the context was sufficient to fully answer, even if the model got it wrong (use RAGAS‑style “answer supported by context?” vs “answer matches ground truth?” distinction).

**Primary end‑to‑end metric** for H1a/H1b:

- **Accuracy@B**: proportion of queries whose answers are judged correct and faithful given a budget B.
- **Sufficiency@B**: proportion of queries where context is judged sufficient (regardless of answer error) – sensitive to retrieval, not generation.


### 3.3 Token efficiency curve – core for H1a

For each system (HCR, flat, others) and corpus size (C_small, C_mid, C_large):

- Evaluate at budgets $B \in \{200, 400, 800, 1200, \text{unconstrained}\}$.
    - Unconstrained: “high but realistic” max (e.g., 3000–4000 tokens) or simply “all retrieved until model context limit,” as in token‑budget RAG work.[^1_3]

Plot:

- **Accuracy@B vs B**
- **Sufficiency@B vs B**
- Optionally **Context Recall@B vs B**

Expected shape for HCR if H1a holds:

- At very low B (200), HCR and flat may be similar or flat slightly better.
- At target B=400: HCR matches or exceeds **flat@800** accuracy and approaches **flat@unconstrained** within a few points.
- Beyond 800–1200, curves flatten for both, with diminishing returns, as seen in recent long‑context/token‑budget evaluations.[^1_20][^1_3]

**Success thresholds (H1a)**

On C_mid:

- At **B=400**:
    - HCR Accuracy@400 ≥ Flat Accuracy@800 − 2 points, and
    - HCR Accuracy@400 ≥ Flat Accuracy@400 + 5 absolute points (p<0.05).
- At **unconstrained**:
    - HCR Accuracy within 3 points of flat’s unconstrained accuracy while using ≤50% of the **average retrieval tokens** (measured separately).

If these do not hold at any corpus size, H1a is not supported.

### 3.4 Beam vs collapsed-tree comparison – H1b

Recall HCR runs both **beam traversal** and **collapsed-tree retrieval** (RAPTOR‑style collapsed summaries that are searched flat, which performed best in RAPTOR).[^1_8][^1_21][^1_13]

Per query and budget:

- Compute:
    - **Beam‑only**: run HCR with only the hierarchical beam.
    - **Collapsed‑only**: run HCR with only the collapsed-tree path.
    - **Dual**: use HCR’s designed “race” (choose the path with higher path‑relevance / confidence).
- For each, measure Accuracy@B, Sufficiency@B, Context Recall@B.

Additional metrics:

- **Win rate per path**:
    - Fraction of queries where Beam‑only is correct but Collapsed‑only is not, and vice versa.
    - Fraction where only Dual is correct (due to selecting the right path).
- **Conditional analysis**:
    - Break down by query type (entity-spanning vs single-branch, multi-hop vs single-hop, DPI vs non‑DPI).

**Hypothesis link (H1b)**

- HCR (Dual) should outperform:
    - Beam‑only and Collapsed‑only by ≥5 absolute accuracy points on at least one major category (multi-hop, cross-branch, DPI) on C_mid or C_large.
- If Dual never beats the better of Beam‑only or Collapsed‑only, the “race” design adds complexity without gain → H1b fails.


### 3.5 Entity cross-link quality – co-primary for H1c

**Static metrics**

Define an entity graph:

- Run NER + coref (or an LLM‑based entity linker) on the corpus to extract entity mentions and canonical IDs.
- Build a gold graph of **document ↔ entity** edges.

Given HCR’s **cross-links** (explicit pointers between nodes for shared entities):

- **Coverage**: proportion of entity‑document pairs in the gold graph that are reachable via at least one cross‑link from any node containing that entity.
- **Precision**: proportion of cross-links that connect nodes whose entity sets truly overlap.
- **Recall**: fraction of all distinct entity co‑occurrences that correspond to at least one cross-link.

**Dynamic impact metrics**

- For **entity-centric \& entity-spanning queries**:
    - Compare HCR full vs **“no cross-links”** variant on:
        - Accuracy@B
        - Context Recall@B
- Correlate per‑entity coverage with end‑to‑end performance on queries mentioning that entity.

**Hypothesis link**

- **H1c** predicts that cross‑link quality is co‑primary for entity-centric queries:
    - On entity-centric \& entity-spanning queries, turning off cross-links should drop Accuracy@400 by ≥5–7 points (p<0.05) while having small effect (<2–3 points) on purely single-branch thematic queries.
    - Static coverage/precision should be high (e.g., coverage ≥0.8, precision ≥0.9 for frequent entities); low coverage with large impact on performance is a red flag.


### 3.6 Tree quality metrics – filling the gap from RB‑004

Introduce a **routing-specific tree quality suite**, grounded in routing behavior and semantic separation:

1. **Routing Accuracy Index (RAI)**:
    - $\text{RAI} = 1 - \varepsilon$ (average per-level routing success).
    - Compute separately by depth and query type (single-branch vs cross-branch).
    - Diagnostic: if RAI is high for single-branch but low for entity-spanning queries, tree is misaligned with entity needs.
2. **Sibling Distinctiveness Score (SDS)**:
    - For each internal node, compute:
        - Pairwise cosine **distance** between sibling summaries.
        - A cluster‑separation index like **Dunn index** or **silhouette score** over children using embedding representations.[^1_22][^1_23][^1_24]
    - Aggregate into SDS per level.
    - Hypothesis: higher SDS correlates with better routing accuracy and answer sufficiency; low SDS with confusion and beam collapse.
3. **Entity Coverage Score (ECS)**:
    - For each entity:
        - Count how many distinct top-level siblings contain that entity (excessive scattering is bad for single-branch; some scattering is needed for cross-branch).
    - Define ECS as the fraction of entities whose mentions are:
        - Either well‑localized (mostly inside one branch, plus a few cross-links), or
        - Have high-quality cross-links covering cross-branch needs.
    - Correlate ECS with performance on entity-centric queries.
4. **Leaf Reachability (LR)**:
    - The fraction of leaves containing any gold evidence that lie along at least one successful route (where $\text{succ}_l(q)=1$ at all depths) under the beam search for some query.
    - Low LR implies many gold leaves are effectively unreachable under current scoring/beam.

These metrics are **tree‑specific** and fill the literature gap noted in RB‑004: there is no routing quality metric beyond end‑to‑end IR scores.

### 3.7 Budget-impossible query detection

For queries with budget-feasibility labels:

- Measure a classifier that predicts **“unanswerable under 400 tokens”** based on:
    - Retrieval statistics (number and spread of relevant chunks).
    - Estimated minimal aggregation size (e.g., sum of token lengths of k top evidence chunks).
    - Heuristics (presence of “all”, “list”, long time ranges).

Metrics:

- **Precision/Recall/F1** of “impossible” prediction.
- Cost-sensitive breakdown:
    - **False positives** (predict impossible when it was feasible) → lost opportunities.
    - **False negatives** (predict feasible and attempt, but judged insufficient) → partial / misleading answers.

Desirable regime:

- High precision on “impossible” (≥0.9) even at cost of some recall; failing safe is preferable.


### 3.8 Failure mode instrumentation

From the 26 failure modes, the benchmark can directly measure those that manifest as:

- Misrouting / missed branches → via $\varepsilon_l$, RAI, LR, beam vs collapsed comparisons.
- Cross-link failures → via ECS and cross-link ablations.
- DPI / identifier loss → via DPI query subset where gold IDs must match (strict string matching).
- Beam collapse / lack of diversity → via:
    - Diversity metrics of beam (pairwise cosine distance across children).
    - Performance drop when k=1 vs k=3–5.
- Summary failure (routing summaries too lossy or misleading) → via:
    - Contrastive vs generic summary ablations.
    - Measuring local summary–child semantic alignment (e.g., average similarity between summary embedding and children) and correlating to ε.

Other failure modes (e.g., production latency, model drift, ACL violations, live feedback loops) require **production telemetry** and are explicitly out‑of‑scope for Phase 1.

***

## 4. Baselines

Prioritize **reproducible, open** baselines that can be implemented quickly and evaluated under matched token budgets.

### 4.1 Core baselines

1. **Flat dense + cross-encoder rerank (strong “do nothing fancy”)**
    - Retriever: high‑quality embedding model (e.g., BGE‑large / E5‑large), HNSW index.
    - Hybrid with BM25: either via reciprocal rank fusion or score interpolation, inspired by BEIR/MTEB practice.[^1_10][^1_9]
    - Reranker: cross‑encoder trained on MS MARCO or similar.
    - Retrieval algorithm: top‑N documents, rerank via cross‑encoder, then feed into AdaGReS‑style submodular knapsack for token‑budget selection.[^1_25][^1_26][^1_27]
    - Purpose: tests whether hierarchy adds value beyond a very strong flat pipeline.
2. **Naive dense top‑k (weak baseline)**
    - Embedding‑only top‑k retrieval, no reranker, no submodular selection.
    - Purpose: demonstrate gains from reranking and AdaGReS vs naive RAG, and contextualize HCR improvements.
3. **BM25‑only (lexical baseline)**
    - Plain BM25 retrieval (e.g., Elasticsearch / Lucene).
    - Purpose: standard IR baseline, especially on DPI and lexical‑exact queries (dates, IDs).
4. **RAPTOR-style collapsed-tree baseline**
    - Implement RAPTOR’s construction and collapsed-tree retrieval but without HCR’s dual‑path/EMA scoring.[^1_21][^1_13][^1_8]
    - Use your corpus instead of narrative QA, but reuse basic design:
        - Bottom-up clustering/summarization.
        - Collapsed flat retrieval over summaries + leaf chunks.
    - Purpose: direct comparison to closest tree‑of‑chunks prior art; isolates incremental value from HCR’s scoring cascade, EMA, and cross-links.
5. **DOS RAG / “long-context baseline”**
    - Inspired by recent work showing strong simple baselines under varying token budgets.[^1_3]
    - Flat retrieval that simply **sorts chunks by relevance and keeps adding until budget B** (no hierarchy, minimal structure).
    - Purpose: verify that HCR’s complexity buys something over a “just stuff the context up to budget” baseline, especially at moderate budgets (≤1200).
6. **LATTICE‑lite (optional / later phase)**
    - Full LATTICE reproductions may be too heavy for Phase 1, but:
        - A simplified LLM‑guided traversal over a semantic tree (like LATTICE’s search agent with path relevance and calibration) can be used for qualitative comparisons where feasible.[^1_28][^1_29]
    - Given time, reserve this for Phase 2 extension.

### 4.2 Baseline evaluation and complexity

All baselines should:

- Use the **same corpus and chunking**, and
- Be evaluated under **identical token budgets** and using the same generator LLM and judge LLM.

Implementation complexity (relative):

- BM25 / naive dense: trivial.
- Flat dense+cross‑encoder+AdaGReS: moderate; reuses public code \& theory.[^1_26][^1_27][^1_25]
- RAPTOR: moderate–high; but reference implementations and explanations exist.[^1_30][^1_13][^1_8]
- DOS RAG: simple (flat retrieval plus cut‑at‑budget).[^1_3]

For Phase 1 go/no‑go, **BM25 + flat dense+CE + DOS RAG + RAPTOR** are sufficient.

***

## 5. Experimental protocol

### 5.1 Data splits and overfitting control

- **Train / Dev / Test split on queries**:
    - Train: for tuning summarization prompts, tree hyperparameters, beam width, EMA α, AdaGReS β.
    - Dev: for early stopping and sanity checks.
    - Test: held‑out, no direct tuning based on its metrics.
- The **tree is built only from the corpus**, not from query data, to avoid overfitting structure to queries.
    - If you tune depth/branching on Dev, re‑build trees from scratch but still without using test queries.


### 5.2 LLM variability control

- Fix generation **temperature=0 (or 0.1)** and deterministic decoding.
- Fix **judge LLM version and prompts**.
- For each configuration and token budget, run **at least 3 independent runs** (re-executing retrieval and generation) to estimate variance.
    - In contrast, some large RAG studies use 5 runs; 3 is a good Phase 1 compromise.[^1_3]


### 5.3 Statistical tests

- For binary answer correctness:
    - Use **McNemar’s test** for paired comparisons between systems over the same query set.
- For continuous metrics (accuracy, sufficiency, context recall as proportions across runs):
    - Use **paired bootstrap resampling** over queries to get 95% confidence intervals.
- Report:
    - Mean ± std over runs.
    - Bootstrap 95% CI.
    - p‑values for HCR vs best baseline on key metrics.


### 5.4 Fairness and budget control across systems

- **Strict retrieval budget parity**:
    - For each B, count only **retrieved context tokens** (question tokens are counted separately; generation tokens don’t matter for retrieval fairness).
- Systems must:
    - Either truncate their chosen set to B tokens (e.g., drop lowest‑scoring chunks),
    - Or choose a subset via knapsack (AdaGReS for all candidates).

This avoids giving HCR extra capacity.

### 5.5 Corpus-size transition tests

Run all main systems at:

- **C_small (~10k chunks)**:
    - Expect flat to be equal or better; verify that HCR is **not catastrophically worse**.
- **C_mid (~50k)**:
    - Expect HCR to start matching or beating flat.
- **C_large (~100k)**:
    - Expect clear advantage for HCR under token budget.

Track:

- Accuracy@B
- Sufficiency@B
- RAI and ε
- Token utilization

If HCR never meaningfully surpasses flat at C_large, the core architectural bet is in question.

### 5.6 Fail-fast experiment order

To minimize wasted effort:

1. **E0 – Flat baselines sanity check on C_small**:
    - Flat dense+CE+AdaGReS, BM25, DOS RAG, on a tiny query set (~50).
    - Ensure corpus and evaluation pipeline work.
2. **E1 – HCR vs flat on C_small (B=unconstrained)**:
    - Check that HCR is within 5–10 points of flat. If HCR is far worse, fix tree/summary/scoring before doing anything else.
3. **E2 – Per-level ε and routing metrics on C_small and C_mid**:
    - Compute ε_l, RAI, SDS.
    - If ε is nowhere near 0.01–0.02 (e.g., ≥0.08) even after tuning scoring, the hierarchy is too lossy; stop or radically revise scoring.
4. **E3 – Token-efficiency curves on C_mid, HCR vs flat + DOS RAG**:
    - Budgets 200, 400, 800, 1200, unconstrained.
    - If HCR not better at any budget (especially near 400), H1a is not supported.
5. **E4 – Entity-centric and multi-hop subset, cross-link ablations**:
    - Evaluate cross-link on/off vs HCR full.
    - If effect is negligible, H1c’s cross‑link emphasis is suspect.
6. **E5 – Full comparison at C_large, including RAPTOR**:
    - If prior steps are promising, scale to C_large and run full suite.

Stop early if E2–E3 show fundamental flaws.

***

## 6. Ablation design

### 6.1 Minimum viable ablation set (Phase 1)

Run the following ablations on C_mid (and on key subsets):

1. **Beam width and diversity**:
    - k=1 (greedy), k=3, k=5 with and without MMR-style diversity.
    - Tests: beam collapse and diversity’s impact on ε and end‑to‑end performance.
    - Hypotheses: H1b (hybrid vs pure), RB‑002/RB‑005 beam search theory.
2. **Collapsed-tree off**:
    - Only hierarchical beam (no collapsed path).
    - Tests: value of dual-path architecture and race design (H1b).
3. **Cross-links off**:
    - Remove entity cross-links; keep soft assignment.
    - Tests: H1c entity cross-link importance on entity-centric \& entity-spanning queries.
4. **Soft assignment → hard assignment**:
    - Force each leaf to have a single parent.
    - Tests: cross-branch resilience (RB‑004/RB‑005) and impact on entity‑spanning performance.
5. **Contrastive vs generic summaries**:
    - Replace structured contrastive routing summaries with generic “summarize this cluster” summaries.
    - Tests: RB‑004’s core open question; impact on ε and RAI.
6. **Path-relevance EMA off**:
    - Use leaf-level scores only (or naive sum of per-level scores).
    - Tests: H1c’s claim that EMA is a high‑leverage scoring component.
7. **Tree depth variations**:
    - d=1 (flat over coarse clusters), d=2 (design target), d=3.
    - Tests: the (1−ε)^d compounding effect empirically and trade‑off between shallow vs deep trees.

Run full ablations on:

- The full query set at B=400.
- The entity‑centric, multi-hop, and DPI subsets.


### 6.2 Highest-value single experiment

If you had to do **one** ablation first:

- **Contrastive vs generic summaries** at fixed depth and k=3, with ε and end‑to‑end metrics.
    - Because:
        - It directly tests RB‑004’s central unknown.
        - It probes whether the expensive routing-summary construction is earning its keep.

***

## 7. Evaluation framework

### 7.1 Tools to reuse

- **ir_measures / BEIR toolkit**:
    - For classic IR metrics (NDCG@k, Recall@k, MRR, MAP) over corpora and qrels.[^1_11][^1_10]
- **RAGAS**:
    - For context precision/recall, answer correctness, faithfulness and related LLM‑based metrics.[^1_2][^1_5]
- **ARES**:
    - To train light‑weight LM judges for context relevance, answer faithfulness, and answer relevance, leveraging prediction‑powered inference to keep human labels low.[^1_31][^1_1][^1_19]
- **Generic RAG benchmarking libraries**:
    - Recent “Benchmarking Library for RAG” provides a unified evaluation harness for multiple RAG systems and metrics.[^1_32]

These frameworks reduce the amount of custom evaluation infrastructure you need to write and align you with current RAG evaluation practice.

### 7.2 Separating sufficiency from accuracy

For each query:

- **Answer sufficiency score** (0–1):
    - LLM judge sees **question + retrieved context + gold answer**; asked:
        - “Could an ideal model answer this fully and correctly from the context alone?”
    - This isolates retrieval quality regardless of generator errors.
- **Answer accuracy score**:
    - LLM judge (or automatic metric where possible) scores the generated answer vs the gold answer.

You can then:

- Attribute failures to retrieval (low sufficiency, low context recall) vs generation (high sufficiency but low accuracy).


### 7.3 Human evaluation

To keep cost manageable:

- Use **human evaluation on ~100 queries** (stratified across types and systems) to:
    - Calibrate LLM judges (ARES-style PPI).
    - Validate that sufficiency and faithfulness judgments match human perception.

This human subset anchors your automated metrics.

### 7.4 Handling thematic / non-single-answer queries

For thematic or comparative queries without a single canonical answer:

- Define **reference answer rubrics** specifying required points.
- Ask LLM/human judges to rate:
    - Coverage of key points.
    - Correctness (no contradictions to corpus).
- Use graded scores (0/0.5/1) and treat ≥0.5 as “acceptable” for binary decisions.

***

## 8. Practical constraints and Minimum Viable Benchmark (MVB)

### 8.1 MVB definition

To get a credible go/no‑go with one person and modest hardware:

1. **Corpus**:
    - C_mid (~40–50k chunks) built from 2–3 public handbooks + 2–3 OSS docs + synthetic DPI/temporal/aggregation augmentations.
    - Tree built once at d=2 (maybe d=3 if feasible).
2. **Queries**:
    - ~300 test queries (plus ~100 dev).
    - Coverage of main categories, though fewer OOD / ambiguous if necessary.
3. **Systems included**:
    - HCR full.
    - Flat dense+CE+AdaGReS.
    - DOS RAG (flat budgeted baseline).
    - BM25-only.
    - (Optional) RAPTOR collapsed-tree baseline.
4. **Metrics**:
    - Per-level ε and RAI.
    - Accuracy@B and Sufficiency@B at B∈{200,400,800,unconstrained}.
    - Token utilization (avg retrieved tokens).
    - Cross-link ablation on entity‑centric subset.
    - Simple tree quality metrics (SDS, ECS) computed once.
5. **Experiments**:
    - E1–E3 from the fail-fast list (C_small sanity, ε, token efficiency on C_mid).
    - At least one ablation (contrastive vs generic summaries) and one cross-link ablation.
6. **Evaluation framework**:
    - Use RAGAS or ARES to avoid writing your own judges.[^1_1][^1_2]

This MVB can be built and run in Phase 1 and will surface fundamental architectural flaws if they exist.

### 8.2 Deferrable to later phases

Can be deferred without compromising go/no‑go:

- Full C_large scaling (beyond spot checks).
- LATTICE or HiRAG replications.
- Fine-grained failure mode mapping beyond the major aggregations.
- Extensive human evaluation beyond calibration.
- Full suite of tree-quality experiments across many configs.


### 8.3 Rough cost estimates

Highly approximate, assuming:

- 300–400 test queries.
- 4 systems (HCR, flat+CE, DOS, BM25).
- 4 budgets (200,400,800,unconstrained) for the main two systems; fewer for weak baselines.
- ~1–2k tokens per query per run (context + answer + overhead).
- 3 runs per configuration.

You are in the **tens of millions of tokens** for generation plus roughly double that for judge evaluations. This is orders of magnitude smaller than some recent RAG studies that used ~2B tokens for comprehensive baselines.[^1_3]

### 8.4 Regression suite

Once built, this benchmark naturally becomes a **regression suite**:

- Keep the corpus and queries fixed.
- Re-run the main metrics (ε, Accuracy@400, token curves, cross-link ablation) after each architectural change to track regressions.

***

## 9. Success criteria and kill switches

Summarizing numeric go/no‑go thresholds:

### 9.1 H1a – Token efficiency

On C_mid:

- **Target** B=400:
    - HCR Accuracy@400 ≥ Flat Accuracy@400 + 5 points (p<0.05).
    - HCR Accuracy@400 ≥ Flat Accuracy@800 − 2 points.
- **Token savings**:
    - At comparable accuracy to Flat@unconstrained (within 3 points), HCR’s mean retrieval token budget ≤50% of flat’s budget.

**Fail** if:

- HCR does not match or exceed flat at any budget 200–1200 on Accuracy@B or Sufficiency@B, or
- HCR’s token‑efficiency curve is dominated by flat across the board.


### 9.2 H1b – Hybrid superiority

On C_mid and C_large:

- HCR Dual must:
    - Beat **Beam‑only** and **Collapsed‑only** by ≥5 absolute points on at least one major subset (multi-hop or entity-spanning) at B=400 (p<0.05).
    - Beat **best flat baseline** (flat+CE or DOS RAG) by ≥5 points on at least one of:
        - Multi-hop queries.
        - Cross-branch entity-spanning queries.
- Plus: the fraction of queries where the dual-path “race” selects the **correct** path when one of Beam/Collapsed is wrong should be ≥10–15%.

**Fail** if:

- Dual is never significantly better than Beam‑only, Collapsed‑only, or strong flat baselines under matched budgets.


### 9.3 H1c – Scoring quality and compounding error

- **Per-level routing error**:
    - After tuning, ε_l ≤0.03 at each depth for single-branch and entity-centric queries.
    - Overall RAI ≥0.9 on single-branch; ≥0.8 on entity-spanning.
- **Compounding correlation**:
    - Per-query estimated route success $\hat{P}_\text{route}(q) = \prod_{l}(1-\varepsilon_l(q))$ should correlate with:
        - Context Recall@B (correlation ≥0.5).
        - Answer Accuracy@B (correlation ≥0.4).
- **Entity cross-links**:
    - Turning off cross-links reduces Accuracy@400 on entity-centric + entity-spanning queries by ≥5 points (p<0.05) while affecting non‑entity queries by ≤3 points.

**Fail** if:

- ε remains ≥0.08 even after scoring optimization, and/or
- ε and RAI do not correlate with end‑to‑end success (correlation <0.2), and cross-links have negligible impact on entity-centric queries.


### 9.4 Overall acceptable failure rate and corpus-size advantage

- Overall **failure rate** (on budget‑feasible queries) ≤25%, with 10–20% as design target (consistent with RB‑005).
- **Transition period**:
    - At C_small, HCR may be slightly worse (≤5 points) than flat at B=400; acceptable if:
        - At C_mid and C_large, HCR’s advantage appears and increases.
- **Kill criterion**:
    - If at C_large (~100k chunks), across all budgets:
        - HCR never significantly outperforms flat baselines on any major query class, and/or
        - Token‑efficiency advantages are negligible (<3 points at all budgets),
        - And ε cannot be brought into the low‑error regime,
    - Then the architecture as currently specified should be considered **no‑go** for implementation.

***

This benchmark design is deliberately biased toward **falsifying** HCR if it does not deliver tangible, statistically meaningful gains under realistic token budgets and corpus sizes. If HCR passes the MVB with these thresholds, Phase 1 implementation has a strong empirical foundation rather than just theoretical and anecdotal motivation.
<span style="display:none">[^1_33][^1_34][^1_35][^1_36][^1_37][^1_38][^1_39][^1_40][^1_41][^1_42][^1_43][^1_44][^1_45][^1_46][^1_47][^1_48][^1_49][^1_50][^1_51][^1_52][^1_53][^1_54][^1_55][^1_56][^1_57][^1_58][^1_59][^1_60][^1_61][^1_62][^1_63][^1_64][^1_65][^1_66][^1_67][^1_68][^1_69][^1_70][^1_71][^1_72][^1_73][^1_74]</span>

<div align="center">⁂</div>

[^1_1]: https://arxiv.org/abs/2311.09476

[^1_2]: https://docs.ragas.io/en/stable/

[^1_3]: https://arxiv.org/pdf/2506.03989.pdf

[^1_4]: https://www.confident-ai.com/blog/rag-evaluation-metrics-answer-relevancy-faithfulness-and-more

[^1_5]: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/

[^1_6]: https://aclanthology.org/2024.acl-long.172/

[^1_7]: https://arxiv.org/abs/2401.15391

[^1_8]: https://arxiv.org/abs/2401.18059

[^1_9]: https://arxiv.org/pdf/2210.07316.pdf

[^1_10]: https://arxiv.org/abs/2104.08663

[^1_11]: https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/file/65b9eea6e1cc6bb9f0cd2a47751a186f-Paper-round2.pdf

[^1_12]: https://openreview.net/pdf/43ab88c33fb4e13c3e723aaf46617f8e731d97c9.pdf

[^1_13]: https://www.themoonlight.io/en/review/raptor-recursive-abstractive-processing-for-tree-organized-retrieval

[^1_14]: https://www.themoonlight.io/en/review/hierarchical-retrieval-augmented-generation-model-with-rethink-for-multi-hop-question-answering

[^1_15]: https://arxiv.org/abs/2408.11875

[^1_16]: https://www.emergentmind.com/topics/longbench-v2-and-zeroscrolls-benchmarks

[^1_17]: https://arxiv.org/pdf/2505.19293.pdf

[^1_18]: https://www.braintrust.dev/articles/rag-evaluation-metrics

[^1_19]: https://ares-ai.vercel.app

[^1_20]: https://www.databricks.com/blog/long-context-rag-performance-llms

[^1_21]: https://arxiv.org/html/2401.18059v1

[^1_22]: https://en.wikipedia.org/wiki/Hierarchical_clustering

[^1_23]: https://www.arxiv.org/pdf/2506.13607.pdf

[^1_24]: https://arxiv.org/pdf/2506.13607.pdf

[^1_25]: https://www.themoonlight.io/en/review/adagresadaptive-greedy-context-selection-via-redundancy-aware-scoring-for-token-budgeted-rag

[^1_26]: https://arxiv.org/abs/2512.25052

[^1_27]: https://arxiv.org/html/2512.25052v1

[^1_28]: https://huggingface.co/papers/2510.13217

[^1_29]: https://nilesh2797.github.io/publications/lattice/

[^1_30]: https://aiexpjourney.substack.com/p/raptor-a-novel-tree-based-retrieval

[^1_31]: https://aclanthology.org/2024.naacl-long.20.pdf

[^1_32]: https://aclanthology.org/2024.findings-emnlp.449.pdf

[^1_33]: https://www.themoonlight.io/en/review/tree-based-text-retrieval-via-hierarchical-clustering-in-ragframeworks-application-on-taiwanese-regulations

[^1_34]: https://github.com/THUDM/LongBench

[^1_35]: https://www.emergentmind.com/topics/hierarchical-retrieval-hr

[^1_36]: https://www.themoonlight.io/tw/review/adagresadaptive-greedy-context-selection-via-redundancy-aware-scoring-for-token-budgeted-rag

[^1_37]: https://devblogs.microsoft.com/ise/hierarchical-waterfall-evaluation-query-classification-rag-llm/

[^1_38]: https://www.cerebras.ai/blog/extending-llm-context-with-99-less-training-tokens

[^1_39]: https://chatpaper.com/paper/197117

[^1_40]: https://www.emergentmind.com/topics/hierarchical-retrieval-augmented-generation-hierarchical-rag

[^1_41]: https://huggingface.co/papers/2401.15391

[^1_42]: https://krisztianbalog.com/files/trecent2008overview.pdf

[^1_43]: https://www.youtube.com/watch?v=bg0WX7Ewe6I

[^1_44]: https://ar5iv.labs.arxiv.org/html/2401.15391

[^1_45]: https://www.academia.edu/55380770/The_open_university_at_TREC_2006_enterprise_track_expert_search_task

[^1_46]: https://trec.nist.gov/pubs/trec14/papers/old.overviews/ENTERPRISE.OVERVIEW.pdf

[^1_47]: https://openreview.net/forum?id=t4eB3zYWBK

[^1_48]: https://oro.open.ac.uk/36078/1/The Open University at TREC2006 Enterprise Track Expert Search Task.pdf

[^1_49]: https://www.nist.gov/publications/overview-trec-2006-enterprise-track

[^1_50]: https://apxml.com/courses/optimizing-rag-for-production/chapter-6-advanced-rag-evaluation-monitoring/rag-evaluation-frameworks-ragas-ares

[^1_51]: https://arxiv.org/abs/2601.11255

[^1_52]: https://www.themoonlight.io/zh/review/tree-based-text-retrieval-via-hierarchical-clustering-in-ragframeworks-application-on-taiwanese-regulations

[^1_53]: https://www.alphaxiv.org/overview/2408.11875

[^1_54]: https://www.emergentmind.com/topics/beir-benchmark

[^1_55]: https://resources.10xvelocity.ai/business-workflows/knowledge-base-rag/

[^1_56]: https://rueckle.net/publication/BEIR/

[^1_57]: https://r.jordan.im/download/language-models/muennighoff2022.pdf

[^1_58]: https://xenoss.io/blog/enterprise-knowledge-base-llm-rag-architecture

[^1_59]: https://modal.com/blog/mteb-leaderboard-article

[^1_60]: https://umbrex.com/resources/ai-primer/retrieval-and-the-enterprise-knowledge-loop/

[^1_61]: https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/hash/65b9eea6e1cc6bb9f0cd2a47751a186f-Abstract-round2.html

[^1_62]: https://aclanthology.org/2023.eacl-main.148.pdf

[^1_63]: https://www.coveo.com/blog/information-retrieval-in-knowledge-management-systems/

[^1_64]: https://aclanthology.org/2023.eacl-main.148/

[^1_65]: https://enterprise-knowledge.com/data-governance-for-retrieval-augmented-generation-rag/

[^1_66]: https://cobbai.com/blog/evaluate-rag-answers

[^1_67]: https://arxiv.org/html/2511.05385v1

[^1_68]: https://langcopilot.com/posts/2025-09-17-rag-evaluation-101-from-recall-k-to-answer-faithfulness

[^1_69]: https://arxiv.org/html/2509.18667v2

[^1_70]: https://www.youtube.com/watch?v=wOoYP55eYF0

[^1_71]: https://superlinear.eu/insights/articles/benchmarking-retrieval-augmented-generation-who-wins-in-document-retrieval

[^1_72]: https://arxiv.org/html/2501.01880v1

[^1_73]: https://docs.evidentlyai.com/examples/LLM_rag_evals

[^1_74]: https://milvus.io/ai-quick-reference/how-do-metrics-like-contextual-precision-and-contextual-recall-such-as-those-in-certain-rag-evaluation-frameworks-work-and-what-do-they-indicate-about-a-systems-performance


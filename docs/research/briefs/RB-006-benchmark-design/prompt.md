# RB-006: Benchmark Design for Hierarchical Coarse-to-Fine Retrieval

**Date:** 2026-02-13
**Status:** Open
**Decision Required:** Yes — this benchmark defines the success criteria for Phase 1 and the go/no-go gate
**Related:** H1a (token efficiency), H1b (hybrid superiority), H1c (scoring lever), RB-001 (prior art), RB-002 (theoretical basis), RB-003 (scoring mechanics), RB-004 (tree construction), RB-005 (failure modes)

## Context

Five prior research briefs have taken HCR from hypothesis to fully specified (but unbuilt) architecture. The findings are:

- **RB-001 (Prior art):** 12+ hierarchical retrieval systems exist. RAPTOR and LATTICE are closest. No system targets hard token budgets. RAPTOR's collapsed-tree outperforms strict traversal.
- **RB-002 (Theory):** Error compounds at (1-ε)^d. Strict elimination is fragile. Hybrid coarse-to-fine is theoretically optimal. Beam search transforms recall from (1-ε)^d to ~(1-(1-p)^k)^d.
- **RB-003 (Scoring):** Cascade architecture (BM25+dense → cross-encoder) achieves ε ≈ 0.01–0.02 per level. Path-relevance EMA is the highest-leverage component. Summary quality is the #1 upstream factor.
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
> - **Target domain:** Organisational knowledge base — policies, procedures, projects, people, tools, communications, technical docs. Consumed by an agentic system (Su) that needs precise retrieval from a growing knowledge base.
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

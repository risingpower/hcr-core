# RB-006: Benchmark Design — Claude Response

**Date:** 2026-02-13
**Source:** Claude
**Status:** Awaiting response

---

*Paste Claude response below this line.*
# The HCR benchmark: a complete validation protocol

**The hierarchical coarse-to-fine retrieval system can be rigorously validated or killed with a ~300-query benchmark costing under $50 and buildable in 10–12 person-days.** The benchmark design below provides go/no-go signals for all three hypotheses (token efficiency, hybrid superiority, scoring quality as lever) by combining a purpose-built synthetic enterprise corpus with adapted multi-hop datasets, measuring seven core metrics against four baselines, and following a fail-fast experimental sequence that surfaces fatal flaws within the first three days. The design prioritizes practical execution by a single person over academic completeness — every component earns its place by directly testing a hypothesis.

---

## 1. A hybrid corpus built in layers

No existing dataset captures the full heterogeneity of an organizational knowledge base. TREC Enterprise (W3C corpus, 2005–2008) is the closest but is dated and partially unavailable. BEIR provides retrieval diversity but uses short passages without enterprise structure. The solution is a **three-layer hybrid corpus** that balances realism, controllability, and practicality.

**Layer 1 — Synthetic enterprise core (primary, ~2,000 documents, ~800K tokens).** Generate a fictional mid-size organization ("Meridian Technologies") with **6–8 topical domains**: HR policies, engineering processes, project documentation, product specs, people profiles, IT systems, communications/decisions, and compliance. Use an LLM (GPT-4o or Claude) to generate documents with controlled properties: entity density, cross-references, temporal layers (v1/v2/v3 of policies), ambiguous terminology, and deliberate overlap between domains. This layer is purpose-built to stress-test all 26 failure modes. Structure it so that **~40% of documents span two or more topical domains** (matching the cross-branch query distribution), and **~50% contain specific identifiers** (ticket numbers, policy codes, people names) to stress-test DPI queries. Include a temporal dimension: generate three quarterly "snapshots" of 50 documents each that change over time (policy updates, project status changes) for temporal query testing.

**Layer 2 — Adapted real-world subset (~1,500 chunks).** Draw from two sources that approximate enterprise content:
- **QASPER** (~200 papers, structured technical documents with sections and cross-references) — closest to enterprise technical documentation
- **MultiHop-RAG** (~500 articles, cross-document multi-hop queries already provided) — closest to enterprise news/communications with pre-built multi-hop ground truth

**Layer 3 — Growth dimension (~500 documents per increment).** Design three corpus sizes: **Small (500 docs)**, **Medium (2,000 docs)**, **Full (3,500+ docs)**. This tests the critical prediction that HCR's advantage manifests at scale. The growth increments should add documents that create new cross-branch connections, forcing the tree to restructure. Literature consistently shows hierarchical advantage emerging at **1K–10K documents** for abstract/thematic queries and scaling logarithmically thereafter.

**Failure-mode instrumentation in the corpus.** Embed specific traps:

- **Entity fragmentation**: Spread information about 20 key entities across 5+ documents each (tests cross-link quality)
- **Near-duplicate clusters**: Include 3–4 groups of semantically similar but factually different documents (tests sibling distinctiveness)
- **Vocabulary mismatch**: Include documents using different terminology for the same concepts (tests routing robustness)
- **Depth-varied answers**: Some answers require only leaf-level detail; others require synthesizing information from multiple hierarchy levels
- **Budget-impossible queries**: Include ~25% of queries requiring information from >10 documents (tests budget-impossible detection)

**Total corpus: ~3,500 documents, ~1.4M tokens, fitting comfortably in memory on a laptop.**

---

## 2. A 300-query suite with built-in difficulty stratification

The query suite must cover the identified distribution while providing enough queries per category for paired statistical testing. Based on Sakai's topic set size research and standard TREC practice, **50 queries is the absolute minimum for stable system comparison; 100+ is recommended**. The design below uses **300 queries** across 10 categories, with difficulty tiers and budget-feasibility labels.

**Query distribution (300 total):**

| Category | Count | % | Budget-feasible | Maps to hypothesis |
|----------|-------|---|-----------------|-------------------|
| Single-branch thematic | 50 | 17% | ~85% yes | H1a, H1b |
| Entity-spanning (2+ branches) | 55 | 18% | ~60% yes | H1b, H1c (cross-links) |
| Detail/identifier (DPI) | 50 | 17% | ~90% yes | H1a, H1c (routing) |
| Multi-hop (2-hop) | 35 | 12% | ~50% yes | H1b, H1c |
| Multi-hop (3+ hop) | 15 | 5% | ~20% yes | H1c (compounding) |
| Comparative | 25 | 8% | ~40% yes | H1b |
| Aggregation/exhaustive listing | 20 | 7% | ~10% yes | H1a (budget-impossible) |
| Temporal | 20 | 7% | ~70% yes | H1c |
| Ambiguous/underspecified | 15 | 5% | ~60% yes | H1b (beam diversity) |
| Out-of-distribution | 15 | 5% | N/A | All (robustness) |

**Each query carries metadata:** `{category, difficulty_tier, budget_feasible, expected_branches, expected_entities, ground_truth_chunks, ground_truth_answer}`. The `budget_feasible` label is determined during annotation: if the minimum context needed to answer exceeds 400 tokens, mark as budget-infeasible.

**Difficulty stratification (3 tiers per category):** Easy queries have answers concentrated in one chunk within the correct branch. Medium queries require 2–3 chunks, possibly across sibling nodes. Hard queries require cross-branch reasoning, entity linking, or synthesis of information at different hierarchy levels. Distribute roughly **40% easy, 35% medium, 25% hard** within each category.

**Query generation method — hybrid approach:**
1. **LLM-generated from corpus (60%):** For each document cluster in the synthetic corpus, prompt GPT-4o to generate queries at each difficulty tier. Apply **consistency filtering**: only accept queries where the target documents appear in top-20 of a BM25 baseline retrieval (following the InPars methodology). This filters out queries that are trivially easy or disconnected from the corpus.
2. **Template-derived (20%):** Create templates for each category (e.g., "What is [entity]'s role in [project]?" for entity-spanning, "How has [policy] changed since [date]?" for temporal) and instantiate with corpus-specific entities. This ensures coverage of specific failure modes.
3. **Manually crafted adversarial (20%):** Hand-write 60 queries specifically designed to break the system: queries with vocabulary mismatch, queries where the obvious branch is wrong, queries requiring information from the deepest and shallowest tree levels simultaneously. These are the most valuable queries in the set.

**Validate a 10% sample (30 queries) with human judgment** to calibrate LLM-generated query quality. Compute Kendall's τ between LLM-judged and human-judged relevance rankings; proceed if τ ≥ 0.7.

---

## 3. Seven core metrics and how to measure each

This is the benchmark's backbone. Each metric maps directly to a hypothesis and has a concrete measurement protocol.

### Metric 1: Per-level routing accuracy (ε) — validates H1c

**Definition:** At each tree level *l*, the fraction of queries where the correct branch is *not* among the top-*k* selected branches (where *k* is the beam width). Formally: ε_l = 1 − (queries where correct branch ∈ top-k at level l) / (total queries with a correct branch at level l).

**Ground truth:** For each query, annotate which leaf nodes contain relevant information, then trace upward to determine the correct branch at each level. A branch is "correct" at level *l* if any of its descendant leaves is relevant. Multi-relevance (multiple correct branches) is handled by treating a level as correct if *any* correct branch is selected. Report both "any-correct-in-beam" (optimistic) and "all-correct-in-beam" (pessimistic) variants.

**Measurement:** Instrument the beam search to log selected branches at each level. Compare against ground truth. Compute ε_l for each level, then compute observed cumulative accuracy ∏(1−ε_l) and compare against the theoretical (1−ε)^d model.

**This metric has never been measured in any retrieval system.** LATTICE's ablation of path relevance smoothing is the closest proxy, showing that path coherence is the single largest contributor to performance. The HCR benchmark would be the first to report explicit per-level routing accuracy, filling a genuine research gap.

### Metric 2: Answer sufficiency under token constraint — validates H1a

**Definition:** Given retrieved context of exactly *B* tokens, can the query be correctly answered? This is distinct from answer accuracy (which conflates retrieval and generation quality).

**Measurement:** Use the **Sufficient Context** approach (ICLR 2025, Google Research): an LLM autorater classifies whether the retrieved context is sufficient to answer the query (binary yes/no). Then, *only for sufficient contexts*, evaluate answer correctness using RAGAS Factual Correctness. Report:
- **Sufficiency rate** = fraction of queries where context is sufficient at budget B
- **Conditional accuracy** = answer correctness given sufficient context
- **Overall accuracy** = sufficiency rate × conditional accuracy

This decomposition is critical because it separates retrieval failures (HCR didn't find the right content) from generation failures (LLM couldn't use the content) from budget failures (answer genuinely requires more tokens).

### Metric 3: Token efficiency curve — validates H1a

**Definition:** Plot answer sufficiency rate as a function of token budget at **B = {200, 400, 600, 800, 1200, unconstrained}** for both HCR and all baselines.

**What success looks like:** The HCR curve should be **left-shifted** relative to flat retrieval — achieving the same sufficiency rate at fewer tokens. Specifically, HCR at 400 tokens should match or exceed flat retrieval at 600–800 tokens. The curve shape should be **sigmoidal**: flat below some minimum budget (where even perfect retrieval can't fit the answer), steep in the middle (where retrieval quality determines outcome), and asymptotic at high budgets (diminishing returns). A good HCR system shifts the inflection point leftward.

**Measurement:** Run each system at each budget point. Use AdaGReS-style submodular selection for HCR; use greedy top-k truncation for baselines (giving baselines the fairest comparison). Plot curves with bootstrap 95% confidence intervals.

### Metric 4: Beam vs. collapsed-tree comparison — validates H1b

**Definition:** For each query, record which retrieval path (beam search or collapsed-tree) produces the higher-confidence result, and whether the winning path changes by query category.

**Measurement:** Run both paths independently. For each query, compute:
- **Path agreement rate**: fraction of queries where both paths return the same top document
- **Path-conditional accuracy**: answer correctness when using beam-only vs. collapsed-only vs. dual-path (winner-take-all)
- **Category breakdown**: which path wins for single-branch vs. entity-spanning vs. multi-hop queries

**Expected finding (from RAPTOR):** Collapsed tree should dominate for thematic/abstract queries; beam search should win for DPI/identifier queries where routing is straightforward. The dual-path architecture's value is demonstrated if it achieves accuracy ≥ max(beam-only, collapsed-only) across all categories.

### Metric 5: Entity cross-link quality — validates H1c

**Definition:** Coverage, precision, and recall of entity cross-links, and their correlation with end-to-end retrieval quality on entity-spanning queries.

**Measurement:**
- **Entity coverage**: fraction of ground-truth entity relationships captured by cross-links
- **RAGAS Context Entity Recall** (built-in, no LLM needed): |entities_in_context ∩ entities_in_reference| / |entities_in_reference|
- **Entity-spanning query accuracy delta**: answer accuracy on entity-spanning queries with cross-links enabled vs. disabled

This metric is critical because entity-spanning queries represent **40–55% of the workload**, and cross-links are the primary defense. If disabling cross-links drops entity-spanning accuracy by >15%, cross-links are confirmed as co-primary with routing quality.

### Metric 6: Four novel tree quality metrics — fills the research gap

No retrieval-specific tree quality metric exists in the literature. The HCR benchmark introduces four, measured offline on the tree structure:

1. **Sibling distinctiveness (SD):** For each internal node, compute mean pairwise cosine distance between sibling routing summary embeddings. Report mean, min, and standard deviation across all internal nodes. Low SD at any node indicates a routing bottleneck where the scorer must discriminate between near-identical descriptions.

2. **Routing summary fidelity (RSF):** For each internal node's routing summary, compute the fraction of its descendant leaf chunks that are semantically consistent with the summary (cosine similarity > threshold). Low RSF means the summary misrepresents its subtree.

3. **Dendrogram purity (DP):** Adapted from Kobren et al. (2017). Given ground-truth topic labels for documents, DP measures whether same-topic documents cluster together in the tree. Apply at each level by cutting the tree at that depth.

4. **Leaf reachability under error (LRE):** Simulate routing errors at each level (flip the top-1 branch selection with probability ε) and measure what fraction of relevant leaves remain reachable via the beam. This directly tests the (1−ε)^d model with the actual tree structure rather than in theory.

### Metric 7: Standard IR metrics — validates H1b, enables baseline comparison

Use **ir_measures** library for standardized computation:
- **nDCG@10** (primary ranking quality — the BEIR standard)
- **Recall@100** (comprehensiveness)
- **MRR** (first relevant result position)
- **P@5** (top-5 precision)

These enable direct comparison against published baselines and ensure the benchmark speaks the standard language of retrieval evaluation.

---

## 4. Four baselines, ordered by what each teaches us

### Baseline 1: BM25-only (the floor)

**Implementation:** `rank_bm25` library, 1 person-day. No embeddings, no reranking. **What it teaches:** The absolute minimum performance any system should exceed. If HCR loses to BM25 on DPI queries (which are keyword-heavy), the routing summaries are actively harmful.

### Baseline 2: Hybrid BM25 + dense retrieval with RRF (the pragmatic default)

**Implementation:** BM25 + `text-embedding-3-small` via FAISS + Reciprocal Rank Fusion, 2–3 person-days. **What it teaches:** Whether hierarchical structure adds value beyond simple score fusion. This is the system most practitioners would actually deploy. RRF is parameter-free and remarkably robust.

### Baseline 3: Flat retrieval + cross-encoder reranking (the value barrier)

**Implementation:** Bi-encoder retrieval (top-100) → `cross-encoder/ms-marco-MiniLM-L-12-v2` reranking, 2–3 person-days. **What it teaches:** This is the **kill baseline**. Cross-encoders capture deep token-level query-document interactions. If HCR cannot beat this, the hierarchy adds no value that a good reranker doesn't already provide. On SEC filings, cross-encoder reranking achieves **MRR@5 of 0.750** vs. 0.160 without reranking — the bar is high.

### Baseline 4: RAPTOR collapsed tree (the hierarchical comparator)

**Implementation:** Official `raptor` library on GitHub, 3–4 person-days. **What it teaches:** Whether HCR's specific innovations (structured routing summaries, dual-path retrieval, scoring cascade, cross-links) improve on the simpler RAPTOR approach of embedding-based collapsed-tree retrieval. RAPTOR achieved **20% absolute accuracy improvement** over flat retrieval on QuALITY — HCR should match or exceed this.

**Deferred to Phase 2:** LATTICE (expensive per-query LLM calls, useful but not essential for go/no-go), ColBERTv2 (late interaction, interesting but tangential), GraphRAG (expensive indexing, relevant only for aggregation queries). Commercial APIs (Cohere Rerank, Voyage AI) can serve as quick reference points if budget allows — Voyage rerank-2.5 costs only **$0.05/1M tokens** with a 200M token free tier.

**Fairness protocol:** All baselines receive the same token budget for context, the same embedding model for dense retrieval, and the same LLM for answer generation and evaluation. The cross-encoder reranking baseline should rerank the same number of candidates that HCR's scoring cascade considers at the first level.

---

## 5. Experimental protocol designed for validity and fail-fast execution

### Statistical framework

**Primary test:** Paired permutation test (theoretically exact p-values), with the paired t-test as confirmatory. Standard threshold α = 0.05. For multiple system comparisons, apply **Holm-Bonferroni correction** to control family-wise error rate.

**Variance estimation:** Run each system configuration **3 times** with different random seeds (affecting tree construction clustering initialization and any stochastic elements). Report mean ± standard deviation. For LLM-as-judge metrics, use temperature=0 and run twice to check consistency; discard and re-run any metric with >5% variation between runs.

**Effect size:** Report both raw metric differences and **Cohen's d**. In retrieval evaluation, nDCG@10 differences of **0.03–0.05** are practically meaningful. Require Cohen's d ≥ 0.3 (small-to-medium effect) for any claimed improvement.

**Bootstrap confidence intervals:** Use B = 10,000 resamples for all reported metrics. A result is significant only if the 95% CI excludes zero.

### Controlling for LLM variability

- Fix the LLM model version (e.g., `gpt-4o-mini-2024-07-18`) and record it
- Temperature = 0 for all evaluation calls; temperature = 0 for routing summary generation
- Log all prompts in version control
- For answer generation: use the same prompt template across all systems, varying only the retrieved context
- Run a **prompt sensitivity check** on 20 queries with 3 prompt variations; if accuracy varies >10%, the result is fragile and should be flagged

### Fail-fast experiment sequence

This ordering surfaces fatal flaws earliest, before investing in full evaluation:

**Day 1–2: Tree construction sanity check.** Build the tree on the synthetic corpus. Measure sibling distinctiveness and dendrogram purity. **Kill criterion:** If mean sibling distinctiveness (cosine distance between sibling summaries) < 0.15, the tree cannot support reliable routing — fix tree construction before proceeding.

**Day 3: Per-level routing accuracy on 50 easy queries.** Run beam search on the 50 easiest single-branch queries. Measure ε at each level. **Kill criterion:** If ε > 0.10 at any level (>10% of easy queries routed wrong), the scoring cascade is fundamentally broken.

**Day 4: HCR vs. flat+cross-encoder on 100 queries.** Run the full pipeline against Baseline 3. Compare nDCG@10. **Kill criterion:** If HCR nDCG@10 < Baseline 3 nDCG@10 − 0.02 (HCR is *worse*), stop and diagnose before proceeding.

**Day 5–6: Token efficiency curve on 100 queries.** Run HCR and all baselines at B = {200, 400, 800, unconstrained}. **Kill criterion:** If HCR at 400 tokens doesn't beat flat retrieval at 400 tokens on sufficiency rate, the token efficiency hypothesis (H1a) is dead.

**Day 7–8: Full 300-query evaluation.** Run all systems, all metrics, all query categories. Generate category-level breakdowns.

**Day 9–10: Ablation studies.** Run the priority ablation set (see Section 6).

### Corpus size testing

Run the full evaluation at three corpus sizes (Small/Medium/Full). **Expected pattern:** HCR should show minimal or no advantage at Small (500 docs), emerging advantage at Medium (2,000 docs), and clear advantage at Full (3,500+ docs). If HCR doesn't beat Baseline 3 at Full corpus size, the scaling hypothesis fails.

### Train/dev/test split

- **Tree construction uses only documents** (never queries) — no information leakage by construction
- Split queries **60/20/20** into tune/dev/test sets, stratified by category and difficulty
- Use the tune set (180 queries) for hyperparameter tuning (beam width, α for EMA, cross-encoder threshold)
- Use the dev set (60 queries) for model selection and early stopping
- **Touch the test set (60 queries) exactly once** for final reporting
- Ensure no topic overlap: if a query in the test set is about "Project Atlas," no tune query should reference the same project

---

## 6. Ablation design: eight experiments in priority order

Each ablation removes or replaces one component, holding everything else constant. The priority order maximizes information per experiment about the three hypotheses.

**Priority 1 (Phase 1 — must run):**

| # | Ablation | What's changed | Tests hypothesis | Expected signal |
|---|----------|---------------|-----------------|----------------|
| A1 | Remove hierarchy (flat index) | Replace tree with flat chunk index, keep cross-encoder | H1b | Δ reveals hierarchy's raw contribution |
| A2 | Remove cross-encoder reranking | Use only BM25+dense pre-filter scores, no rerank | H1c | Δ reveals per-level scoring quality impact |
| A3 | Beam-only (disable collapsed tree) | Remove collapsed-tree co-primary path | H1b | Shows dual-path value vs. single-path |
| A4 | Disable entity cross-links | Remove all cross-branch entity links | H1c | Shows cross-link value on entity-spanning queries |
| A5 | Fixed 400-token cap (no adaptation) | Replace AdaGReS selection with greedy top-k truncation | H1a | Isolates submodular selection's contribution |

**Priority 2 (Phase 2 — run if Phase 1 is promising):**

| # | Ablation | Tests |
|---|----------|-------|
| A6 | Remove routing summaries (use centroid embeddings only) | Whether structured summaries beat raw embeddings for routing |
| A7 | Reduce tree depth from 3 to 2 | Depth vs. breadth tradeoff, error compounding sensitivity |
| A8 | Remove diversity enforcement from beam | Whether MMR-style diversity prevents missed branches |

**The single highest-value first experiment is A1 (remove hierarchy).** It directly tests H1b by comparing the full system against a flat alternative using the same scoring components. If the delta is near zero, hierarchy adds no value and the project should pivot.

**Interaction effects:** After running A1–A5 independently, run A2+A4 together (remove both cross-encoder and cross-links) to test whether their contributions are additive or synergistic. If Δ(A2) + Δ(A4) < Δ(A2+A4), there is a synergistic interaction worth investigating.

---

## 7. Evaluation framework: separating retrieval from generation judgment

### Primary framework: RAGAS + custom sufficiency metric

Use **RAGAS** as the evaluation backbone for its proven metrics and low setup cost, augmented with a custom sufficiency check. RAGAS achieves **95% agreement** with human annotators on faithfulness and **78%** on answer relevancy — adequate for a go/no-go decision.

**Retrieval evaluation (does the context contain what's needed?):**
- `ContextRecall` (RAGAS): decomposes ground truth into statements, checks attribution to context. Requires ground truth answers.
- `ContextEntityRecall` (RAGAS): entity overlap between context and reference. No LLM needed — uses NER. Directly relevant for entity-centric evaluation.
- Custom `SufficientContext` autorater: binary classification ("Is this context sufficient to answer the query?") following the ICLR 2025 methodology. Single LLM call per query.

**Generation evaluation (did the LLM use the context correctly?):**
- `Faithfulness` (RAGAS): decomposes answer into claims, verifies each against context. Two LLM calls per query.
- `FactualCorrectness` (RAGAS): compares answer claims against ground truth claims. Classifies as TP/FP/FN.

**Conditional evaluation strategy:** First classify context sufficiency. Then evaluate generation quality *only on queries with sufficient context*. Report retrieval sufficiency rate and conditional generation accuracy separately. This prevents generation failures from masking retrieval quality differences between systems.

### LLM-as-judge configuration

- **Primary judge:** GPT-4o-mini (cost-effective at **$0.15/$0.60 per 1M tokens**, adequate reliability)
- **Validation judge:** Run 50 queries through Claude 3.5 Haiku as a second judge; check inter-judge agreement (Kendall's τ ≥ 0.7)
- **Temperature:** 0 for all evaluation calls
- **Rubric:** Provide explicit scoring criteria in the evaluation prompt. For sufficiency: "The context is sufficient if it contains all facts needed to construct a correct and complete answer. Partial sufficiency counts as insufficient." For faithfulness: "Every claim in the answer must be directly supported by or inferable from the context."
- **Bias mitigation:** For pairwise comparisons, swap presentation order and average. Do not include system identifiers in evaluation prompts.

### Human evaluation — when and how

**Minimum human evaluation (Phase 1):** Annotate 50 queries (the test set's most ambiguous results) with binary sufficiency and 1–5 answer quality scores. Use this to compute RAGAS-to-human correlation and calibrate LLM-as-judge thresholds. Estimated time: **4–6 hours** for one person.

**Threshold for triggering more human evaluation:** If LLM judges disagree on >20% of queries, or if the go/no-go decision hangs on a metric difference smaller than the bootstrap CI width, expand human evaluation to the full test set (60 queries).

### Handling queries with no single correct answer

For thematic and opinion-dependent queries, use **answer relevancy** (RAGAS) rather than factual correctness. Define "correct" as "addresses the query's information need with factually grounded claims" rather than matching a specific ground truth string. For these queries, evaluate only faithfulness (is the answer grounded in context?) and relevancy (does it address the query?), not factual correctness.

---

## 8. Practical constraints and the minimum viable benchmark

### The MVB that provides a credible go/no-go signal

Strip everything to the essential core:

**Must-have (Phase 1, 10–12 person-days, ~$15–30):**
- Synthetic enterprise corpus: 2,000 documents (3–4 days to generate and validate)
- 200 queries (120 LLM-generated + 40 template-derived + 40 manual adversarial) with ground truth
- 3 baselines: BM25-only, hybrid BM25+dense+RRF, flat+cross-encoder reranking
- 5 metrics: nDCG@10, Recall@100, answer sufficiency rate at 400 tokens, faithfulness, per-level routing accuracy
- 3 ablations: A1 (remove hierarchy), A2 (remove cross-encoder), A4 (disable cross-links)
- Token efficiency curve at 3 budget points: 400, 800, unconstrained
- Fail-fast protocol (Days 1–4 are go/no-go checkpoints)

**Defer to Phase 2:**
- RAPTOR and LATTICE baselines (implement after confirming HCR beats simpler baselines)
- Growth dimension testing (start after validating at fixed corpus size)
- Full 300-query suite (expand from 200 after Phase 1)
- Tree quality metrics beyond sibling distinctiveness (novel but not essential for go/no-go)
- Budget-impossible query detection precision/recall (interesting for production, not decisive for architecture validation)
- Human evaluation beyond 50-query calibration set
- ColBERTv2, GraphRAG, commercial API comparisons
- Full regression suite CI/CD setup

### Cost breakdown

| Component | Budget estimate |
|-----------|----------------|
| Corpus generation (2K docs, GPT-4o-mini) | $2–5 |
| HCR tree construction (routing summaries) | $0.50–2 |
| Embedding generation (corpus + queries, `text-embedding-3-small`) | $0.05 |
| Cross-encoder reranking (local `ms-marco-MiniLM-L-12-v2`) | $0 (CPU) |
| RAGAS evaluation (200 queries × 3 metrics, GPT-4o-mini) | $0.50–1 |
| Sufficiency autorater (200 queries) | $0.10–0.30 |
| Answer generation for evaluation (200 queries × 5 systems) | $1–3 |
| Token efficiency curve (200 queries × 5 systems × 3 budgets) | $3–9 |
| **Total Phase 1** | **$8–20** |
| Phase 2 additions (RAPTOR baseline, expanded queries, human eval) | $15–30 |

### Reusable tools and frameworks

The evaluation stack fits together as follows:

- **ir_measures** (`pip install ir-measures`): Core IR metric computation. Supports nDCG, MAP, MRR, P, R with standardized interfaces.
- **RAGAS** (`pip install ragas`): RAG-specific metrics. Context recall, entity recall, faithfulness, factual correctness.
- **rank_bm25** (`pip install rank-bm25`): BM25 baseline. Zero-config.
- **sentence-transformers** (`pip install sentence-transformers`): Bi-encoder embeddings and cross-encoder reranking. One library for both.
- **FAISS** (`pip install faiss-cpu`): Vector similarity search. CPU version is sufficient for <10K documents.
- **spaCy** (`pip install spacy`): NER for entity extraction (used by entity coverage metrics).
- **ranx** (`pip install ranx`): Statistical significance tests (bootstrap, Student's t, Wilcoxon) between retrieval runs, plus LaTeX table export.

**Regression suite design:** Structure the benchmark as a pytest suite from day one. The 200-query evaluation becomes the full regression test. Extract a 20-query smoke test (2 per category) that runs in <60 seconds with cached embeddings. Store baseline results as frozen JSON files. Any commit that drops nDCG@10 by >0.02 from the stored baseline fails the test.

---

## 9. Success criteria: specific numbers for go, no-go, and kill

### H1a (Token efficiency) — go threshold

**Go:** HCR at 400 tokens achieves answer sufficiency rate ≥ flat+cross-encoder at 400 tokens, AND the sufficiency rate is ≥ **55%** (accounting for the ~25% budget-impossible queries and ~10% expected retrieval failures). The critical comparison: HCR's 400-token performance should match flat retrieval's performance at **≥600 tokens** — a 1.5× token efficiency gain.

**No-go (soft):** HCR at 400 tokens is within 5% of flat retrieval. The hierarchy doesn't help with token efficiency, but may still provide other benefits (proceed with caution, adjust H1a confidence downward).

**Kill:** HCR at 400 tokens is *worse* than flat retrieval at 400 tokens by >5% sufficiency rate. The tree structure and routing overhead actively harm retrieval under tight budgets.

### H1b (Hybrid superiority) — go threshold

**Go:** Dual-path HCR achieves nDCG@10 improvement of **≥0.03** over the best single-path variant (beam-only or collapsed-only) AND **≥0.05** over flat+cross-encoder reranking, with statistical significance (p < 0.05, paired permutation test). On entity-spanning queries specifically, the improvement should be **≥0.08 nDCG@10**.

**No-go (soft):** HCR beats beam-only and collapsed-only individually, but the dual-path advantage is <0.03 nDCG@10. Simplify to the better single path.

**Kill:** Flat+cross-encoder reranking beats HCR on nDCG@10 (even by 0.01) at the full corpus size. The hierarchy adds no value over a well-tuned flat system.

### H1c (Scoring quality as lever) — go threshold

**Go:** The Pearson correlation between per-level routing accuracy (1−ε) and end-to-end retrieval quality (nDCG@10) across experimental conditions is **r ≥ 0.7**, AND disabling entity cross-links drops entity-spanning query accuracy by **≥15%** (confirming cross-links as co-primary).

**Quantitative validation of the compounding model:** Plot observed cumulative accuracy vs. predicted (1−ε)^d. If the observed values fall within **±10%** of the prediction at each depth, the compounding model is validated. If observed accuracy is significantly *higher* than (1−ε)^d, beam diversity and cross-links are providing error recovery (a positive finding that means the defenses work). If significantly *lower*, there are additional error sources beyond routing.

**Kill:** Per-level routing accuracy shows no correlation with end-to-end quality (r < 0.3), suggesting routing errors are not the bottleneck — the architecture's core assumption is wrong.

### Overall failure rate

**Acceptable:** 10–20% overall failure rate (consistent with prior estimate). Define "failure" as: answer sufficiency = false AND query is budget-feasible. This means the system fails to retrieve sufficient context for a query it *should* be able to answer.

**Concerning:** 20–30% failure rate. Investigate which failure modes dominate and whether they're fixable.

**Kill:** >30% failure rate on budget-feasible queries. The system is unreliable for production use.

### Corpus size threshold

HCR must demonstrate statistical advantage over flat+cross-encoder at the **Medium corpus size (2,000 docs)** on at least entity-spanning and multi-hop query categories. At Full corpus size (3,500+ docs), the advantage should be present across all categories except DPI (where flat retrieval may remain competitive due to keyword matching strength).

### The single kill criterion

**If flat retrieval + cross-encoder reranking beats HCR on nDCG@10 at the Full corpus size with statistical significance (p < 0.05), the architecture is invalidated.** This is the one result that would definitively prove the hierarchical structure adds negative value compared to the simpler alternative. All other negative results suggest specific components need fixing rather than architectural abandonment.

---

## What this benchmark does not cover (and when it matters)

Several important dimensions are deliberately excluded from Phase 1 to keep the benchmark buildable in 10–12 days. **Latency benchmarking** is deferred because the system isn't built yet — measure latency during implementation, not during architecture validation. **Production telemetry** for failure modes like stale summaries, tree drift, and incremental updates requires a running system. **Multi-user query patterns** and permission-aware retrieval are production concerns, not architecture concerns. **Adversarial robustness** (prompt injection, deliberately misleading queries) matters for deployment but not for validating the core retrieval hypotheses.

The benchmark is designed to answer one question definitively: **does the hierarchical coarse-to-fine architecture retrieve better information under token constraints than simpler alternatives?** If the answer is yes with the margins specified above, build the system. If no, the benchmark will have identified exactly which component failed and why — routing quality, cross-link coverage, tree structure, or the fundamental assumption that hierarchy helps — providing a clear path to either fix or abandon the approach.
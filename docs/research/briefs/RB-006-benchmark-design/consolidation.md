# RB-006: Benchmark Design — Consolidation

**Date:** 2026-02-13
**Status:** Complete
**Sources:** Claude, GPT, Gemini, Perplexity (4/4)
**Brief:** [RB-006 Prompt](./prompt.md)

## Summary

All four sources converge on a remarkably consistent benchmark design. The level of agreement is the highest of any RB to date — there are no fundamental conflicts, only calibration differences in threshold values and corpus implementation details. The consolidated design is a **hybrid corpus of 50K–100K chunks**, a **300–400 query stratified suite**, **7 core metrics** (anchored by per-level routing accuracy ε and token efficiency curves), **4 baselines** (BM25, hybrid flat, flat+cross-encoder, RAPTOR), and a **fail-fast experimental sequence** that surfaces fatal flaws within the first 3–4 experiments before investing in full evaluation. The minimum viable benchmark is buildable by one person with AI assistance and costs under $50 in LLM API calls.

The single most important output of this consolidation: **the benchmark is feasible, the design is convergent, and there are no blockers to proceeding with Phase 1.**

---

## Consensus

| Finding | GPT | Gemini | Perplexity | Claude | Confidence |
|---------|-----|--------|------------|--------|------------|
| Hybrid corpus (real + synthetic) is the right approach | Yes | Yes | Yes | Yes | **Very High** |
| No existing dataset is sufficient alone — must build custom | Yes | Yes | Yes | Yes | **Very High** |
| 300–400 queries needed for statistical significance | 300 | 400 | 400 | 300 | **High** |
| Per-level ε is the single most important novel metric | Yes | Yes | Yes | Yes | **Very High** |
| ε must be defined as recall-of-relevant-branches (not single-label hit) | Yes | Yes | Yes | Yes | **Very High** |
| Answer sufficiency under token constraint is the key H1a metric | Yes | Yes | Yes | Yes | **Very High** |
| Token efficiency curve at multiple budgets (200–unconstrained) | Yes | Yes | Yes | Yes | **Very High** |
| Flat+cross-encoder reranking is the "kill baseline" | Yes | Yes | Yes | Yes | **Very High** |
| RAPTOR is the hierarchical comparator baseline | Yes | Yes | Yes | Yes | **Very High** |
| BM25-only as lexical floor baseline | Yes | Yes | Yes | Yes | **Very High** |
| LATTICE deferred to Phase 2 (too complex for Phase 1) | Yes | Yes | Yes | Yes | **Very High** |
| Commercial systems not worth comparing in Phase 1 | Yes | Yes | Yes | Yes | **High** |
| Fail-fast sequence: tree quality → ε check → HCR vs flat → token curves | Yes | Yes | Yes | Yes | **Very High** |
| Sibling distinctiveness as pre-retrieval tree quality diagnostic | Yes | Yes | Yes | Yes | **Very High** |
| RAGAS as primary evaluation framework | Partial (ARES too) | Yes | Yes (+ ARES) | Yes | **High** |
| LLM-as-judge at temperature 0, fixed model version | Yes | Yes | Yes | Yes | **Very High** |
| Paired permutation/bootstrap tests for significance | Yes | Yes | Yes | Yes | **Very High** |
| Cross-link ablation is essential for H1c | Yes | Yes | Yes | Yes | **Very High** |
| Contrastive vs generic summaries is the highest-value single ablation | Yes (second) | Yes (first) | Yes (first) | Partial (ranked A1 first) | **High** |
| Multi-corpus-size testing for transition period | Yes (10K/50K/200K) | Yes (10K/50K/100K) | Yes (10K/50K/100K) | Yes (500/2K/3.5K) | **High** |
| Budget-feasibility labels on every query | Yes | Yes | Yes | Yes | **Very High** |
| Separate retrieval sufficiency from generation accuracy | Yes | Yes | Yes | Yes | **Very High** |
| Train/dev/test split on queries, tree built from corpus only | Yes | Yes | Yes | Yes | **Very High** |

---

## Conflicts

| Point of Conflict | Position A | Position B | Assessment |
|-------------------|-----------|-----------|------------|
| **Corpus scale** | Claude: 3,500 docs (~1.4M tokens) | GPT: 10K/50K/200K chunks; Gemini: 10K/50K/100K chunks; Perplexity: 10K/50K/100K chunks | **Resolve toward chunks, not docs.** Claude conflated documents and chunks. The other three correctly specify chunk units. 50K–100K chunks is the right scale for the main evaluation. Claude's corpus is too small to demonstrate HCR's advantage. |
| **Corpus sources** | Claude: fully synthetic "Meridian Technologies" + QASPER + MultiHop-RAG | GPT: GitLab handbook + Enron emails + K8s release notes + synthetic | Gemini: EnronQA + RAGBench subsets + NIAH injections | Perplexity: public handbooks + OSS docs + synthetic | **No conflict — complementary.** Synthetic core is right for controllability; real-world sources add realism. Recommend hybrid: 1–2 real enterprise-adjacent sources (GitLab handbook is best candidate per GPT) + targeted synthetic augmentation. EnronQA (Gemini) is a strong candidate for entity-dense temporal content. |
| **H1a go threshold** | Claude: HCR@400 ≥ flat@600–800 (1.5× efficiency) | GPT: HCR@400 ≥ flat@400 + 8pp AND ≥ flat@∞ − 2pp | Perplexity: HCR@400 ≥ flat@800 − 2pp AND ≥ flat@400 + 5pp | Gemini: HCR@400 ≥ flat@800 | **GPT is strictest and most rigorous.** The +8pp threshold may be too aggressive for a Phase 1 go/no-go. Recommend Perplexity's formulation as the primary gate (+5pp over flat@400, within 2pp of flat@800) with Claude's 1.5× efficiency framing as the aspirational target. |
| **H1b go threshold** | Claude: ≥0.03 nDCG@10 over best single-path, ≥0.05 over flat+CE | GPT: ≥3pp Race uplift over best single path in ≥2 strata | Perplexity: ≥5pp on at least one major category | Gemini: ≥5% absolute improvement | **Calibration difference, not conflict.** Claude's nDCG-based thresholds are more principled; Perplexity/Gemini use answer accuracy. Recommend: dual-path must beat best single-path by ≥3pp on answer sufficiency@400, AND beat flat+CE by ≥5pp on at least entity-spanning or multi-hop queries. |
| **H1c kill threshold for ε** | Claude: ε > 0.10 at any level on easy queries | GPT: ε₁ > 0.05 at first level | Gemini: ε₁ > 0.05 at root | Perplexity: ε ≥ 0.08 even after optimization | **GPT/Gemini alignment is tighter and correct.** ε > 0.05 at level 1 is already catastrophic given compounding. Recommend GPT's ε₁ > 0.05 as the hard kill on easy queries, with ε > 0.03 per level as the go threshold for the full system. |
| **Number of random seeds** | Claude: 3 runs | GPT: 5 seeds | Perplexity: 3 runs | Gemini: not specified | **Pragmatic compromise: 3 for Phase 1, 5 for final reporting.** 5 is more rigorous but doubles cost. 3 seeds with bootstrap CIs is sufficient for go/no-go. |
| **Highest-value first ablation** | Claude: A1 (remove hierarchy entirely) | GPT: ε measurement first, then contrastive vs generic summaries | Gemini: contrastive vs generic summaries | Perplexity: contrastive vs generic summaries | **Both are correct for different purposes.** A1 (remove hierarchy) is the existential test — does hierarchy help at all? Contrastive vs generic is the highest-value *component* ablation. Recommend: the fail-fast sequence handles A1 implicitly (HCR vs flat+CE comparison). The first *deliberate ablation* should be contrastive vs generic summaries (3/4 sources agree). |
| **Primary metric for H1b** | Claude: nDCG@10 | GPT: A@T (answerability at token budget) | Perplexity: Accuracy@B | Gemini: Answer Correctness | **A@T/Sufficiency@B is better than nDCG.** nDCG measures ranking quality for human consumption; A@T measures what actually matters for RAG: did the context enable a correct answer? Recommend A@T as primary for hypothesis testing, nDCG@10 as secondary for comparability with published work. |

---

## Gaps

### 1. No source addressed cold-start realism
All sources test at fixed corpus sizes (small/medium/large) but none design a protocol for testing incremental document addition *into an existing tree* — which is how the system will actually be used. The "growth dimension" tests rebuild the tree at each size. A true growth test would add 500 docs to a 50K-doc tree and measure whether routing quality degrades. **Defer to Phase 2** — static rebuilds at multiple sizes are sufficient for go/no-go.

### 2. Latency is explicitly deferred by all sources
All four sources agree latency benchmarking is premature for architecture validation. This is correct. Flag it for Phase 1 implementation: the dual-path (beam + collapsed) design doubles retrieval cost. Measure wall-clock time during implementation to ensure it's acceptable.

### 3. No source specified how to handle the "confidence score" for dual-path race
All sources mention the race design returns the "higher-confidence result" but none specify how confidence is computed or compared between fundamentally different retrieval paths (beam search score vs flat similarity score). **This is an implementation detail, not a benchmark design gap** — but it must be specified during Phase 1 implementation. GPT's suggestion to use a "deterministic confidence function based on retrieval scores" is correct.

### 4. Cost estimates vary wildly
Claude: $8–20 Phase 1. GPT: not specified in dollar terms. Perplexity: "tens of millions of tokens." Gemini: not quantified. Claude's estimate is the most concrete and seems realistic for 200–300 queries with GPT-4o-mini as judge. **Recommend budgeting $30–50 to account for iteration and reruns.**

### 5. None addressed consumer integration testing
The benchmark validates HCR as a retrieval system. It does not test how an agentic consumer would decompose budget-impossible queries into multi-turn retrieval. **Correct to defer** — consumer integration is a Phase 2 concern. Phase 1 validates the retrieval primitive.

---

## Key Takeaways

### 1. The benchmark design is convergent and buildable
Four independent sources produced nearly identical designs across corpus, queries, metrics, baselines, and protocol. This is strong evidence that the benchmark is well-specified and not missing critical components. The remaining disagreements are calibration (threshold values), not architecture.

### 2. Per-level routing accuracy (ε) is the breakthrough metric
All four sources agree this has never been measured in any retrieval system and is the single most important novel contribution of the HCR benchmark. The definition is convergent: recall-of-relevant-branches at each tree level, handling multi-relevance via "any correct branch in beam = success." Requires instrumented logging of the scoring cascade at every level.

### 3. Answer sufficiency under token budget replaces traditional IR metrics
The benchmark's primary metric is not nDCG or Recall@k — it's "did the ≤400-token context contain enough information to answer correctly?" This is measured via LLM-as-judge sufficiency classification (RAGAS framework), with answer accuracy evaluated conditionally only on sufficient contexts. This separation of retrieval quality from generation quality is critical.

### 4. The fail-fast sequence is the most valuable protocol design
All sources agree on approximately the same sequence: (1) tree quality sanity check → (2) ε measurement on easy queries → (3) HCR vs flat+CE head-to-head → (4) token efficiency curves → (5) full evaluation → (6) ablations. Each step has a kill criterion. This prevents wasting effort if the architecture is fundamentally broken.

### 5. Contrastive vs generic summaries is the highest-value component experiment
Three of four sources rank this as the #1 ablation. It directly tests RB-004's central open question: do structured contrastive routing summaries {theme, includes, excludes, key_entities, key_terms} actually improve per-level routing accuracy compared to generic "summarize this cluster" summaries? This is the experiment most likely to produce a novel, publishable finding.

### 6. The corpus should be chunk-based at 50K–100K scale
Claude's document-level corpus (3,500 docs) is too small. The other three sources correctly specify chunk units and target 50K–100K chunks. This aligns with RB-005's prediction that HCR's advantage manifests at >50K retrieval units. Build the corpus from real enterprise-adjacent sources (GitLab handbook, EnronQA) augmented with synthetic failure-mode injectors.

### 7. Kill criterion is clear and agreed
If flat retrieval + cross-encoder reranking beats HCR on answer sufficiency at the full corpus size with statistical significance, the architecture is invalidated. All four sources converge on this. Secondary kills: ε₁ > 0.05 at root level, or ε uncorrelated with end-to-end quality.

---

## Consolidated Benchmark Specification

### Corpus
- **Type:** Hybrid real + synthetic
- **Scale:** Three sizes — Small (~10K chunks), Medium (~50K chunks), Large (~100K chunks), strict supersets
- **Real sources:** GitLab handbook (policy/procedure), EnronQA subset (entity-dense temporal), K8s/OSS docs (technical versioned)
- **Synthetic augmentation:** Entity fragmentation traps, near-duplicate clusters, vocabulary mismatch, NIAH identifier injections, budget-impossible aggregation pages, temporal version diffs
- **Growth:** Build tree fresh at each size (not incremental — defer incremental to Phase 2)

### Query Suite
- **Count:** 300 queries minimum (MVB), expandable to 400
- **Split:** 60% tune / 20% dev / 20% test (stratified by category and difficulty)
- **Categories:** Single-branch thematic, entity-spanning, DPI, multi-hop (2-hop/3+), comparative, aggregation/listing, temporal, ambiguous, OOD
- **Metadata per query:** {category, difficulty_tier, budget_feasible@400, expected_branches, gold_evidence_chunks, gold_answer}
- **Generation:** 60% LLM-generated (evidence-anchored, InPars-filtered), 20% template-derived, 20% manually crafted adversarial
- **Difficulty:** 3 tiers (40% easy / 35% medium / 25% hard) based on evidence span, entity complexity, cross-branch requirements

### Core Metrics (7)
1. **Per-level routing accuracy (ε):** Fraction of queries where no correct branch appears in beam at level l. Ground truth via bottom-up Oracle mapping from gold evidence chunks. Report ε_l per level, observed (1-ε)^d vs predicted. First-ever measurement in any retrieval system.
2. **Answer sufficiency@B:** Binary LLM-as-judge classification — "is this context sufficient to answer correctly?" Separate from answer accuracy. Primary H1a metric.
3. **Token efficiency curve:** Sufficiency@B at B ∈ {200, 400, 600, 800, 1200, unconstrained}. Compute budget-at-parity and AUC. HCR curve should be left-shifted vs flat.
4. **Beam vs collapsed comparison:** Path-conditional accuracy, path agreement rate, per-category win rates. Validates dual-path H1b value.
5. **Entity cross-link quality:** Cross-link ablation drop on entity-spanning queries, entity coverage recall (RAGAS ContextEntityRecall), cross-branch reachability.
6. **Tree quality metrics (novel):** Sibling distinctiveness (pairwise cosine distance of sibling summaries), routing summary fidelity, dendrogram purity, leaf reachability under simulated error.
7. **Standard IR metrics:** nDCG@10, Recall@100, MRR, P@5 via ir_measures for comparability with published work.

### Baselines (4 for Phase 1)
1. **BM25-only** — lexical floor (rank_bm25, trivial)
2. **Hybrid BM25+dense+RRF** — pragmatic default (FAISS + RRF, moderate)
3. **Flat+cross-encoder reranking** — the kill baseline (sentence-transformers, moderate)
4. **RAPTOR collapsed-tree** — hierarchical comparator (reference implementation, moderate-high)

Deferred: LATTICE, ColBERTv2, GraphRAG, commercial APIs.

Fairness: all baselines get same token budget, same embedding model, same LLM for generation/evaluation.

### Ablations (Priority ordered)
**Phase 1 must-run (5):**
1. Remove hierarchy entirely (flat index, keep cross-encoder) — H1b existential test
2. Remove cross-encoder reranking — H1c scoring lever
3. Beam-only (disable collapsed-tree) — H1b dual-path value
4. Disable entity cross-links — H1c co-primary mechanism
5. Contrastive vs generic summaries — RB-004 central open question

**Phase 2 (3):**
6. Remove diversity enforcement from beam — H1b beam collapse risk
7. Soft assignment → hard assignment — cross-branch resilience
8. Tree depth d=1 vs d=2 vs d=3 — compounding tradeoff

### Experimental Protocol
- **Statistical tests:** Paired permutation test (primary), bootstrap 95% CIs (B=10,000), Cohen's d for effect size
- **Variance:** 3 random seeds per configuration, mean ± SD
- **LLM control:** Fixed model version, temperature=0, prompts in version control
- **Evaluation framework:** RAGAS (context recall, entity recall, faithfulness, factual correctness) + custom sufficiency autorater
- **LLM judge:** GPT-4o-mini (primary), second judge on 50-query sample for inter-judge calibration (τ ≥ 0.7)
- **Human eval:** 50-query calibration set, 4–6 hours, expand if LLM judges disagree >20%

### Fail-Fast Sequence
| Step | What | Kill Criterion |
|------|------|----------------|
| 1 | Tree topology: build tree@10K, measure sibling distinctiveness | SD < 0.15 mean cosine distance |
| 2 | ε check: beam search on 50 easy queries@50K | ε > 0.05 at any level |
| 3 | HCR vs flat+CE: 100 queries, nDCG@10 + sufficiency@400 | HCR sufficiency < flat −5pp |
| 4 | Token efficiency: curves at {400, 800, unconstrained} on 100 queries | HCR@400 < flat@400 |
| 5 | Full 300-query evaluation | Overall failure rate >30% on budget-feasible |
| 6 | Ablations (Priority 1 set) | — |

### Success Criteria

**H1a (Token efficiency):**
- **Go:** HCR sufficiency@400 ≥ flat+CE sufficiency@400 + 5pp (p<0.05) AND HCR@400 within 2pp of flat@800
- **Kill:** HCR@400 worse than flat@400 by >5pp

**H1b (Hybrid superiority):**
- **Go:** Dual-path ≥ best single-path + 3pp on sufficiency@400 AND ≥ flat+CE + 5pp on entity-spanning or multi-hop
- **Kill:** Flat+CE beats HCR at full corpus size (even by 1pp with significance)

**H1c (Scoring lever):**
- **Go:** Pearson r ≥ 0.7 between (1-ε) and end-to-end quality; cross-link ablation drops entity-spanning accuracy ≥ 10pp
- **Kill:** ε uncorrelated with outcomes (r < 0.3) OR ε₁ > 0.05 on easy queries

**Overall:**
- Acceptable failure rate: 10–20% on budget-feasible queries
- Concerning: 20–30%
- Kill: >30%
- HCR must demonstrate advantage at Medium corpus size (50K chunks) on at least entity-spanning and multi-hop categories

### Toolchain
- `ir_measures` — standard IR metric computation
- `ragas` — RAG-specific evaluation metrics
- `rank_bm25` — BM25 baseline
- `sentence-transformers` — bi-encoder embeddings + cross-encoder reranking
- `faiss-cpu` — vector similarity search
- `spacy` — NER for entity extraction
- `ranx` — statistical significance tests + LaTeX tables

### Cost Estimate
- Corpus generation: $2–5
- Tree construction (routing summaries): $1–3
- Embeddings: <$1
- Cross-encoder: $0 (local CPU)
- RAGAS evaluation: $1–3
- Answer generation (300 queries × 5 systems × 3 budgets): $5–15
- **Total Phase 1: $15–30**
- Phase 2 additions: $20–40

---

## Recommendation

**Proceed to Phase 1. The benchmark design is convergent, buildable, and provides clear go/no-go signals for all three hypotheses.**

The consolidation reveals no unresolved design questions that would block implementation. The four sources produced nearly identical designs independently, which is strong evidence the benchmark is well-specified. The fail-fast sequence ensures we learn quickly whether the architecture works before investing in full evaluation.

The benchmark should be structured as a pytest suite from day one, with a 20-query smoke test extractable for CI use. This transforms the benchmark into both a validation gate and an ongoing regression suite.

**The go/no-go decision on Phase 1 implementation is itself now a go.** This benchmark design is the final research brief. All six RBs are complete. No showstoppers identified across 5 research briefs. The architecture is fully specified and the success criteria are defined. Build it.

---

## Next Steps

1. **Update CLAUDE.md** — mark RB-006 as complete, update phase status
2. **Update `_state.yaml`** — record consolidation completion
3. **Go/no-go decision** — all evidence supports "go" on Phase 1
4. **Phase 1 kickoff:** scaffold the benchmark as the first implementation deliverable
   - Build corpus pipeline (GitLab handbook + EnronQA + synthetic injectors)
   - Implement tree construction with instrumented logging
   - Stand up the flat+CE baseline first (it's the comparison target)
   - Run fail-fast experiments 1–3 before investing in full evaluation

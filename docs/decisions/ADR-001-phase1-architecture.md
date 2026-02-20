# ADR-001: Phase 1 Architecture

**Date:** 2026-02-13
**Status:** Accepted
**Deciders:** JC

## Context

Phase 0 (research) is complete with six research briefs confirming the HCR approach. No showstoppers identified. Phase 1 validates the core hypothesis empirically: does coarse-to-fine retrieval beat flat retrieval under a token budget?

This ADR records the architectural decisions for Phase 1 implementation.

## Decisions

### 1. Benchmark-first build order

**Decision:** Build the measurement infrastructure before the thing being measured.

**Rationale:** The fail-fast sequence (RB-006) is designed to kill the project early if the architecture is broken. Building HCR first and the benchmark second risks investing weeks before discovering a fundamental flaw. The correct order: corpus pipeline → baselines (BM25, hybrid, flat+CE) → metrics → then incrementally build HCR components and measure against baselines.

**Alternatives rejected:**
- Build HCR first, then benchmark: delays validation, wastes effort if architecture fails
- Build in parallel: creates integration risk, harder to isolate measurement issues

### 2. Flat+CE as kill baseline

**Decision:** The flat corpus + cross-encoder reranker is the kill baseline. If flat+CE beats HCR at full corpus with statistical significance, the project is killed.

**Rationale:** Flat+CE represents the strongest non-hierarchical approach — the same cross-encoder quality without the tree overhead. If the tree doesn't add value over brute-force reranking, HCR has no reason to exist. Per RB-006, this is the only baseline that matters for go/no-go.

### 3. Stripped scope — fail-fast minimum only

**Decision:** Phase 1 includes only what is needed to reach fail-fast Steps 1-3. Specifically excluded:

| Excluded | Reason | When |
|----------|--------|------|
| Pointer resolution module | Benchmark corpus is local files | Phase 2 |
| Entity cross-links / spacy | Cross-branch defense, not core hypothesis | Phase 2 |
| RAPTOR baseline | Secondary comparator, replication risk | Phase 2 |
| ColBERT multi-vector | Single dense vector sufficient for validation | Phase 2 |
| Incremental tree updates | Rebuild-at-threshold is simpler | Phase 2 |
| GPU acceleration | CPU sufficient at 50-100K chunks | Production |

**Rationale:** Every excluded component can be added later if the core hypothesis validates. None are needed to answer the Phase 1 question.

### 4. Single LLM client (Anthropic)

**Decision:** Use `anthropic` as the only LLM client. Claude serves as both summary generator and evaluation judge.

**Rationale:** The consumer application uses `anthropic>=0.49`. Adding `openai` for evaluation creates a second dependency with different auth, rate limits, and failure modes. Claude is capable as an eval judge. One client simplifies the stack.

**Alternative rejected:** OpenAI GPT-4o-mini for cheaper eval — adds dependency complexity, and Claude evaluation quality is sufficient for R&D validation.

### 5. Dual-path as co-primary

**Decision:** Beam search traversal and collapsed-tree retrieval are co-primary strategies that race in parallel. Return the higher-confidence result.

**Rationale:** RB-005 identified beam collapse as a top-3 residual risk. Collapsed-tree retrieval (RAPTOR-style flat search over all node summaries) catches cases where beam search fails. Promoting it from fallback to co-primary was a design change from RB-005 analysis.

### 6. Bisecting k-means tree backbone

**Decision:** Use bisecting k-means for tree construction with d=2-3 depth, b=6-15 branching factor.

**Rationale:** Four-source convergence in RB-004. Bisecting k-means is simpler than GMM, more interpretable than hierarchical agglomerative clustering, and naturally produces balanced trees. Soft assignment (1-3 parents per leaf) handles multi-topic content.

**Alternatives rejected:**
- GMM: soft clustering is elegant but harder to control branching factor
- GraphRAG: 10-50x more expensive, entity cross-links provide similar benefit at lower cost
- GRINCH/PERCH: online algorithms better suited for incremental updates (Phase 2)

### 7. Baselines and evaluation outside library package

**Decision:** `hcr_core/` contains only library code that consumers will import. Baselines, evaluation metrics, and benchmark infrastructure live outside `hcr_core/` — in `tests/benchmark/` and a top-level `benchmark/` data directory.

**Rationale:** Clean separation. Consumers import `hcr_core.tree`, `hcr_core.traversal`, etc. They do not need BM25 baselines or LLM judges.

### 8. Consumer alignment

**Decision:** Match the consumer application's stack where dependencies overlap.

| Dependency | Version | Source |
|------------|---------|--------|
| Python | >=3.12 (3.12.3) | Consumer |
| pydantic | >=2.12 | Consumer |
| anthropic | >=0.49 | Consumer |
| httpx | >=0.28 | Consumer |

## Consequences

- Phase 1 is tightly scoped: we validate one hypothesis and stop
- Benchmark-first means we can measure from day one
- Excluded components may be needed if Phase 1 validates — that's Phase 2
- Single LLM client means eval costs are Anthropic API costs (~$15-30 MVB)
- If flat+CE wins, we kill the project — that's a valid and valuable outcome

## References

- RB-002: Theoretical basis (hybrid coarse-to-fine)
- RB-003: Scoring mechanics (cascade architecture)
- RB-004: Tree construction (bisecting k-means convergence)
- RB-005: Failure modes (dual-path, beam diversity)
- RB-006: Benchmark design (fail-fast sequence, kill criteria)

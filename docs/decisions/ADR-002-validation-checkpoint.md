# ADR-002: Validation Checkpoint — Small-Corpus Results and Next Steps

**Date:** 2026-02-16
**Status:** Accepted
**Deciders:** JC

## Context

Ten HCR configurations (v1-v10) tested against the flat+CE kill baseline on a 315-chunk corpus (50 queries). Results:

| Config | Key Change | nDCG@10 | L1 ε | MeanTok |
|--------|-----------|---------|------|---------|
| v2 | CE all levels | 0.318 | 0.32 | 234 |
| v5 | Beam=8 ceiling | 0.509 | 0.14 | 297 |
| v6 | Enriched embed text | 0.493 | 0.16 | 249 |
| v10 | mpnet + rebuilt tree | **0.540** | 0.24 | **231** |
| **Kill baseline** | Flat+CE | **0.835** | — | 354 |

Best HCR result: nDCG=0.540 (v10). Gap to kill: **0.295** (35%).

Levers exhausted at this scale:
- Tree structure (flat → hierarchical, branching factor)
- Routing cascade (CE vs cosine-only, beam width 3→5→8)
- Summary text quality (enriched fields, contrastive prompts, content snippets)
- Embedding model (MiniLM 384-dim → mpnet 768-dim)

Key findings:
1. **CE is net negative** for routing on structured metadata
2. **Tree structure is sound** — wider beam monotonically improves results
3. **Routing epsilon (0.16-0.24) is 5-10x above target (≤0.03)** — the core problem
4. **mpnet helps leaf scoring, not routing** — 768-dim benefits chunks but not structured summaries
5. **Token efficiency confirmed** — HCR uses 231-297 tokens vs 354 for flat+CE

## Decision

**Phase A: Two ceiling experiments on the small corpus, then Phase B: scale up.**

### Phase A — Small-Corpus Ceiling (next session)

Two targeted experiments to establish the ceiling before investing in scale-up:

1. **Beam=8 on mpnet tree** — v10 used beam=5. Beam=8 gives the routing ceiling for this tree. Quick, no code changes beyond config. If this doesn't break 0.65, dense-only routing has a hard ceiling on this corpus.

2. **BM25 hybrid routing** — the original design (RB-002/003) called for BM25+dense pre-filter at each level. We never tested it. Summary nodes have `key_terms` and `key_entities` — BM25 on these could rescue queries where cosine fails on structured text. This is the last untested lever from the original architecture.

**Phase A success criterion:** either experiment breaks nDCG=0.65.
**Phase A kill criterion:** neither breaks 0.65 → dense-embedding routing on structured summaries has a fundamental ceiling at small corpus scale.

### Phase B — Scale-Up Validation

Regardless of Phase A outcome, the real test is at scale:

- RB-006 designed the benchmark for 50K-100K chunks, not 315
- At 315 chunks, flat+CE examines everything cheaply — HCR's advantage (avoiding irrelevant branches) has no room to show
- Routing epsilon matters more at scale (more branches to prune)
- Token efficiency gap widens at scale (flat+CE costs grow linearly, HCR costs grow logarithmically)

Build the larger corpus (GitLab handbook + synthetic) and rerun the fail-fast sequence from RB-006.

## Rationale

**Why not call it now?** The 315-chunk corpus is a confound. HCR is designed for large corpora where flat search is expensive. Testing at 315 chunks is like benchmarking a database index on a 10-row table — the full scan always wins. The hypothesis may be scale-dependent, and we haven't tested at the designed scale.

**Why not skip to scale-up?** Phase A is cheap and informative. If BM25 hybrid routing dramatically improves routing epsilon, that insight transfers to the larger corpus. If nothing helps, we know the problem is structural and can design the scale-up accordingly.

**Why these two experiments?** Beam=8 establishes the pure routing ceiling. BM25 hybrid tests the one architectural component from the original design we never implemented. Together they bound what's possible at small scale.

## Consequences

- Phase A: 1 session, no new infrastructure
- Phase B: corpus construction + LLM summarization costs (~$15-30 per RB-006)
- If Phase A ceiling < 0.65 AND Phase B at scale also loses → H1a/H1b invalidated with confidence
- If Phase B at scale wins → hypothesis was scale-dependent, which is itself a finding
- Token efficiency (H1a partial) is already validated — HCR uses 35% fewer tokens

## References

- ADR-001: Phase 1 architecture (kill baseline, fail-fast sequence)
- RB-002: Hybrid coarse-to-fine theoretical basis
- RB-003: Cascade scoring (BM25+dense+CE target ε≤0.03)
- RB-006: Benchmark design (50K-100K corpus, kill criteria)
- v1-v10 results: `docs/research/_state.yaml`

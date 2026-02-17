# hcr-core

Hierarchical Context Retrieval — coarse-to-fine retrieval for LLM systems. Minimum viable context: correct answer, fewest tokens.

**This is R&D.** Phase 0 (research) complete. Phase 1 (core library) implemented. Now in **empirical validation** — baselines established, ready for HCR vs baseline comparison.

## Git Workflow

- **Branch naming:** `{MMDD}jc` (e.g., `0213jc` for Feb 13th)
- **On startup:** If no branch exists for today, create one from `main`
- **If yesterday's branch exists and has unmerged work:** Ask if we should continue or start fresh
- **Commits:** After each meaningful checkpoint, commit and push immediately. Don't accumulate.
- **Before every commit:** Ensure CLAUDE.md is up to date with any state changes. Mandatory.
- **NO Co-Authored-By:** Never. Universal rule.
- **End of session:** All changes pushed, `_state.yaml` updated, next steps stated.

## Startup Behaviour

When JC says "what's next" or starts a session:
1. Check git status — uncommitted changes? Ask: commit, stash, or discard
2. Check current branch:
   - On `main` → pull latest, create today's branch
   - On yesterday's branch → ask: continue or merge and start fresh?
   - On today's branch → continue working
3. Read this file — understand current state and phase
4. Read `docs/research/_state.yaml` — check blockers and next actions
5. State what I plan to work on, ask if correct
6. Begin work

## Session End Behaviour

When JC says "done for today" or "wrap up":
1. Commit and push all changes
2. Update `docs/research/_state.yaml` with session state
3. Update this file if project status changed
4. Summarise what was done
5. State next steps for next session

## Available Commands

| Command | Description |
|---------|-------------|
| `/au-plan` | Create implementation plan. WAITS for confirmation before coding. |
| `/au-tdd` | Test-driven development. Writes tests first, then implements. |
| `/au-review` | Review uncommitted changes for quality/security. |
| `/au-verify` | Full verification: types, lint, tests. |
| `/au-fix` | Incrementally fix build/type errors. |
| `/au-checkpoint` | Save progress checkpoint. |
| `/au-fresh` | Fresh context execution (manual handoff or auto subagent). |
| `/au-learn` | Extract patterns from debugging sessions into knowledge base. |
| `/rnd-debug` | 5-level debugging escalation (pattern → variant → context → domain → edge case). |
| `/au-security` | Security vulnerability review (read-only). |

### Workflow Selection

JC describes tasks in plain English. I select the workflow:

| JC Says | Workflow |
|---------|----------|
| "Research X" / "What about Y?" | Deep research brief (RB-NNN) |
| "Build X" / "Implement Y" | `/au-plan` → `/au-tdd` → execute |
| "Fix the build" / "Type errors" | `/au-fix` |
| "Review my changes" | `/au-review` |
| "Let's validate H-NNN" | Design experiment, run, measure |

For anything architectural or uncertain, I research first and recommend.

## My Role

Lead research assistant. JC steers, I lead execution. I recommend (defaulting to gold standard), JC decides. I question everything — including my own recommendations.

## Current Phase

**Phase 1: Core Library + Benchmark Validation**

| Phase | Scope | Status |
|-------|-------|--------|
| **0. Research & validation** | Validate hypothesis, prior art, scoring mechanics | **Complete** (6/6 briefs) |
| **1. Core library** | Tree, traversal, scoring, pointer resolution, benchmark | **Current** |
| **2. Integration layer** | Connectors for external data sources | Planned |
| **3. Autonomous index manager** | Agent that maintains the tree | Planned |

## The Hypotheses

Original H1 ("elimination > similarity") retired after RB-002. Reframed as three independent, testable sub-hypotheses:

| ID | Statement | Confidence | Key Test |
|----|-----------|------------|----------|
| **H1a** | Hierarchical coarse-to-fine achieves equivalent or better accuracy than flat similarity while using fewer tokens (design target: 400 tokens, adaptive not hard-capped) | 65% | RB-006 benchmark |
| **H1b** | Coarse elimination + fine similarity outperforms either pure approach alone | 80% | RB-006 benchmark |
| **H1c** | Per-level scoring quality is the primary determinant of retrieval quality — error compounds at (1-ε)^d | 75% | **RB-003** (confirmed — cascade achieves ε ≈ 0.01–0.02) |

Scoring feasibility (RB-003), construction feasibility (RB-004), failure mode analysis (RB-005), and benchmark design (RB-006) all confirmed. No showstopper identified across six research briefs. Remaining uncertainty is empirical — Phase 1 benchmark will validate or invalidate all three hypotheses.

**Baseline results (2026-02-15):**

| System | nDCG@10 | Recall@10 | MRR | MeanTok |
|--------|---------|-----------|-----|---------|
| BM25 | 0.705 | 0.82 | 0.669 | 333 |
| Hybrid-RRF | 0.719 | 0.90 | 0.662 | 343 |
| **Flat+CE (kill)** | **0.835** | **0.94** | **0.803** | 354 |

Flat+CE is the kill baseline. HCR must beat nDCG@10=0.835 under token constraints to validate H1a/H1b.

**HCR beam width sweep (2026-02-16, depth=3, branching=8, cosine-only routing):**

| Config | Beam | nDCG@10 | Recall@10 | MRR | MeanTok | L1 ε | L2 ε |
|--------|------|---------|-----------|-----|---------|------|------|
| v2 (CE all) | 3 | 0.318 | 0.40 | 0.298 | 234 | 0.32 | 0.62 |
| v3 cosine | 3 | 0.287 | 0.32 | 0.281 | 235 | 0.32 | 0.58 |
| v4 wide | 5 | 0.420 | 0.46 | 0.411 | 255 | 0.24 | 0.46 |
| **v5 ceiling** | **8** | **0.509** | **0.58** | **0.490** | 297 | **0.14** | **0.36** |

Tree: L0:1(8) L1:8(8) L2:64(avg4.7) L3+L4:333 leaves. Sibling distinctiveness: 0.608 (pass >0.15).

**Summary text experiments (2026-02-16, beam=5, cosine-only):**

| Config | Change | nDCG@10 | MeanTok | L1 ε | L2 ε |
|--------|--------|---------|---------|------|------|
| **v6 enriched** | **All fields in embed text** | **0.493** | **249** | **0.16** | **0.36** |
| v7 prompts | Contrastive prompt rewrite | 0.484 | 269 | 0.14 | 0.44 |
| v8 snippets | Content snippets in embeds | 0.485 | 279 | 0.16 | 0.42 |

**Embedding model swap (2026-02-16, beam=5, cosine-only, NO tree rebuild):**

| Config | Model | Dims | Tree | nDCG@10 | Recall@10 | MeanTok | L1 ε | L2 ε | L4 ε |
|--------|-------|------|------|---------|-----------|---------|------|------|------|
| v6 (ref) | MiniLM | 384 | MiniLM | 0.493 | 0.54 | 249 | 0.16 | 0.36 | 0.81 |
| v9 | mpnet | 768 | MiniLM | 0.450 | 0.54 | 296 | 0.18 | 0.38 | 0.76 |
| **v10** | **mpnet** | **768** | **mpnet** | **0.540** | **0.62** | **231** | 0.24 | 0.42 | **0.75** |

**Phase A ceiling experiment #1 (2026-02-16, mpnet rebuilt tree, beam=8):**

| Config | Beam | nDCG@10 | Recall@10 | MRR | MeanTok | L1 ε | L2 ε | L4 ε |
|--------|------|---------|-----------|-----|---------|------|------|------|
| v10 (ref) | 5 | 0.540 | 0.62 | 0.516 | 231 | 0.24 | 0.42 | 0.75 |
| **v11 ceiling** | **8** | **0.580** | **0.66** | **0.556** | 290 | **0.06** | **0.28** | 0.84 |

**Key findings (2026-02-16):**
1. **CE is net negative for routing** — MS-MARCO CE trained on natural language, not structured metadata. Flips 26 correct cosine decisions to wrong, saves only 14. Now skipped for internal nodes.
2. **Tree structure is sound** — wider beam monotonically improves epsilon and nDCG. Correct branches exist but cosine ranks them too low with current summary embeddings.
3. **MiniLM embedding space is the bottleneck** — enriched text helped +17% (v6) but prompts and snippets are washes. All plateau at nDCG ~0.49. 384-dim space is saturated.
4. **Token efficiency confirmed** — even beam=8 uses 297 tokens vs flat+CE 354. Best config (v6) uses only 249.
5. **mpnet swap without tree rebuild is WORSE** — nDCG dropped 8.7% (0.493→0.450). Tree was clustered in MiniLM space; mpnet embedding space is misaligned. **Tree must be rebuilt for any embedding model change.**
6. **mpnet with rebuilt tree is BEST nDCG (0.540)** — but routing epsilon is worse (L1 0.24 vs 0.16). Gains come from better leaf-level discrimination (L4 ε 0.75 vs 0.81), not routing. 768-dim helps chunks more than structured summaries. Routing quality needs a different lever (BM25 hybrid?).
7. **L1 routing nearly solved at beam=8 mpnet (ε=0.06)** — dramatic improvement from 0.24. Bottleneck shifted to L2 (ε=0.28). L4 ε worsened (0.84 vs 0.75) — wider beam introduces noise in leaf CE scoring. nDCG=0.580 below Phase A 0.65 threshold but encouraging.
8. **BM25 hybrid routing is net negative (v12: nDCG=0.465, -14%)** — RRF(cosine, BM25) over summary `key_terms`/`key_entities` hurts. BM25 signal too sparse on short structured text (~10-20 tokens per node). Reverted to cosine-only. **Phase A complete: both ceiling experiments done. Best nDCG=0.580, below 0.65 threshold. Proceed to Phase B (scale-up).**

**Phase B infrastructure (2026-02-17):**

Phase B code infrastructure is complete. All scripts support `--scale small|medium|large`:

| Component | Change |
|-----------|--------|
| `hcr_core/corpus/wikipedia.py` | New. Streams Wikipedia via HuggingFace `datasets`, keyword-filtered. |
| `scripts/prepare_corpus.py` | `--scale` flag. Medium: full GitLab (~13-25K). Large: GitLab + Wikipedia (~60K). |
| `hcr_core/corpus/embedder.py` | Batched embedding with tqdm progress for large corpora. |
| `scripts/generate_queries.py` | Checkpointing every 50 queries. Source-proportional sampling. |
| `hcr_core/tree/builder.py` | Progress logging every 100 LLM summary calls. |
| `scripts/run_benchmark.py` | `--scale`, `--tree-depth`, `--tree-branching`, `failfast` mode (RB-006 kill sequence). |

**Next: Execute the pipeline** — medium corpus first (stepping stone), then large (definitive test).

**Per-category analysis (2026-02-15):**

| Category | N | CE nDCG@10 | CE-BM25 gap | HCR opportunity |
|----------|---|-----------|-------------|-----------------|
| ambiguous | 2 | 0.565 | +0.315 | High (all systems weak, low N) |
| dpi | 7 | 0.615 | +0.006 | High (CE adds nothing over BM25) |
| comparative | 5 | 0.663 | +0.451 | High (cross-branch hard for flat) |
| single_branch | 12 | 0.792 | +0.023 | Medium (CE adds little) |
| entity_spanning | 10 | 1.000 | +0.137 | Token-only (CE perfect) |
| multi_hop | 5 | 1.000 | +0.274 | Token-only (CE perfect) |

HCR should target dpi + comparative (12 queries) for accuracy wins. Per-query results: `benchmark/results/per_query_results.json`.

Full details: `docs/research/hypotheses.md`

**Consumer:** Su — agentic command centre. Purely outcomes-focused, minimal context, needs precise retrieval from a growing organisation.

## Research Briefs (Phase 0)

| Brief | Topic | Status |
|-------|-------|--------|
| RB-001 | Prior art survey | **Complete** (3/4 sources — Gemini pending) |
| RB-002 | Theoretical basis: elimination vs similarity | **Complete** (3/4 sources — Gemini unavailable) |
| RB-003 | Scoring mechanics | **Complete** (3/4 sources — cascade architecture confirmed) |
| RB-004 | Tree construction | **Complete** (4/4 sources — convergent construction recipe confirmed) |
| RB-005 | Failure modes | **Complete** (3/4 sources — no showstopper, 10–20% expected failure rate) |
| RB-006 | Benchmark design | **Complete** (4/4 sources — highest convergence of any brief) |

**All research briefs complete. Go/no-go decision: GO on Phase 1.**

## Deep Research Protocol

When a question needs deep research:
1. I create `docs/research/briefs/RB-{NNN}-{slug}/` with `prompt.md`
2. I scaffold empty response files: `response-gpt.md`, `response-gemini.md`, `response-perplexity.md`, `response-claude.md`
3. I create `consolidation.md`
4. JC runs the prompt across sources, pastes responses
5. I consolidate: consensus, conflicts, gaps, recommendation

Templates: `docs/research/briefs/_template-*.md`

## Current Design (Unvalidated)

### Tree Construction (RB-004)
1. **Decompose** multi-topic content into atomic semantic units before clustering
2. **Partition** top-down via bisecting k-means in embedding space, constrained to d=2–3, b∈[6,15]
3. **Soft assign** multi-topic leaves to 1–3 parents (cheap because leaves are pointers)
4. **Summarise** each node with LLM — structured routing summaries: `{theme, includes, excludes, key_entities, key_terms}`
5. **Represent** summaries as: dense embedding + ColBERT-style multi-vector (8–16 per node) + BM25 index over key terms
6. **Cross-link** entity index across branches for cross-branch query support

### Query-Time Traversal (RB-002, RB-003, RB-005)
1. Query enters at root. **Per-level cascade:** hybrid BM25+dense pre-filter (all children) → top-3 → cross-encoder rerank → top-1–2
2. **Path-relevance EMA** smooths scores across depth; beam search (k=3–5) over frontier with **diversity enforcement** (MMR-style penalty against beams exploring same branch — RB-005 design change)
3. **Dual-path retrieval:** beam-search traversal AND collapsed-tree retrieval run in parallel; return higher-confidence result (RB-005: collapsed-tree promoted to co-primary, not fallback)
4. **Fine retrieval:** within surviving branches, AdaGReS-style greedy packing (relevance − redundancy, token budget)
5. Leaf pointers **resolve to external sources** (APIs, repos, databases, files) with retry/cache/fallback for unavailability (RB-005 design change) — data stays where it lives
6. Target: **400 tokens as design aspiration, not hard limit.** Architecture optimises for 400; actual budget is adaptive per query. Success metric: "fraction of queries answerable under 400 tokens" (should grow as routing improves). Budget-impossible queries → multi-turn agentic decomposition by Su.

### Maintenance
- Incremental insertion: route new leaves via scoring cascade to best-matching cluster(s)
- Local repair: split/merge when branch bounds exceeded or routing accuracy drops
- Dirty-flag summary staleness: lazy regeneration prioritised by access frequency
- Periodic rebuild: full reconstruction when 20–30% of subtree is new content

*Cross-branch defense:* five layers — decomposition, soft assignment, entity cross-links, beam search (k=3–5), collapsed-tree fallback (emergency only).

## Tech Stack

- **Language:** Python
- **Type checking:** mypy (strict)
- **Linting:** ruff
- **Testing:** pytest
- **Async:** asyncio for parallel traversal

```bash
mypy hcr_core/                     # Type check
ruff check hcr_core/               # Lint
pytest                              # Tests
pytest --cov=hcr_core               # Coverage
```

## Project Structure

```
hcr_core/                        # Library source (Phase 1+)
docs/
  research/
    _state.yaml                  # Session state (read on startup)
    hypotheses.md                # Hypothesis tracking
    briefs/                      # Deep research (RB-NNN-slug/)
  knowledge/                     # Pattern taxonomy
  decisions/                     # Architecture Decision Records (ADR-NNN)
tests/                           # Test suite (Phase 1+)
```

## Naming Conventions

| Entity | Pattern | Example |
|--------|---------|---------|
| Research briefs | `RB-{NNN}-{slug}/` | `RB-001-prior-art/` |
| Decisions | `ADR-{NNN}-{slug}.md` | `ADR-001-tree-vs-graph.md` |
| Hypotheses | `H-{NNN}` | `H-001` |
| Metrics | `M-{NNN}` | `M-001` |
| Findings | `FINDINGS-{NNN}-{slug}.md` | `FINDINGS-001-raptor-comparison.md` |

## Decisions Made

- **ADR-001:** Go/no-go on Phase 1 — decision is GO based on six research briefs with no showstoppers. Benchmark design convergent across 4 sources. First implementation deliverable: benchmark infrastructure.
- **ADR-002:** Validation checkpoint after 10 HCR configs on 315-chunk corpus. Best nDCG=0.540, kill baseline=0.835. Decision: **Phase A** (2 ceiling experiments: beam=8 mpnet, BM25 hybrid routing) then **Phase B** (scale up to 50K-100K chunks per RB-006). Scale is a confound — HCR designed for large corpora, tested on small. **Phase A complete (nDCG=0.580). Phase B infrastructure built. Ready for execution.**

## Open Questions

- **RESOLVED (RB-002):** ~~Under what conditions does elimination beat enriched flat?~~ — Strict elimination wins only under stringent conditions. Hybrid coarse-to-fine is theoretically superior.
- **RESOLVED:** ~~H1 needs reframing~~ — Split into H1a/H1b/H1c (2026-02-13). See hypotheses.md.
- **RESOLVED (RB-003):** ~~Scoring quality is the exponential lever~~ — Confirmed. Cascade architecture (hybrid pre-filter → cross-encoder) achieves ε ≈ 0.01–0.02. Strict admissibility impossible for semantic relevance; design for probabilistic ε control. Path-relevance EMA is higher leverage than per-node scoring.
- **RESOLVED (RB-004):** ~~Summary quality is the #1 upstream factor. How should trees be built?~~ — Convergent recipe: top-down divisive clustering + LLM contrastive summaries + soft assignment. Structured routing summaries `{theme, includes, excludes, key_entities, key_terms}` are a distinct artifact class.
- **RESOLVED (RB-004):** ~~How is the tree constructed and maintained?~~ — Bisecting k-means backbone (d=2–3, b∈[6,15]), PERCH/GRINCH-style local repairs, periodic full rebuild at 20–30% new content threshold.
- **OPEN (RB-004 gap):** Do contrastive summaries ("covers X, NOT Y") actually improve per-level routing accuracy vs generic summaries? No empirical evidence exists. Highest-value experiment for Phase 1.
- **OPEN (RB-004 gap):** No routing-specific tree quality metric exists in the literature. Per-level routing accuracy, sibling distinctiveness, entity coverage proposed but unvalidated. HCR can fill this gap.
- **RESOLVED (empirical):** ~~Cross-encoder (MS-MARCO) is net negative for routing on structured summary text.~~ — Confirmed. Cosine-only routing implemented. Wider beam (not CE) is the lever. Beam sweep: beam=3→5→8 shows monotonic improvement. Summary embedding quality is the real bottleneck.
- **RESOLVED (empirical):** ~~Can summary embedding quality be improved enough to reach ε≤0.03?~~ — Three approaches tested. Enriched embed text (v6) improved L1 ε from 0.24→0.16, nDCG +17%. Contrastive prompts and content snippets were washes. MiniLM 384-dim embedding space is saturated. ε≤0.03 not achievable with this model. Next: stronger embedding model.
- **OPEN (empirical):** L4 epsilon is 0.78-0.81 across all configs. Is leaf-level CE also hurting? Or is chunk embedding quality poor?
- **PARTIALLY RESOLVED (empirical):** ~~Will a stronger embedding model (mpnet 768-dim, E5-large 1024-dim) close the gap to kill baseline?~~ — mpnet with rebuilt tree (v10): nDCG=0.540 (+9.5% vs MiniLM best). Gains from leaf scoring, NOT routing. L1 ε actually worse (0.24 vs 0.16). 768-dim helps chunks but not structured summaries. Routing improvement needs different approach (BM25 hybrid?). Kill baseline (0.835) still far.
- **RESOLVED (RB-005):** ~~Where does this approach break?~~ — 26 failure modes identified. No showstopper. 10–20% expected failure rate. Top residual risks: DPI information loss (#1), budget impossibility for aggregation, beam collapse. Three design changes needed: beam diversity enforcement, collapsed-tree as co-primary, external source handling. Entity cross-links elevated to primary mechanism for dominant query type.
- **RESOLVED (RB-006):** ~~What benchmark validates the architecture?~~ — Four-source convergent design: hybrid corpus (50K–100K chunks), 300–400 stratified queries, 7 core metrics (ε, sufficiency@B, token efficiency curve, beam vs collapsed, cross-link quality, tree quality, standard IR), 4 baselines, fail-fast sequence with kill criteria. MVB costs $15–30. Per-level routing accuracy ε is the breakthrough metric (never measured in any system). Kill criterion: flat+CE beats HCR at full corpus with significance.
- LATTICE (UT Austin, Oct 2025) is the closest competitor. How does HCR differentiate? (Token budget, external source pointers, coarse-to-fine hybrid.)

## Constraints

- **Proprietary IP** — not open-sourced
- **No AI in compliance decisions** — HCR retrieves context, humans decide
- **Portable** — standalone library, imported as dependency. No coupling to consumers.

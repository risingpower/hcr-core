# hcr-core

Hierarchical Context Retrieval — coarse-to-fine retrieval for LLM systems. Minimum viable context: correct answer, fewest tokens.

**This is R&D.** The concept is unproven. Validate before building.

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

**Phase 0: Research & Validation**

| Phase | Scope | Status |
|-------|-------|--------|
| **0. Research & validation** | Validate hypothesis, prior art, scoring mechanics | **Current** |
| **1. Core library** | Tree, traversal, scoring, pointer resolution | Next |
| **2. Integration layer** | Connectors for external data sources | Planned |
| **3. Autonomous index manager** | Agent that maintains the tree | Planned |

## The Hypotheses

Original H1 ("elimination > similarity") retired after RB-002. Reframed as three independent, testable sub-hypotheses:

| ID | Statement | Confidence | Key Test |
|----|-----------|------------|----------|
| **H1a** | Under hard token budgets (<400 tokens), hierarchical coarse-to-fine achieves equivalent or better accuracy than flat similarity with unconstrained tokens | 65% | RB-006 benchmark |
| **H1b** | Coarse elimination + fine similarity outperforms either pure approach alone | 75% | RB-006 benchmark |
| **H1c** | Per-level scoring quality is the primary determinant of retrieval quality — error compounds at (1-ε)^d | 75% | **RB-003** (confirmed — cascade achieves ε ≈ 0.01–0.02) |

H1c is the immediate research priority — scoring feasibility gates the other two.

Full details: `docs/research/hypotheses.md`

**Consumer:** Su — agentic command centre. Purely outcomes-focused, minimal context, needs precise retrieval from a growing organisation.

## Research Briefs (Phase 0)

| Brief | Topic | Status |
|-------|-------|--------|
| RB-001 | Prior art survey | **Complete** (3/4 sources — Gemini pending) |
| RB-002 | Theoretical basis: elimination vs similarity | **Complete** (3/4 sources — Gemini unavailable) |
| RB-003 | Scoring mechanics | **Complete** (3/4 sources — cascade architecture confirmed) |
| RB-004 | Tree construction | **Scaffolded** — prompt ready, awaiting source responses |
| RB-005 | Failure modes | Pending RB-003/004 |
| RB-006 | Benchmark design | Pending RB-005 |

After RB-006: **Go/no-go decision** on Phase 1.

## Deep Research Protocol

When a question needs deep research:
1. I create `docs/research/briefs/RB-{NNN}-{slug}/` with `prompt.md`
2. I scaffold empty response files: `response-gpt.md`, `response-gemini.md`, `response-perplexity.md`, `response-claude.md`
3. I create `consolidation.md`
4. JC runs the prompt across sources, pastes responses
5. I consolidate: consensus, conflicts, gaps, recommendation

Templates: `docs/research/briefs/_template-*.md`

## Current Design (Unvalidated)

1. Data **mapped** into hierarchical index tree — nodes hold descriptions + pointers to children or leaf sources
2. Query enters at root. **Per-level cascade:** hybrid BM25+dense pre-filter (all children) → top-3 → cross-encoder rerank → top-1–2
3. **Path-relevance EMA** smooths scores across depth; beam search over frontier
4. **Fine retrieval:** within surviving branches, AdaGReS-style greedy packing (relevance − redundancy, token budget)
5. Leaf pointers **resolve to external sources** (APIs, repos, databases, files) — data stays where it lives
6. Target: **under 400 tokens** retrieved context

*Design note:* Traversal strategy shifted from strict elimination to coarse-to-fine hybrid after RB-002 theoretical analysis.

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

*None yet — Phase 0.*

## Open Questions

- **RESOLVED (RB-002):** ~~Under what conditions does elimination beat enriched flat?~~ — Strict elimination wins only under stringent conditions. Hybrid coarse-to-fine is theoretically superior.
- **RESOLVED:** ~~H1 needs reframing~~ — Split into H1a/H1b/H1c (2026-02-13). See hypotheses.md.
- **RESOLVED (RB-003):** ~~Scoring quality is the exponential lever~~ — Confirmed. Cascade architecture (hybrid pre-filter → cross-encoder) achieves ε ≈ 0.01–0.02. Strict admissibility impossible for semantic relevance; design for probabilistic ε control. Path-relevance EMA is higher leverage than per-node scoring.
- **CRITICAL (RB-004):** Summary quality is the #1 upstream factor for scoring accuracy. How should trees be built to produce routing-friendly summaries?
- How is the tree constructed and maintained? Shallow wide trees preferred over deep narrow. (RB-004)
- Where does this approach break? Cross-branch queries confirmed as #1 failure mode by theory. (RB-005)
- LATTICE (UT Austin, Oct 2025) is the closest competitor. How does HCR differentiate? (Token budget, external source pointers, coarse-to-fine hybrid.)

## Constraints

- **Proprietary IP** — not open-sourced
- **No AI in compliance decisions** — HCR retrieves context, humans decide
- **Portable** — standalone library, imported as dependency. No coupling to consumers.

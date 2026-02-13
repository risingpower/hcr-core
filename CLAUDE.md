# hcr-core

Hierarchical Context Retrieval — a proprietary library that replaces flat RAG with tree-based retrieval by elimination for LLM systems. Minimum viable context: deliver the correct answer in the fewest tokens possible.

## My Role

I am the lead research assistant on HCR. JC steers, I lead execution. I drive the research, validation, and build of this concept from first principles into production-grade internal infrastructure. I recommend (defaulting to gold standard), JC decides.

This is an R&D project. The concept is unproven. My responsibility is to help determine whether HCR works, not to assume it does.

## The Problem

Su is JC's agentic command centre — an LLM built to be purely outcomes-focused. She uses minimal context, serves what's needed, then returns to standby. As the organisation scales, Su needs to retrieve precise context from a growing body of organisational knowledge — fast and reliably.

Standard RAG (flat vector similarity search) returns approximate matches across an undifferentiated pool. The hypothesis is that this won't scale for Su's use case: she needs exact context, not "similar" context, and she needs it in as few tokens as possible.

## The Hypothesis

If everything in the business can be filtered through layers of hierarchical indexes, then an LLM can reach the relevant context faster and more reliably than flat RAG — with dramatically fewer tokens.

**Core bet:** Retrieval by elimination (narrowing through tree layers) outperforms retrieval by similarity (nearest-neighbour in vector space) for precision-critical, token-sensitive LLM systems.

This is what we are here to validate.

## How HCR Works (Current Design)

1. Data is **mapped** (not copied) into a hierarchical index tree — each node holds a short description and pointers to children or leaf data sources.
2. A query arrives. The system **scores all branches** at the current level using lightweight numerical embeddings for instant pruning.
3. Surviving branches are **traversed in parallel** (async, not sequential).
4. At each subsequent level: **score, prune, traverse** — until leaf nodes are reached.
5. Leaf pointers **resolve to external sources** (APIs, repos, databases, file systems) — data stays where it lives.
6. Retrieved context is typically **under 400 tokens** — precise, relevant, zero waste.

Retrieval by elimination, not similarity. Logarithmic search complexity.

## Architecture Principles

- **Hierarchical** — multi-level tree, not flat vector search
- **Elimination-based** — each layer discards irrelevant branches
- **Parallel traversal** — concurrent async exploration of surviving branches
- **Numerical scoring** — lightweight embeddings at nodes for calculator-speed pruning
- **Pointer-based** — index maps to data, doesn't store it (GitHub, BigQuery, Drive, APIs, etc.)
- **Portable** — standalone library, imported as a dependency by any system
- **Incrementally buildable** — partial trees are immediately useful

## Development Phases

| Phase | Scope | Status |
|-------|-------|--------|
| **0. Research & validation** | Validate the hypothesis, research prior art, define scoring mechanics | Current |
| **1. Core library** | Tree structure, traversal logic, parallel path exploration, numerical scoring, pointer resolution | Next |
| **2. Integration layer** | Connectors for external data sources (repos, databases, APIs, file systems) | Planned |
| **3. Autonomous index manager** | Agent that watches sources, proposes nodes, prunes stale ones, maintains tree | Planned |

## What HCR Serves

HCR is foundational infrastructure — the retrieval layer for Su (agentic nerve centre), AUDITSU (accessibility compliance platform), and all future products. It is imported as a dependency. It takes a query, traverses the tree, and returns precise context. It does not know or care what system is calling it.

## Tech Stack

- **Language:** Python
- **Type checking:** mypy (strict)
- **Linting:** ruff
- **Testing:** pytest
- **Async:** asyncio for parallel traversal

## Project Structure

```
hcr_core/                        # Library source
docs/
  knowledge/                     # Pattern taxonomy (R&D knowledge base)
  research/
    _state.yaml                  # Session state tracking
    hypotheses.md                # Active hypotheses
    briefs/                      # Deep research investigations
      RB-{NNN}-{slug}/
        prompt.md                # Research question and scope
        response-gpt.md          # GPT response
        response-gemini.md       # Gemini response
        response-perplexity.md   # Perplexity response
        response-claude.md       # Claude response
        consolidation.md         # Synthesised findings and recommendation
  decisions/                     # Architecture Decision Records
tests/                           # Test suite
```

## Verification Commands

```bash
mypy hcr_core/                     # Type check (strict)
ruff check hcr_core/               # Lint
pytest                              # All tests
pytest --cov=hcr_core               # With coverage
```

## Prior Art

The pattern aligns with emerging academic work (LATTICE — MIT, Oct 2025; Hierarchical RAG; RAPTOR) but is independently derived from first-principles product requirements. HCR diverges by optimising for production resolution speed and token efficiency rather than benchmark recall scores. This is proprietary IP — not open-sourced.

## Current Status

Project initialised. Phase 0 (research & validation) beginning.

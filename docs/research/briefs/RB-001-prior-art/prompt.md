# RB-001: Prior Art Survey — Hierarchical and Tree-Based Retrieval for LLMs

**Date:** 2026-02-13
**Status:** Open
**Decision Required:** No — informational, shapes all subsequent research
**Related:** H1 (core hypothesis), RB-002 through RB-006

## Context

We are building HCR (Hierarchical Context Retrieval), a system that replaces flat RAG with tree-based retrieval by elimination. Instead of vector similarity search across a flat pool of chunks, HCR organises knowledge into a hierarchical index tree. A query enters at the root, branches are scored and pruned at each level, surviving branches are traversed in parallel, and leaf nodes resolve to external data sources. The goal is precise context retrieval in under 400 tokens with logarithmic search complexity.

Before designing or building anything, we need to understand what already exists in this space — what's been tried, what works, what fails, and where HCR's proposed approach genuinely differs from prior work.

## Research Question

What is the current state of hierarchical, tree-based, and elimination-based retrieval systems for LLM context delivery? Specifically:

1. What systems, papers, and frameworks exist that use hierarchical or tree-structured retrieval (as opposed to flat vector search)?
2. How do they work mechanically — tree construction, scoring, traversal, pruning?
3. What are their demonstrated strengths and measured weaknesses?
4. Where does the research consensus stand on hierarchical vs flat retrieval for precision and token efficiency?
5. What are the open problems that remain unsolved?

## Scope

**In scope:**
- Academic papers (RAPTOR, LATTICE, Hierarchical RAG, tree-of-thought retrieval, recursive summarisation trees, etc.)
- Production systems or frameworks that implement hierarchical retrieval
- Comparative studies: hierarchical vs flat RAG performance
- Adjacent work: tree-based search in information retrieval (pre-LLM) that may inform LLM retrieval

**Out of scope:**
- General RAG tutorials or overviews
- Vector database comparisons (Pinecone vs Weaviate etc.)
- Prompt engineering techniques
- Fine-tuning approaches for retrieval

## What We Already Know

- **RAPTOR** (Recursive Abstractive Processing for Tree-Organized Retrieval) — builds a tree by recursively clustering and summarising text chunks. Retrieval can traverse the tree or collapse layers. Published 2024.
- **LATTICE** — MIT, Oct 2025. Appears to use hierarchical structure for retrieval. Details limited.
- **Hierarchical RAG** — term used loosely in industry. Unclear whether it refers to a specific system or a general pattern.
- HCR's proposed design was derived independently from first-principles product requirements (Su's need for minimal, precise context), not from academic literature. We need to now check how it overlaps with and diverges from existing work.

## Prompt for Sources

> I am researching hierarchical and tree-based retrieval systems for delivering context to LLMs — as an alternative to standard flat RAG (vector similarity search over a flat chunk pool).
>
> I need a comprehensive survey of prior art in this space. Specifically:
>
> 1. **Systems and papers**: What academic papers, frameworks, or production systems exist that use hierarchical, tree-structured, or elimination-based retrieval for LLM context? Include RAPTOR, LATTICE (MIT 2025), and any others. For each, explain:
>    - How the tree/hierarchy is constructed
>    - How queries are routed or scored at each level
>    - How pruning/elimination works
>    - Whether retrieval is top-down (root to leaf) or bottom-up or hybrid
>    - Measured performance vs flat RAG (precision, recall, token efficiency, latency)
>
> 2. **Pre-LLM precedent**: Are there established tree-based retrieval techniques from information retrieval, library science, or database systems that predate LLMs but are directly applicable? (e.g., B-trees for search, hierarchical classification systems, faceted search, decision trees for routing)
>
> 3. **Comparative evidence**: What empirical evidence exists comparing hierarchical retrieval to flat vector retrieval? Are there benchmarks, ablation studies, or production case studies?
>
> 4. **Open problems**: What are the known unsolved challenges in hierarchical retrieval? (e.g., tree construction, cross-branch queries, maintaining hierarchy as data changes, scoring accuracy at internal nodes)
>
> 5. **Gaps**: What has NOT been tried or explored? Where are the opportunities for novel contribution?
>
> Be specific. Cite papers with titles, authors, and dates where possible. Distinguish between peer-reviewed work, preprints, blog posts, and commercial claims. If something is speculative or unvalidated, say so.

## Success Criteria

A good response will:
- Name at least 5 distinct systems or papers with specific details on their mechanics
- Distinguish between peer-reviewed, preprint, and informal sources
- Provide concrete performance comparisons where they exist
- Identify at least 3 open problems in the space
- Be honest about gaps in the evidence rather than filling them with speculation

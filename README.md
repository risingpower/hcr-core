# HCR: Hierarchical Context Retrieval

[![DOI](https://zenodo.org/badge/1162601095.svg)](https://doi.org/10.5281/zenodo.18713920)

Coarse-to-fine retrieval for LLM systems. Research code accompanying:

> **Per-Level Routing Error Compounds Exponentially: A Negative Result on Embedding-Based Hierarchical Retrieval at Scale**
>
> Jason Crispin, February 2026

## What This Is

HCR tests whether embedding-based routing through a tree of LLM-generated summaries can achieve token-efficient retrieval for LLM systems. The answer is **no** --- routing error compounds exponentially with tree depth, collapsing retrieval quality at scale.

**Key result:** At 315 chunks (depth 3), the best configuration achieved nDCG@10 = 0.580. At 21,897 chunks (depth 5), performance collapsed to nDCG@10 = 0.094 versus 0.749 for flat retrieval with cross-encoder reranking.

## Novel Contribution

**Per-level routing epsilon** --- a metric that measures routing accuracy at each tree level independently. No prior hierarchical retrieval system (RAPTOR, LATTICE, HIRO) has exposed or measured per-level routing decisions. This metric reveals *where* hierarchical retrieval fails, not just *that* it fails.

## Repository Structure

```
hcr_core/              # Library source
  tree/                # Tree construction (bisecting k-means + LLM summaries)
  traversal/           # Beam search routing
  scoring/             # Cosine, cross-encoder, BM25 scoring
  corpus/              # Corpus preparation and embedding
  llm/                 # LLM client for summary generation
benchmark/             # Benchmark configuration and results
scripts/               # Corpus prep, tree building, query generation, benchmarking
docs/
  research/
    paper.md           # Full paper (markdown)
    paper.tex          # Full paper (LaTeX)
    hypotheses.md      # Hypothesis tracking
    briefs/            # Deep research briefs (RB-001 through RB-006)
  decisions/           # Architecture Decision Records
tests/                 # Test suite
```

## Research Process

This repo includes the full research trail:

- **6 research briefs** (`docs/research/briefs/`) --- multi-source deep research on prior art, scoring mechanics, tree construction, failure modes, and benchmark design. Each brief consolidates responses from GPT-4, Claude, Gemini, and Perplexity.
- **12 HCR configurations** tested systematically, varying beam width, embedding model, routing strategy, and summary representation.
- **Hypothesis tracking** (`docs/research/hypotheses.md`) --- three sub-hypotheses, all empirically resolved.
- **Architecture decisions** (`docs/decisions/`) --- recorded with rationale.

## Running the Code

```bash
# Install
pip install -e ".[dev]"

# Type check and lint
mypy hcr_core/
ruff check hcr_core/

# Tests
pytest

# Prepare corpus (small scale)
python scripts/prepare_corpus.py --scale small

# Build tree
python scripts/build_tree.py --scale small

# Generate evaluation queries
python scripts/generate_queries.py --scale small

# Run benchmark
python scripts/run_benchmark.py --scale small
```

Requires an Anthropic API key for tree construction (LLM summary generation):

```bash
export ANTHROPIC_API_KEY=your-key-here
```

## Five Empirical Patterns

1. **DPI Summary Blindness** --- routing summaries lose specific facts; detail queries score poorly against thematic summaries.
2. **Cross-Encoder Routing Damage** --- MS-MARCO cross-encoder trained on natural language is poorly calibrated for structured routing metadata. Net negative for routing decisions.
3. **Beam Width as Diagnostic** --- monotonic improvement with wider beams confirms the tree structure is sound; routing cannot find the right branches.
4. **Embedding Saturation** --- MiniLM 384-dim saturates; mpnet 768-dim helps leaf scoring but not routing.
5. **BM25 Routing Sparsity** --- summary text is too short (~10-20 tokens) for meaningful lexical matching.

## Citation

```bibtex
@article{crispin2026hcr,
  title={Per-Level Routing Error Compounds Exponentially: A Negative Result on Embedding-Based Hierarchical Retrieval at Scale},
  author={Crispin, Jason},
  year={2026},
  note={Available at https://github.com/risingpower/hcr-core}
}
```

## License

MIT. See [LICENSE](LICENSE).

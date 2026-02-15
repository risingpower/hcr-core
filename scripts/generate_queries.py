"""Generate benchmark queries from corpus using LLM.

Usage:
    python scripts/generate_queries.py [--corpus-dir benchmark/corpus] [--count 50]

Generates stratified queries across categories and difficulty levels.
Requires ANTHROPIC_API_KEY environment variable.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
import sys
from pathlib import Path

from hcr_core.llm.claude import ClaudeClient
from hcr_core.types.corpus import Chunk
from hcr_core.types.query import Query, QueryCategory
from tests.benchmark.queries.generator import generate_queries_for_chunk
from tests.benchmark.queries.suite import QuerySuite

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Categories to generate, weighted by importance from RB-006
CATEGORY_WEIGHTS: dict[QueryCategory, float] = {
    QueryCategory.SINGLE_BRANCH: 0.25,
    QueryCategory.ENTITY_SPANNING: 0.20,
    QueryCategory.DPI: 0.15,
    QueryCategory.MULTI_HOP: 0.10,
    QueryCategory.COMPARATIVE: 0.10,
    QueryCategory.AGGREGATION: 0.05,
    QueryCategory.TEMPORAL: 0.05,
    QueryCategory.AMBIGUOUS: 0.05,
    QueryCategory.OOD: 0.05,
}


def select_chunks_for_generation(
    chunks: list[Chunk],
    count: int,
    seed: int = 42,
) -> list[Chunk]:
    """Select a diverse sample of chunks for query generation."""
    rng = random.Random(seed)
    # Filter out very short chunks (< 50 tokens) — not enough content for good queries
    viable = [c for c in chunks if c.token_count >= 50]
    logger.info("Viable chunks (>=50 tokens): %d / %d", len(viable), len(chunks))

    if len(viable) <= count:
        return viable

    return rng.sample(viable, count)


def generate_query_suite(
    client: ClaudeClient,
    chunks: list[Chunk],
    target_count: int,
    seed: int = 42,
) -> QuerySuite:
    """Generate a stratified query suite from corpus chunks."""
    rng = random.Random(seed)
    queries: list[Query] = []
    categories = list(CATEGORY_WEIGHTS.keys())

    # Determine per-category counts
    category_counts: dict[QueryCategory, int] = {}
    remaining = target_count
    for cat in categories[:-1]:
        n = max(1, int(target_count * CATEGORY_WEIGHTS[cat]))
        category_counts[cat] = n
        remaining -= n
    category_counts[categories[-1]] = max(1, remaining)

    logger.info("Target query counts per category:")
    for cat, n in category_counts.items():
        logger.info("  %s: %d", cat.value, n)

    # Generate queries per category
    chunk_pool = list(chunks)
    rng.shuffle(chunk_pool)
    chunk_idx = 0

    for category, count in category_counts.items():
        generated = 0
        attempts = 0
        max_attempts = count * 3  # Allow some failures

        while generated < count and attempts < max_attempts and chunk_idx < len(chunk_pool):
            chunk = chunk_pool[chunk_idx]
            chunk_idx += 1
            attempts += 1

            query = generate_queries_for_chunk(
                client,
                chunk,
                category,
                query_id_prefix=f"gen-{category.value}",
            )
            if query is not None:
                queries.append(query)
                generated += 1
                if generated % 5 == 0:
                    logger.info("  %s: %d/%d generated", category.value, generated, count)

        logger.info(
            "  %s: %d/%d generated (%d attempts)",
            category.value, generated, count, attempts,
        )

    logger.info("Total queries generated: %d / %d target", len(queries), target_count)
    return QuerySuite(queries)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate benchmark queries")
    parser.add_argument(
        "--corpus-dir", type=str, default="benchmark/corpus",
        help="Directory containing prepared corpus.",
    )
    parser.add_argument(
        "--output", type=str, default="benchmark/queries/queries.json",
        help="Output path for query suite.",
    )
    parser.add_argument(
        "--count", type=int, default=50,
        help="Target number of queries to generate.",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for reproducibility.",
    )
    args = parser.parse_args()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not set. Required for query generation.")
        sys.exit(1)

    project_root = Path(__file__).parent.parent
    corpus_dir = project_root / args.corpus_dir
    output_path = project_root / args.output

    # Load chunks
    chunks_path = corpus_dir / "chunks.json"
    if not chunks_path.exists():
        logger.error("No chunks found at %s. Run scripts/prepare_corpus.py first.", chunks_path)
        sys.exit(1)

    data = json.loads(chunks_path.read_text())
    chunks = [Chunk(**item) for item in data]
    logger.info("Loaded %d chunks", len(chunks))

    # Select chunks for generation
    selected = select_chunks_for_generation(chunks, count=args.count * 2, seed=args.seed)
    logger.info("Selected %d chunks for query generation", len(selected))

    # Generate queries
    client = ClaudeClient()
    suite = generate_query_suite(client, selected, target_count=args.count, seed=args.seed)

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    suite.save(output_path)
    logger.info("Saved %d queries to %s", len(suite), output_path)

    # Print summary
    print(f"\nGenerated {len(suite)} queries:")
    for cat in QueryCategory:
        cat_queries = suite.filter_category(cat)
        if len(cat_queries) > 0:
            print(f"  {cat.value}: {len(cat_queries)}")


if __name__ == "__main__":
    main()

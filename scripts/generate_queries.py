"""Generate benchmark queries from corpus using LLM.

Usage:
    python scripts/generate_queries.py [--corpus-dir benchmark/corpus] [--count 50]

Generates stratified queries across categories and difficulty levels.
Requires ANTHROPIC_API_KEY environment variable.

Supports checkpointing: saves partial results every 50 queries so
long-running generation for large corpora can be resumed.
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

CHECKPOINT_INTERVAL = 50


def select_chunks_for_generation(
    chunks: list[Chunk],
    count: int,
    seed: int = 42,
) -> list[Chunk]:
    """Select a diverse, source-proportional sample of chunks for query generation.

    When chunks come from multiple sources (e.g., gitlab-handbook + wikipedia),
    sampling is proportional to each source's chunk count.
    """
    rng = random.Random(seed)
    # Filter out very short chunks (< 50 tokens) — not enough content for good queries
    viable = [c for c in chunks if c.token_count >= 50]
    logger.info("Viable chunks (>=50 tokens): %d / %d", len(viable), len(chunks))

    if len(viable) <= count:
        return viable

    # Group by document source prefix (e.g., "gitlab-handbook-00001" -> "gitlab-handbook")
    source_groups: dict[str, list[Chunk]] = {}
    for chunk in viable:
        # Extract source from document_id: everything before the last "-NNNNN"
        parts = chunk.document_id.rsplit("-", 1)
        source = parts[0] if len(parts) == 2 and parts[1].isdigit() else chunk.document_id
        source_groups.setdefault(source, []).append(chunk)

    if len(source_groups) <= 1:
        return rng.sample(viable, count)

    # Proportional sampling across sources
    selected: list[Chunk] = []
    total_viable = len(viable)
    for source, group in source_groups.items():
        proportion = len(group) / total_viable
        source_count = max(1, int(count * proportion))
        sample_size = min(source_count, len(group))
        selected.extend(rng.sample(group, sample_size))
        logger.info(
            "  Source %s: %d chunks, sampling %d (%.0f%%)",
            source,
            len(group),
            sample_size,
            proportion * 100,
        )

    # If rounding left us short, fill from remaining
    remaining_pool = [c for c in viable if c not in set(selected)]
    while len(selected) < count and remaining_pool:
        selected.append(remaining_pool.pop(rng.randrange(len(remaining_pool))))

    rng.shuffle(selected)
    return selected[:count]


def generate_query_suite(
    client: ClaudeClient,
    chunks: list[Chunk],
    target_count: int,
    output_path: Path,
    seed: int = 42,
) -> QuerySuite:
    """Generate a stratified query suite from corpus chunks.

    Saves checkpoints every CHECKPOINT_INTERVAL queries to output_path
    so generation can be resumed after interruption.
    """
    rng = random.Random(seed)
    queries: list[Query] = []

    # Check for existing checkpoint
    checkpoint_path = output_path.with_suffix(".checkpoint.json")
    if checkpoint_path.exists():
        checkpoint_data = json.loads(checkpoint_path.read_text())
        queries = [Query(**q) for q in checkpoint_data]
        logger.info("Resumed from checkpoint: %d queries already generated", len(queries))

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

    # Count already-generated per category (from checkpoint)
    existing_per_cat: dict[QueryCategory, int] = {}
    for q in queries:
        existing_per_cat[q.category] = existing_per_cat.get(q.category, 0) + 1

    # Generate queries per category
    chunk_pool = list(chunks)
    rng.shuffle(chunk_pool)
    chunk_idx = 0

    for category, count in category_counts.items():
        already = existing_per_cat.get(category, 0)
        needed = count - already
        if needed <= 0:
            logger.info("  %s: already have %d/%d, skipping", category.value, already, count)
            continue

        generated = 0
        attempts = 0
        max_attempts = needed * 3  # Allow some failures

        while generated < needed and attempts < max_attempts and chunk_idx < len(chunk_pool):
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

                # Checkpoint periodically
                if len(queries) % CHECKPOINT_INTERVAL == 0:
                    _save_checkpoint(queries, checkpoint_path)
                    logger.info("  Checkpoint saved: %d queries", len(queries))

                if generated % 5 == 0:
                    logger.info("  %s: %d/%d generated", category.value, generated, needed)

        logger.info(
            "  %s: %d/%d generated (%d attempts)",
            category.value, generated, needed, attempts,
        )

    # Clean up checkpoint
    if checkpoint_path.exists():
        checkpoint_path.unlink()

    logger.info("Total queries generated: %d / %d target", len(queries), target_count)
    return QuerySuite(queries)


def _save_checkpoint(queries: list[Query], path: Path) -> None:
    """Save partial query list as checkpoint."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [q.model_dump() for q in queries]
    path.write_text(json.dumps(data))


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

    # Generate queries (haiku is cheaper and sufficient for query generation)
    client = ClaudeClient(model="claude-3-5-haiku-20241022")
    suite = generate_query_suite(
        client, selected, target_count=args.count, output_path=output_path, seed=args.seed,
    )

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

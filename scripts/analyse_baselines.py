"""Analyse baseline results per query category and difficulty.

Runs all three baselines and breaks down IR metrics by category.
Identifies where flat+CE is strong vs weak — i.e., where HCR has
the best chance of winning.

Usage:
    python scripts/analyse_baselines.py \
        --corpus-dir benchmark/corpus \
        --queries-path benchmark/queries/queries.json
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from hcr_core.corpus.embedder import ChunkEmbedder, EmbeddingCache
from hcr_core.types.corpus import Chunk
from hcr_core.types.query import DifficultyTier, Query, QueryCategory
from tests.benchmark.baselines.bm25_baseline import BM25Baseline
from tests.benchmark.baselines.flat_ce_baseline import FlatCrossEncoderBaseline
from tests.benchmark.baselines.hybrid_baseline import HybridBaseline
from tests.benchmark.eval.ir_metrics import mrr, ndcg_at_k, recall_at_k
from tests.benchmark.queries.suite import QuerySuite

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """Per-query evaluation result."""

    query_id: str
    category: str
    difficulty: str
    system: str
    ndcg_at_10: float
    recall_at_10: float
    mrr: float
    rank_of_first_relevant: int  # 0 = not found
    tokens_used: float


@dataclass
class CategoryStats:
    """Aggregated stats for a category."""

    category: str
    n: int = 0
    ndcg_scores: list[float] = field(default_factory=list)
    recall_scores: list[float] = field(default_factory=list)
    mrr_scores: list[float] = field(default_factory=list)
    tokens: list[float] = field(default_factory=list)

    @property
    def mean_ndcg(self) -> float:
        return sum(self.ndcg_scores) / self.n if self.n else 0.0

    @property
    def mean_recall(self) -> float:
        return sum(self.recall_scores) / self.n if self.n else 0.0

    @property
    def mean_mrr(self) -> float:
        return sum(self.mrr_scores) / self.n if self.n else 0.0

    @property
    def mean_tokens(self) -> float:
        return sum(self.tokens) / self.n if self.n else 0.0

    @property
    def perfect_recall_rate(self) -> float:
        """Fraction of queries where recall@10 = 1.0."""
        if not self.n:
            return 0.0
        return sum(1 for r in self.recall_scores if r >= 1.0) / self.n


def load_chunks(corpus_dir: Path) -> list[Chunk]:
    """Load prepared chunks from corpus directory."""
    chunks_path = corpus_dir / "chunks.json"
    if not chunks_path.exists():
        raise FileNotFoundError(f"No chunks found at {chunks_path}")
    data = json.loads(chunks_path.read_text())
    return [Chunk(**item) for item in data]


def load_embeddings(
    chunks: list[Chunk],
    cache_dir: Path,
) -> tuple[ChunkEmbedder, NDArray[np.float32]]:
    """Load cached embeddings."""
    cache = EmbeddingCache(cache_dir)
    embedder = ChunkEmbedder(cache=cache)
    corpus_key = f"benchmark-{len(chunks)}"
    cached = cache.load(corpus_key)
    if cached is None:
        raise RuntimeError(
            "No cached embeddings found. Run run_benchmark.py first."
        )
    _, embeddings = cached
    return embedder, embeddings


def find_first_relevant_rank(
    ranked_ids: list[str], relevant: set[str]
) -> int:
    """Return 1-indexed rank of first relevant result, or 0 if not found."""
    for i, chunk_id in enumerate(ranked_ids):
        if chunk_id in relevant:
            return i + 1
    return 0


def evaluate_per_query(
    baseline_name: str,
    rank_fn: object,
    retrieve_fn: object,
    queries: list[Query],
    token_budget: int = 400,
) -> list[QueryResult]:
    """Evaluate a baseline per-query and return individual results."""
    results: list[QueryResult] = []
    for query in queries:
        ranked = rank_fn(query.text, top_k=50)  # type: ignore[operator]
        ranked_ids = [chunk_id for chunk_id, _ in ranked]
        relevant = set(query.gold_chunk_ids)

        packed = retrieve_fn(query.text, token_budget)  # type: ignore[operator]
        tokens = sum(c.token_count for c in packed)

        results.append(
            QueryResult(
                query_id=query.id,
                category=query.category.value,
                difficulty=query.difficulty.value,
                system=baseline_name,
                ndcg_at_10=ndcg_at_k(ranked_ids, relevant, k=10),
                recall_at_10=recall_at_k(ranked_ids, relevant, k=10),
                mrr=mrr(ranked_ids, relevant),
                rank_of_first_relevant=find_first_relevant_rank(
                    ranked_ids, relevant
                ),
                tokens_used=tokens,
            )
        )
    return results


def group_by_category(
    results: list[QueryResult],
) -> dict[str, CategoryStats]:
    """Group per-query results into per-category stats."""
    groups: dict[str, CategoryStats] = {}
    for r in results:
        if r.category not in groups:
            groups[r.category] = CategoryStats(category=r.category)
        s = groups[r.category]
        s.n += 1
        s.ndcg_scores.append(r.ndcg_at_10)
        s.recall_scores.append(r.recall_at_10)
        s.mrr_scores.append(r.mrr)
        s.tokens.append(r.tokens_used)
    return groups


def print_category_table(
    system_name: str,
    stats: dict[str, CategoryStats],
    category_order: list[str],
) -> None:
    """Print a per-category metrics table."""
    print(f"\n{'=' * 80}")
    print(f"  {system_name}")
    print(f"{'=' * 80}")
    fmt = "{:<20} {:>4} {:>10} {:>10} {:>10} {:>10} {:>10}"
    print(
        fmt.format(
            "Category", "N", "nDCG@10", "Recall@10", "MRR", "PerfRec%", "Tok"
        )
    )
    print("-" * 80)
    for cat in category_order:
        if cat in stats:
            s = stats[cat]
            print(
                fmt.format(
                    cat,
                    str(s.n),
                    f"{s.mean_ndcg:.3f}",
                    f"{s.mean_recall:.3f}",
                    f"{s.mean_mrr:.3f}",
                    f"{s.perfect_recall_rate:.0%}",
                    f"{s.mean_tokens:.0f}",
                )
            )


def print_comparison_table(
    all_stats: dict[str, dict[str, CategoryStats]],
    category_order: list[str],
) -> None:
    """Print a cross-system comparison table per category."""
    systems = list(all_stats.keys())

    for metric_name, metric_attr in [
        ("nDCG@10", "mean_ndcg"),
        ("Recall@10", "mean_recall"),
        ("MRR", "mean_mrr"),
    ]:
        print(f"\n{'=' * 100}")
        print(f"  CROSS-SYSTEM COMPARISON: {metric_name} by Category")
        print(f"{'=' * 100}")
        header = "{:<20} {:>4}" + " {:>12}" * len(systems)
        print(header.format("Category", "N", *systems))
        print("-" * 100)

        for cat in category_order:
            row: list[str] = []
            n = "0"
            for sys_name in systems:
                if cat in all_stats[sys_name]:
                    s = all_stats[sys_name][cat]
                    n = str(s.n)
                    row.append(f"{getattr(s, metric_attr):.3f}")
                else:
                    row.append("-")
            fmt = "{:<20} {:>4}" + " {:>12}" * len(systems)
            print(fmt.format(cat, n, *row))


def print_hcr_opportunity_analysis(
    all_stats: dict[str, dict[str, CategoryStats]],
    category_order: list[str],
) -> None:
    """Identify categories where HCR has the best chance."""
    ce_stats = all_stats.get("flat-ce", {})
    bm25_stats = all_stats.get("bm25", {})

    print(f"\n{'=' * 100}")
    print("  HCR OPPORTUNITY ANALYSIS")
    print(f"{'=' * 100}")
    print(
        "\nCategories ranked by HCR opportunity "
        "(lower CE nDCG = more room to beat):\n"
    )

    category_gaps: list[tuple[str, float, float, int]] = []
    for cat in category_order:
        if cat in ce_stats:
            ce_ndcg = ce_stats[cat].mean_ndcg
            bm25_ndcg = bm25_stats[cat].mean_ndcg if cat in bm25_stats else 0
            n = ce_stats[cat].n
            category_gaps.append((cat, ce_ndcg, bm25_ndcg, n))

    # Sort by CE nDCG ascending (weakest CE = biggest opportunity)
    category_gaps.sort(key=lambda x: x[1])

    fmt = "{:<3} {:<20} {:>4} {:>12} {:>12} {:>12}"
    print(
        fmt.format(
            "#", "Category", "N", "CE nDCG@10", "BM25 nDCG@10", "CE-BM25 gap"
        )
    )
    print("-" * 70)

    for i, (cat, ce_ndcg, bm25_ndcg, n) in enumerate(category_gaps, 1):
        gap = ce_ndcg - bm25_ndcg
        print(
            fmt.format(
                str(i),
                cat,
                str(n),
                f"{ce_ndcg:.3f}",
                f"{bm25_ndcg:.3f}",
                f"+{gap:.3f}",
            )
        )

    print("\nInterpretation:")
    print(
        "  - Categories where CE nDCG is low: flat retrieval struggles, "
        "HCR may win via better routing"
    )
    print(
        "  - Categories where CE-BM25 gap is small: reranking adds little, "
        "structure may help more"
    )
    print(
        "  - Categories where CE nDCG is already ~1.0: hard for HCR to "
        "improve, focus on token savings"
    )


def print_difficulty_breakdown(
    all_results: dict[str, list[QueryResult]],
) -> None:
    """Print metrics breakdown by difficulty tier."""
    print(f"\n{'=' * 100}")
    print("  DIFFICULTY BREAKDOWN: nDCG@10 by Tier")
    print(f"{'=' * 100}")

    systems = list(all_results.keys())
    tiers = ["easy", "medium", "hard"]

    header = "{:<10} {:>4}" + " {:>12}" * len(systems)
    print(header.format("Difficulty", "N", *systems))
    print("-" * 70)

    for tier in tiers:
        row: list[str] = []
        n = 0
        for sys_name in systems:
            tier_results = [
                r for r in all_results[sys_name] if r.difficulty == tier
            ]
            if tier_results:
                n = len(tier_results)
                mean = sum(r.ndcg_at_10 for r in tier_results) / n
                row.append(f"{mean:.3f}")
            else:
                row.append("-")
        fmt = "{:<10} {:>4}" + " {:>12}" * len(systems)
        print(fmt.format(tier, str(n), *row))


def save_per_query_results(
    all_results: dict[str, list[QueryResult]],
    output_path: Path,
) -> None:
    """Save per-query results to JSON for further analysis."""
    data: list[dict[str, object]] = []
    for results in all_results.values():
        for r in results:
            data.append(
                {
                    "query_id": r.query_id,
                    "category": r.category,
                    "difficulty": r.difficulty,
                    "system": r.system,
                    "ndcg_at_10": round(r.ndcg_at_10, 4),
                    "recall_at_10": round(r.recall_at_10, 4),
                    "mrr": round(r.mrr, 4),
                    "rank_of_first_relevant": r.rank_of_first_relevant,
                    "tokens_used": round(r.tokens_used, 1),
                }
            )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2))
    logger.info("Per-query results saved to %s", output_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyse baseline results per category"
    )
    parser.add_argument(
        "--corpus-dir",
        type=str,
        default="benchmark/corpus",
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        default="benchmark/embeddings",
    )
    parser.add_argument(
        "--queries-path",
        type=str,
        default="benchmark/queries/queries.json",
    )
    parser.add_argument(
        "--results-dir",
        type=str,
        default="benchmark/results",
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    corpus_dir = project_root / args.corpus_dir
    cache_dir = project_root / args.cache_dir
    queries_path = project_root / args.queries_path
    results_dir = project_root / args.results_dir

    # Load data
    chunks = load_chunks(corpus_dir)
    logger.info("Loaded %d chunks", len(chunks))

    embedder, embeddings = load_embeddings(chunks, cache_dir)
    logger.info("Loaded embeddings: %s", embeddings.shape)

    suite = QuerySuite.load(queries_path)
    queries = suite.queries
    logger.info("Loaded %d queries", len(queries))

    # Print query distribution
    cat_counts: dict[str, int] = defaultdict(int)
    diff_counts: dict[str, int] = defaultdict(int)
    for q in queries:
        cat_counts[q.category.value] += 1
        diff_counts[q.difficulty.value] += 1

    print("\n=== Query Distribution ===")
    print(f"  Total: {len(queries)}")
    print("  By category:")
    category_order = sorted(cat_counts.keys())
    for cat in category_order:
        print(f"    {cat}: {cat_counts[cat]}")
    print("  By difficulty:")
    for diff in ["easy", "medium", "hard"]:
        print(f"    {diff}: {diff_counts.get(diff, 0)}")

    # Build baselines
    logger.info("Building baselines...")
    bm25 = BM25Baseline(chunks)
    hybrid = HybridBaseline(chunks, embeddings, embedder=embedder)
    flat_ce = FlatCrossEncoderBaseline(
        chunks, embeddings, embedder=embedder
    )

    baselines = [
        ("bm25", bm25),
        ("hybrid-rrf", hybrid),
        ("flat-ce", flat_ce),
    ]

    # Evaluate per-query
    all_results: dict[str, list[QueryResult]] = {}
    all_stats: dict[str, dict[str, CategoryStats]] = {}

    for name, baseline in baselines:
        logger.info("Evaluating %s per-query...", name)
        start = time.time()
        results = evaluate_per_query(
            name, baseline.rank, baseline.retrieve, queries
        )
        elapsed = time.time() - start
        logger.info("  %s done in %.1fs", name, elapsed)

        all_results[name] = results
        stats = group_by_category(results)
        all_stats[name] = stats
        print_category_table(name, stats, category_order)

    # Cross-system comparison
    print_comparison_table(all_stats, category_order)

    # Difficulty breakdown
    print_difficulty_breakdown(all_results)

    # HCR opportunity analysis
    print_hcr_opportunity_analysis(all_stats, category_order)

    # Save per-query results
    output_path = results_dir / "per_query_results.json"
    save_per_query_results(all_results, Path(output_path))


if __name__ == "__main__":
    main()

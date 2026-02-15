"""Run HCR benchmark evaluation.

Usage:
    python scripts/run_benchmark.py [--mode sanity|baselines|full] [--corpus-dir benchmark/corpus]

Modes:
    sanity    - Quick pipeline validation on small corpus (no LLM calls)
    baselines - Run all baselines with IR metrics (no sufficiency judge)
    full      - Full evaluation including LLM sufficiency judge

Requires prepared corpus (run scripts/prepare_corpus.py first).
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from hcr_core.corpus.embedder import ChunkEmbedder, EmbeddingCache
from hcr_core.types.corpus import Chunk
from hcr_core.types.metrics import BenchmarkResult
from hcr_core.types.query import Query
from tests.benchmark.baselines import RetrievalBaseline
from tests.benchmark.baselines.bm25_baseline import BM25Baseline
from tests.benchmark.baselines.flat_ce_baseline import FlatCrossEncoderBaseline
from tests.benchmark.baselines.hybrid_baseline import HybridBaseline
from tests.benchmark.eval.ir_metrics import mrr, ndcg_at_k, recall_at_k
from tests.benchmark.queries.suite import QuerySuite

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def load_chunks(corpus_dir: Path) -> list[Chunk]:
    """Load prepared chunks from corpus directory."""
    chunks_path = corpus_dir / "chunks.json"
    if not chunks_path.exists():
        raise FileNotFoundError(
            f"No chunks found at {chunks_path}. "
            "Run scripts/prepare_corpus.py first."
        )
    data = json.loads(chunks_path.read_text())
    return [Chunk(**item) for item in data]


def load_or_compute_embeddings(
    chunks: list[Chunk],
    cache_dir: Path,
    corpus_key: str = "benchmark",
) -> tuple[list[str], NDArray[np.float32]]:
    """Load cached embeddings or compute fresh ones."""
    cache = EmbeddingCache(cache_dir)
    embedder = ChunkEmbedder(cache=cache)

    cached = cache.load(corpus_key)
    if cached is not None:
        logger.info(
            "Loaded cached embeddings for %d chunks", len(cached[0])
        )
        return cached

    logger.info("Computing embeddings for %d chunks...", len(chunks))
    start = time.time()
    chunk_ids, embeddings = embedder.embed(chunks, corpus_key=corpus_key)
    elapsed = time.time() - start
    logger.info("Embeddings computed in %.1fs", elapsed)
    return chunk_ids, embeddings


def evaluate_baseline(
    baseline: RetrievalBaseline,
    queries: list[Query],
    corpus_size: int,
    token_budget: int = 400,
) -> BenchmarkResult:
    """Evaluate a single baseline and return metrics.

    IR metrics (nDCG@10, Recall@10, MRR) are computed on the full ranked
    list from baseline.rank(), NOT on the token-packed result. Token
    efficiency (mean_tokens_used) is computed on the packed result from
    baseline.retrieve().
    """
    all_ranked_ids: list[list[str]] = []
    total_tokens = 0.0

    for query in queries:
        # Full ranked list for IR metrics
        ranked = baseline.rank(query.text, top_k=50)
        all_ranked_ids.append([chunk_id for chunk_id, _ in ranked])

        # Token-packed result for budget metrics
        packed = baseline.retrieve(query.text, token_budget)
        total_tokens += sum(c.token_count for c in packed)

    n = len(queries)
    mean_tokens = total_tokens / n if n > 0 else 0.0

    ndcg_scores: list[float] = []
    recall_scores: list[float] = []
    mrr_scores: list[float] = []

    for query, ranked_ids in zip(queries, all_ranked_ids, strict=True):
        relevant = set(query.gold_chunk_ids)
        ndcg_scores.append(ndcg_at_k(ranked_ids, relevant, k=10))
        recall_scores.append(recall_at_k(ranked_ids, relevant, k=10))
        mrr_scores.append(mrr(ranked_ids, relevant))

    return BenchmarkResult(
        system_name=baseline.name,
        corpus_size=corpus_size,
        query_count=n,
        epsilon_per_level=[],
        sufficiency_at_400=0.0,
        ndcg_at_10=sum(ndcg_scores) / n if n > 0 else 0.0,
        recall_at_10=sum(recall_scores) / n if n > 0 else 0.0,
        mrr=sum(mrr_scores) / n if n > 0 else 0.0,
        mean_tokens_used=mean_tokens,
    )


def _log_retrieval(name: str, result: list[Chunk]) -> None:
    """Log retrieval results."""
    tokens = sum(c.token_count for c in result)
    logger.info(
        "%s retrieved %d chunks, %d tokens", name, len(result), tokens
    )


def run_sanity(
    chunks: list[Chunk],
    embeddings: NDArray[np.float32],
    embedder: ChunkEmbedder,
) -> None:
    """Quick sanity check: build indexes, run a query, verify pipeline."""
    logger.info("=== SANITY CHECK ===")
    logger.info("Corpus: %d chunks", len(chunks))

    test_query = "company values and culture"

    logger.info("Building BM25 baseline...")
    bm25 = BM25Baseline(chunks)
    _log_retrieval("BM25", bm25.retrieve(test_query, token_budget=400))

    logger.info("Building hybrid baseline...")
    hybrid = HybridBaseline(chunks, embeddings, embedder=embedder)
    _log_retrieval(
        "Hybrid", hybrid.retrieve(test_query, token_budget=400)
    )

    logger.info("Building flat+CE baseline...")
    flat_ce = FlatCrossEncoderBaseline(
        chunks, embeddings, embedder=embedder
    )
    _log_retrieval(
        "Flat+CE", flat_ce.retrieve(test_query, token_budget=400)
    )

    logger.info("=== SANITY CHECK PASSED ===")
    logger.info("All three baselines operational.")


def _log_baseline_result(
    name: str, result: BenchmarkResult, elapsed: float
) -> None:
    """Log baseline evaluation result."""
    logger.info(
        "%s: nDCG@10=%.4f, Recall@10=%.4f, MRR=%.4f, "
        "mean_tokens=%.0f (%.1fs)",
        name,
        result.ndcg_at_10,
        result.recall_at_10,
        result.mrr,
        result.mean_tokens_used,
        elapsed,
    )


def run_baselines(
    chunks: list[Chunk],
    embeddings: NDArray[np.float32],
    embedder: ChunkEmbedder,
    queries: list[Query],
    results_dir: Path,
) -> list[BenchmarkResult]:
    """Run all baselines with IR metrics (no LLM judge)."""
    logger.info("=== BASELINE EVALUATION ===")
    logger.info("Corpus: %d chunks, Queries: %d", len(chunks), len(queries))

    results: list[BenchmarkResult] = []

    # BM25
    logger.info("Evaluating BM25...")
    bm25 = BM25Baseline(chunks)
    start = time.time()
    bm25_result = evaluate_baseline(bm25, queries, len(chunks))
    _log_baseline_result("BM25", bm25_result, time.time() - start)
    results.append(bm25_result)

    # Hybrid
    logger.info("Evaluating Hybrid (BM25+Vector RRF)...")
    hybrid = HybridBaseline(chunks, embeddings, embedder=embedder)
    start = time.time()
    hybrid_result = evaluate_baseline(hybrid, queries, len(chunks))
    _log_baseline_result("Hybrid", hybrid_result, time.time() - start)
    results.append(hybrid_result)

    # Flat+CE (kill baseline)
    logger.info("Evaluating Flat+CE (kill baseline)...")
    flat_ce = FlatCrossEncoderBaseline(
        chunks, embeddings, embedder=embedder
    )
    start = time.time()
    ce_result = evaluate_baseline(flat_ce, queries, len(chunks))
    _log_baseline_result("Flat+CE", ce_result, time.time() - start)
    results.append(ce_result)

    # Save results
    results_dir.mkdir(parents=True, exist_ok=True)
    output_path = results_dir / "baseline_results.json"
    data = [r.model_dump() for r in results]
    output_path.write_text(json.dumps(data, indent=2))
    logger.info("Results saved to %s", output_path)

    # Print comparison table
    print("\n" + "=" * 70)
    fmt = "{:<15} {:>10} {:>10} {:>10} {:>10}"
    print(fmt.format("System", "nDCG@10", "Recall@10", "MRR", "MeanTok"))
    print("-" * 70)
    for r in results:
        print(fmt.format(
            r.system_name,
            f"{r.ndcg_at_10:.4f}",
            f"{r.recall_at_10:.4f}",
            f"{r.mrr:.4f}",
            f"{r.mean_tokens_used:.0f}",
        ))
    print("=" * 70)

    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run HCR benchmark evaluation"
    )
    parser.add_argument(
        "--mode",
        choices=["sanity", "baselines", "full"],
        default="sanity",
        help="Evaluation mode.",
    )
    parser.add_argument(
        "--corpus-dir",
        type=str,
        default="benchmark/corpus",
        help="Directory containing prepared corpus.",
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        default="benchmark/embeddings",
        help="Directory for embedding cache.",
    )
    parser.add_argument(
        "--results-dir",
        type=str,
        default="benchmark/results",
        help="Directory for results output.",
    )
    parser.add_argument(
        "--queries-path",
        type=str,
        default="benchmark/queries/queries.json",
        help="Path to query suite JSON.",
    )
    parser.add_argument(
        "--max-chunks",
        type=int,
        default=None,
        help="Limit chunks for testing (None = use all).",
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    corpus_dir = project_root / args.corpus_dir
    cache_dir = project_root / args.cache_dir
    results_dir = project_root / args.results_dir

    # Load corpus
    chunks = load_chunks(corpus_dir)
    if args.max_chunks:
        chunks = chunks[: args.max_chunks]
    logger.info("Loaded %d chunks", len(chunks))

    # Compute/load embeddings
    embedder = ChunkEmbedder(cache=EmbeddingCache(cache_dir))
    corpus_key = f"benchmark-{len(chunks)}"
    _, embeddings = load_or_compute_embeddings(
        chunks, cache_dir, corpus_key=corpus_key
    )

    if args.mode == "sanity":
        run_sanity(chunks, embeddings, embedder)
        return

    # Load queries for baselines/full mode
    queries_path = project_root / args.queries_path
    if not queries_path.exists():
        logger.error(
            "No query suite found at %s. Generate queries first.",
            queries_path,
        )
        sys.exit(1)

    suite = QuerySuite.load(queries_path)
    logger.info("Loaded %d queries", len(suite))

    if args.mode == "baselines":
        run_baselines(
            chunks, embeddings, embedder, suite.queries, results_dir
        )
    elif args.mode == "full":
        logger.error(
            "Full mode with LLM judge not yet implemented. "
            "Use --mode baselines."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()

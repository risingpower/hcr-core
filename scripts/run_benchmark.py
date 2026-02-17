"""Run HCR benchmark evaluation.

Usage:
    python scripts/run_benchmark.py [--mode sanity|baselines|hcr|failfast|full]
           [--scale small|medium|large]
           [--tree-depth N] [--tree-branching N]

Modes:
    sanity    - Quick pipeline validation on small corpus (no LLM calls)
    baselines - Run all baselines with IR metrics (no sufficiency judge)
    hcr       - Build HCR tree, evaluate HCR vs baselines, compute epsilon + tree quality
    failfast  - RB-006 kill sequence: topology → epsilon → HCR vs flat+CE → token curves → full
    full      - Full evaluation including LLM sufficiency judge

Scales:
    small  - Phase A corpus (benchmark/corpus, ~315 chunks)
    medium - Full GitLab handbook (benchmark/corpus-medium, ~13-25K chunks)
    large  - GitLab + Wikipedia (benchmark/corpus-large, ~60K chunks)

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
from hcr_core.llm.claude import ClaudeClient
from hcr_core.scoring.cross_encoder import CrossEncoderScorer
from hcr_core.tree.builder import TreeBuilder
from hcr_core.types.corpus import Chunk
from hcr_core.types.metrics import BenchmarkResult, EpsilonMeasurement
from hcr_core.types.query import Query
from hcr_core.types.tree import HCRTree
from tests.benchmark.baselines import RetrievalBaseline
from tests.benchmark.baselines.bm25_baseline import BM25Baseline
from tests.benchmark.baselines.flat_ce_baseline import FlatCrossEncoderBaseline
from tests.benchmark.baselines.hcr_baseline import HCRBaseline
from tests.benchmark.baselines.hybrid_baseline import HybridBaseline
from tests.benchmark.eval.epsilon import compute_epsilon
from tests.benchmark.eval.ir_metrics import mrr, ndcg_at_k, recall_at_k
from tests.benchmark.eval.tree_quality import sibling_distinctiveness
from tests.benchmark.queries.suite import QuerySuite

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Scale-specific directory defaults
SCALE_DIRS: dict[str, dict[str, str]] = {
    "small": {
        "corpus": "benchmark/corpus",
        "embeddings": "benchmark/embeddings",
        "results": "benchmark/results",
        "queries": "benchmark/queries/queries.json",
        "trees": "benchmark/trees",
        "cache": "benchmark/cache",
    },
    "medium": {
        "corpus": "benchmark/corpus-medium",
        "embeddings": "benchmark/embeddings-medium",
        "results": "benchmark/results-medium",
        "queries": "benchmark/queries-medium/queries.json",
        "trees": "benchmark/trees-medium",
        "cache": "benchmark/cache-medium",
    },
    "large": {
        "corpus": "benchmark/corpus-large",
        "embeddings": "benchmark/embeddings-large",
        "results": "benchmark/results-large",
        "queries": "benchmark/queries-large/queries.json",
        "trees": "benchmark/trees-large",
        "cache": "benchmark/cache-large",
    },
}


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
    show_progress = len(chunks) > 1000
    chunk_ids, embeddings = embedder.embed(
        chunks, corpus_key=corpus_key, show_progress=show_progress,
    )
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


def evaluate_hcr(
    hcr_baseline: HCRBaseline,
    queries: list[Query],
    corpus_size: int,
    token_budget: int = 400,
) -> BenchmarkResult:
    """Evaluate HCR baseline, storing beam results for epsilon measurement."""
    all_ranked_ids: list[list[str]] = []
    total_tokens = 0.0

    for query in queries:
        ranked = hcr_baseline.rank(query.text, top_k=50)
        all_ranked_ids.append([chunk_id for chunk_id, _ in ranked])
        hcr_baseline.store_beam_result(query.id)

        packed = hcr_baseline.retrieve(query.text, token_budget)
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
        system_name=hcr_baseline.name,
        corpus_size=corpus_size,
        query_count=n,
        epsilon_per_level=[],
        sufficiency_at_400=0.0,
        ndcg_at_10=sum(ndcg_scores) / n if n > 0 else 0.0,
        recall_at_10=sum(recall_scores) / n if n > 0 else 0.0,
        mrr=sum(mrr_scores) / n if n > 0 else 0.0,
        mean_tokens_used=mean_tokens,
    )


def _build_or_load_tree(
    chunks: list[Chunk],
    embeddings: NDArray[np.float32],
    embedder: ChunkEmbedder,
    tree_cache_path: Path,
    tree_depth: int,
    tree_branching: int,
    compact_json: bool = False,
) -> HCRTree:
    """Build HCR tree or load from cache."""
    if tree_cache_path.exists():
        logger.info("Loading cached tree from %s", tree_cache_path)
        return HCRTree.model_validate_json(tree_cache_path.read_text())

    logger.info("Building HCR tree (LLM calls for routing summaries)...")
    llm = ClaudeClient(model="claude-3-5-haiku-20241022")
    builder = TreeBuilder(
        embedder=embedder,
        llm=llm,
        depth=tree_depth,
        branching=tree_branching,
    )
    start = time.time()
    tree = builder.build(chunks, embeddings)
    elapsed = time.time() - start
    logger.info(
        "Tree built in %.1fs: %d nodes, depth=%d",
        elapsed,
        len(tree.nodes),
        tree.depth,
    )
    # Cache tree
    tree_cache_path.parent.mkdir(parents=True, exist_ok=True)
    indent = None if compact_json else 2
    tree_cache_path.write_text(tree.model_dump_json(indent=indent))
    logger.info("Tree cached to %s", tree_cache_path)
    return tree


def _reembed_summaries(
    tree: HCRTree,
    embedder: ChunkEmbedder,
) -> None:
    """Re-embed tree node summaries with enriched text."""
    from hcr_core.tree.builder import summary_to_text

    reembed_count = 0
    for node in tree.nodes.values():
        if node.summary is not None:
            new_emb = embedder.embed_text(summary_to_text(node.summary))
            node.summary_embedding = list(new_emb.tolist())
            reembed_count += 1
    logger.info("Re-embedded %d node summaries with enriched text", reembed_count)


def _compute_tree_quality(
    tree: HCRTree,
) -> float:
    """Compute and log tree quality metrics. Returns sibling distinctiveness."""
    node_embeddings: dict[str, NDArray[np.float32]] = {}
    for node_id, node in tree.nodes.items():
        if node.summary_embedding is not None:
            node_embeddings[node_id] = np.array(
                node.summary_embedding, dtype=np.float32
            )

    sd = sibling_distinctiveness(tree, node_embeddings)
    logger.info("Sibling distinctiveness: %.4f (kill < 0.15)", sd)

    leaf_count = sum(1 for n in tree.nodes.values() if n.is_leaf)
    internal_count = len(tree.nodes) - leaf_count
    root = tree.nodes[tree.root_id]
    branch_count = len(root.child_ids)
    logger.info(
        "Tree: %d leaves, %d internal nodes, %d branches at root",
        leaf_count,
        internal_count,
        branch_count,
    )

    if sd < 0.15:
        logger.warning(
            "KILL: Sibling distinctiveness %.4f < 0.15 — tree is too "
            "homogeneous for effective routing",
            sd,
        )

    return sd


def run_hcr(
    chunks: list[Chunk],
    embeddings: NDArray[np.float32],
    embedder: ChunkEmbedder,
    queries: list[Query],
    results_dir: Path,
    tree_cache_path: Path | None = None,
    tree_depth: int = 3,
    tree_branching: int = 8,
    compact_json: bool = False,
) -> None:
    """Build HCR tree, evaluate against baselines, compute epsilon + tree quality."""
    logger.info("=== HCR EVALUATION ===")
    logger.info("Corpus: %d chunks, Queries: %d", len(chunks), len(queries))

    # Step 1: Build or load tree
    tree_path = tree_cache_path or (results_dir / "hcr_tree.json")
    tree = _build_or_load_tree(
        chunks, embeddings, embedder, tree_path,
        tree_depth, tree_branching, compact_json,
    )

    # Re-embed summaries with enriched text
    _reembed_summaries(tree, embedder)

    # Step 2: Tree quality metrics
    sd = _compute_tree_quality(tree)

    # Step 3: Evaluate HCR
    logger.info("Evaluating HCR (dual-path: beam + collapsed)...")
    cross_encoder = CrossEncoderScorer()
    hcr_baseline = HCRBaseline(
        tree=tree,
        chunks=chunks,
        embeddings=embeddings,
        embedder=embedder,
        cross_encoder=cross_encoder,
    )

    start = time.time()
    hcr_result = evaluate_hcr(hcr_baseline, queries, len(chunks))
    elapsed = time.time() - start
    _log_baseline_result("HCR", hcr_result, elapsed)

    # Step 4: Compute epsilon (per-level routing accuracy)
    epsilon_measurements = compute_epsilon(
        tree, queries, hcr_baseline.beam_results
    )
    hcr_result.epsilon_per_level = epsilon_measurements
    for em in epsilon_measurements:
        logger.info(
            "Epsilon at level %d: %.4f (%d/%d correct)",
            em.level,
            em.epsilon,
            em.correct_branch_in_beam,
            em.queries_evaluated,
        )

    # Step 5: Per-query results for HCR
    per_query_hcr: list[dict[str, object]] = []
    for query in queries:
        ranked = hcr_baseline.rank(query.text, top_k=50)
        ranked_ids = [cid for cid, _ in ranked]
        relevant = set(query.gold_chunk_ids)
        packed = hcr_baseline.retrieve(query.text, 400)
        per_query_hcr.append({
            "query_id": query.id,
            "query_text": query.text,
            "category": (
                query.category.value
                if hasattr(query.category, "value")
                else str(query.category)
            ),
            "ndcg_at_10": ndcg_at_k(ranked_ids, relevant, k=10),
            "recall_at_10": recall_at_k(ranked_ids, relevant, k=10),
            "mrr": mrr(ranked_ids, relevant),
            "tokens_used": sum(c.token_count for c in packed),
            "chunks_retrieved": len(ranked),
        })

    # Step 6: Save results
    results_dir.mkdir(parents=True, exist_ok=True)
    hcr_output = results_dir / "hcr_results.json"
    hcr_output.write_text(json.dumps(hcr_result.model_dump(), indent=2))
    logger.info("HCR results saved to %s", hcr_output)

    per_query_path = results_dir / "hcr_per_query_results.json"
    per_query_path.write_text(json.dumps(per_query_hcr, indent=2))
    logger.info("Per-query HCR results saved to %s", per_query_path)

    # Step 7: Comparison table (load baseline results if available)
    _print_comparison_table(results_dir, hcr_result, epsilon_measurements, sd)


def run_failfast(
    chunks: list[Chunk],
    embeddings: NDArray[np.float32],
    embedder: ChunkEmbedder,
    queries: list[Query],
    results_dir: Path,
    tree_depth: int = 4,
    tree_branching: int = 8,
    compact_json: bool = True,
) -> None:
    """RB-006 fail-fast kill sequence for scale evaluation.

    Steps:
        1. Tree topology check (sibling distinctiveness > 0.15)
        2. Epsilon check on 50 easy queries (epsilon <= 0.05 at L1)
        3. HCR vs flat+CE on 100 queries
        4. Token efficiency curves
        5. Full evaluation
    """
    logger.info("=== FAIL-FAST EVALUATION (RB-006) ===")
    logger.info("Corpus: %d chunks, Queries: %d", len(chunks), len(queries))

    # Step 1: Build tree and check topology
    logger.info("--- Step 1/5: Tree topology check ---")
    tree_path = results_dir / "hcr_tree.json"
    tree = _build_or_load_tree(
        chunks, embeddings, embedder, tree_path,
        tree_depth, tree_branching, compact_json,
    )
    _reembed_summaries(tree, embedder)
    sd = _compute_tree_quality(tree)
    if sd < 0.15:
        logger.error("KILL at step 1: Sibling distinctiveness %.4f < 0.15", sd)
        _save_failfast_result(results_dir, "KILLED", "step_1_topology", sd=sd)
        return
    logger.info("Step 1 PASSED: SD=%.4f", sd)

    # Step 2: Epsilon check on 50 easy queries
    logger.info("--- Step 2/5: Epsilon check (50 easy queries) ---")
    easy_queries = [q for q in queries if q.difficulty.value == "easy"][:50]
    if len(easy_queries) < 10:
        logger.warning(
            "Only %d easy queries available, using all queries subset",
            len(easy_queries),
        )
        easy_queries = queries[:50]

    cross_encoder = CrossEncoderScorer()
    hcr_baseline = HCRBaseline(
        tree=tree,
        chunks=chunks,
        embeddings=embeddings,
        embedder=embedder,
        cross_encoder=cross_encoder,
    )

    for query in easy_queries:
        hcr_baseline.rank(query.text, top_k=50)
        hcr_baseline.store_beam_result(query.id)

    epsilon_measurements = compute_epsilon(
        tree, easy_queries, hcr_baseline.beam_results
    )
    l1_epsilon = next(
        (em.epsilon for em in epsilon_measurements if em.level == 1), 1.0
    )
    logger.info("L1 epsilon on easy queries: %.4f (kill > 0.05)", l1_epsilon)
    if l1_epsilon > 0.05:
        logger.warning(
            "Step 2 WARNING: L1 epsilon %.4f > 0.05. "
            "Routing at level 1 is poor, but continuing...",
            l1_epsilon,
        )
    else:
        logger.info("Step 2 PASSED: L1 epsilon=%.4f", l1_epsilon)

    # Step 3: HCR vs flat+CE on first 100 queries
    logger.info("--- Step 3/5: HCR vs Flat+CE (100 queries) ---")
    eval_queries = queries[:100]

    # Reset beam results for clean eval
    hcr_baseline.beam_results.clear()
    start = time.time()
    hcr_result = evaluate_hcr(hcr_baseline, eval_queries, len(chunks))
    hcr_elapsed = time.time() - start
    _log_baseline_result("HCR (100q)", hcr_result, hcr_elapsed)

    flat_ce = FlatCrossEncoderBaseline(chunks, embeddings, embedder=embedder)
    start = time.time()
    ce_result = evaluate_baseline(flat_ce, eval_queries, len(chunks))
    ce_elapsed = time.time() - start
    _log_baseline_result("Flat+CE (100q)", ce_result, ce_elapsed)

    ndcg_delta = hcr_result.ndcg_at_10 - ce_result.ndcg_at_10
    token_delta = hcr_result.mean_tokens_used - ce_result.mean_tokens_used
    logger.info(
        "HCR vs Flat+CE: nDCG delta=%+.4f, token delta=%+.0f",
        ndcg_delta,
        token_delta,
    )
    if ndcg_delta < -0.15:
        logger.error(
            "KILL at step 3: HCR nDCG %.4f is %.4f below Flat+CE — "
            "too far behind at this corpus size",
            hcr_result.ndcg_at_10,
            abs(ndcg_delta),
        )
        _save_failfast_result(
            results_dir, "KILLED", "step_3_ndcg",
            sd=sd, hcr_ndcg=hcr_result.ndcg_at_10,
            ce_ndcg=ce_result.ndcg_at_10, delta=ndcg_delta,
        )
        return
    logger.info("Step 3 PASSED: delta=%.4f (within tolerance)", ndcg_delta)

    # Step 4: Token efficiency
    logger.info("--- Step 4/5: Token efficiency ---")
    logger.info(
        "HCR: %.0f tokens avg, Flat+CE: %.0f tokens avg, saving: %.0f tokens",
        hcr_result.mean_tokens_used,
        ce_result.mean_tokens_used,
        ce_result.mean_tokens_used - hcr_result.mean_tokens_used,
    )

    # Step 5: Full evaluation on all queries
    logger.info("--- Step 5/5: Full evaluation (%d queries) ---", len(queries))
    hcr_baseline.beam_results.clear()
    start = time.time()
    full_hcr_result = evaluate_hcr(hcr_baseline, queries, len(chunks))
    full_elapsed = time.time() - start
    _log_baseline_result("HCR (full)", full_hcr_result, full_elapsed)

    full_epsilon = compute_epsilon(tree, queries, hcr_baseline.beam_results)
    full_hcr_result.epsilon_per_level = full_epsilon

    # Full baselines
    bm25 = BM25Baseline(chunks)
    bm25_result = evaluate_baseline(bm25, queries, len(chunks))
    hybrid = HybridBaseline(chunks, embeddings, embedder=embedder)
    hybrid_result = evaluate_baseline(hybrid, queries, len(chunks))
    full_ce_result = evaluate_baseline(flat_ce, queries, len(chunks))

    # Save all results
    results_dir.mkdir(parents=True, exist_ok=True)
    all_results = [bm25_result, hybrid_result, full_ce_result, full_hcr_result]
    results_path = results_dir / "failfast_results.json"
    results_path.write_text(json.dumps(
        [r.model_dump() for r in all_results], indent=2,
    ))
    logger.info("Full results saved to %s", results_path)

    _save_failfast_result(
        results_dir, "PASSED", "complete",
        sd=sd,
        hcr_ndcg=full_hcr_result.ndcg_at_10,
        ce_ndcg=full_ce_result.ndcg_at_10,
        delta=full_hcr_result.ndcg_at_10 - full_ce_result.ndcg_at_10,
        l1_epsilon=l1_epsilon,
    )

    # Print final table
    print("\n" + "=" * 80)
    fmt = "{:<15} {:>10} {:>10} {:>10} {:>10}"
    print(fmt.format("System", "nDCG@10", "Recall@10", "MRR", "MeanTok"))
    print("-" * 80)
    for r in all_results:
        print(fmt.format(
            r.system_name,
            f"{r.ndcg_at_10:.4f}",
            f"{r.recall_at_10:.4f}",
            f"{r.mrr:.4f}",
            f"{r.mean_tokens_used:.0f}",
        ))
    print("-" * 80)
    delta = full_hcr_result.ndcg_at_10 - full_ce_result.ndcg_at_10
    print(f"\nHCR vs Flat+CE: nDCG delta={delta:+.4f}")
    if full_epsilon:
        print("\nPer-level epsilon:")
        for em in full_epsilon:
            print(f"  Level {em.level}: ε={em.epsilon:.4f}")
    print(f"\nSibling distinctiveness: {sd:.4f}")
    print("=" * 80)


def _save_failfast_result(
    results_dir: Path,
    outcome: str,
    stopped_at: str,
    **kwargs: object,
) -> None:
    """Save failfast outcome summary."""
    results_dir.mkdir(parents=True, exist_ok=True)
    result: dict[str, object] = {
        "outcome": outcome,
        "stopped_at": stopped_at,
        **kwargs,
    }
    path = results_dir / "failfast_outcome.json"
    path.write_text(json.dumps(result, indent=2))
    logger.info("Failfast outcome saved to %s: %s at %s", path, outcome, stopped_at)


def _print_comparison_table(
    results_dir: Path,
    hcr_result: BenchmarkResult,
    epsilon_measurements: list[EpsilonMeasurement],
    sd: float,
) -> None:
    """Print comparison table with all available results."""

    baseline_path = results_dir / "baseline_results.json"
    all_results = []
    if baseline_path.exists():
        baseline_data = json.loads(baseline_path.read_text())
        for bd in baseline_data:
            all_results.append(BenchmarkResult(**bd))
    all_results.append(hcr_result)

    print("\n" + "=" * 80)
    fmt = "{:<15} {:>10} {:>10} {:>10} {:>10}"
    print(fmt.format("System", "nDCG@10", "Recall@10", "MRR", "MeanTok"))
    print("-" * 80)
    for r in all_results:
        print(fmt.format(
            r.system_name,
            f"{r.ndcg_at_10:.4f}",
            f"{r.recall_at_10:.4f}",
            f"{r.mrr:.4f}",
            f"{r.mean_tokens_used:.0f}",
        ))
    print("-" * 80)

    # Delta vs kill baseline
    ce_ndcg = next(
        (r.ndcg_at_10 for r in all_results if r.system_name == "flat-ce"),
        None,
    )
    if ce_ndcg is not None:
        delta = hcr_result.ndcg_at_10 - ce_ndcg
        token_delta = hcr_result.mean_tokens_used - next(
            r.mean_tokens_used for r in all_results if r.system_name == "flat-ce"
        )
        print("\nHCR vs Flat+CE (kill baseline):")
        print(f"  nDCG@10 delta: {delta:+.4f} ({'WIN' if delta > 0 else 'LOSE'})")
        print(f"  Token delta:   {token_delta:+.0f}")

    # Epsilon summary
    if epsilon_measurements:
        print("\nPer-level routing accuracy (epsilon, lower=better):")
        for em in epsilon_measurements:
            print(f"  Level {em.level}: ε={em.epsilon:.4f}")

    # Tree quality
    print("\nTree quality:")
    print(f"  Sibling distinctiveness: {sd:.4f} (kill < 0.15)")
    print("=" * 80)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run HCR benchmark evaluation"
    )
    parser.add_argument(
        "--mode",
        choices=["sanity", "baselines", "hcr", "failfast", "full"],
        default="sanity",
        help="Evaluation mode.",
    )
    parser.add_argument(
        "--scale",
        choices=["small", "medium", "large"],
        default="small",
        help="Corpus scale (sets default directories).",
    )
    parser.add_argument(
        "--corpus-dir",
        type=str,
        default=None,
        help="Directory containing prepared corpus (overrides --scale default).",
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        default=None,
        help="Directory for embedding cache (overrides --scale default).",
    )
    parser.add_argument(
        "--results-dir",
        type=str,
        default=None,
        help="Directory for results output (overrides --scale default).",
    )
    parser.add_argument(
        "--queries-path",
        type=str,
        default=None,
        help="Path to query suite JSON (overrides --scale default).",
    )
    parser.add_argument(
        "--tree-depth",
        type=int,
        default=None,
        help="Tree depth for HCR. Default: 3 (small), 4 (medium/large).",
    )
    parser.add_argument(
        "--tree-branching",
        type=int,
        default=8,
        help="Tree branching factor for HCR.",
    )
    parser.add_argument(
        "--max-chunks",
        type=int,
        default=None,
        help="Limit chunks for testing (None = use all).",
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    scale_dirs = SCALE_DIRS[args.scale]

    # Resolve directories with scale defaults, CLI overrides take precedence
    corpus_dir = project_root / (args.corpus_dir or scale_dirs["corpus"])
    cache_dir = project_root / (args.cache_dir or scale_dirs["embeddings"])
    results_dir = project_root / (args.results_dir or scale_dirs["results"])
    queries_path = project_root / (args.queries_path or scale_dirs["queries"])

    # Default tree depth: 3 for small, 4 for medium/large
    tree_depth = args.tree_depth
    if tree_depth is None:
        tree_depth = 3 if args.scale == "small" else 4

    # Use compact JSON for medium/large to save disk space
    compact_json = args.scale != "small"

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

    # Load queries for baselines/hcr/failfast/full modes
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
    elif args.mode == "hcr":
        run_hcr(
            chunks, embeddings, embedder, suite.queries, results_dir,
            tree_depth=tree_depth, tree_branching=args.tree_branching,
            compact_json=compact_json,
        )
    elif args.mode == "failfast":
        run_failfast(
            chunks, embeddings, embedder, suite.queries, results_dir,
            tree_depth=tree_depth, tree_branching=args.tree_branching,
            compact_json=compact_json,
        )
    elif args.mode == "full":
        logger.error(
            "Full mode with LLM judge not yet implemented. "
            "Use --mode baselines."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()

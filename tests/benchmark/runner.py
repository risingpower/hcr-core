"""Benchmark runner: orchestrates full evaluation of retrieval systems."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from hcr_core.types.metrics import BenchmarkResult
from hcr_core.types.query import Query
from tests.benchmark.baselines import RetrievalBaseline
from tests.benchmark.eval.ir_metrics import mrr, ndcg_at_k, recall_at_k
from tests.benchmark.eval.sufficiency import SufficiencyJudge


@dataclass
class RunConfig:
    """Configuration for a benchmark run."""

    budgets: list[int] = field(default_factory=lambda: [200, 400, 600, 800, 1200, 10000])
    top_k_eval: int = 10
    results_dir: Path = field(default_factory=lambda: Path("benchmark/results"))


class BenchmarkRunner:
    """Orchestrates benchmark evaluation for one or more retrieval systems."""

    def __init__(
        self,
        config: RunConfig,
        baselines: list[RetrievalBaseline],
        judge: SufficiencyJudge,
        corpus_size: int = 1,
    ) -> None:
        self._config = config
        self._baselines = baselines
        self._judge = judge
        self._corpus_size = corpus_size

    def run(
        self,
        queries: list[Query],
        gold_chunk_map: dict[str, set[str]] | None = None,
    ) -> list[BenchmarkResult]:
        """Run all baselines against the query set and compute metrics."""
        results: list[BenchmarkResult] = []

        for baseline in self._baselines:
            result = self._evaluate_baseline(baseline, queries, gold_chunk_map)
            results.append(result)

        return results

    def _evaluate_baseline(
        self,
        baseline: RetrievalBaseline,
        queries: list[Query],
        gold_chunk_map: dict[str, set[str]] | None,
    ) -> BenchmarkResult:
        """Evaluate a single baseline across all queries."""
        budget_400 = 400

        # Sufficiency at 400
        sufficient_count = 0
        all_retrieved_ids: list[list[str]] = []
        total_tokens = 0.0

        for query in queries:
            chunks = baseline.retrieve(query.text, token_budget=budget_400)
            chunk_ids = [c.id for c in chunks]
            all_retrieved_ids.append(chunk_ids)
            total_tokens += sum(c.token_count for c in chunks)

            result = self._judge.evaluate(query, chunks, token_budget=budget_400)
            if result.is_sufficient:
                sufficient_count += 1

        n = len(queries)
        sufficiency_rate = sufficient_count / n if n > 0 else 0.0
        mean_tokens = total_tokens / n if n > 0 else 0.0

        # IR metrics
        if gold_chunk_map is None:
            gold_chunk_map = {q.id: set(q.gold_chunk_ids) for q in queries}

        ndcg_scores: list[float] = []
        recall_scores: list[float] = []
        mrr_scores: list[float] = []

        for query, retrieved_ids in zip(queries, all_retrieved_ids, strict=True):
            relevant = gold_chunk_map.get(query.id, set())
            k = self._config.top_k_eval
            ndcg_scores.append(ndcg_at_k(retrieved_ids, relevant, k=k))
            recall_scores.append(recall_at_k(retrieved_ids, relevant, k=k))
            mrr_scores.append(mrr(retrieved_ids, relevant))

        return BenchmarkResult(
            system_name=baseline.name,
            corpus_size=self._corpus_size,
            query_count=n,
            epsilon_per_level=[],  # Only applicable to HCR
            sufficiency_at_400=sufficiency_rate,
            ndcg_at_10=sum(ndcg_scores) / n if n > 0 else 0.0,
            recall_at_10=sum(recall_scores) / n if n > 0 else 0.0,
            mrr=sum(mrr_scores) / n if n > 0 else 0.0,
            mean_tokens_used=mean_tokens,
        )

    def save_results(self, results: list[BenchmarkResult]) -> Path:
        """Save benchmark results to JSON."""
        output_dir = self._config.results_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "benchmark_results.json"
        data = [r.model_dump() for r in results]
        output_path.write_text(json.dumps(data, indent=2))
        return output_path

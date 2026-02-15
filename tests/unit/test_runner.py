"""Tests for benchmark runner."""

from pathlib import Path
from unittest.mock import MagicMock

from hcr_core.types.corpus import Chunk
from hcr_core.types.metrics import SufficiencyResult
from hcr_core.types.query import DifficultyTier, Query, QueryCategory
from tests.benchmark.baselines import RetrievalBaseline
from tests.benchmark.runner import BenchmarkRunner, RunConfig


class MockBaseline(RetrievalBaseline):
    def __init__(self, chunks: list[Chunk]) -> None:
        self._chunks = chunks

    @property
    def name(self) -> str:
        return "mock-baseline"

    def retrieve(self, query: str, token_budget: int) -> list[Chunk]:
        return self._chunks[:2]


def _make_test_data() -> tuple[list[Chunk], list[Query]]:
    chunks = [
        Chunk(id="c1", document_id="d1", content="Python info", token_count=5),
        Chunk(id="c2", document_id="d1", content="Java info", token_count=5),
    ]
    queries = [
        Query(
            id="q1", text="What is Python?",
            category=QueryCategory.SINGLE_BRANCH,
            difficulty=DifficultyTier.EASY,
            gold_chunk_ids=["c1"],
            gold_answer="A programming language.",
        ),
    ]
    return chunks, queries


class TestBenchmarkRunner:
    def test_run_returns_results(self) -> None:
        chunks, queries = _make_test_data()
        baseline = MockBaseline(chunks)

        mock_judge = MagicMock()
        mock_judge.evaluate.return_value = SufficiencyResult(
            query_id="q1", token_budget=400,
            is_sufficient=True, judge_reasoning="Complete answer.",
        )

        config = RunConfig()
        runner = BenchmarkRunner(config, [baseline], mock_judge)
        results = runner.run(queries)

        assert len(results) == 1
        assert results[0].system_name == "mock-baseline"
        assert results[0].query_count == 1
        assert results[0].sufficiency_at_400 == 1.0

    def test_run_multiple_baselines(self) -> None:
        chunks, queries = _make_test_data()
        baseline1 = MockBaseline(chunks)
        baseline2 = MockBaseline(chunks)

        mock_judge = MagicMock()
        mock_judge.evaluate.return_value = SufficiencyResult(
            query_id="q1", token_budget=400,
            is_sufficient=False, judge_reasoning="Insufficient.",
        )

        config = RunConfig()
        runner = BenchmarkRunner(config, [baseline1, baseline2], mock_judge)
        results = runner.run(queries)

        assert len(results) == 2

    def test_save_results(self, tmp_path: Path) -> None:
        chunks, queries = _make_test_data()
        baseline = MockBaseline(chunks)

        mock_judge = MagicMock()
        mock_judge.evaluate.return_value = SufficiencyResult(
            query_id="q1", token_budget=400,
            is_sufficient=True, judge_reasoning="OK",
        )

        config = RunConfig(results_dir=tmp_path / "results")
        runner = BenchmarkRunner(config, [baseline], mock_judge)
        results = runner.run(queries)
        path = runner.save_results(results)
        assert path.exists()

    def test_ir_metrics_computed(self) -> None:
        chunks, queries = _make_test_data()
        baseline = MockBaseline(chunks)

        mock_judge = MagicMock()
        mock_judge.evaluate.return_value = SufficiencyResult(
            query_id="q1", token_budget=400,
            is_sufficient=True, judge_reasoning="OK",
        )

        config = RunConfig()
        runner = BenchmarkRunner(config, [baseline], mock_judge)
        results = runner.run(queries)

        result = results[0]
        # c1 is in gold, and MockBaseline returns c1 and c2
        assert result.ndcg_at_10 > 0
        assert result.recall_at_10 > 0
        assert result.mrr > 0

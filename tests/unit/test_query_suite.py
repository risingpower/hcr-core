"""Tests for query suite management."""

from pathlib import Path

from hcr_core.types.query import DifficultyTier, Query, QueryCategory
from tests.benchmark.queries.suite import QuerySuite


def _make_queries() -> list[Query]:
    return [
        Query(
            id="q1", text="What is Python?", category=QueryCategory.SINGLE_BRANCH,
            difficulty=DifficultyTier.EASY, gold_chunk_ids=["c1"], gold_answer="A language.",
        ),
        Query(
            id="q2", text="Compare Java and Python", category=QueryCategory.COMPARATIVE,
            difficulty=DifficultyTier.MEDIUM, gold_chunk_ids=["c1", "c2"], gold_answer="Both.",
        ),
        Query(
            id="q3", text="Sum all departments", category=QueryCategory.AGGREGATION,
            difficulty=DifficultyTier.HARD, budget_feasible_400=False,
            gold_chunk_ids=["c1"], gold_answer="Many.",
        ),
        Query(
            id="q4", text="What is ML?", category=QueryCategory.SINGLE_BRANCH,
            difficulty=DifficultyTier.EASY, gold_chunk_ids=["c3"], gold_answer="Machine learning.",
        ),
        Query(
            id="q5", text="Timeline of releases", category=QueryCategory.TEMPORAL,
            difficulty=DifficultyTier.MEDIUM, gold_chunk_ids=["c4"], gold_answer="2020-2024.",
        ),
    ]


class TestQuerySuite:
    def test_create_suite(self) -> None:
        suite = QuerySuite(_make_queries())
        assert len(suite) == 5

    def test_save_and_load(self, tmp_path: Path) -> None:
        suite = QuerySuite(_make_queries())
        path = tmp_path / "queries.json"
        suite.save(path)
        loaded = QuerySuite.load(path)
        assert len(loaded) == 5
        assert loaded.queries[0].id == "q1"

    def test_filter_budget_feasible(self) -> None:
        suite = QuerySuite(_make_queries())
        feasible = suite.filter_budget_feasible(True)
        assert len(feasible) == 4  # q3 is budget_infeasible

    def test_filter_category(self) -> None:
        suite = QuerySuite(_make_queries())
        single = suite.filter_category(QueryCategory.SINGLE_BRANCH)
        assert len(single) == 2

    def test_filter_difficulty(self) -> None:
        suite = QuerySuite(_make_queries())
        easy = suite.filter_difficulty(DifficultyTier.EASY)
        assert len(easy) == 2

    def test_split(self) -> None:
        suite = QuerySuite(_make_queries())
        train, dev, test = suite.split(train=0.6, dev=0.2, test=0.2)
        assert len(train) + len(dev) + len(test) == 5

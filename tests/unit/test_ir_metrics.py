"""Tests for standard IR metrics."""

import pytest

from tests.benchmark.eval.ir_metrics import mrr, ndcg_at_k, precision_at_k, recall_at_k


class TestNDCG:
    def test_perfect_ranking(self) -> None:
        # All relevant docs ranked first
        retrieved = ["a", "b", "c"]
        relevant = {"a", "b", "c"}
        score = ndcg_at_k(retrieved, relevant, k=3)
        assert abs(score - 1.0) < 1e-6

    def test_no_relevant(self) -> None:
        retrieved = ["a", "b", "c"]
        relevant: set[str] = set()
        score = ndcg_at_k(retrieved, relevant, k=3)
        assert score == 0.0

    def test_partial_ranking(self) -> None:
        retrieved = ["x", "a", "y", "b"]
        relevant = {"a", "b"}
        score = ndcg_at_k(retrieved, relevant, k=4)
        assert 0.0 < score < 1.0

    def test_empty_retrieved(self) -> None:
        score = ndcg_at_k([], {"a", "b"}, k=5)
        assert score == 0.0


class TestRecall:
    def test_perfect_recall(self) -> None:
        retrieved = ["a", "b", "c"]
        relevant = {"a", "b", "c"}
        assert recall_at_k(retrieved, relevant, k=3) == 1.0

    def test_partial_recall(self) -> None:
        retrieved = ["a", "x", "y"]
        relevant = {"a", "b"}
        assert recall_at_k(retrieved, relevant, k=3) == 0.5

    def test_zero_recall(self) -> None:
        retrieved = ["x", "y"]
        relevant = {"a", "b"}
        assert recall_at_k(retrieved, relevant, k=2) == 0.0

    def test_empty_relevant(self) -> None:
        retrieved = ["a"]
        relevant: set[str] = set()
        assert recall_at_k(retrieved, relevant, k=1) == 0.0


class TestMRR:
    def test_first_result_relevant(self) -> None:
        assert mrr(["a", "b"], {"a"}) == 1.0

    def test_second_result_relevant(self) -> None:
        assert mrr(["x", "a"], {"a"}) == 0.5

    def test_no_relevant(self) -> None:
        assert mrr(["x", "y"], {"a"}) == 0.0


class TestPrecision:
    def test_all_relevant(self) -> None:
        assert precision_at_k(["a", "b"], {"a", "b"}, k=2) == 1.0

    def test_half_relevant(self) -> None:
        assert precision_at_k(["a", "x"], {"a"}, k=2) == 0.5

    def test_none_relevant(self) -> None:
        assert precision_at_k(["x", "y"], {"a"}, k=2) == 0.0

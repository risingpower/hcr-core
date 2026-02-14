"""Tests for scoring components."""

import pytest

from hcr_core.scoring.path_score import path_relevance_ema


class TestPathRelevanceEMA:
    def test_equal_weight(self) -> None:
        result = path_relevance_ema(0.8, 0.6, alpha=0.5)
        assert abs(result - 0.7) < 1e-6

    def test_current_only(self) -> None:
        result = path_relevance_ema(0.8, 0.2, alpha=1.0)
        assert abs(result - 0.8) < 1e-6

    def test_parent_only(self) -> None:
        result = path_relevance_ema(0.8, 0.2, alpha=0.0)
        assert abs(result - 0.2) < 1e-6

    def test_accumulation(self) -> None:
        # Simulate traversal: high scores should accumulate
        score = 1.0
        for level_score in [0.9, 0.85, 0.8]:
            score = path_relevance_ema(level_score, score, alpha=0.5)
        assert 0.5 < score < 1.0

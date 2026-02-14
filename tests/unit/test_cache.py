"""Tests for benchmark caching (judge cache, cross-encoder cache)."""

import json
from pathlib import Path

import pytest

from tests.benchmark.cache.manager import CrossEncoderCache, JudgeCache


class TestJudgeCache:
    def test_save_and_load(self, tmp_path: Path) -> None:
        cache = JudgeCache(cache_dir=tmp_path)
        result = {"is_sufficient": True, "reasoning": "Complete answer."}
        cache.save("q-1", ["c1", "c2"], result)

        loaded = cache.load("q-1", ["c1", "c2"])
        assert loaded is not None
        assert loaded["is_sufficient"] is True

    def test_load_missing_returns_none(self, tmp_path: Path) -> None:
        cache = JudgeCache(cache_dir=tmp_path)
        result = cache.load("q-1", ["c1"])
        assert result is None

    def test_different_chunk_ids_different_key(self, tmp_path: Path) -> None:
        cache = JudgeCache(cache_dir=tmp_path)
        result1 = {"is_sufficient": True, "reasoning": "A"}
        result2 = {"is_sufficient": False, "reasoning": "B"}
        cache.save("q-1", ["c1"], result1)
        cache.save("q-1", ["c2"], result2)

        loaded1 = cache.load("q-1", ["c1"])
        loaded2 = cache.load("q-1", ["c2"])
        assert loaded1 is not None
        assert loaded2 is not None
        assert loaded1["is_sufficient"] is True
        assert loaded2["is_sufficient"] is False

    def test_has_cache(self, tmp_path: Path) -> None:
        cache = JudgeCache(cache_dir=tmp_path)
        assert not cache.has("q-1", ["c1"])
        cache.save("q-1", ["c1"], {"result": True})
        assert cache.has("q-1", ["c1"])


class TestCrossEncoderCache:
    def test_save_and_load(self, tmp_path: Path) -> None:
        cache = CrossEncoderCache(cache_dir=tmp_path)
        cache.save("query text", "c1", 0.95)

        loaded = cache.load("query text", "c1")
        assert loaded is not None
        assert abs(loaded - 0.95) < 1e-6

    def test_load_missing_returns_none(self, tmp_path: Path) -> None:
        cache = CrossEncoderCache(cache_dir=tmp_path)
        result = cache.load("query", "c1")
        assert result is None

    def test_batch_save_and_load(self, tmp_path: Path) -> None:
        cache = CrossEncoderCache(cache_dir=tmp_path)
        scores = {"c1": 0.9, "c2": 0.7, "c3": 0.5}
        cache.save_batch("query text", scores)

        for chunk_id, expected_score in scores.items():
            loaded = cache.load("query text", chunk_id)
            assert loaded is not None
            assert abs(loaded - expected_score) < 1e-6

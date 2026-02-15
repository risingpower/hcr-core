"""Tests for retrieval baselines."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from hcr_core.cache import CrossEncoderCache
from hcr_core.types.corpus import Chunk
from tests.benchmark.baselines import RetrievalBaseline
from tests.benchmark.baselines.bm25_baseline import BM25Baseline
from tests.benchmark.baselines.flat_ce_baseline import FlatCrossEncoderBaseline
from tests.benchmark.baselines.hybrid_baseline import HybridBaseline


def _make_test_chunks() -> list[Chunk]:
    return [
        Chunk(
            id="c1", document_id="d1",
            content="Python is great for machine learning",
            token_count=7,
        ),
        Chunk(
            id="c2", document_id="d1",
            content="Java is used for web development",
            token_count=7,
        ),
        Chunk(
            id="c3", document_id="d1",
            content="Python data science and statistics",
            token_count=6,
        ),
        Chunk(
            id="c4", document_id="d1",
            content="JavaScript frontend React development",
            token_count=5,
        ),
        Chunk(
            id="c5", document_id="d1",
            content="Deep learning with neural networks in Python",
            token_count=8,
        ),
    ]


def _make_embedder() -> ChunkEmbedder:  # noqa: F821
    from hcr_core.corpus.embedder import ChunkEmbedder

    return ChunkEmbedder(model_name="all-MiniLM-L6-v2")


def _make_embeddings(
    chunks: list[Chunk],
) -> tuple[np.ndarray, ChunkEmbedder]:  # noqa: F821
    from hcr_core.corpus.embedder import ChunkEmbedder

    embedder = ChunkEmbedder(model_name="all-MiniLM-L6-v2")
    _, embs = embedder.embed(chunks)
    return embs, embedder


class TestBM25Baseline:
    def test_is_retrieval_baseline(self) -> None:
        chunks = _make_test_chunks()
        baseline = BM25Baseline(chunks)
        assert isinstance(baseline, RetrievalBaseline)

    def test_name(self) -> None:
        chunks = _make_test_chunks()
        baseline = BM25Baseline(chunks)
        assert baseline.name == "bm25"

    def test_retrieve_returns_chunks(self) -> None:
        chunks = _make_test_chunks()
        baseline = BM25Baseline(chunks)
        results = baseline.retrieve("python machine learning", token_budget=100)
        assert len(results) > 0
        for chunk in results:
            assert isinstance(chunk, Chunk)

    def test_retrieve_respects_token_budget(self) -> None:
        chunks = _make_test_chunks()
        baseline = BM25Baseline(chunks)
        results = baseline.retrieve("python", token_budget=15)
        total_tokens = sum(c.token_count for c in results)
        assert total_tokens <= 15

    def test_retrieve_returns_relevant_chunks(self) -> None:
        chunks = _make_test_chunks()
        baseline = BM25Baseline(chunks)
        results = baseline.retrieve("python", token_budget=100)
        result_ids = {c.id for c in results}
        assert "c1" in result_ids or "c3" in result_ids or "c5" in result_ids


class TestHybridBaseline:
    def test_is_retrieval_baseline(self) -> None:
        chunks = _make_test_chunks()
        embeddings, embedder = _make_embeddings(chunks)
        baseline = HybridBaseline(chunks, embeddings, embedder=embedder)
        assert isinstance(baseline, RetrievalBaseline)

    def test_name(self) -> None:
        chunks = _make_test_chunks()
        embeddings, embedder = _make_embeddings(chunks)
        baseline = HybridBaseline(chunks, embeddings, embedder=embedder)
        assert baseline.name == "hybrid-rrf"

    def test_retrieve_returns_chunks(self) -> None:
        chunks = _make_test_chunks()
        embeddings, embedder = _make_embeddings(chunks)
        baseline = HybridBaseline(chunks, embeddings, embedder=embedder)
        results = baseline.retrieve(
            "python machine learning", token_budget=100,
        )
        assert len(results) > 0

    def test_retrieve_respects_token_budget(self) -> None:
        chunks = _make_test_chunks()
        embeddings, embedder = _make_embeddings(chunks)
        baseline = HybridBaseline(chunks, embeddings, embedder=embedder)
        results = baseline.retrieve("python", token_budget=15)
        total_tokens = sum(c.token_count for c in results)
        assert total_tokens <= 15


class TestFlatCrossEncoderBaseline:
    def test_is_retrieval_baseline(self) -> None:
        chunks = _make_test_chunks()
        embeddings, embedder = _make_embeddings(chunks)
        baseline = FlatCrossEncoderBaseline(
            chunks, embeddings, embedder=embedder,
        )
        assert isinstance(baseline, RetrievalBaseline)

    def test_name(self) -> None:
        chunks = _make_test_chunks()
        embeddings, embedder = _make_embeddings(chunks)
        baseline = FlatCrossEncoderBaseline(
            chunks, embeddings, embedder=embedder,
        )
        assert baseline.name == "flat-ce"

    def test_retrieve_returns_chunks(self) -> None:
        chunks = _make_test_chunks()
        embeddings, embedder = _make_embeddings(chunks)
        baseline = FlatCrossEncoderBaseline(
            chunks, embeddings, embedder=embedder,
        )
        results = baseline.retrieve(
            "python machine learning", token_budget=100,
        )
        assert len(results) > 0
        for chunk in results:
            assert isinstance(chunk, Chunk)

    def test_retrieve_respects_token_budget(self) -> None:
        chunks = _make_test_chunks()
        embeddings, embedder = _make_embeddings(chunks)
        baseline = FlatCrossEncoderBaseline(
            chunks, embeddings, embedder=embedder,
        )
        results = baseline.retrieve("python", token_budget=15)
        total_tokens = sum(c.token_count for c in results)
        assert total_tokens <= 15

    def test_cache_stores_and_reuses_scores(self, tmp_path: Path) -> None:
        chunks = _make_test_chunks()
        embeddings, embedder = _make_embeddings(chunks)
        cache = CrossEncoderCache(tmp_path)

        baseline = FlatCrossEncoderBaseline(
            chunks, embeddings, embedder=embedder, ce_cache=cache,
        )

        # First call — populates cache
        results1 = baseline.retrieve("python", token_budget=100)
        assert len(results1) > 0

        # Second call — should use cached scores (verify via cache)
        # Check that scores were cached
        for chunk in chunks:
            score = cache.load("python", chunk.id)
            # At least some chunks should have cached scores
            if score is not None:
                assert isinstance(score, float)
                break
        else:
            raise AssertionError("No scores found in cache after retrieve")

        # Second call should produce same results
        results2 = baseline.retrieve("python", token_budget=100)
        assert [c.id for c in results1] == [c.id for c in results2]

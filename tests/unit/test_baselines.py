"""Tests for retrieval baselines."""

import numpy as np
import pytest

from hcr_core.index.bm25 import BM25Index
from hcr_core.index.hybrid import HybridIndex
from hcr_core.index.vector import VectorIndex
from hcr_core.types.corpus import Chunk
from tests.benchmark.baselines import RetrievalBaseline
from tests.benchmark.baselines.bm25_baseline import BM25Baseline
from tests.benchmark.baselines.hybrid_baseline import HybridBaseline


def _make_test_chunks() -> list[Chunk]:
    return [
        Chunk(id="c1", document_id="d1", content="Python is great for machine learning", token_count=7),
        Chunk(id="c2", document_id="d1", content="Java is used for web development", token_count=7),
        Chunk(id="c3", document_id="d1", content="Python data science and statistics", token_count=6),
        Chunk(id="c4", document_id="d1", content="JavaScript frontend React development", token_count=5),
        Chunk(id="c5", document_id="d1", content="Deep learning with neural networks in Python", token_count=8),
    ]


def _make_embedder() -> "ChunkEmbedder":
    from hcr_core.corpus.embedder import ChunkEmbedder

    return ChunkEmbedder(model_name="all-MiniLM-L6-v2")


def _make_embeddings(
    chunks: list[Chunk],
) -> tuple[np.ndarray[tuple[int, int], np.dtype[np.float32]], "ChunkEmbedder"]:
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
        results = baseline.retrieve("python machine learning", token_budget=100)
        assert len(results) > 0

    def test_retrieve_respects_token_budget(self) -> None:
        chunks = _make_test_chunks()
        embeddings, embedder = _make_embeddings(chunks)
        baseline = HybridBaseline(chunks, embeddings, embedder=embedder)
        results = baseline.retrieve("python", token_budget=15)
        total_tokens = sum(c.token_count for c in results)
        assert total_tokens <= 15

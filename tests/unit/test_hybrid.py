"""Tests for hybrid index (RRF fusion)."""

import numpy as np

from hcr_core.index.bm25 import BM25Index
from hcr_core.index.hybrid import HybridIndex
from hcr_core.index.vector import VectorIndex
from hcr_core.types.corpus import Chunk


def _make_chunks() -> list[Chunk]:
    return [
        Chunk(id="c1", document_id="d1", content="python machine learning", token_count=3),
        Chunk(id="c2", document_id="d1", content="java web development", token_count=3),
        Chunk(id="c3", document_id="d1", content="python data science", token_count=3),
    ]


def _make_hybrid_index(
    chunks: list[Chunk], embeddings: np.ndarray[tuple[int, int], np.dtype[np.float32]]
) -> HybridIndex:
    bm25 = BM25Index(chunks)
    chunk_ids = [c.id for c in chunks]
    vector = VectorIndex(embeddings, chunk_ids)
    return HybridIndex(bm25=bm25, vector=vector)


class TestHybridIndex:
    def test_search_returns_results(self) -> None:
        chunks = _make_chunks()
        embeddings = np.random.rand(3, 4).astype(np.float32)
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / norms
        index = _make_hybrid_index(chunks, embeddings)
        query_emb = np.random.rand(4).astype(np.float32)
        query_emb = query_emb / np.linalg.norm(query_emb)
        results = index.search("python", query_emb, top_k=2)
        assert len(results) > 0
        assert len(results) <= 2

    def test_search_returns_chunk_id_score_tuples(self) -> None:
        chunks = _make_chunks()
        embeddings = np.random.rand(3, 4).astype(np.float32)
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / norms
        index = _make_hybrid_index(chunks, embeddings)
        query_emb = np.random.rand(4).astype(np.float32)
        query_emb = query_emb / np.linalg.norm(query_emb)
        results = index.search("python", query_emb, top_k=3)
        for chunk_id, score in results:
            assert isinstance(chunk_id, str)
            assert isinstance(score, float)

    def test_rrf_fusion_combines_both(self) -> None:
        chunks = _make_chunks()
        # Make c1 the best vector match
        embeddings = np.array(
            [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0]],
            dtype=np.float32,
        )
        index = _make_hybrid_index(chunks, embeddings)
        query_emb = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
        # "python" matches c1 and c3 via BM25; c1 also best vector match
        results = index.search("python", query_emb, top_k=3)
        top_ids = [r[0] for r in results]
        # c1 should rank highly since it's the best in both
        assert "c1" in top_ids[:2]

    def test_scores_sorted_descending(self) -> None:
        chunks = _make_chunks()
        embeddings = np.random.rand(3, 4).astype(np.float32)
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / norms
        index = _make_hybrid_index(chunks, embeddings)
        query_emb = np.random.rand(4).astype(np.float32)
        query_emb = query_emb / np.linalg.norm(query_emb)
        results = index.search("python", query_emb, top_k=3)
        scores = [s for _, s in results]
        assert scores == sorted(scores, reverse=True)

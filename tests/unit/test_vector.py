"""Tests for vector index (FAISS)."""

import numpy as np
import pytest

from hcr_core.index.vector import VectorIndex


def _make_index() -> VectorIndex:
    dim = 4
    embeddings = np.array(
        [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.9, 0.1, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
        ],
        dtype=np.float32,
    )
    # L2 normalize
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / norms
    chunk_ids = ["c1", "c2", "c3", "c4"]
    return VectorIndex(embeddings, chunk_ids)


class TestVectorIndex:
    def test_search_returns_results(self) -> None:
        index = _make_index()
        query_emb = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
        results = index.search(query_emb, top_k=2)
        assert len(results) == 2

    def test_search_returns_chunk_id_score_tuples(self) -> None:
        index = _make_index()
        query_emb = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
        results = index.search(query_emb, top_k=2)
        for chunk_id, score in results:
            assert isinstance(chunk_id, str)
            assert isinstance(score, float)

    def test_nearest_neighbor_is_correct(self) -> None:
        index = _make_index()
        # Query most similar to c1 (1, 0, 0, 0)
        query_emb = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
        results = index.search(query_emb, top_k=1)
        assert results[0][0] == "c1"

    def test_scores_are_sorted_descending(self) -> None:
        index = _make_index()
        query_emb = np.array([0.5, 0.5, 0.0, 0.0], dtype=np.float32)
        query_emb = query_emb / np.linalg.norm(query_emb)
        results = index.search(query_emb, top_k=4)
        scores = [s for _, s in results]
        assert scores == sorted(scores, reverse=True)

    def test_search_respects_top_k(self) -> None:
        index = _make_index()
        query_emb = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
        results = index.search(query_emb, top_k=1)
        assert len(results) == 1

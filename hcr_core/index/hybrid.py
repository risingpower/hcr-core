"""Hybrid index combining BM25 and vector search via Reciprocal Rank Fusion."""

import numpy as np
from numpy.typing import NDArray

from hcr_core.index.bm25 import BM25Index
from hcr_core.index.vector import VectorIndex


class HybridIndex:
    """Hybrid retrieval using RRF to fuse BM25 and vector search results."""

    def __init__(
        self,
        bm25: BM25Index,
        vector: VectorIndex,
        rrf_k: int = 60,
    ) -> None:
        self._bm25 = bm25
        self._vector = vector
        self._rrf_k = rrf_k

    def search(
        self,
        query: str,
        query_embedding: NDArray[np.float32],
        top_k: int = 10,
    ) -> list[tuple[str, float]]:
        """Search using RRF fusion of BM25 and vector results."""
        # Get results from both indexes with a larger pool
        pool_k = top_k * 3
        bm25_results = self._bm25.search(query, top_k=pool_k)
        vector_results = self._vector.search(query_embedding, top_k=pool_k)

        # Compute RRF scores
        rrf_scores: dict[str, float] = {}
        for rank, (chunk_id, _) in enumerate(bm25_results):
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + 1.0 / (
                self._rrf_k + rank + 1
            )
        for rank, (chunk_id, _) in enumerate(vector_results):
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + 1.0 / (
                self._rrf_k + rank + 1
            )

        # Sort by RRF score descending
        sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[:top_k]

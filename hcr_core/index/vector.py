"""FAISS vector index for dense retrieval."""

import faiss
import numpy as np
from numpy.typing import NDArray


class VectorIndex:
    """FAISS IndexFlatIP index over L2-normalized embeddings."""

    def __init__(
        self,
        embeddings: NDArray[np.float32],
        chunk_ids: list[str],
    ) -> None:
        if len(chunk_ids) != embeddings.shape[0]:
            raise ValueError(
                f"chunk_ids length ({len(chunk_ids)}) != embeddings rows ({embeddings.shape[0]})"
            )
        self._chunk_ids = chunk_ids
        dim = embeddings.shape[1]
        self._index = faiss.IndexFlatIP(dim)
        # Ensure normalized
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        normalized = embeddings / np.maximum(norms, 1e-10)
        self._index.add(normalized)

    def search(
        self, query_embedding: NDArray[np.float32], top_k: int = 10
    ) -> list[tuple[str, float]]:
        """Search for nearest chunks, returning (chunk_id, score) sorted descending."""
        query = query_embedding.reshape(1, -1)
        norm = np.linalg.norm(query)
        if norm > 0:
            query = query / norm

        scores, indices = self._index.search(query, min(top_k, len(self._chunk_ids)))
        results: list[tuple[str, float]] = []
        for i in range(indices.shape[1]):
            idx = int(indices[0, i])
            if idx >= 0:
                results.append((self._chunk_ids[idx], float(scores[0, i])))
        return results

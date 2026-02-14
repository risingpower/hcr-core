"""BM25 sparse retrieval index."""

from rank_bm25 import BM25Okapi

from hcr_core.types.corpus import Chunk


class BM25Index:
    """BM25 index over chunks for sparse keyword retrieval."""

    def __init__(self, chunks: list[Chunk]) -> None:
        self._chunk_ids = [c.id for c in chunks]
        tokenized = [c.content.lower().split() for c in chunks]
        self._bm25 = BM25Okapi(tokenized)

    def search(self, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        """Search for chunks matching query, returning (chunk_id, score) sorted descending."""
        tokenized_query = query.lower().split()
        scores: list[float] = self._bm25.get_scores(tokenized_query).tolist()

        scored = list(zip(self._chunk_ids, scores, strict=True))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

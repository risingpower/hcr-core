"""BM25 baseline: sparse keyword retrieval with greedy token packing."""

from hcr_core.index.bm25 import BM25Index
from hcr_core.types.corpus import Chunk

from . import RetrievalBaseline


def greedy_token_pack(
    chunks: list[Chunk], scores: list[tuple[str, float]], token_budget: int
) -> list[Chunk]:
    """Pack chunks greedily by score until budget is exhausted."""
    chunk_map = {c.id: c for c in chunks}
    packed: list[Chunk] = []
    tokens_used = 0
    for chunk_id, _ in scores:
        chunk = chunk_map.get(chunk_id)
        if chunk is None:
            continue
        if tokens_used + chunk.token_count > token_budget:
            continue
        packed.append(chunk)
        tokens_used += chunk.token_count
    return packed


class BM25Baseline(RetrievalBaseline):
    """BM25 keyword retrieval + greedy token packing."""

    def __init__(self, chunks: list[Chunk]) -> None:
        self._chunks = chunks
        self._index = BM25Index(chunks)

    @property
    def name(self) -> str:
        return "bm25"

    def retrieve(self, query: str, token_budget: int) -> list[Chunk]:
        scores = self._index.search(query, top_k=50)
        return greedy_token_pack(self._chunks, scores, token_budget)

"""Hybrid baseline: RRF fusion of BM25 + vector with greedy token packing."""

import numpy as np
from numpy.typing import NDArray

from hcr_core.corpus.embedder import ChunkEmbedder
from hcr_core.index.bm25 import BM25Index
from hcr_core.index.hybrid import HybridIndex
from hcr_core.index.vector import VectorIndex
from hcr_core.types.corpus import Chunk

from . import RetrievalBaseline
from .bm25_baseline import greedy_token_pack


class HybridBaseline(RetrievalBaseline):
    """Hybrid BM25+vector (RRF) retrieval + greedy token packing."""

    def __init__(
        self,
        chunks: list[Chunk],
        embeddings: NDArray[np.float32],
        embedder: ChunkEmbedder | None = None,
    ) -> None:
        self._chunks = chunks
        self._embeddings = embeddings
        chunk_ids = [c.id for c in chunks]
        bm25 = BM25Index(chunks)
        vector = VectorIndex(embeddings, chunk_ids)
        self._index = HybridIndex(bm25=bm25, vector=vector)
        self._embedder = embedder or ChunkEmbedder()

    @property
    def name(self) -> str:
        return "hybrid-rrf"

    def rank(self, query: str, top_k: int = 50) -> list[tuple[str, float]]:
        query_emb = self._embedder.embed_text(query)
        return self._index.search(query, query_emb, top_k=top_k)

    def retrieve(self, query: str, token_budget: int) -> list[Chunk]:
        query_emb = self._embedder.embed_text(query)
        scores = self._index.search(query, query_emb, top_k=50)
        return greedy_token_pack(self._chunks, scores, token_budget)

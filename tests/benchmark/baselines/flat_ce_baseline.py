"""Flat cross-encoder baseline: hybrid pre-filter + CE rerank + greedy packing.

This is the KILL baseline. If flat+CE beats HCR, the project is killed.
"""

import numpy as np
from numpy.typing import NDArray
from sentence_transformers import CrossEncoder

from hcr_core.cache import CrossEncoderCache
from hcr_core.corpus.embedder import ChunkEmbedder
from hcr_core.index.bm25 import BM25Index
from hcr_core.index.hybrid import HybridIndex
from hcr_core.index.vector import VectorIndex
from hcr_core.types.corpus import Chunk

from . import RetrievalBaseline
from .bm25_baseline import greedy_token_pack


class FlatCrossEncoderBaseline(RetrievalBaseline):
    """Hybrid pre-filter -> cross-encoder rerank -> greedy token packing."""

    def __init__(
        self,
        chunks: list[Chunk],
        embeddings: NDArray[np.float32],
        embedder: ChunkEmbedder | None = None,
        ce_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        pre_filter_k: int = 50,
        ce_cache: CrossEncoderCache | None = None,
    ) -> None:
        self._chunks = chunks
        self._chunk_map = {c.id: c for c in chunks}
        chunk_ids = [c.id for c in chunks]
        bm25 = BM25Index(chunks)
        vector = VectorIndex(embeddings, chunk_ids)
        self._index = HybridIndex(bm25=bm25, vector=vector)
        self._embedder = embedder or ChunkEmbedder()
        self._cross_encoder = CrossEncoder(ce_model)
        self._pre_filter_k = pre_filter_k
        self._ce_cache = ce_cache

    @property
    def name(self) -> str:
        return "flat-ce"

    def retrieve(self, query: str, token_budget: int) -> list[Chunk]:
        # Step 1: hybrid pre-filter
        query_emb = self._embedder.embed_text(query)
        candidates = self._index.search(query, query_emb, top_k=self._pre_filter_k)

        # Step 2: cross-encoder rerank
        cached_scores: dict[str, float] = {}
        pairs: list[tuple[str, str]] = []
        candidate_ids: list[str] = []

        for chunk_id, _ in candidates:
            chunk = self._chunk_map.get(chunk_id)
            if chunk is None:
                continue

            # Check cache first
            if self._ce_cache is not None:
                cached = self._ce_cache.load(query, chunk_id)
                if cached is not None:
                    cached_scores[chunk_id] = cached
                    continue

            pairs.append((query, chunk.content))
            candidate_ids.append(chunk_id)

        # Compute scores for uncached pairs
        ce_scores: dict[str, float] = dict(cached_scores)

        if pairs:
            new_scores: list[float] = self._cross_encoder.predict(
                pairs
            ).tolist()

            for cid, score in zip(candidate_ids, new_scores, strict=True):
                ce_scores[cid] = score

            # Cache new scores
            if self._ce_cache is not None:
                for cid, score in zip(candidate_ids, new_scores, strict=True):
                    self._ce_cache.save(query, cid, score)

        # Step 3: sort by CE score, greedy pack
        scored = sorted(ce_scores.items(), key=lambda x: x[1], reverse=True)
        return greedy_token_pack(self._chunks, scored, token_budget)

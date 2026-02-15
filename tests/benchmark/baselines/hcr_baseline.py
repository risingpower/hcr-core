"""HCR baseline: tree-based dual-path retrieval (beam search + collapsed tree).

This is the system under test. HCR must beat flat+CE (the kill baseline)
on nDCG@10 while using fewer tokens.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from hcr_core.corpus.embedder import ChunkEmbedder
from hcr_core.scoring.cascade import ScoringCascade
from hcr_core.scoring.cross_encoder import CrossEncoderScorer
from hcr_core.traversal.beam import BeamSearchResult, BeamSearchTraversal
from hcr_core.traversal.collapsed import CollapsedTreeRetrieval
from hcr_core.traversal.dual_path import DualPathRetrieval
from hcr_core.types.corpus import Chunk
from hcr_core.types.tree import HCRTree

from . import RetrievalBaseline
from .bm25_baseline import greedy_token_pack


class HCRBaseline(RetrievalBaseline):
    """HCR dual-path retrieval: beam search + collapsed tree race.

    Wraps TreeBuilder output + DualPathRetrieval into the baseline interface.
    Stores beam_per_level results for epsilon measurement.
    """

    def __init__(
        self,
        tree: HCRTree,
        chunks: list[Chunk],
        embeddings: NDArray[np.float32],
        embedder: ChunkEmbedder,
        cross_encoder: CrossEncoderScorer,
        beam_width: int = 3,
        diversity_lambda: float = 0.3,
    ) -> None:
        self._tree = tree
        self._chunks = chunks
        self._chunk_map = {c.id: c for c in chunks}
        self._embedder = embedder

        # Build leaf node -> chunk_id lookup
        self._leaf_to_chunk: dict[str, str] = {}
        for node in tree.nodes.values():
            if node.is_leaf and node.chunk_id is not None:
                self._leaf_to_chunk[node.id] = node.chunk_id

        # Build chunk_id -> embedding lookup for leaf scoring
        chunk_ids = [c.id for c in chunks]
        chunk_embeddings: dict[str, NDArray[np.float32]] = {}
        for i, cid in enumerate(chunk_ids):
            chunk_embeddings[cid] = embeddings[i]

        # Build chunk_id -> text lookup for leaf CE scoring
        chunk_texts: dict[str, str] = {c.id: c.content for c in chunks}

        # Build summary embeddings dict for collapsed retrieval
        summary_embeddings: dict[str, NDArray[np.float32]] = {}
        for node_id, node in tree.nodes.items():
            if node.summary_embedding is not None:
                summary_embeddings[node_id] = np.array(
                    node.summary_embedding, dtype=np.float32
                )

        # Set up traversal components
        cascade = ScoringCascade(
            cross_encoder=cross_encoder,
            chunk_embeddings=chunk_embeddings,
            chunk_texts=chunk_texts,
        )
        beam_traversal = BeamSearchTraversal(
            tree=tree,
            scorer=cascade,
            beam_width=beam_width,
            diversity_lambda=diversity_lambda,
        )
        collapsed = CollapsedTreeRetrieval(
            tree=tree,
            summary_embeddings=summary_embeddings,
            cross_encoder=cross_encoder,
        )
        self._dual_path = DualPathRetrieval(
            beam=beam_traversal, collapsed=collapsed
        )

        # Store beam results for epsilon measurement
        self._last_beam_results: dict[str, dict[int, list[str]]] = {}

    @property
    def name(self) -> str:
        return "hcr"

    @property
    def beam_results(self) -> dict[str, dict[int, list[str]]]:
        """Beam-per-level results for epsilon measurement, keyed by query text."""
        return self._last_beam_results

    def rank(self, query: str, top_k: int = 50) -> list[tuple[str, float]]:
        """Rank chunks via dual-path retrieval."""
        query_emb = self._embedder.embed_text(query)
        result = self._dual_path.retrieve(query, query_emb)

        # Store beam results for epsilon (keyed by query text, will be re-keyed by caller)
        if result.beam_result is not None:
            self._last_beam_result = result.beam_result
        else:
            self._last_beam_result = BeamSearchResult(
                leaf_node_ids=[], leaf_scores=[], beam_per_level={}
            )

        # Resolve leaf nodes to chunk IDs with scores
        scored_chunks: list[tuple[str, float]] = []
        seen_chunks: set[str] = set()
        for leaf_id, score in zip(
            result.leaf_node_ids, result.leaf_scores, strict=True
        ):
            chunk_id = self._leaf_to_chunk.get(leaf_id)
            if chunk_id is not None and chunk_id not in seen_chunks:
                scored_chunks.append((chunk_id, score))
                seen_chunks.add(chunk_id)

        return scored_chunks[:top_k]

    def retrieve(self, query: str, token_budget: int) -> list[Chunk]:
        """Retrieve chunks within token budget via dual-path + greedy packing."""
        scored = self.rank(query, top_k=50)
        return greedy_token_pack(self._chunks, scored, token_budget)

    def store_beam_result(self, query_id: str) -> None:
        """Store the last beam result under a query ID for epsilon computation."""
        if hasattr(self, "_last_beam_result"):
            self._last_beam_results[query_id] = (
                self._last_beam_result.beam_per_level
            )

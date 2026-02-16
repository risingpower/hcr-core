"""Scoring cascade: hybrid pre-filter + cross-encoder rerank."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from hcr_core.scoring.cross_encoder import CrossEncoderScorer
from hcr_core.types.tree import HCRTree, TreeNode


class ScoringCascade:
    """Per-level scoring cascade for tree traversal.

    Stage 1: Dense similarity pre-filter (all children) -> top pre_filter_k
    Stage 2: Cross-encoder rerank -> top final_k

    For leaf nodes (no summary embedding), falls back to chunk embeddings
    and chunk content for scoring.
    """

    def __init__(
        self,
        cross_encoder: CrossEncoderScorer,
        pre_filter_k: int = 3,
        final_k: int = 2,
        chunk_embeddings: dict[str, NDArray[np.float32]] | None = None,
        chunk_texts: dict[str, str] | None = None,
    ) -> None:
        self._cross_encoder = cross_encoder
        self._pre_filter_k = pre_filter_k
        self._final_k = final_k
        self._chunk_embeddings = chunk_embeddings or {}
        self._chunk_texts = chunk_texts or {}

    def _get_embedding(
        self, child: TreeNode
    ) -> NDArray[np.float32] | None:
        """Get embedding for a node: summary embedding or chunk embedding."""
        if child.summary_embedding is not None:
            return np.array(child.summary_embedding, dtype=np.float32)
        if child.is_leaf and child.chunk_id is not None:
            return self._chunk_embeddings.get(child.chunk_id)
        return None

    def _get_text(self, child: TreeNode) -> str | None:
        """Get text for cross-encoder scoring: summary or chunk content."""
        if child.summary is not None:
            return (
                f"Theme: {child.summary.theme}. "
                f"Includes: {', '.join(child.summary.includes)}. "
                f"Excludes: {', '.join(child.summary.excludes)}."
            )
        if child.is_leaf and child.chunk_id is not None:
            return self._chunk_texts.get(child.chunk_id)
        return None

    def score_children(
        self,
        query: str,
        query_embedding: NDArray[np.float32],
        tree: HCRTree,
        parent_node: TreeNode,
    ) -> list[tuple[str, float]]:
        """Score children of a node, returning (child_id, score) sorted descending.

        Stage 1: Cosine similarity pre-filter using embeddings.
        Stage 2: Cross-encoder rerank on text.
        """
        children = [
            tree.nodes[cid]
            for cid in parent_node.child_ids
            if cid in tree.nodes
        ]

        if not children:
            return []

        # Stage 1: Dense similarity pre-filter
        scored: list[tuple[str, float]] = []
        for child in children:
            emb = self._get_embedding(child)
            if emb is not None:
                norm = float(np.linalg.norm(emb))
                if norm > 0:
                    emb = emb / norm
                sim = float(np.dot(query_embedding, emb))
                scored.append((child.id, sim))
            else:
                scored.append((child.id, 0.0))

        scored.sort(key=lambda x: x[1], reverse=True)
        top_candidates = scored[: self._pre_filter_k]

        # Skip CE for internal nodes — MS-MARCO CE is net negative on
        # structured routing metadata (scores deeply negative for all
        # candidates, flips correct cosine decisions to wrong).
        # Only use CE when children are leaves with actual chunk content.
        children_are_leaves = all(
            tree.nodes[cid].is_leaf for cid, _ in top_candidates
        )
        if not children_are_leaves:
            return top_candidates[: self._final_k]

        # Stage 2: Cross-encoder rerank (leaf nodes only)
        texts = []
        ids = []
        for cid, _ in top_candidates:
            node = tree.nodes[cid]
            text = self._get_text(node)
            if text is not None:
                texts.append(text)
                ids.append(cid)

        if not texts:
            return top_candidates[: self._final_k]

        ce_scores = self._cross_encoder.score_batch(
            query, texts, chunk_ids=ids
        )
        reranked = list(zip(ids, ce_scores, strict=True))
        reranked.sort(key=lambda x: x[1], reverse=True)

        return reranked[: self._final_k]

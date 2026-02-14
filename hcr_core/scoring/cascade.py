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
    """

    def __init__(
        self,
        cross_encoder: CrossEncoderScorer,
        pre_filter_k: int = 3,
        final_k: int = 2,
    ) -> None:
        self._cross_encoder = cross_encoder
        self._pre_filter_k = pre_filter_k
        self._final_k = final_k

    def score_children(
        self,
        query: str,
        query_embedding: NDArray[np.float32],
        tree: HCRTree,
        parent_node: TreeNode,
    ) -> list[tuple[str, float]]:
        """Score children of a node, returning (child_id, score) sorted descending.

        Stage 1: Cosine similarity pre-filter using summary embeddings.
        Stage 2: Cross-encoder rerank on summary text.
        """
        children = [tree.nodes[cid] for cid in parent_node.child_ids if cid in tree.nodes]

        if not children:
            return []

        # Stage 1: Dense similarity pre-filter
        scored: list[tuple[str, float]] = []
        for child in children:
            if child.summary_embedding is not None:
                child_emb = np.array(child.summary_embedding, dtype=np.float32)
                norm = float(np.linalg.norm(child_emb))
                if norm > 0:
                    child_emb = child_emb / norm
                sim = float(np.dot(query_embedding, child_emb))
                scored.append((child.id, sim))
            else:
                scored.append((child.id, 0.0))

        scored.sort(key=lambda x: x[1], reverse=True)
        top_candidates = scored[: self._pre_filter_k]

        # Stage 2: Cross-encoder rerank
        candidate_nodes = [tree.nodes[cid] for cid, _ in top_candidates]
        texts = []
        ids = []
        for node in candidate_nodes:
            if node.summary is not None:
                summary_text = (
                    f"Theme: {node.summary.theme}. "
                    f"Includes: {', '.join(node.summary.includes)}. "
                    f"Excludes: {', '.join(node.summary.excludes)}."
                )
                texts.append(summary_text)
                ids.append(node.id)

        if not texts:
            return top_candidates[: self._final_k]

        ce_scores = self._cross_encoder.score_batch(query, texts, chunk_ids=ids)
        reranked = list(zip(ids, ce_scores, strict=True))
        reranked.sort(key=lambda x: x[1], reverse=True)

        return reranked[: self._final_k]

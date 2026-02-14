"""Collapsed tree retrieval: flat search over all node summaries."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from hcr_core.scoring.cross_encoder import CrossEncoderScorer
from hcr_core.types.tree import HCRTree


@dataclass
class CollapsedResult:
    """Result of collapsed-tree retrieval."""

    leaf_node_ids: list[str]
    leaf_scores: list[float]
    confidence: float


class CollapsedTreeRetrieval:
    """RAPTOR-style flat search over all node summaries.

    Co-primary strategy alongside beam search (RB-005).
    Catches cases where beam search fails due to beam collapse.
    """

    def __init__(
        self,
        tree: HCRTree,
        summary_embeddings: dict[str, NDArray[np.float32]],
        cross_encoder: CrossEncoderScorer,
        top_k: int = 10,
    ) -> None:
        self._tree = tree
        self._summary_embeddings = summary_embeddings
        self._cross_encoder = cross_encoder
        self._top_k = top_k

    def retrieve(
        self,
        query: str,
        query_embedding: NDArray[np.float32],
    ) -> CollapsedResult:
        """Flat search: score all summaries, find best leaf paths."""
        # Score all nodes with summaries
        scored_nodes: list[tuple[str, float]] = []

        for node_id, emb in self._summary_embeddings.items():
            node = self._tree.nodes.get(node_id)
            if node is None:
                continue
            norm = float(np.linalg.norm(emb))
            if norm > 0:
                sim = float(np.dot(query_embedding, emb / norm))
                scored_nodes.append((node_id, sim))

        scored_nodes.sort(key=lambda x: x[1], reverse=True)

        # Take top candidates and cross-encoder rerank
        top_candidates = scored_nodes[: self._top_k]

        if not top_candidates:
            return CollapsedResult(leaf_node_ids=[], leaf_scores=[], confidence=0.0)

        texts = []
        ids = []
        for node_id, _ in top_candidates:
            node = self._tree.nodes[node_id]
            if node.summary is not None:
                texts.append(
                    f"Theme: {node.summary.theme}. "
                    f"Includes: {', '.join(node.summary.includes)}."
                )
                ids.append(node_id)

        if not texts:
            return CollapsedResult(leaf_node_ids=[], leaf_scores=[], confidence=0.0)

        ce_scores = self._cross_encoder.score_batch(query, texts, chunk_ids=ids)
        reranked = sorted(
            zip(ids, ce_scores, strict=True), key=lambda x: x[1], reverse=True
        )

        # Find leaf nodes under the best-scoring nodes
        leaf_ids: list[str] = []
        leaf_scores: list[float] = []
        for node_id, score in reranked:
            leaves = self._get_descendant_leaves(node_id)
            for leaf_id in leaves:
                if leaf_id not in leaf_ids:
                    leaf_ids.append(leaf_id)
                    leaf_scores.append(score)

        confidence = reranked[0][1] if reranked else 0.0

        return CollapsedResult(
            leaf_node_ids=leaf_ids,
            leaf_scores=leaf_scores,
            confidence=confidence,
        )

    def _get_descendant_leaves(self, node_id: str) -> list[str]:
        """Get all leaf descendants of a node."""
        node = self._tree.nodes.get(node_id)
        if node is None:
            return []
        if node.is_leaf:
            return [node_id]

        leaves: list[str] = []
        for child_id in node.child_ids:
            leaves.extend(self._get_descendant_leaves(child_id))
        return leaves

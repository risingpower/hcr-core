"""Dual-path retrieval: beam search + collapsed tree race."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from hcr_core.traversal.beam import BeamSearchResult, BeamSearchTraversal
from hcr_core.traversal.collapsed import CollapsedResult, CollapsedTreeRetrieval


@dataclass
class DualPathResult:
    """Result of dual-path retrieval."""

    leaf_node_ids: list[str]
    leaf_scores: list[float]
    strategy_used: str  # "beam" or "collapsed"
    beam_result: BeamSearchResult | None = None
    collapsed_result: CollapsedResult | None = None


class DualPathRetrieval:
    """Runs beam search and collapsed tree in parallel, returns higher confidence.

    Per RB-005: collapsed-tree promoted to co-primary, not fallback.
    """

    def __init__(
        self,
        beam: BeamSearchTraversal,
        collapsed: CollapsedTreeRetrieval,
    ) -> None:
        self._beam = beam
        self._collapsed = collapsed

    def retrieve(
        self,
        query: str,
        query_embedding: NDArray[np.float32],
    ) -> DualPathResult:
        """Run both strategies and return the higher-confidence result."""
        beam_result = self._beam.traverse(query, query_embedding)
        collapsed_result = self._collapsed.retrieve(query, query_embedding)

        # Compare confidence: use max leaf score as proxy
        beam_confidence = max(beam_result.leaf_scores) if beam_result.leaf_scores else 0.0
        collapsed_confidence = collapsed_result.confidence

        if beam_confidence >= collapsed_confidence:
            return DualPathResult(
                leaf_node_ids=beam_result.leaf_node_ids,
                leaf_scores=beam_result.leaf_scores,
                strategy_used="beam",
                beam_result=beam_result,
                collapsed_result=collapsed_result,
            )
        else:
            return DualPathResult(
                leaf_node_ids=collapsed_result.leaf_node_ids,
                leaf_scores=collapsed_result.leaf_scores,
                strategy_used="collapsed",
                beam_result=beam_result,
                collapsed_result=collapsed_result,
            )

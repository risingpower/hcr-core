"""Beam search traversal over the HCR tree."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from hcr_core.scoring.cascade import ScoringCascade
from hcr_core.scoring.path_score import path_relevance_ema
from hcr_core.types.tree import HCRTree


@dataclass
class BeamEntry:
    """A single entry in the beam: node + accumulated path score."""

    node_id: str
    path_score: float
    depth: int


@dataclass
class BeamSearchResult:
    """Result of beam search traversal."""

    leaf_node_ids: list[str]
    leaf_scores: list[float]
    beam_per_level: dict[int, list[str]] = field(default_factory=dict)


class BeamSearchTraversal:
    """Beam search traversal with diversity enforcement.

    Traverses the tree from root to leaves, maintaining a beam of
    candidate paths with MMR-style diversity penalty.
    """

    def __init__(
        self,
        tree: HCRTree,
        scorer: ScoringCascade,
        beam_width: int = 3,
        diversity_lambda: float = 0.3,
    ) -> None:
        self._tree = tree
        self._scorer = scorer
        self._beam_width = beam_width
        self._diversity_lambda = diversity_lambda

    def traverse(
        self,
        query: str,
        query_embedding: NDArray[np.float32],
    ) -> BeamSearchResult:
        """Traverse the tree using beam search, returning leaf nodes."""
        root = self._tree.nodes[self._tree.root_id]
        beam = [BeamEntry(node_id=root.id, path_score=1.0, depth=0)]
        beam_per_level: dict[int, list[str]] = {0: [root.id]}

        while True:
            # Expand all non-leaf nodes in beam
            candidates: list[BeamEntry] = []
            leaves: list[BeamEntry] = []

            for entry in beam:
                node = self._tree.nodes[entry.node_id]
                if node.is_leaf:
                    leaves.append(entry)
                    continue

                # Score children using cascade
                child_scores = self._scorer.score_children(
                    query, query_embedding, self._tree, node
                )

                for child_id, score in child_scores:
                    smoothed = path_relevance_ema(score, entry.path_score)
                    candidates.append(
                        BeamEntry(
                            node_id=child_id,
                            path_score=smoothed,
                            depth=entry.depth + 1,
                        )
                    )

            if not candidates:
                # All beam entries are leaves (or dead ends)
                return BeamSearchResult(
                    leaf_node_ids=[e.node_id for e in leaves],
                    leaf_scores=[e.path_score for e in leaves],
                    beam_per_level=beam_per_level,
                )

            # Apply diversity penalty and select top beam_width
            beam = self._select_diverse_beam(candidates + leaves)

            # Record beam at this level
            if candidates:
                level = candidates[0].depth
                beam_per_level[level] = [e.node_id for e in beam]

            # Check if all remaining are leaves
            all_leaves = all(
                self._tree.nodes[e.node_id].is_leaf for e in beam
            )
            if all_leaves:
                return BeamSearchResult(
                    leaf_node_ids=[e.node_id for e in beam],
                    leaf_scores=[e.path_score for e in beam],
                    beam_per_level=beam_per_level,
                )

    def _select_diverse_beam(
        self, candidates: list[BeamEntry]
    ) -> list[BeamEntry]:
        """Select beam entries with MMR-style diversity enforcement."""
        if len(candidates) <= self._beam_width:
            return candidates

        # Sort by score first
        candidates.sort(key=lambda x: x.path_score, reverse=True)

        selected: list[BeamEntry] = [candidates[0]]
        remaining = candidates[1:]

        while len(selected) < self._beam_width and remaining:
            best_idx = 0
            best_score = -float("inf")

            for i, candidate in enumerate(remaining):
                # Penalty for sharing ancestors with already-selected
                penalty = 0.0
                for sel in selected:
                    if self._share_branch(candidate.node_id, sel.node_id):
                        penalty = max(penalty, self._diversity_lambda)

                adjusted = candidate.path_score - penalty
                if adjusted > best_score:
                    best_score = adjusted
                    best_idx = i

            selected.append(remaining.pop(best_idx))

        return selected

    def _share_branch(self, node_a: str, node_b: str) -> bool:
        """Check if two nodes share a parent (same branch)."""
        a = self._tree.nodes.get(node_a)
        b = self._tree.nodes.get(node_b)
        if a is None or b is None:
            return False
        return bool(set(a.parent_ids) & set(b.parent_ids))

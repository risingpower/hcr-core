"""K-means clustering for hierarchical tree construction."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray
from sklearn.cluster import KMeans


@dataclass
class ClusterNode:
    """A node in the hierarchical cluster tree.

    Leaf cluster nodes hold chunk_ids directly.
    Internal cluster nodes hold children (sub-clusters).
    """

    chunk_ids: list[str]
    embeddings: NDArray[np.float32]
    children: list[ClusterNode] = field(default_factory=list)

    @property
    def is_leaf_cluster(self) -> bool:
        return len(self.children) == 0


def bisecting_kmeans(
    embeddings: NDArray[np.float32],
    chunk_ids: list[str],
    target_branching: int = 10,
    max_depth: int = 2,
) -> list[list[str]]:
    """Flat clustering output for backwards compatibility.

    Returns:
        List of clusters, each a list of chunk_ids.
    """
    root = hierarchical_kmeans(embeddings, chunk_ids, target_branching, max_depth)
    return _collect_leaves(root)


def _collect_leaves(node: ClusterNode) -> list[list[str]]:
    """Collect leaf clusters from a ClusterNode tree."""
    if node.is_leaf_cluster:
        return [node.chunk_ids]
    result: list[list[str]] = []
    for child in node.children:
        result.extend(_collect_leaves(child))
    return result


def hierarchical_kmeans(
    embeddings: NDArray[np.float32],
    chunk_ids: list[str],
    target_branching: int = 10,
    max_depth: int = 2,
) -> ClusterNode:
    """Top-down k-ary clustering that preserves hierarchical structure.

    At each level, splits into min(target_branching, N) clusters using k-means.
    Recurses until max_depth reached or clusters are small enough.

    Args:
        embeddings: (N, D) L2-normalized embeddings.
        chunk_ids: Corresponding chunk IDs.
        target_branching: Target number of children per node.
        max_depth: Number of internal levels to build.

    Returns:
        Root ClusterNode with hierarchical children.
    """
    root = ClusterNode(chunk_ids=chunk_ids, embeddings=embeddings)

    if len(chunk_ids) <= 1 or max_depth == 0:
        return root

    # Don't split if already small enough
    if len(chunk_ids) <= target_branching:
        return root

    # Split into k clusters
    k = min(target_branching, len(chunk_ids))
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels: NDArray[np.int64] = kmeans.fit_predict(embeddings)

    # Group by cluster label
    unique_labels = sorted(set(int(lab) for lab in labels))

    for label in unique_labels:
        mask = labels == label
        child_ids = [chunk_ids[i] for i in range(len(chunk_ids)) if mask[i]]
        child_embs = embeddings[mask]

        if len(child_ids) == 0:
            continue

        child = hierarchical_kmeans(
            child_embs, child_ids, target_branching, max_depth - 1
        )
        root.children.append(child)

    # If k-means produced only 1 non-empty cluster, don't create a useless level
    if len(root.children) <= 1:
        root.children = []

    return root

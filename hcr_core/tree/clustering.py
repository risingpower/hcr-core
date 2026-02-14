"""Bisecting k-means clustering for tree construction."""

import numpy as np
from numpy.typing import NDArray
from sklearn.cluster import KMeans


def bisecting_kmeans(
    embeddings: NDArray[np.float32],
    chunk_ids: list[str],
    target_branching: int = 10,
    max_depth: int = 2,
) -> list[list[str]]:
    """Bisecting k-means: recursively split clusters top-down.

    Args:
        embeddings: (N, D) L2-normalized embeddings.
        chunk_ids: Corresponding chunk IDs.
        target_branching: Max children per node (split until cluster <= this).
        max_depth: Maximum recursion depth.

    Returns:
        List of clusters, each a list of chunk_ids.
    """
    if len(chunk_ids) <= 1 or max_depth == 0:
        return [chunk_ids]

    if len(chunk_ids) <= target_branching:
        return [chunk_ids]

    # Split into 2
    indices = list(range(len(chunk_ids)))
    sub_embeddings = embeddings[indices]

    kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
    labels: NDArray[np.int64] = kmeans.fit_predict(sub_embeddings)

    cluster_0_ids = [chunk_ids[i] for i in range(len(chunk_ids)) if labels[i] == 0]
    cluster_1_ids = [chunk_ids[i] for i in range(len(chunk_ids)) if labels[i] == 1]
    cluster_0_embs = embeddings[[i for i in range(len(chunk_ids)) if labels[i] == 0]]
    cluster_1_embs = embeddings[[i for i in range(len(chunk_ids)) if labels[i] == 1]]

    # Handle degenerate splits
    if len(cluster_0_ids) == 0 or len(cluster_1_ids) == 0:
        return [chunk_ids]

    # Recurse
    result: list[list[str]] = []
    result.extend(
        bisecting_kmeans(cluster_0_embs, cluster_0_ids, target_branching, max_depth - 1)
    )
    result.extend(
        bisecting_kmeans(cluster_1_embs, cluster_1_ids, target_branching, max_depth - 1)
    )

    return result

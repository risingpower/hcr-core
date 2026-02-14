"""Tests for bisecting k-means clustering."""

import numpy as np
import pytest

from hcr_core.tree.clustering import bisecting_kmeans


class TestBisectingKmeans:
    def _make_clustered_embeddings(self) -> tuple[np.ndarray, list[str]]:
        """Create embeddings with 2 clear clusters."""
        rng = np.random.RandomState(42)
        # Cluster A: near [1, 0, 0, 0]
        cluster_a = rng.randn(10, 4).astype(np.float32) * 0.1
        cluster_a[:, 0] += 1.0
        # Cluster B: near [0, 1, 0, 0]
        cluster_b = rng.randn(10, 4).astype(np.float32) * 0.1
        cluster_b[:, 1] += 1.0

        embeddings = np.vstack([cluster_a, cluster_b])
        # L2 normalize
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / norms
        chunk_ids = [f"c{i}" for i in range(20)]
        return embeddings, chunk_ids

    def test_returns_cluster_assignments(self) -> None:
        embeddings, chunk_ids = self._make_clustered_embeddings()
        clusters = bisecting_kmeans(
            embeddings, chunk_ids, target_branching=10, max_depth=2
        )
        assert len(clusters) > 0
        # Each cluster is a list of chunk_ids
        all_assigned = []
        for cluster in clusters:
            all_assigned.extend(cluster)
        # All chunks should be assigned
        assert set(all_assigned) == set(chunk_ids)

    def test_respects_max_depth(self) -> None:
        embeddings, chunk_ids = self._make_clustered_embeddings()
        clusters_d1 = bisecting_kmeans(
            embeddings, chunk_ids, target_branching=10, max_depth=1
        )
        clusters_d2 = bisecting_kmeans(
            embeddings, chunk_ids, target_branching=5, max_depth=2
        )
        # Depth 1 should have fewer clusters
        assert len(clusters_d1) <= len(clusters_d2)

    def test_finds_two_clusters(self) -> None:
        embeddings, chunk_ids = self._make_clustered_embeddings()
        clusters = bisecting_kmeans(
            embeddings, chunk_ids, target_branching=10, max_depth=1
        )
        assert len(clusters) == 2
        # Each cluster should roughly contain its group
        cluster_sizes = sorted([len(c) for c in clusters])
        assert cluster_sizes[0] >= 8  # At least 8 of 10 in smaller cluster
        assert cluster_sizes[1] >= 8

    def test_single_item_not_split(self) -> None:
        embeddings = np.array([[1.0, 0.0, 0.0]], dtype=np.float32)
        clusters = bisecting_kmeans(
            embeddings, ["c0"], target_branching=10, max_depth=2
        )
        assert len(clusters) == 1
        assert clusters[0] == ["c0"]

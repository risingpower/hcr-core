"""Tree builder: hierarchical clustering + summarization -> HCRTree."""

from __future__ import annotations

import logging

import numpy as np
from numpy.typing import NDArray

from hcr_core.corpus.embedder import ChunkEmbedder
from hcr_core.llm.claude import ClaudeClient
from hcr_core.tree.clustering import ClusterNode, hierarchical_kmeans
from hcr_core.tree.summarizer import generate_routing_summary
from hcr_core.types.corpus import Chunk
from hcr_core.types.tree import HCRTree, RoutingSummary, TreeNode

logger = logging.getLogger(__name__)


class TreeBuilder:
    """Builds an HCR tree from chunks using hierarchical clustering and LLM summarization."""

    def __init__(
        self,
        embedder: ChunkEmbedder,
        llm: ClaudeClient,
        depth: int = 2,
        branching: int = 10,
    ) -> None:
        self._embedder = embedder
        self._llm = llm
        self._depth = depth
        self._branching = branching
        self._node_counter = 0

    def _next_id(self, prefix: str) -> str:
        nid = f"{prefix}-{self._node_counter}"
        self._node_counter += 1
        return nid

    def build(
        self,
        chunks: list[Chunk],
        embeddings: NDArray[np.float32],
    ) -> HCRTree:
        """Build an HCR tree from chunks and their embeddings.

        1. Cluster chunks hierarchically using bisecting k-means
        2. Recursively create tree nodes with LLM routing summaries
        3. Embed summaries for traversal scoring
        """
        self._node_counter = 0
        chunk_map = {c.id: c for c in chunks}
        chunk_ids = [c.id for c in chunks]

        # Step 1: Hierarchical clustering
        cluster_root = hierarchical_kmeans(
            embeddings, chunk_ids, self._branching, self._depth
        )

        # Step 2: Recursively build tree nodes
        nodes: dict[str, TreeNode] = {}
        root_id = self._build_subtree(
            cluster_node=cluster_root,
            chunk_map=chunk_map,
            nodes=nodes,
            level=0,
        )

        # Compute actual depth from the tree
        max_level = max(n.level for n in nodes.values())

        return HCRTree(root_id=root_id, nodes=nodes, depth=max_level)

    def _build_subtree(
        self,
        cluster_node: ClusterNode,
        chunk_map: dict[str, Chunk],
        nodes: dict[str, TreeNode],
        level: int,
    ) -> str:
        """Recursively build TreeNodes from a ClusterNode subtree.

        Returns the node ID of the created subtree root.
        """
        if cluster_node.is_leaf_cluster:
            # Leaf cluster: create leaf nodes for each chunk,
            # plus a branch node if there are multiple chunks
            if len(cluster_node.chunk_ids) == 1:
                # Single chunk -> leaf node directly
                chunk_id = cluster_node.chunk_ids[0]
                leaf_id = self._next_id("leaf")
                nodes[leaf_id] = TreeNode(
                    id=leaf_id,
                    level=level,
                    parent_ids=[],
                    child_ids=[],
                    is_leaf=True,
                    chunk_id=chunk_id,
                )
                return leaf_id

            # Multiple chunks in this leaf cluster: create a branch
            # with individual leaf children
            branch_id = self._next_id("branch")
            child_ids: list[str] = []
            for chunk_id in cluster_node.chunk_ids:
                leaf_id = self._next_id("leaf")
                nodes[leaf_id] = TreeNode(
                    id=leaf_id,
                    level=level + 1,
                    parent_ids=[branch_id],
                    child_ids=[],
                    is_leaf=True,
                    chunk_id=chunk_id,
                )
                child_ids.append(leaf_id)

            # Generate routing summary for this cluster
            cluster_texts = [
                chunk_map[cid].content
                for cid in cluster_node.chunk_ids
                if cid in chunk_map
            ]
            summary = generate_routing_summary(self._llm, cluster_texts)
            summary.content_snippet = _extract_snippet(cluster_texts)
            summary_emb = self._embed_summary(summary)

            nodes[branch_id] = TreeNode(
                id=branch_id,
                level=level,
                parent_ids=[],
                child_ids=child_ids,
                is_leaf=False,
                summary=summary,
                summary_embedding=summary_emb,
            )
            return branch_id

        # Internal cluster: recurse into children
        branch_id = self._next_id("branch")
        child_tree_ids: list[str] = []
        sibling_summaries: list[RoutingSummary] = []

        for child_cluster in cluster_node.children:
            child_node_id = self._build_subtree(
                cluster_node=child_cluster,
                chunk_map=chunk_map,
                nodes=nodes,
                level=level + 1,
            )
            child_tree_ids.append(child_node_id)
            nodes[child_node_id].parent_ids.append(branch_id)

            # Collect sibling summaries for contrastive generation
            child_node = nodes[child_node_id]
            if child_node.summary is not None:
                sibling_summaries.append(child_node.summary)

        # Generate routing summary for this internal node
        cluster_texts = [
            chunk_map[cid].content
            for cid in cluster_node.chunk_ids
            if cid in chunk_map
        ]
        summary = generate_routing_summary(
            self._llm, cluster_texts, sibling_summaries or None
        )
        summary.content_snippet = _extract_snippet(cluster_texts)
        summary_emb = self._embed_summary(summary)

        nodes[branch_id] = TreeNode(
            id=branch_id,
            level=level,
            parent_ids=[],
            child_ids=child_tree_ids,
            is_leaf=False,
            summary=summary,
            summary_embedding=summary_emb,
        )

        logger.info(
            "Built node %s at level %d with %d children (%d chunks)",
            branch_id,
            level,
            len(child_tree_ids),
            len(cluster_node.chunk_ids),
        )

        return branch_id

    def _embed_summary(self, summary: RoutingSummary) -> list[float]:
        """Embed a routing summary for vector similarity scoring."""
        emb = self._embedder.embed_text(summary_to_text(summary))
        return list(emb.tolist())


def _extract_snippet(cluster_texts: list[str], max_chars: int = 200) -> str:
    """Extract a representative content snippet from cluster texts.

    Takes the first sentence(s) from the first chunk, up to max_chars.
    Gives the embedding model real content terms to work with.
    """
    if not cluster_texts:
        return ""
    # Take from first chunk — it's representative of the cluster
    text = cluster_texts[0].strip()
    if len(text) <= max_chars:
        return text
    # Cut at last space before limit to avoid mid-word
    cut = text[:max_chars].rfind(" ")
    if cut > 0:
        return text[:cut]
    return text[:max_chars]


def summary_to_text(summary: RoutingSummary) -> str:
    """Convert a RoutingSummary to text for embedding.

    Includes all discriminative fields: theme, includes, excludes,
    key_entities, key_terms, and content_snippet.
    """
    parts = [summary.theme]
    if summary.includes:
        parts.append(f"Covers: {', '.join(summary.includes)}")
    if summary.excludes:
        parts.append(f"Not: {', '.join(summary.excludes)}")
    if summary.key_entities:
        parts.append(f"Entities: {', '.join(summary.key_entities)}")
    if summary.key_terms:
        parts.append(f"Terms: {', '.join(summary.key_terms)}")
    if summary.content_snippet:
        parts.append(f"Sample: {summary.content_snippet}")
    return ". ".join(parts)

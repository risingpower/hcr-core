"""Tree builder: clustering + summarization -> HCRTree."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from hcr_core.corpus.embedder import ChunkEmbedder
from hcr_core.llm.claude import ClaudeClient
from hcr_core.tree.clustering import bisecting_kmeans
from hcr_core.tree.summarizer import generate_routing_summary
from hcr_core.types.corpus import Chunk
from hcr_core.types.tree import HCRTree, RoutingSummary, TreeNode


class TreeBuilder:
    """Builds an HCR tree from chunks using clustering and LLM summarization."""

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

    def build(
        self,
        chunks: list[Chunk],
        embeddings: NDArray[np.float32],
    ) -> HCRTree:
        """Build an HCR tree from chunks and their embeddings.

        1. Cluster chunks using bisecting k-means
        2. Create leaf nodes for each chunk
        3. Create internal nodes for each cluster
        4. Generate routing summaries via LLM
        5. Embed summaries for traversal
        """
        chunk_ids = [c.id for c in chunks]
        chunk_map = {c.id: c for c in chunks}

        # Step 1: Cluster
        clusters = bisecting_kmeans(
            embeddings, chunk_ids, self._branching, self._depth
        )

        nodes: dict[str, TreeNode] = {}
        node_counter = 0

        # Step 2: Create leaf nodes
        leaf_nodes: dict[str, str] = {}  # chunk_id -> leaf_node_id
        for chunk in chunks:
            leaf_id = f"leaf-{node_counter}"
            node_counter += 1
            nodes[leaf_id] = TreeNode(
                id=leaf_id,
                level=self._depth,
                parent_ids=[],
                child_ids=[],
                is_leaf=True,
                chunk_id=chunk.id,
            )
            leaf_nodes[chunk.id] = leaf_id

        # Step 3: Create internal nodes for clusters
        branch_ids: list[str] = []
        for cluster_chunk_ids in clusters:
            branch_id = f"branch-{node_counter}"
            node_counter += 1

            child_leaf_ids = [leaf_nodes[cid] for cid in cluster_chunk_ids if cid in leaf_nodes]
            for child_id in child_leaf_ids:
                nodes[child_id].parent_ids.append(branch_id)

            nodes[branch_id] = TreeNode(
                id=branch_id,
                level=self._depth - 1,
                parent_ids=[],
                child_ids=child_leaf_ids,
                is_leaf=False,
            )
            branch_ids.append(branch_id)

        # Step 4: Generate routing summaries
        summaries: list[RoutingSummary] = []
        for i, (branch_id, cluster_chunk_ids) in enumerate(
            zip(branch_ids, clusters, strict=True)
        ):
            cluster_texts = [
                chunk_map[cid].content
                for cid in cluster_chunk_ids
                if cid in chunk_map
            ]
            sibling_summaries = summaries[:i] if i > 0 else None
            summary = generate_routing_summary(
                self._llm, cluster_texts, sibling_summaries
            )
            summaries.append(summary)

            # Embed the summary
            summary_text = (
                f"{summary.theme} {' '.join(summary.includes)} "
                f"{' '.join(summary.key_terms)}"
            )
            summary_emb = self._embedder.embed_text(summary_text)
            nodes[branch_id].summary = summary
            nodes[branch_id].summary_embedding = summary_emb.tolist()

        # Step 5: Create root node
        root_id = f"root-{node_counter}"
        for bid in branch_ids:
            nodes[bid].parent_ids.append(root_id)

        root_summary = RoutingSummary(
            theme="Root",
            includes=["all topics"],
            excludes=[],
            key_entities=[],
            key_terms=[],
        )

        nodes[root_id] = TreeNode(
            id=root_id,
            level=0,
            parent_ids=[],
            child_ids=branch_ids,
            is_leaf=False,
            summary=root_summary,
        )

        return HCRTree(root_id=root_id, nodes=nodes, depth=self._depth)

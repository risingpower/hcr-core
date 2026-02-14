"""Tree quality metrics: sibling distinctiveness."""

import numpy as np
from numpy.typing import NDArray

from hcr_core.types.tree import HCRTree


def sibling_distinctiveness(
    tree: HCRTree,
    node_embeddings: dict[str, NDArray[np.float32]],
) -> float:
    """Compute mean pairwise cosine distance among sibling node embeddings.

    For each internal node, compute pairwise cosine distances between its
    children's embeddings. Return the global mean.

    Kill criterion: SD < 0.15 means sibling nodes are too similar for
    effective routing.
    """
    all_distances: list[float] = []

    for node in tree.nodes.values():
        if node.is_leaf or len(node.child_ids) < 2:
            continue

        # Get embeddings for children that have them
        child_embs: list[NDArray[np.float32]] = []
        for child_id in node.child_ids:
            if child_id in node_embeddings:
                emb = node_embeddings[child_id]
                norm = float(np.linalg.norm(emb))
                if norm > 0:
                    child_embs.append(emb / norm)

        if len(child_embs) < 2:
            continue

        # Compute pairwise cosine distances
        for i in range(len(child_embs)):
            for j in range(i + 1, len(child_embs)):
                cos_sim = float(np.dot(child_embs[i], child_embs[j]))
                cos_dist = 1.0 - cos_sim
                all_distances.append(cos_dist)

    if not all_distances:
        return 0.0

    return float(np.mean(all_distances))

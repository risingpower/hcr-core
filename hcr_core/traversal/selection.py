"""Greedy token packing with redundancy penalty."""

import numpy as np
from numpy.typing import NDArray

from hcr_core.types.corpus import Chunk


def greedy_token_packing(
    chunks: list[Chunk],
    scores: list[float],
    budget: int,
    redundancy_lambda: float = 0.3,
    embeddings: NDArray[np.float32] | None = None,
) -> list[Chunk]:
    """Pack chunks greedily by score until budget is exhausted.

    Optionally applies MMR-style redundancy penalty if embeddings are provided.

    Args:
        chunks: Candidate chunks.
        scores: Relevance scores aligned with chunks.
        budget: Maximum token budget.
        redundancy_lambda: Weight for redundancy penalty (0 = ignore, 1 = strong).
        embeddings: Optional embeddings for redundancy computation.

    Returns:
        Selected chunks within budget.
    """
    if not chunks:
        return []

    n = len(chunks)
    indexed = list(zip(range(n), scores, strict=True))
    indexed.sort(key=lambda x: x[1], reverse=True)

    selected: list[Chunk] = []
    selected_indices: list[int] = []
    tokens_used = 0

    for orig_idx, score in indexed:
        chunk = chunks[orig_idx]
        if tokens_used + chunk.token_count > budget:
            continue

        # Apply redundancy penalty if embeddings available
        if embeddings is not None and selected_indices and redundancy_lambda > 0:
            candidate_emb = embeddings[orig_idx]
            max_sim = 0.0
            for sel_idx in selected_indices:
                sim = float(np.dot(candidate_emb, embeddings[sel_idx]))
                if sim > max_sim:
                    max_sim = sim
            adjusted_score = score - redundancy_lambda * max_sim
            if adjusted_score < 0:
                continue

        selected.append(chunk)
        selected_indices.append(orig_idx)
        tokens_used += chunk.token_count

    return selected

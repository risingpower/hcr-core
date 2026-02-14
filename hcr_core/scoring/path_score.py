"""Path-relevance EMA for smoothing scores across tree depth."""


def path_relevance_ema(
    current_score: float,
    parent_score: float,
    alpha: float = 0.5,
) -> float:
    """Compute exponential moving average of path relevance.

    Smooths the per-level score with the accumulated path score.
    Higher leverage than per-node scoring alone (RB-003).

    Args:
        current_score: Score at the current level.
        parent_score: Accumulated EMA from parent path.
        alpha: Weight for current score (1-alpha for parent).

    Returns:
        Smoothed path relevance score.
    """
    return alpha * current_score + (1 - alpha) * parent_score

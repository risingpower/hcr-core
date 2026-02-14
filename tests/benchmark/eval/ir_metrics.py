"""Standard IR metrics: nDCG, Recall, MRR, Precision."""

import math


def ndcg_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """Compute normalized discounted cumulative gain at k."""
    if not relevant or not retrieved:
        return 0.0

    # DCG
    dcg = 0.0
    for i, doc_id in enumerate(retrieved[:k]):
        if doc_id in relevant:
            dcg += 1.0 / math.log2(i + 2)  # i+2 because log2(1) = 0

    # Ideal DCG: all relevant docs ranked first
    ideal_dcg = 0.0
    for i in range(min(len(relevant), k)):
        ideal_dcg += 1.0 / math.log2(i + 2)

    if ideal_dcg == 0.0:
        return 0.0

    return dcg / ideal_dcg


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """Compute recall at k: fraction of relevant docs retrieved."""
    if not relevant:
        return 0.0
    retrieved_set = set(retrieved[:k])
    return len(retrieved_set & relevant) / len(relevant)


def precision_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """Compute precision at k: fraction of retrieved docs that are relevant."""
    retrieved_top_k = retrieved[:k]
    if not retrieved_top_k:
        return 0.0
    return sum(1 for d in retrieved_top_k if d in relevant) / len(retrieved_top_k)


def mrr(retrieved: list[str], relevant: set[str]) -> float:
    """Compute mean reciprocal rank: 1/rank of first relevant result."""
    for i, doc_id in enumerate(retrieved):
        if doc_id in relevant:
            return 1.0 / (i + 1)
    return 0.0

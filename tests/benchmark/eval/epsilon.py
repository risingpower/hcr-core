"""Per-level routing accuracy (epsilon) — novel metric for HCR.

Epsilon measures the fraction of queries where the beam search at a given
tree level does NOT contain the correct branch (the one leading to the
gold-standard chunk). Lower is better. epsilon=0 means perfect routing.
"""

from hcr_core.types.metrics import EpsilonMeasurement
from hcr_core.types.query import Query
from hcr_core.types.tree import HCRTree, TreeNode


def _find_ancestor_at_level(
    tree: HCRTree, chunk_id: str, target_level: int
) -> str | None:
    """Find the ancestor node of a chunk at a specific tree level."""
    # Find leaf node with this chunk_id
    leaf_node: TreeNode | None = None
    for node in tree.nodes.values():
        if node.is_leaf and node.chunk_id == chunk_id:
            leaf_node = node
            break

    if leaf_node is None:
        return None

    # Walk up the tree to find the ancestor at the target level
    current = leaf_node
    while current.level > target_level:
        if not current.parent_ids:
            return None
        parent_id = current.parent_ids[0]
        parent = tree.nodes.get(parent_id)
        if parent is None:
            return None
        current = parent

    if current.level == target_level:
        return current.id
    return None


def compute_epsilon(
    tree: HCRTree,
    queries: list[Query],
    beam_results: dict[str, dict[int, list[str]]],
) -> list[EpsilonMeasurement]:
    """Compute per-level routing accuracy.

    Args:
        tree: The HCR tree.
        queries: Queries with gold_chunk_ids.
        beam_results: For each query_id, a dict of {level: [node_ids in beam]}.

    Returns:
        EpsilonMeasurement per level.
    """
    # Collect all levels that have beam data
    all_levels: set[int] = set()
    for level_beams in beam_results.values():
        all_levels.update(level_beams.keys())

    measurements: list[EpsilonMeasurement] = []

    for level in sorted(all_levels):
        evaluated = 0
        correct = 0

        for query in queries:
            if query.id not in beam_results:
                continue
            level_beam = beam_results[query.id].get(level)
            if level_beam is None:
                continue

            evaluated += 1

            # Check if ANY gold chunk's ancestor at this level is in the beam
            found = False
            for gold_chunk_id in query.gold_chunk_ids:
                ancestor = _find_ancestor_at_level(tree, gold_chunk_id, level)
                if ancestor is not None and ancestor in level_beam:
                    found = True
                    break

            if found:
                correct += 1

        if evaluated > 0:
            epsilon = 1.0 - (correct / evaluated)
            measurements.append(
                EpsilonMeasurement(
                    level=level,
                    queries_evaluated=evaluated,
                    correct_branch_in_beam=correct,
                    epsilon=epsilon,
                )
            )

    return measurements

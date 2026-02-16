#!/usr/bin/env python3
"""Summary quality inspector — traces query routing through HCR tree.

For each query, shows:
1. The gold chunk's path through the tree (leaf → root)
2. What the beam search actually selected at each level
3. Cross-encoder scores for correct branch vs selected branches
4. Summary text comparison (what the correct branch says vs what was chosen)

Usage:
    set -a && source .env && set +a
    python scripts/inspect_summaries.py                      # All queries
    python scripts/inspect_summaries.py --failures-only      # Only misrouted queries
    python scripts/inspect_summaries.py --level 1            # Focus on L1 failures
    python scripts/inspect_summaries.py --query-id <id>      # Single query trace
    python scripts/inspect_summaries.py --top-n 5            # Worst N failures
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hcr_core.corpus.embedder import ChunkEmbedder, EmbeddingCache
from hcr_core.scoring.cross_encoder import CrossEncoderScorer
from hcr_core.types.corpus import Chunk
from hcr_core.types.query import Query
from hcr_core.types.tree import HCRTree, TreeNode


def load_chunks(corpus_dir: Path) -> list[Chunk]:
    """Load prepared chunks from corpus directory."""
    chunks_path = corpus_dir / "chunks.json"
    raw = json.loads(chunks_path.read_text())
    return [Chunk.model_validate(c) for c in raw]


def load_tree(results_dir: Path) -> HCRTree:
    tree_path = results_dir / "hcr_tree.json"
    return HCRTree.model_validate_json(tree_path.read_text())


def load_queries(queries_dir: Path) -> list[Query]:
    queries_path = queries_dir / "queries.json"
    raw = json.loads(queries_path.read_text())
    return [Query.model_validate(q) for q in raw]


def find_ancestor_path(
    tree: HCRTree, chunk_id: str
) -> list[str]:
    """Find the full path from leaf to root for a chunk."""
    # Find leaf
    leaf: TreeNode | None = None
    for node in tree.nodes.values():
        if node.is_leaf and node.chunk_id == chunk_id:
            leaf = node
            break

    if leaf is None:
        return []

    path = [leaf.id]
    current = leaf
    while current.parent_ids:
        parent_id = current.parent_ids[0]
        parent = tree.nodes.get(parent_id)
        if parent is None:
            break
        path.append(parent.id)
        current = parent

    path.reverse()
    return path


def summary_text(node: TreeNode) -> str:
    """Format a node's summary for display."""
    if node.summary is None:
        if node.chunk_id:
            return f"[leaf: {node.chunk_id}]"
        return "[no summary]"
    s = node.summary
    lines = [
        f"Theme: {s.theme}",
        f"Includes: {', '.join(s.includes)}",
        f"Excludes: {', '.join(s.excludes)}",
        f"Entities: {', '.join(s.key_entities)}",
        f"Terms: {', '.join(s.key_terms)}",
    ]
    return "\n".join(lines)


def cascade_text(node: TreeNode) -> str:
    """The text the cross-encoder actually sees for this node."""
    if node.summary is not None:
        return (
            f"Theme: {node.summary.theme}. "
            f"Includes: {', '.join(node.summary.includes)}. "
            f"Excludes: {', '.join(node.summary.excludes)}."
        )
    if node.is_leaf and node.chunk_id is not None:
        return f"[chunk content: {node.chunk_id}]"
    return "[no text]"


def trace_query(
    query: Query,
    tree: HCRTree,
    embedder: ChunkEmbedder,
    cross_encoder: CrossEncoderScorer,
    chunk_embeddings: dict[str, NDArray[np.float32]],
    chunk_texts: dict[str, str],
    focus_level: int | None = None,
) -> dict:
    """Trace a single query through the tree, scoring at each level."""
    gold_chunk_id = query.gold_chunk_ids[0]
    gold_path = find_ancestor_path(tree, gold_chunk_id)

    if not gold_path:
        return {
            "query_id": query.id,
            "query_text": query.text,
            "error": f"Gold chunk {gold_chunk_id} not found in tree",
        }

    query_embedding = embedder.embed_text(query.text)
    # Normalise
    norm = float(np.linalg.norm(query_embedding))
    if norm > 0:
        query_embedding = query_embedding / norm

    levels: list[dict] = []
    root = tree.nodes[tree.root_id]

    # Walk down from root, at each internal node score ALL children
    nodes_to_inspect = [root]

    for gold_node_id in gold_path:
        node = tree.nodes[gold_node_id]
        if node.is_leaf:
            break
        if not node.child_ids:
            break

        # Find the correct child (next in gold path)
        node_idx = gold_path.index(gold_node_id)
        if node_idx + 1 >= len(gold_path):
            break
        correct_child_id = gold_path[node_idx + 1]

        # Score ALL children of this node
        children = [tree.nodes[cid] for cid in node.child_ids if cid in tree.nodes]

        # Stage 1: Cosine similarity
        cosine_scores: list[tuple[str, float]] = []
        for child in children:
            emb: NDArray[np.float32] | None = None
            if child.summary_embedding is not None:
                emb = np.array(child.summary_embedding, dtype=np.float32)
            elif child.is_leaf and child.chunk_id:
                emb = chunk_embeddings.get(child.chunk_id)

            if emb is not None:
                child_norm = float(np.linalg.norm(emb))
                if child_norm > 0:
                    emb = emb / child_norm
                sim = float(np.dot(query_embedding, emb))
            else:
                sim = 0.0
            cosine_scores.append((child.id, sim))

        cosine_scores.sort(key=lambda x: x[1], reverse=True)

        # Find rank of correct child in cosine scores
        cosine_rank = next(
            (i + 1 for i, (cid, _) in enumerate(cosine_scores) if cid == correct_child_id),
            -1,
        )

        # Stage 2: Cross-encoder scores for ALL children
        ce_scores: list[tuple[str, float]] = []
        for child in children:
            text = cascade_text(child)
            score = cross_encoder.score(query.text, text, chunk_id=child.id)
            ce_scores.append((child.id, score))

        ce_scores.sort(key=lambda x: x[1], reverse=True)

        # Find rank of correct child in CE scores
        ce_rank = next(
            (i + 1 for i, (cid, _) in enumerate(ce_scores) if cid == correct_child_id),
            -1,
        )

        correct_cosine = next(s for cid, s in cosine_scores if cid == correct_child_id)
        correct_ce = next(s for cid, s in ce_scores if cid == correct_child_id)

        level_data = {
            "parent_node": node.id,
            "parent_level": node.level,
            "num_children": len(children),
            "correct_child": correct_child_id,
            "correct_child_summary": summary_text(tree.nodes[correct_child_id]),
            "cosine": {
                "correct_rank": cosine_rank,
                "correct_score": round(correct_cosine, 4),
                "top1_id": cosine_scores[0][0],
                "top1_score": round(cosine_scores[0][1], 4),
                "top3": [(cid, round(s, 4)) for cid, s in cosine_scores[:3]],
                "in_top3": cosine_rank <= 3,
            },
            "cross_encoder": {
                "correct_rank": ce_rank,
                "correct_score": round(correct_ce, 4),
                "top1_id": ce_scores[0][0],
                "top1_score": round(ce_scores[0][1], 4),
                "top3": [(cid, round(s, 4)) for cid, s in ce_scores[:3]],
                "in_top3": ce_rank <= 3,
            },
        }

        # Add top1 summary for comparison if top1 != correct
        if ce_scores[0][0] != correct_child_id:
            wrong_node = tree.nodes[ce_scores[0][0]]
            level_data["top1_ce_summary"] = summary_text(wrong_node)

        levels.append(level_data)

    # Determine first failure level
    first_fail_cosine = None
    first_fail_ce = None
    for lvl in levels:
        if not lvl["cosine"]["in_top3"] and first_fail_cosine is None:
            first_fail_cosine = lvl["parent_level"]
        if not lvl["cross_encoder"]["in_top3"] and first_fail_ce is None:
            first_fail_ce = lvl["parent_level"]

    return {
        "query_id": query.id,
        "query_text": query.text,
        "category": (
            query.category.value if hasattr(query.category, "value") else str(query.category)
        ),
        "gold_chunk_id": gold_chunk_id,
        "gold_path": gold_path,
        "gold_path_levels": [tree.nodes[nid].level for nid in gold_path],
        "first_fail_cosine": first_fail_cosine,
        "first_fail_ce": first_fail_ce,
        "levels": levels,
    }


def print_trace(trace: dict, verbose: bool = True) -> None:
    """Pretty-print a query trace."""
    print(f"\n{'='*80}")
    print(f"QUERY: {trace['query_text']}")
    print(f"ID: {trace['query_id']}")
    print(f"Category: {trace.get('category', 'N/A')}")
    print(f"Gold chunk: {trace.get('gold_chunk_id', 'N/A')}")
    print(f"Gold path: {' -> '.join(trace.get('gold_path', []))}")

    if "error" in trace:
        print(f"ERROR: {trace['error']}")
        return

    first_cos = trace.get("first_fail_cosine")
    first_ce = trace.get("first_fail_ce")
    print(f"First cosine failure: {'None (all correct)' if first_cos is None else f'Level {first_cos}'}")
    print(f"First CE failure: {'None (all correct)' if first_ce is None else f'Level {first_ce}'}")

    for lvl in trace["levels"]:
        print(f"\n  --- Level {lvl['parent_level']} ({lvl['parent_node']}, {lvl['num_children']} children) ---")

        cos = lvl["cosine"]
        ce = lvl["cross_encoder"]
        correct = lvl["correct_child"]

        # Cosine summary
        cos_status = "OK" if cos["in_top3"] else "MISS"
        print(f"  Cosine: rank={cos['correct_rank']}/{lvl['num_children']} "
              f"score={cos['correct_score']} [{cos_status}]")
        print(f"    Top-3: {cos['top3']}")

        # CE summary
        ce_status = "OK" if ce["in_top3"] else "MISS"
        print(f"  CE:     rank={ce['correct_rank']}/{lvl['num_children']} "
              f"score={ce['correct_score']} [{ce_status}]")
        print(f"    Top-3: {ce['top3']}")

        if verbose:
            print(f"\n  Correct child ({correct}):")
            for line in lvl["correct_child_summary"].split("\n"):
                print(f"    {line}")

            if "top1_ce_summary" in lvl:
                print(f"\n  CE chose ({ce['top1_id']}) instead:")
                for line in lvl["top1_ce_summary"].split("\n"):
                    print(f"    {line}")


def print_aggregate(traces: list[dict]) -> None:
    """Print aggregate failure analysis."""
    total = len(traces)
    valid = [t for t in traces if "error" not in t]

    # Per-level failure counts
    level_cosine_fails: dict[int, int] = {}
    level_ce_fails: dict[int, int] = {}
    level_total: dict[int, int] = {}

    for t in valid:
        for lvl in t["levels"]:
            level = lvl["parent_level"]
            level_total[level] = level_total.get(level, 0) + 1
            if not lvl["cosine"]["in_top3"]:
                level_cosine_fails[level] = level_cosine_fails.get(level, 0) + 1
            if not lvl["cross_encoder"]["in_top3"]:
                level_ce_fails[level] = level_ce_fails.get(level, 0) + 1

    print(f"\n{'='*80}")
    print("AGGREGATE ANALYSIS")
    print(f"{'='*80}")
    print(f"Total queries: {total}, Valid traces: {len(valid)}")

    print(f"\n{'Per-Level Routing Accuracy':^50}")
    print(f"{'Level':<8} {'Cosine miss':>14} {'CE miss':>14} {'Queries':>10}")
    print("-" * 50)
    for level in sorted(level_total.keys()):
        cos_f = level_cosine_fails.get(level, 0)
        ce_f = level_ce_fails.get(level, 0)
        n = level_total[level]
        print(
            f"L{level:<7} {cos_f:>6}/{n:<4} ({cos_f/n*100:>4.0f}%) "
            f"{ce_f:>4}/{n:<4} ({ce_f/n*100:>4.0f}%)"
        )

    # Where does cosine get it right but CE screws it up?
    cosine_ok_ce_fail = 0
    cosine_fail_ce_ok = 0
    both_fail = 0
    both_ok = 0
    for t in valid:
        for lvl in t["levels"]:
            cos_ok = lvl["cosine"]["in_top3"]
            ce_ok = lvl["cross_encoder"]["in_top3"]
            if cos_ok and ce_ok:
                both_ok += 1
            elif cos_ok and not ce_ok:
                cosine_ok_ce_fail += 1
            elif not cos_ok and ce_ok:
                cosine_fail_ce_ok += 1
            else:
                both_fail += 1

    total_decisions = both_ok + cosine_ok_ce_fail + cosine_fail_ce_ok + both_fail
    print(f"\nRouting Decision Breakdown (all levels, N={total_decisions}):")
    print(f"  Both correct:         {both_ok:>4} ({both_ok/total_decisions*100:.0f}%)")
    print(f"  Cosine OK, CE wrong:  {cosine_ok_ce_fail:>4} ({cosine_ok_ce_fail/total_decisions*100:.0f}%)")
    print(f"  Cosine wrong, CE OK:  {cosine_fail_ce_ok:>4} ({cosine_fail_ce_ok/total_decisions*100:.0f}%)")
    print(f"  Both wrong:           {both_fail:>4} ({both_fail/total_decisions*100:.0f}%)")

    if cosine_ok_ce_fail > 0:
        print(f"\n  ** CE is HURTING routing in {cosine_ok_ce_fail} decisions "
              f"where cosine alone was correct **")

    # CE score distribution for correct vs incorrect
    correct_ce_scores: list[float] = []
    incorrect_ce_scores: list[float] = []
    for t in valid:
        for lvl in t["levels"]:
            ce = lvl["cross_encoder"]
            if ce["correct_rank"] == 1:
                correct_ce_scores.append(ce["correct_score"])
            else:
                incorrect_ce_scores.append(ce["correct_score"])
                # Also get the score of whatever CE picked
                incorrect_ce_scores.append(ce["top1_score"])

    if correct_ce_scores:
        print(f"\nCE Score Distribution:")
        print(f"  When correct (rank=1): mean={np.mean(correct_ce_scores):.3f}, "
              f"min={np.min(correct_ce_scores):.3f}, max={np.max(correct_ce_scores):.3f}")
    if incorrect_ce_scores:
        print(f"  When incorrect: mean correct branch score={np.mean([s for i, s in enumerate(incorrect_ce_scores) if i % 2 == 0]):.3f}, "
              f"mean top1 score={np.mean([s for i, s in enumerate(incorrect_ce_scores) if i % 2 == 1]):.3f}")

    # Category breakdown
    cat_fails: dict[str, tuple[int, int]] = {}  # cat -> (fails, total)
    for t in valid:
        cat = t.get("category", "unknown")
        has_any_fail = any(not lvl["cross_encoder"]["in_top3"] for lvl in t["levels"])
        prev = cat_fails.get(cat, (0, 0))
        cat_fails[cat] = (prev[0] + (1 if has_any_fail else 0), prev[1] + 1)

    print(f"\nPer-Category Failure Rate (any level CE miss):")
    for cat in sorted(cat_fails, key=lambda c: cat_fails[c][0] / max(cat_fails[c][1], 1), reverse=True):
        fails, total = cat_fails[cat]
        print(f"  {cat:<20} {fails}/{total} ({fails/total*100:.0f}%)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect HCR routing summary quality")
    parser.add_argument("--failures-only", action="store_true", help="Only show queries with routing failures")
    parser.add_argument("--level", type=int, help="Focus on failures at this tree level")
    parser.add_argument("--query-id", type=str, help="Trace a single query")
    parser.add_argument("--top-n", type=int, help="Show N worst failures")
    parser.add_argument("--results-dir", type=str, default="benchmark/results")
    parser.add_argument("--queries-dir", type=str, default="benchmark/queries")
    parser.add_argument("--corpus-dir", type=str, default="benchmark/corpus")
    parser.add_argument("--brief", action="store_true", help="Aggregate only, skip per-query traces")
    parser.add_argument("--json", action="store_true", help="Output traces as JSON")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    queries_dir = Path(args.queries_dir)
    corpus_dir = Path(args.corpus_dir)

    # Load everything
    print("Loading tree...")
    tree = load_tree(results_dir)

    print("Loading queries...")
    queries = load_queries(queries_dir)

    print("Loading corpus and embeddings...")
    chunks = load_chunks(corpus_dir)
    chunk_map = {c.id: c for c in chunks}

    cache = EmbeddingCache(Path("benchmark/cache/embeddings"))
    embedder = ChunkEmbedder(cache=cache)
    chunk_ids, embeddings = embedder.embed(chunks, corpus_key="benchmark")
    chunk_embeddings = {
        cid: embeddings[i] for i, cid in enumerate(chunk_ids)
    }
    chunk_texts = {c.id: c.content for c in chunks}

    print("Loading cross-encoder...")
    cross_encoder = CrossEncoderScorer()

    # Filter queries if needed
    if args.query_id:
        queries = [q for q in queries if q.id == args.query_id]
        if not queries:
            print(f"Query {args.query_id} not found")
            return

    # Trace all queries
    print(f"\nTracing {len(queries)} queries through tree...")
    traces: list[dict] = []
    for i, query in enumerate(queries):
        trace = trace_query(
            query=query,
            tree=tree,
            embedder=embedder,
            cross_encoder=cross_encoder,
            chunk_embeddings=chunk_embeddings,
            chunk_texts=chunk_texts,
            focus_level=args.level,
        )
        traces.append(trace)
        if (i + 1) % 10 == 0:
            print(f"  Traced {i + 1}/{len(queries)} queries")

    # Filter for display
    display_traces = traces

    if args.failures_only:
        display_traces = [
            t for t in display_traces
            if t.get("first_fail_ce") is not None
        ]

    if args.level is not None:
        display_traces = [
            t for t in display_traces
            if any(
                lvl["parent_level"] == args.level
                and not lvl["cross_encoder"]["in_top3"]
                for lvl in t.get("levels", [])
            )
        ]

    if args.top_n:
        # Sort by earliest failure level (worst first)
        def fail_severity(t: dict) -> tuple[int, float]:
            fail_level = t.get("first_fail_ce")
            if fail_level is None:
                return (999, 0.0)
            # Earlier failure = worse. For ties, lower CE score = worse.
            worst_ce = min(
                (lvl["cross_encoder"]["correct_score"] for lvl in t["levels"]),
                default=0.0,
            )
            return (fail_level, worst_ce)

        display_traces.sort(key=fail_severity)
        display_traces = display_traces[: args.top_n]

    if args.json:
        print(json.dumps(traces, indent=2))
        return

    # Print aggregate first
    print_aggregate(traces)

    # Print individual traces
    if not args.brief:
        for trace in display_traces:
            print_trace(trace)

    print(f"\n{'='*80}")
    print(f"Total traced: {len(traces)}, Displayed: {len(display_traces)}")


if __name__ == "__main__":
    main()

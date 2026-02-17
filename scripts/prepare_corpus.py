"""Download and prepare benchmark corpus at various scales.

Usage:
    python scripts/prepare_corpus.py [--scale small|medium|large] [--skip-download]

Scales:
    small  - GitLab handbook subset (50 docs, ~315 chunks). Phase A default.
    medium - Full GitLab handbook (~13-25K chunks).
    large  - Full GitLab handbook + Wikipedia articles (~60K chunks).

Downloads the GitLab handbook (public), optionally loads Wikipedia articles,
chunks everything, and saves prepared corpus for benchmark evaluation.
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path

from hcr_core.corpus.chunker import chunk_document
from hcr_core.corpus.loader import load_corpus
from hcr_core.types.corpus import Chunk, Document

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

HANDBOOK_REPO = "https://github.com/AnswerDotAI/gitlab-handbook.git"
HANDBOOK_DIR_NAME = "gitlab-handbook"
CONTENT_SUBDIR = "content/handbook"  # Where handbook markdown lives

# Scale-specific output directory names
SCALE_OUTPUT_DIRS: dict[str, str] = {
    "small": "benchmark/corpus",
    "medium": "benchmark/corpus-medium",
    "large": "benchmark/corpus-large",
}


def clone_handbook(data_dir: Path) -> Path:
    """Clone the GitLab handbook repo (shallow) into data_dir."""
    repo_dir = data_dir / HANDBOOK_DIR_NAME
    if repo_dir.exists():
        logger.info("Handbook repo already exists at %s, skipping clone", repo_dir)
        return repo_dir

    data_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Cloning GitLab handbook (shallow)...")
    subprocess.run(
        ["git", "clone", "--depth", "1", HANDBOOK_REPO, str(repo_dir)],
        check=True,
    )
    logger.info("Clone complete: %s", repo_dir)
    return repo_dir


def find_content_dir(repo_dir: Path) -> Path:
    """Find the directory containing handbook markdown content."""
    # Try known paths
    candidates = [
        repo_dir / CONTENT_SUBDIR,
        repo_dir / "content",
        repo_dir / "handbook",
        repo_dir / "source" / "handbook",
        repo_dir,
    ]
    for candidate in candidates:
        if candidate.is_dir():
            # Check it actually has markdown files
            md_files = list(candidate.rglob("*.md"))
            if len(md_files) > 10:
                logger.info("Found content dir: %s (%d markdown files)", candidate, len(md_files))
                return candidate

    raise FileNotFoundError(
        f"Could not find handbook content directory in {repo_dir}. "
        f"Tried: {[str(c) for c in candidates]}"
    )


def load_and_chunk(
    content_dir: Path,
    source_name: str = "gitlab-handbook",
    max_docs: int | None = None,
    max_chunk_tokens: int = 512,
    overlap_tokens: int = 50,
) -> tuple[list[Document], list[Chunk]]:
    """Load documents and chunk them."""
    documents = load_corpus(content_dir, source_name=source_name)
    logger.info("Loaded %d documents", len(documents))

    if max_docs is not None:
        documents = documents[:max_docs]
        logger.info("Subset to %d documents", len(documents))

    all_chunks: list[Chunk] = []
    for doc in documents:
        chunks = chunk_document(doc, max_tokens=max_chunk_tokens, overlap_tokens=overlap_tokens)
        all_chunks.extend(chunks)

    logger.info("Chunked into %d chunks", len(all_chunks))

    total_tokens = sum(c.token_count for c in all_chunks)
    logger.info("Total tokens: %d", total_tokens)
    logger.info(
        "Chunk token stats: min=%d, max=%d, mean=%.0f",
        min(c.token_count for c in all_chunks),
        max(c.token_count for c in all_chunks),
        total_tokens / len(all_chunks),
    )

    return documents, all_chunks


def save_corpus(
    output_dir: Path,
    documents: list[Document],
    chunks: list[Chunk],
    compact: bool = False,
) -> None:
    """Save prepared corpus to disk.

    Args:
        output_dir: Where to write output files.
        documents: List of source documents.
        chunks: List of text chunks.
        compact: If True, write JSON without indentation (smaller files for large corpora).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    indent = None if compact else 2

    # Save documents
    docs_path = output_dir / "documents.json"
    docs_data = [d.model_dump() for d in documents]
    docs_path.write_text(json.dumps(docs_data, indent=indent))
    logger.info("Saved %d documents to %s", len(documents), docs_path)

    # Save chunks
    chunks_path = output_dir / "chunks.json"
    chunks_data = [c.model_dump() for c in chunks]
    chunks_path.write_text(json.dumps(chunks_data, indent=indent))
    logger.info("Saved %d chunks to %s", len(chunks), chunks_path)

    # Compute source breakdown
    source_counts: dict[str, int] = {}
    for doc in documents:
        source_counts[doc.source] = source_counts.get(doc.source, 0) + 1
    doc_source_map = {doc.id: doc.source for doc in documents}
    source_chunk_counts: dict[str, int] = {}
    for chunk in chunks:
        source = doc_source_map.get(chunk.document_id, "unknown")
        source_chunk_counts[source] = source_chunk_counts.get(source, 0) + 1

    # Save summary stats
    stats: dict[str, object] = {
        "document_count": len(documents),
        "chunk_count": len(chunks),
        "total_tokens": sum(c.token_count for c in chunks),
        "mean_chunk_tokens": sum(c.token_count for c in chunks) / len(chunks),
        "min_chunk_tokens": min(c.token_count for c in chunks),
        "max_chunk_tokens": max(c.token_count for c in chunks),
        "source_documents": source_counts,
        "source_chunks": source_chunk_counts,
    }
    stats_path = output_dir / "corpus_stats.json"
    stats_path.write_text(json.dumps(stats, indent=2))
    logger.info("Saved corpus stats to %s", stats_path)


def prepare_small(
    data_dir: Path,
    output_dir: Path,
    skip_download: bool,
    max_chunk_tokens: int,
) -> None:
    """Prepare small corpus (Phase A default): 50-doc subset of GitLab handbook."""
    repo_dir = _get_handbook(data_dir, skip_download)
    content_dir = find_content_dir(repo_dir)
    documents, chunks = load_and_chunk(
        content_dir, max_docs=50, max_chunk_tokens=max_chunk_tokens,
    )
    save_corpus(output_dir, documents, chunks)


def prepare_medium(
    data_dir: Path,
    output_dir: Path,
    skip_download: bool,
    max_chunk_tokens: int,
) -> None:
    """Prepare medium corpus: full GitLab handbook, no subset."""
    repo_dir = _get_handbook(data_dir, skip_download)
    content_dir = find_content_dir(repo_dir)
    documents, chunks = load_and_chunk(
        content_dir, max_docs=None, max_chunk_tokens=max_chunk_tokens,
    )
    save_corpus(output_dir, documents, chunks, compact=True)


def prepare_large(
    data_dir: Path,
    output_dir: Path,
    skip_download: bool,
    max_chunk_tokens: int,
) -> None:
    """Prepare large corpus: full GitLab handbook + Wikipedia articles."""
    from hcr_core.corpus.wikipedia import load_wikipedia_articles

    # Part 1: Full GitLab handbook
    repo_dir = _get_handbook(data_dir, skip_download)
    content_dir = find_content_dir(repo_dir)
    gitlab_docs, gitlab_chunks = load_and_chunk(
        content_dir, max_docs=None, max_chunk_tokens=max_chunk_tokens,
    )
    logger.info(
        "GitLab handbook: %d documents, %d chunks",
        len(gitlab_docs),
        len(gitlab_chunks),
    )

    # Part 2: Wikipedia articles
    logger.info("Loading Wikipedia articles...")
    wiki_docs = load_wikipedia_articles(target_count=2500, seed=42)
    logger.info("Wikipedia: %d articles loaded", len(wiki_docs))

    # Chunk Wikipedia articles
    wiki_chunks: list[Chunk] = []
    for doc in wiki_docs:
        chunks = chunk_document(doc, max_tokens=max_chunk_tokens, overlap_tokens=50)
        wiki_chunks.extend(chunks)
    logger.info("Wikipedia: %d chunks", len(wiki_chunks))

    # Combine
    all_docs = gitlab_docs + wiki_docs
    all_chunks = gitlab_chunks + wiki_chunks
    logger.info(
        "Combined corpus: %d documents, %d chunks",
        len(all_docs),
        len(all_chunks),
    )

    save_corpus(output_dir, all_docs, all_chunks, compact=True)


def _get_handbook(data_dir: Path, skip_download: bool) -> Path:
    """Get handbook repo directory, downloading if needed."""
    if not skip_download:
        return clone_handbook(data_dir)

    repo_dir = data_dir / HANDBOOK_DIR_NAME
    if not repo_dir.exists():
        logger.error(
            "No handbook data at %s. Run without --skip-download.",
            repo_dir,
        )
        sys.exit(1)
    return repo_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare benchmark corpus")
    parser.add_argument(
        "--scale",
        choices=["small", "medium", "large"],
        default="small",
        help="Corpus scale: small (315 chunks), medium (full GitLab), large (GitLab + Wikipedia).",
    )
    parser.add_argument(
        "--subset", type=int, default=None,
        help="(Deprecated, use --scale) Limit to N documents.",
    )
    parser.add_argument(
        "--output-dir", type=str, default=None,
        help="Output directory. Defaults to scale-specific directory.",
    )
    parser.add_argument(
        "--data-dir", type=str, default="data",
        help="Directory for raw downloaded data (gitignored).",
    )
    parser.add_argument(
        "--max-chunk-tokens", type=int, default=512,
        help="Maximum tokens per chunk.",
    )
    parser.add_argument(
        "--skip-download", action="store_true",
        help="Skip download, use existing data.",
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    data_dir = project_root / args.data_dir

    # Determine output directory
    if args.output_dir:
        output_dir = project_root / args.output_dir
    else:
        output_dir = project_root / SCALE_OUTPUT_DIRS[args.scale]

    # Handle deprecated --subset flag
    if args.subset is not None:
        logger.warning("--subset is deprecated. Use --scale instead.")
        repo_dir = _get_handbook(data_dir, args.skip_download)
        content_dir = find_content_dir(repo_dir)
        documents, chunks = load_and_chunk(
            content_dir,
            max_docs=args.subset,
            max_chunk_tokens=args.max_chunk_tokens,
        )
        save_corpus(output_dir, documents, chunks)
        logger.info("Corpus preparation complete.")
        return

    # Scale-specific preparation
    if args.scale == "small":
        prepare_small(data_dir, output_dir, args.skip_download, args.max_chunk_tokens)
    elif args.scale == "medium":
        prepare_medium(data_dir, output_dir, args.skip_download, args.max_chunk_tokens)
    elif args.scale == "large":
        prepare_large(data_dir, output_dir, args.skip_download, args.max_chunk_tokens)

    logger.info("Corpus preparation complete (%s scale).", args.scale)


if __name__ == "__main__":
    main()

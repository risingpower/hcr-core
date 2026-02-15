"""Download and prepare benchmark corpus from GitLab handbook.

Usage:
    python scripts/prepare_corpus.py [--subset N] [--output-dir benchmark/corpus]

Downloads the GitLab handbook (public), chunks it, and saves prepared corpus
for benchmark evaluation. Use --subset to limit document count for testing.
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
) -> None:
    """Save prepared corpus to disk."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save documents
    docs_path = output_dir / "documents.json"
    docs_data = [d.model_dump() for d in documents]
    docs_path.write_text(json.dumps(docs_data, indent=2))
    logger.info("Saved %d documents to %s", len(documents), docs_path)

    # Save chunks
    chunks_path = output_dir / "chunks.json"
    chunks_data = [c.model_dump() for c in chunks]
    chunks_path.write_text(json.dumps(chunks_data, indent=2))
    logger.info("Saved %d chunks to %s", len(chunks), chunks_path)

    # Save summary stats
    stats = {
        "document_count": len(documents),
        "chunk_count": len(chunks),
        "total_tokens": sum(c.token_count for c in chunks),
        "mean_chunk_tokens": sum(c.token_count for c in chunks) / len(chunks),
        "min_chunk_tokens": min(c.token_count for c in chunks),
        "max_chunk_tokens": max(c.token_count for c in chunks),
    }
    stats_path = output_dir / "corpus_stats.json"
    stats_path.write_text(json.dumps(stats, indent=2))
    logger.info("Saved corpus stats to %s", stats_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare benchmark corpus")
    parser.add_argument(
        "--subset", type=int, default=None,
        help="Limit to N documents (for testing). None = full corpus.",
    )
    parser.add_argument(
        "--output-dir", type=str, default="benchmark/corpus",
        help="Output directory for prepared corpus.",
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
    output_dir = project_root / args.output_dir

    if not args.skip_download:
        repo_dir = clone_handbook(data_dir)
    else:
        repo_dir = data_dir / HANDBOOK_DIR_NAME
        if not repo_dir.exists():
            logger.error(
                "No handbook data at %s. Run without --skip-download.",
                repo_dir,
            )
            sys.exit(1)

    content_dir = find_content_dir(repo_dir)

    documents, chunks = load_and_chunk(
        content_dir,
        max_docs=args.subset,
        max_chunk_tokens=args.max_chunk_tokens,
    )

    save_corpus(output_dir, documents, chunks)
    logger.info("Corpus preparation complete.")


if __name__ == "__main__":
    main()

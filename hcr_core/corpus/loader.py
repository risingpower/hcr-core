"""Corpus loading from various sources."""

from pathlib import Path

from hcr_core.types.corpus import Document


def load_corpus(source_dir: Path, source_name: str) -> list[Document]:
    """Load all text/markdown files from a directory as Documents."""
    source_dir = Path(source_dir)
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    documents: list[Document] = []
    extensions = {".md", ".txt", ".rst"}

    for idx, filepath in enumerate(sorted(source_dir.rglob("*"))):
        if filepath.suffix.lower() not in extensions:
            continue
        if not filepath.is_file():
            continue
        content = filepath.read_text(encoding="utf-8", errors="replace").strip()
        if not content:
            continue
        rel_path = filepath.relative_to(source_dir)
        documents.append(
            Document(
                id=f"{source_name}-{idx:05d}",
                source=source_name,
                content=content,
                metadata={"path": str(rel_path)},
            )
        )

    return documents


def load_gitlab_handbook(path: Path) -> list[Document]:
    """Load GitLab handbook markdown files."""
    return load_corpus(path, source_name="gitlab-handbook")

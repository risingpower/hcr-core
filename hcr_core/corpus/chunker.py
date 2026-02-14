"""Document chunking with semantic boundary preservation."""

import tiktoken

from hcr_core.types.corpus import Chunk, Document

_ENCODER = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """Count tokens using tiktoken cl100k_base encoding."""
    if not text:
        return 0
    return len(_ENCODER.encode(text))


def chunk_document(
    doc: Document,
    max_tokens: int = 512,
    overlap_tokens: int = 50,
) -> list[Chunk]:
    """Split a document into chunks respecting token limits and semantic boundaries.

    Strategy: split on paragraph boundaries first, then sentence boundaries,
    then fall back to token-level splitting.
    """
    content = doc.content.strip()
    if not content:
        return []

    total_tokens = count_tokens(content)
    if total_tokens <= max_tokens:
        return [
            Chunk(
                id=f"{doc.id}-0",
                document_id=doc.id,
                content=content,
                token_count=total_tokens,
            )
        ]

    segments = _split_into_segments(content)
    chunks: list[Chunk] = []
    current_segments: list[str] = []
    current_tokens = 0
    chunk_idx = 0

    for segment in segments:
        seg_tokens = count_tokens(segment)

        if seg_tokens > max_tokens:
            if current_segments:
                text = _join_segments(current_segments)
                chunks.append(
                    Chunk(
                        id=f"{doc.id}-{chunk_idx}",
                        document_id=doc.id,
                        content=text,
                        token_count=count_tokens(text),
                    )
                )
                chunk_idx += 1
                current_segments = []
                current_tokens = 0

            sub_chunks = _force_split(doc.id, chunk_idx, segment, max_tokens, overlap_tokens)
            chunks.extend(sub_chunks)
            chunk_idx += len(sub_chunks)
            continue

        if current_tokens + seg_tokens > max_tokens:
            text = _join_segments(current_segments)
            chunks.append(
                Chunk(
                    id=f"{doc.id}-{chunk_idx}",
                    document_id=doc.id,
                    content=text,
                    token_count=count_tokens(text),
                )
            )
            chunk_idx += 1

            overlap_segs = _get_overlap_segments(current_segments, overlap_tokens)
            current_segments = overlap_segs
            current_tokens = sum(count_tokens(s) for s in current_segments)

        current_segments.append(segment)
        current_tokens += seg_tokens

    if current_segments:
        text = _join_segments(current_segments)
        tc = count_tokens(text)
        if tc > 0:
            chunks.append(
                Chunk(
                    id=f"{doc.id}-{chunk_idx}",
                    document_id=doc.id,
                    content=text,
                    token_count=tc,
                )
            )

    return chunks


def _split_into_segments(text: str) -> list[str]:
    """Split text into segments: prefer paragraph boundaries, then sentences."""
    paragraphs = text.split("\n\n")
    segments: list[str] = []
    for para in paragraphs:
        para = para.strip()
        if para:
            segments.append(para)
    return segments if len(segments) > 1 else _split_sentences(text)


def _split_sentences(text: str) -> list[str]:
    """Simple sentence splitting."""
    sentences: list[str] = []
    current = ""
    for char in text:
        current += char
        if char in ".!?" and len(current.strip()) > 1:
            sentences.append(current.strip())
            current = ""
    if current.strip():
        sentences.append(current.strip())
    return sentences if sentences else [text]


def _join_segments(segments: list[str]) -> str:
    """Join segments with appropriate spacing."""
    return " ".join(s.strip() for s in segments if s.strip())


def _get_overlap_segments(segments: list[str], overlap_tokens: int) -> list[str]:
    """Get trailing segments that fit within the overlap token budget."""
    if overlap_tokens <= 0:
        return []
    result: list[str] = []
    tokens = 0
    for seg in reversed(segments):
        seg_tokens = count_tokens(seg)
        if tokens + seg_tokens > overlap_tokens:
            break
        result.insert(0, seg)
        tokens += seg_tokens
    return result


def _force_split(
    doc_id: str,
    start_idx: int,
    text: str,
    max_tokens: int,
    overlap_tokens: int,
) -> list[Chunk]:
    """Force-split text that exceeds max_tokens at the token level."""
    tokens = _ENCODER.encode(text)
    chunks: list[Chunk] = []
    idx = start_idx
    pos = 0
    while pos < len(tokens):
        end = min(pos + max_tokens, len(tokens))
        chunk_text = _ENCODER.decode(tokens[pos:end])
        tc = end - pos
        if tc > 0 and chunk_text.strip():
            chunks.append(
                Chunk(
                    id=f"{doc_id}-{idx}",
                    document_id=doc_id,
                    content=chunk_text.strip(),
                    token_count=tc,
                )
            )
            idx += 1
        step = max_tokens - overlap_tokens if overlap_tokens < max_tokens else max_tokens
        pos += step
    return chunks

"""Tests for document chunking."""


from hcr_core.corpus.chunker import chunk_document, count_tokens
from hcr_core.types.corpus import Chunk, Document


class TestCountTokens:
    def test_count_empty_string(self) -> None:
        assert count_tokens("") == 0

    def test_count_simple_text(self) -> None:
        count = count_tokens("Hello world")
        assert count > 0
        assert isinstance(count, int)

    def test_count_longer_text(self) -> None:
        short = count_tokens("Hello")
        long = count_tokens("Hello world, this is a longer sentence with more tokens")
        assert long > short


class TestChunkDocument:
    def _make_doc(self, content: str, doc_id: str = "doc-1") -> Document:
        return Document(id=doc_id, source="test", content=content)

    def test_short_document_single_chunk(self) -> None:
        doc = self._make_doc("This is a short document.")
        chunks = chunk_document(doc, max_tokens=512, overlap_tokens=50)
        assert len(chunks) == 1
        assert chunks[0].document_id == "doc-1"
        assert chunks[0].content == "This is a short document."
        assert chunks[0].token_count > 0

    def test_chunk_ids_are_unique(self) -> None:
        doc = self._make_doc("Word " * 2000)
        chunks = chunk_document(doc, max_tokens=100, overlap_tokens=10)
        ids = [c.id for c in chunks]
        assert len(ids) == len(set(ids))

    def test_chunks_respect_max_tokens(self) -> None:
        doc = self._make_doc("Word " * 2000)
        chunks = chunk_document(doc, max_tokens=100, overlap_tokens=10)
        assert len(chunks) > 1
        for chunk in chunks:
            assert chunk.token_count <= 100 + 5  # small tolerance for boundary

    def test_chunks_cover_full_content(self) -> None:
        content = "Sentence one. Sentence two. Sentence three. Sentence four."
        doc = self._make_doc(content)
        chunks = chunk_document(doc, max_tokens=512, overlap_tokens=0)
        combined = " ".join(c.content for c in chunks)
        # All original words should appear
        for word in content.split():
            assert word in combined

    def test_chunk_document_id_links(self) -> None:
        doc = self._make_doc("Some text here.", doc_id="my-doc")
        chunks = chunk_document(doc, max_tokens=512, overlap_tokens=0)
        for chunk in chunks:
            assert chunk.document_id == "my-doc"

    def test_all_chunks_are_chunk_type(self) -> None:
        doc = self._make_doc("Test content for chunking.")
        chunks = chunk_document(doc, max_tokens=512, overlap_tokens=0)
        for chunk in chunks:
            assert isinstance(chunk, Chunk)

    def test_paragraph_boundary_chunking(self) -> None:
        paragraphs = ["Paragraph one about topic A."] * 5 + [
            "Paragraph two about topic B."
        ] * 5
        content = "\n\n".join(paragraphs)
        doc = self._make_doc(content)
        chunks = chunk_document(doc, max_tokens=50, overlap_tokens=5)
        assert len(chunks) >= 2

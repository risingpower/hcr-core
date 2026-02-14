"""Corpus data models: documents and chunks."""

from pydantic import BaseModel, Field, field_validator


class Document(BaseModel):
    """A source document before chunking."""

    id: str
    source: str
    content: str
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("content must not be empty")
        return v


class Chunk(BaseModel):
    """An atomic text unit with token count."""

    id: str
    document_id: str
    content: str
    token_count: int = Field(gt=0)
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("content must not be empty")
        return v

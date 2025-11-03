"""Data models for FileIntel query responses."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    """Metadata about a specific document chunk."""

    page_number: Optional[int] = None
    extraction_method: Optional[str] = None
    source: Optional[str] = None
    backend: Optional[str] = None
    format: Optional[str] = None
    chunk_strategy: Optional[str] = None
    chunk_type: Optional[str] = None


class DocumentMetadata(BaseModel):
    """Metadata about the source document."""

    title: str
    authors: List[str] = Field(default_factory=list)
    author_surnames: List[str] = Field(default_factory=list)
    publication_date: Optional[str] = None
    publisher: Optional[str] = None
    document_type: Optional[str] = None
    language: Optional[str] = None
    harvard_citation: Optional[str] = None
    abstract: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)


class Source(BaseModel):
    """A source from FileIntel with complete metadata.

    This represents a single chunk/source returned by FileIntel's query endpoint.
    It includes pre-formatted citations and complete document metadata.
    """

    document_id: str
    chunk_id: str
    filename: str
    citation: str  # Pre-formatted bibliography citation
    in_text_citation: str  # Pre-formatted inline citation like "(Author, Year, p.X)"
    text: str  # Chunk content/excerpt
    similarity_score: float
    relevance_score: float
    chunk_metadata: ChunkMetadata
    document_metadata: DocumentMetadata

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Source":
        """Create Source from FileIntel API response dict.

        Args:
            data: Raw source dictionary from API

        Returns:
            Source instance
        """
        return cls(
            document_id=data["document_id"],
            chunk_id=data["chunk_id"],
            filename=data["filename"],
            citation=data["citation"],
            in_text_citation=data["in_text_citation"],
            text=data["text"],
            similarity_score=data["similarity_score"],
            relevance_score=data["relevance_score"],
            chunk_metadata=ChunkMetadata(**data.get("chunk_metadata", {})),
            document_metadata=DocumentMetadata(**data.get("document_metadata", {})),
        )


class QueryResponse(BaseModel):
    """Response from FileIntel query endpoint.

    The answer field already includes inline citations in the format [Author, Year, p.X].
    No additional citation placement is needed.
    """

    answer: str  # Generated answer with inline citations
    sources: List[Source]
    query_type: str  # "vector" | "graph" | "hybrid"
    collection_id: str
    question: str
    processing_time_ms: Optional[int] = None
    routing_explanation: Optional[str] = None

    @classmethod
    def from_fileintel_response(cls, data: Dict[str, Any]) -> "QueryResponse":
        """Create QueryResponse from FileIntel API response.

        Args:
            data: Raw API response data (the 'data' field from the response)

        Returns:
            QueryResponse instance
        """
        return cls(
            answer=data["answer"],
            sources=[Source.from_dict(s) for s in data["sources"]],
            query_type=data["query_type"],
            collection_id=data["collection_id"],
            question=data["question"],
            processing_time_ms=data.get("processing_time_ms"),
            routing_explanation=data.get("routing_explanation"),
        )

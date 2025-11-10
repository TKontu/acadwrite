"""
Tests for DocumentProcessor - Smart document processing with operations.
"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from acadwrite.models.query import ChunkMetadata, DocumentMetadata, QueryResponse, Source
from acadwrite.workflows.document_processor import DocumentProcessor, ProcessedChunk
from acadwrite.workflows.markdown_chunker import Chunk, ChunkType


def create_test_source(
    author="Smith",
    publication_date="2020",
    page=None,
    text="Sample text",
) -> Source:
    """Helper to create a test Source with all required fields."""
    return Source(
        document_id="doc1",
        chunk_id="chunk1",
        filename="test.pdf",
        citation=f"{author}, {publication_date}",
        in_text_citation=f"[{author}, {publication_date}]",
        text=text,
        similarity_score=0.95,
        relevance_score=0.90,
        chunk_metadata=ChunkMetadata(page_number=page),
        document_metadata=DocumentMetadata(
            title="Test Document",
            authors=[author] if author else [],
            author_surnames=[author] if author else [],
            publication_date=publication_date,
        ),
    )


def create_test_query_response(sources=None, answer="Test answer") -> QueryResponse:
    """Helper to create a test QueryResponse with all required fields."""
    return QueryResponse(
        sources=sources or [],
        answer=answer,
        query_type="standard",
        collection_id="test_collection",
        question="test question",
    )


class TestDocumentProcessor:
    """Tests for DocumentProcessor class."""

    def test_init_default(self):
        """Test processor initialization with defaults."""
        processor = DocumentProcessor()

        assert processor.fileintel is None
        assert processor.llm is None
        assert processor.chunker is not None

    def test_init_with_clients(self):
        """Test processor initialization with clients."""
        mock_fileintel = Mock()
        mock_llm = Mock()

        processor = DocumentProcessor(fileintel_client=mock_fileintel, llm_client=mock_llm)

        assert processor.fileintel is mock_fileintel
        assert processor.llm is mock_llm

    def test_extract_claims_with_percentages(self):
        """Test extracting claims with percentage statistics."""
        processor = DocumentProcessor()

        text = "Machine learning improves accuracy by 95%. This is a major advancement."

        claims = processor._extract_claims(text)

        # Should extract sentence with percentage
        assert len(claims) >= 1
        assert any("95%" in claim for claim in claims)

    def test_extract_claims_with_decimals(self):
        """Test extracting claims with decimal statistics."""
        processor = DocumentProcessor()

        text = "The model achieved an F1 score of 0.87. Performance varied across datasets."

        claims = processor._extract_claims(text)

        # Should extract sentence with decimal
        assert len(claims) >= 1
        assert any("0.87" in claim for claim in claims)

    def test_extract_claims_with_research_indicators(self):
        """Test extracting claims with research indicators."""
        processor = DocumentProcessor()

        text = "Research shows that deep learning is effective. Studies indicate improvements."

        claims = processor._extract_claims(text)

        # Should extract sentences with research indicators
        assert len(claims) >= 2
        assert any("research shows" in claim.lower() for claim in claims)
        assert any("studies indicate" in claim.lower() for claim in claims)

    def test_extract_claims_with_comparatives(self):
        """Test extracting claims with comparative statements."""
        processor = DocumentProcessor()

        text = "Neural networks are more accurate than traditional methods."

        claims = processor._extract_claims(text)

        # Should extract comparative statement
        assert len(claims) >= 1
        assert any("more accurate than" in claim.lower() for claim in claims)

    def test_extract_claims_no_claims(self):
        """Test extracting claims from text without obvious claims."""
        processor = DocumentProcessor()

        text = "This is a simple sentence. It contains no statistics or claims."

        claims = processor._extract_claims(text)

        # Should return empty or very short list
        assert len(claims) == 0

    def test_has_citation_inline(self):
        """Test detecting inline citations."""
        processor = DocumentProcessor()

        claim = "Machine learning improves accuracy"
        text = "Machine learning improves accuracy [Smith, 2020, p. 15]. Additional text."

        has_citation = processor._has_citation(claim, text)

        assert has_citation is True

    def test_has_citation_footnote(self):
        """Test detecting footnote citations."""
        processor = DocumentProcessor()

        claim = "Deep learning is effective"
        text = "Deep learning is effective[^1]. Additional text."

        has_citation = processor._has_citation(claim, text)

        assert has_citation is True

    def test_has_citation_no_citation(self):
        """Test detecting absence of citations."""
        processor = DocumentProcessor()

        claim = "This is a claim"
        text = "This is a claim without any citation. More text."

        has_citation = processor._has_citation(claim, text)

        assert has_citation is False

    def test_format_inline_citation_full(self):
        """Test formatting citation with all fields."""
        processor = DocumentProcessor()

        source = create_test_source(author="Smith", publication_date="2020", page=42)

        citation = processor._format_inline_citation(source)

        assert citation == "[Smith, 2020, p. 42]"

    def test_format_inline_citation_no_page(self):
        """Test formatting citation without page number."""
        processor = DocumentProcessor()

        source = create_test_source(author="Jones", publication_date="2019", page=None)

        citation = processor._format_inline_citation(source)

        assert citation == "[Jones, 2019]"

    def test_format_inline_citation_missing_author(self):
        """Test formatting citation with missing author."""
        processor = DocumentProcessor()

        source = create_test_source(author="", publication_date="2021", page=10)

        citation = processor._format_inline_citation(source)

        assert citation == "[Unknown, 2021, p. 10]"

    def test_format_inline_citation_missing_date(self):
        """Test formatting citation with missing date."""
        processor = DocumentProcessor()

        source = create_test_source(author="Brown", publication_date=None, page=None)

        citation = processor._format_inline_citation(source)

        assert citation == "[Brown, n.d.]"

    @pytest.mark.asyncio
    async def test_find_citations_basic(self):
        """Test finding citations for uncited claims."""
        # Mock FileIntel client
        mock_fileintel = AsyncMock()
        test_source = create_test_source(author="Smith", publication_date="2020", page=15)
        mock_response = create_test_query_response(sources=[test_source])
        mock_fileintel.query = AsyncMock(return_value=mock_response)

        processor = DocumentProcessor(fileintel_client=mock_fileintel)

        # Create chunk with uncited claim
        chunk = Chunk(
            heading="Test",
            text="Research shows that machine learning is effective.",
            type=ChunkType.PARAGRAPH,
            context="Test",
            start_pos=0,
            end_pos=50,
        )

        result = await processor._find_citations(chunk, collection="test_collection")

        # Should add citation
        assert len(result.citations_added) >= 1
        assert "[Smith, 2020, p. 15]" in result.processed_text

    @pytest.mark.asyncio
    async def test_find_citations_already_cited(self):
        """Test that existing citations are preserved."""
        mock_fileintel = AsyncMock()
        processor = DocumentProcessor(fileintel_client=mock_fileintel)

        # Chunk already has citation
        chunk = Chunk(
            heading="Test",
            text="Machine learning is effective [Smith, 2020].",
            type=ChunkType.PARAGRAPH,
            context="Test",
            start_pos=0,
            end_pos=50,
        )

        result = await processor._find_citations(chunk, collection="test_collection")

        # Should not add duplicate citations
        # Text should be mostly unchanged
        assert result.processed_text == chunk.text or "[Smith, 2020]" in result.processed_text

    @pytest.mark.asyncio
    async def test_find_citations_no_fileintel(self):
        """Test that find_citations requires FileIntel client."""
        processor = DocumentProcessor(fileintel_client=None)

        chunk = Chunk(
            heading="Test",
            text="Test text",
            type=ChunkType.PARAGRAPH,
            context="Test",
            start_pos=0,
            end_pos=10,
        )

        with pytest.raises(ValueError, match="FileIntel client required"):
            await processor._find_citations(chunk, collection="test")

    @pytest.mark.asyncio
    async def test_add_evidence_basic(self):
        """Test adding evidence to a chunk."""
        mock_fileintel = AsyncMock()
        test_source = create_test_source(
            author="Jones",
            publication_date="2019",
            page=42,
            text="Evidence text supporting the claim",
        )
        mock_response = create_test_query_response(sources=[test_source])
        mock_fileintel.query = AsyncMock(return_value=mock_response)

        processor = DocumentProcessor(fileintel_client=mock_fileintel)

        chunk = Chunk(
            heading="Test",
            text="Machine learning has applications.",
            type=ChunkType.PARAGRAPH,
            context="Test",
            start_pos=0,
            end_pos=40,
        )

        result = await processor._add_evidence(chunk, collection="test")

        # Should add evidence section
        assert "Supporting evidence:" in result.processed_text
        assert len(result.evidence_added) >= 1

    @pytest.mark.asyncio
    async def test_add_evidence_no_sources(self):
        """Test add_evidence when no sources found."""
        mock_fileintel = AsyncMock()
        mock_response = create_test_query_response(sources=[])
        mock_fileintel.query = AsyncMock(return_value=mock_response)

        processor = DocumentProcessor(fileintel_client=mock_fileintel)

        chunk = Chunk(
            heading="Test",
            text="Some text.",
            type=ChunkType.PARAGRAPH,
            context="Test",
            start_pos=0,
            end_pos=10,
        )

        result = await processor._add_evidence(chunk, collection="test")

        # Should return original text unchanged
        assert result.processed_text == chunk.text
        assert len(result.evidence_added) == 0

    @pytest.mark.asyncio
    async def test_improve_clarity_complex_text(self):
        """Test improving clarity of complex text."""
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(return_value="This is clearer simplified text.")

        processor = DocumentProcessor(llm_client=mock_llm)

        # Create chunk with long average sentence length
        long_text = (
            "This is an extraordinarily complex sentence with many clauses and subclauses "
            "that makes it difficult for readers to comprehend the main point being conveyed "
            "about the subject matter under discussion."
        )

        chunk = Chunk(
            heading="Test",
            text=long_text,
            type=ChunkType.PARAGRAPH,
            context="Test",
            start_pos=0,
            end_pos=len(long_text),
        )

        result = await processor._improve_clarity(chunk)

        # Should return improved text
        assert result.processed_text != chunk.text
        assert "clearer" in result.processed_text.lower()

    @pytest.mark.asyncio
    async def test_improve_clarity_simple_text(self):
        """Test that simple text is not modified."""
        mock_llm = AsyncMock()
        processor = DocumentProcessor(llm_client=mock_llm)

        # Simple, clear text
        simple_text = "This is clear. It is easy to read."

        chunk = Chunk(
            heading="Test",
            text=simple_text,
            type=ChunkType.PARAGRAPH,
            context="Test",
            start_pos=0,
            end_pos=len(simple_text),
        )

        result = await processor._improve_clarity(chunk)

        # Should return unchanged
        assert result.processed_text == chunk.text

    @pytest.mark.asyncio
    async def test_find_contradictions_basic(self):
        """Test finding contradictions."""
        mock_fileintel = AsyncMock()
        mock_llm = AsyncMock()

        # Mock LLM inversion
        mock_llm.invert_claim = AsyncMock(return_value="Machine learning is not effective")

        # Mock FileIntel finding contradicting sources
        test_source = create_test_source(
            author="Brown", publication_date="2021", text="Contradicting evidence"
        )
        mock_response = create_test_query_response(sources=[test_source])
        mock_fileintel.query = AsyncMock(return_value=mock_response)

        processor = DocumentProcessor(fileintel_client=mock_fileintel, llm_client=mock_llm)

        chunk = Chunk(
            heading="Test",
            text="Research shows that machine learning is highly effective.",
            type=ChunkType.PARAGRAPH,
            context="Test",
            start_pos=0,
            end_pos=60,
        )

        result = await processor._find_contradictions(chunk, collection="test")

        # Should find contradictions
        assert len(result.contradictions) >= 1
        assert result.contradictions[0]["original_claim"]
        assert result.contradictions[0]["inverted_claim"]

    @pytest.mark.asyncio
    async def test_process_chunk_unknown_operation(self):
        """Test that unknown operation raises error."""
        processor = DocumentProcessor()

        chunk = Chunk(
            heading="Test",
            text="Test",
            type=ChunkType.PARAGRAPH,
            context="Test",
            start_pos=0,
            end_pos=4,
        )

        with pytest.raises(ValueError, match="Unknown operation"):
            await processor._process_chunk(chunk, "invalid_operation", "collection")

    @pytest.mark.asyncio
    async def test_process_document_basic(self, tmp_path):
        """Test processing entire document."""
        # Create test markdown file
        test_file = tmp_path / "test.md"
        test_file.write_text(
            """# Test Document

## Section 1

This is test content."""
        )

        # Mock FileIntel client
        mock_fileintel = AsyncMock()
        mock_response = create_test_query_response(sources=[])
        mock_fileintel.query = AsyncMock(return_value=mock_response)

        processor = DocumentProcessor(fileintel_client=mock_fileintel)

        result = await processor.process_document(
            markdown_path=test_file, operation="find_citations", collection="test"
        )

        # Should process successfully
        assert result.operation == "find_citations"
        assert result.chunks_processed > 0
        assert isinstance(result.processed_text, str)

    def test_reassemble_document(self):
        """Test reassembling processed chunks."""
        processor = DocumentProcessor()

        # Create mock processed chunks
        chunks = [
            ProcessedChunk(
                original=Mock(),
                processed_text="First chunk",
                operation="test",
                citations_added=[{"claim": "test"}],
            ),
            ProcessedChunk(
                original=Mock(),
                processed_text="Second chunk",
                operation="test",
                evidence_added=[Mock()],
            ),
        ]

        result = processor._reassemble_document(
            original_text="Original", processed_chunks=chunks, operation="test"
        )

        # Should combine chunks
        assert "First chunk" in result.processed_text
        assert "Second chunk" in result.processed_text
        assert result.chunks_processed == 2
        assert result.citations_added == 1
        assert result.evidence_added == 1

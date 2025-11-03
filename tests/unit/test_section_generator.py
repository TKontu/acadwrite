"""Unit tests for section generator."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from acadwrite.models import CitationStyle, WritingStyle
from acadwrite.models.query import (
    ChunkMetadata,
    DocumentMetadata,
    QueryResponse,
    Source,
)
from acadwrite.services import FormatterService
from acadwrite.workflows import SectionGenerator


class TestSectionGenerator:
    """Tests for SectionGenerator."""

    @pytest.fixture
    def mock_fileintel(self) -> AsyncMock:
        """Create mocked FileIntel client."""
        return AsyncMock()

    @pytest.fixture
    def formatter(self) -> FormatterService:
        """Create formatter service."""
        return FormatterService()

    @pytest.fixture
    def generator(self, mock_fileintel: AsyncMock, formatter: FormatterService) -> SectionGenerator:
        """Create section generator."""
        return SectionGenerator(mock_fileintel, formatter)

    @pytest.fixture
    def sample_response(self) -> QueryResponse:
        """Create sample query response."""
        sources = [
            Source(
                document_id="doc1",
                chunk_id="chunk1",
                filename="test.pdf",
                citation="Smith, J. (2020). Test Article. Journal of Testing.",
                in_text_citation="(Smith, 2020, p. 5)",
                text="This is a test excerpt.",
                similarity_score=0.9,
                relevance_score=0.85,
                chunk_metadata=ChunkMetadata(
                    chunk_number=1,
                    total_chunks=10,
                    char_count=100,
                ),
                document_metadata=DocumentMetadata(
                    title="Test Article",
                    authors=["Smith, J."],
                    publication_date="2020-01-01",
                ),
            ),
            Source(
                document_id="doc2",
                chunk_id="chunk2",
                filename="test2.pdf",
                citation="Jones, A. (2021). Another Test. Journal of Examples.",
                in_text_citation="(Jones, 2021, p. 10)",
                text="Another excerpt.",
                similarity_score=0.85,
                relevance_score=0.80,
                chunk_metadata=ChunkMetadata(
                    chunk_number=2,
                    total_chunks=15,
                    char_count=90,
                ),
                document_metadata=DocumentMetadata(
                    title="Another Test",
                    authors=["Jones, A."],
                    publication_date="2021-06-15",
                ),
            ),
        ]

        return QueryResponse(
            answer="This is generated content with citations [Smith, 2020, p. 5]. More content [Jones, 2021, p. 10].",
            sources=sources,
            query_type="vector",
            collection_id="test_collection",
            question="test query",
        )

    @pytest.mark.asyncio
    async def test_generate_success(
        self,
        generator: SectionGenerator,
        mock_fileintel: AsyncMock,
        sample_response: QueryResponse,
    ) -> None:
        """Test successful section generation."""
        mock_fileintel.query.return_value = sample_response

        section = await generator.generate(
            heading="Test Section",
            collection="test_collection",
        )

        assert section.heading == "Test Section"
        assert section.level == 2
        assert "generated content" in section.content
        assert len(section.citations) == 2
        assert section.citations[0].author == "Smith, J."
        assert section.citations[0].page == 5
        assert section.citations[1].author == "Jones, A."
        assert section.citations[1].page == 10

        # Verify FileIntel was called correctly
        mock_fileintel.query.assert_called_once_with(
            collection="test_collection",
            question="Test Section",
            rag_type="vector",
            max_sources=None,
        )

    @pytest.mark.asyncio
    async def test_generate_with_context(
        self,
        generator: SectionGenerator,
        mock_fileintel: AsyncMock,
        sample_response: QueryResponse,
    ) -> None:
        """Test generation with context."""
        mock_fileintel.query.return_value = sample_response

        await generator.generate(
            heading="Test Section",
            collection="test_collection",
            context="Previous section discussed X.",
        )

        # Verify context was included in query
        call_args = mock_fileintel.query.call_args
        assert "Previous section discussed X" in call_args[1]["question"]

    @pytest.mark.asyncio
    async def test_generate_with_max_sources(
        self,
        generator: SectionGenerator,
        mock_fileintel: AsyncMock,
        sample_response: QueryResponse,
    ) -> None:
        """Test generation with max sources limit."""
        mock_fileintel.query.return_value = sample_response

        await generator.generate(
            heading="Test Section",
            collection="test_collection",
            max_sources=3,
        )

        mock_fileintel.query.assert_called_once_with(
            collection="test_collection",
            question="Test Section",
            rag_type="vector",
            max_sources=3,
        )

    @pytest.mark.asyncio
    async def test_generate_with_word_limit(
        self,
        generator: SectionGenerator,
        mock_fileintel: AsyncMock,
    ) -> None:
        """Test word count truncation."""
        # Create response with long content
        long_content = " ".join(["word"] * 100)
        response = QueryResponse(
            answer=long_content,
            sources=[],
            query_type="vector",
            collection_id="test",
            question="test",
        )
        mock_fileintel.query.return_value = response

        section = await generator.generate(
            heading="Test",
            collection="test",
            max_words=50,
        )

        assert section.word_count() <= 55  # Allow some margin for ellipsis

    @pytest.mark.asyncio
    async def test_citation_extraction_with_page_numbers(
        self,
        generator: SectionGenerator,
        mock_fileintel: AsyncMock,
        sample_response: QueryResponse,
    ) -> None:
        """Test citation extraction with page numbers."""
        mock_fileintel.query.return_value = sample_response

        section = await generator.generate(
            heading="Test",
            collection="test",
        )

        # Check page numbers extracted
        assert section.citations[0].page == 5
        assert section.citations[1].page == 10

    @pytest.mark.asyncio
    async def test_citation_extraction_without_page_numbers(
        self,
        generator: SectionGenerator,
        mock_fileintel: AsyncMock,
    ) -> None:
        """Test citation extraction without page numbers."""
        source = Source(
            document_id="doc1",
            chunk_id="chunk1",
            filename="test.pdf",
            citation="Smith (2020). Test.",
            in_text_citation="(Smith, 2020)",  # No page number
            text="Text",
            similarity_score=0.9,
            relevance_score=0.9,
            chunk_metadata=ChunkMetadata(chunk_number=1, total_chunks=1, char_count=10),
            document_metadata=DocumentMetadata(
                title="Test",
                authors=["Smith"],
                publication_date="2020-01-01",
            ),
        )

        response = QueryResponse(
            answer="Content",
            sources=[source],
            query_type="vector",
            collection_id="test",
            question="test",
        )

        mock_fileintel.query.return_value = response

        section = await generator.generate(
            heading="Test",
            collection="test",
        )

        assert section.citations[0].page is None

    @pytest.mark.asyncio
    async def test_citation_extraction_year_from_date(
        self,
        generator: SectionGenerator,
        mock_fileintel: AsyncMock,
        sample_response: QueryResponse,
    ) -> None:
        """Test year extraction from publication date."""
        mock_fileintel.query.return_value = sample_response

        section = await generator.generate(
            heading="Test",
            collection="test",
        )

        assert section.citations[0].year == "2020"
        assert section.citations[1].year == "2021"

    @pytest.mark.asyncio
    async def test_build_query_with_context(self, generator: SectionGenerator) -> None:
        """Test query building with context."""
        query = generator._build_query("Test Heading", "Some context")
        assert "Test Heading" in query
        assert "Some context" in query

    @pytest.mark.asyncio
    async def test_build_query_without_context(self, generator: SectionGenerator) -> None:
        """Test query building without context."""
        query = generator._build_query("Test Heading", None)
        assert query == "Test Heading"

    def test_count_words(self, generator: SectionGenerator) -> None:
        """Test word counting."""
        assert generator._count_words("one two three") == 3
        assert generator._count_words("single") == 1
        assert generator._count_words("") == 0  # Empty string has no words
        assert generator._count_words("multiple   spaces") == 2

    def test_truncate_to_word_limit(self, generator: SectionGenerator) -> None:
        """Test word limit truncation."""
        text = "This is a test. Another sentence. More content here."
        truncated = generator._truncate_to_word_limit(text, 5)

        # Should be truncated
        assert len(truncated.split()) <= 6  # 5 + ellipsis
        assert "test" in truncated

    def test_truncate_at_sentence_boundary(self, generator: SectionGenerator) -> None:
        """Test truncation at sentence boundaries."""
        text = "First sentence. Second sentence. Third sentence."
        truncated = generator._truncate_to_word_limit(text, 6)

        # Should end with period (sentence boundary)
        if not truncated.endswith("..."):
            assert truncated.endswith(".")

    def test_extract_page_number(self, generator: SectionGenerator) -> None:
        """Test page number extraction."""
        assert generator._extract_page_number("(Author, 2020, p. 5)") == 5
        assert generator._extract_page_number("(Author, 2020, p.10)") == 10
        assert generator._extract_page_number("(Author, 2020)") is None
        assert generator._extract_page_number("No page") is None

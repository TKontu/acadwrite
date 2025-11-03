"""Unit tests for counterargument generator."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from acadwrite.models.query import (
    ChunkMetadata,
    DocumentMetadata,
    QueryResponse,
    Source,
)
from acadwrite.workflows import (
    AnalysisDepth,
    CounterargumentGenerator,
)


class TestCounterargumentGenerator:
    """Tests for CounterargumentGenerator."""

    @pytest.fixture
    def mock_fileintel(self) -> AsyncMock:
        """Create mocked FileIntel client."""
        return AsyncMock()

    @pytest.fixture
    def mock_llm(self) -> AsyncMock:
        """Create mocked LLM client."""
        mock = AsyncMock()
        mock.model = "test-model"
        mock.temperature = 0.1
        mock.client = AsyncMock()
        return mock

    @pytest.fixture
    def generator(self, mock_fileintel: AsyncMock, mock_llm: AsyncMock) -> CounterargumentGenerator:
        """Create counterargument generator."""
        return CounterargumentGenerator(mock_fileintel, mock_llm)

    @pytest.fixture
    def sample_source(self) -> Source:
        """Create sample source."""
        return Source(
            document_id="doc1",
            chunk_id="chunk1",
            filename="test.pdf",
            citation="Smith, J. (2020). Test Article.",
            in_text_citation="(Smith, 2020, p. 5)",
            text="This is a test excerpt showing some evidence. It has multiple sentences.",
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
        )

    @pytest.fixture
    def sample_response(self, sample_source: Source) -> QueryResponse:
        """Create sample query response."""
        return QueryResponse(
            answer="Generated answer with evidence.",
            sources=[sample_source],
            query_type="vector",
            collection_id="test_collection",
            question="test query",
        )

    @pytest.mark.asyncio
    async def test_generate_without_synthesis(
        self,
        generator: CounterargumentGenerator,
        mock_fileintel: AsyncMock,
        mock_llm: AsyncMock,
        sample_response: QueryResponse,
    ) -> None:
        """Test report generation without synthesis."""
        # Setup mocks
        mock_fileintel.query.return_value = sample_response
        mock_llm.invert_claim.return_value = "Inverted test claim"

        report = await generator.generate(
            claim="Test claim",
            collection="test_collection",
            depth=AnalysisDepth.STANDARD,
            include_synthesis=False,
        )

        assert report.original_claim == "Test claim"
        assert report.inverted_claim == "Inverted test claim"
        assert len(report.supporting_evidence) == 1
        assert len(report.contradicting_evidence) == 1
        assert report.synthesis is None
        assert report.depth == AnalysisDepth.STANDARD

        # Verify LLM was called to invert claim
        mock_llm.invert_claim.assert_called_once_with("Test claim")

        # Verify FileIntel was called twice (supporting + contradicting)
        assert mock_fileintel.query.call_count == 2

        # First call for supporting evidence
        first_call = mock_fileintel.query.call_args_list[0]
        assert first_call[1]["question"] == "Test claim"

        # Second call for contradicting evidence
        second_call = mock_fileintel.query.call_args_list[1]
        assert second_call[1]["question"] == "Inverted test claim"

    @pytest.mark.asyncio
    async def test_generate_with_synthesis(
        self,
        generator: CounterargumentGenerator,
        mock_fileintel: AsyncMock,
        mock_llm: AsyncMock,
        sample_response: QueryResponse,
    ) -> None:
        """Test report generation with synthesis."""
        # Setup mocks
        mock_fileintel.query.return_value = sample_response
        mock_llm.invert_claim.return_value = "Inverted claim"

        # Mock synthesis response
        mock_synthesis_response = MagicMock()
        mock_synthesis_response.choices = [MagicMock()]
        mock_synthesis_response.choices[0].message.content = "Synthesized analysis of evidence."
        mock_llm.client.chat.completions.create = AsyncMock(return_value=mock_synthesis_response)

        report = await generator.generate(
            claim="Test claim",
            collection="test_collection",
            include_synthesis=True,
        )

        assert report.synthesis == "Synthesized analysis of evidence."
        mock_llm.client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_with_max_sources(
        self,
        generator: CounterargumentGenerator,
        mock_fileintel: AsyncMock,
        mock_llm: AsyncMock,
        sample_response: QueryResponse,
    ) -> None:
        """Test generation with max sources limit."""
        mock_fileintel.query.return_value = sample_response
        mock_llm.invert_claim.return_value = "Inverted"

        await generator.generate(
            claim="Test",
            collection="test",
            max_sources_per_side=3,
        )

        # Both queries should have max_sources=3
        for call in mock_fileintel.query.call_args_list:
            assert call[1]["max_sources"] == 3

    @pytest.mark.asyncio
    async def test_build_evidence_list(
        self,
        generator: CounterargumentGenerator,
        sample_response: QueryResponse,
    ) -> None:
        """Test building evidence list from query response."""
        evidence_list = generator._build_evidence_list(sample_response, "Test relevance")

        assert len(evidence_list) == 1
        assert evidence_list[0].source == sample_response.sources[0]
        assert evidence_list[0].relevance == "Test relevance"
        assert len(evidence_list[0].key_point) > 0

    @pytest.mark.asyncio
    async def test_extract_key_point_sentence(self, generator: CounterargumentGenerator) -> None:
        """Test extracting key point at sentence boundary."""
        text = "First sentence. Second sentence. Third sentence."
        key_point = generator._extract_key_point(text)

        assert key_point == "First sentence."

    @pytest.mark.asyncio
    async def test_extract_key_point_truncate(self, generator: CounterargumentGenerator) -> None:
        """Test extracting key point with truncation."""
        text = "A" * 300  # Long text with no sentence boundaries
        key_point = generator._extract_key_point(text, max_length=200)

        assert len(key_point) <= 203  # 200 + "..."
        assert key_point.endswith("...")

    @pytest.mark.asyncio
    async def test_extract_key_point_short_text(self, generator: CounterargumentGenerator) -> None:
        """Test extracting key point from short text."""
        text = "Short text"
        key_point = generator._extract_key_point(text)

        assert key_point == "Short text"

    @pytest.mark.asyncio
    async def test_analysis_depth_enum(self) -> None:
        """Test AnalysisDepth enum values."""
        assert AnalysisDepth.QUICK.value == "quick"
        assert AnalysisDepth.STANDARD.value == "standard"
        assert AnalysisDepth.DEEP.value == "deep"

    @pytest.mark.asyncio
    async def test_evidence_structure(self, sample_source: Source) -> None:
        """Test Evidence dataclass structure."""
        from acadwrite.workflows import Evidence

        evidence = Evidence(
            source=sample_source,
            key_point="Test key point",
            relevance="Test relevance",
        )

        assert evidence.source == sample_source
        assert evidence.key_point == "Test key point"
        assert evidence.relevance == "Test relevance"

    @pytest.mark.asyncio
    async def test_counterargument_report_structure(self, sample_source: Source) -> None:
        """Test CounterargumentReport dataclass structure."""
        from acadwrite.workflows import CounterargumentReport, Evidence

        evidence = Evidence(
            source=sample_source,
            key_point="Test",
            relevance="Test",
        )

        report = CounterargumentReport(
            original_claim="Original",
            inverted_claim="Inverted",
            supporting_evidence=[evidence],
            contradicting_evidence=[],
            synthesis="Test synthesis",
            depth=AnalysisDepth.QUICK,
        )

        assert report.original_claim == "Original"
        assert report.inverted_claim == "Inverted"
        assert len(report.supporting_evidence) == 1
        assert len(report.contradicting_evidence) == 0
        assert report.synthesis == "Test synthesis"
        assert report.depth == AnalysisDepth.QUICK

    @pytest.mark.asyncio
    async def test_multiple_sources(
        self,
        generator: CounterargumentGenerator,
        mock_fileintel: AsyncMock,
        mock_llm: AsyncMock,
        sample_source: Source,
    ) -> None:
        """Test handling multiple sources."""
        # Create response with multiple sources
        sources = [sample_source, sample_source, sample_source]
        response = QueryResponse(
            answer="Answer",
            sources=sources,
            query_type="vector",
            collection_id="test",
            question="test",
        )

        mock_fileintel.query.return_value = response
        mock_llm.invert_claim.return_value = "Inverted"

        report = await generator.generate(
            claim="Test",
            collection="test",
        )

        assert len(report.supporting_evidence) == 3
        assert len(report.contradicting_evidence) == 3

    @pytest.mark.asyncio
    async def test_empty_response(
        self,
        generator: CounterargumentGenerator,
        mock_fileintel: AsyncMock,
        mock_llm: AsyncMock,
    ) -> None:
        """Test handling empty query response."""
        empty_response = QueryResponse(
            answer="No results",
            sources=[],
            query_type="vector",
            collection_id="test",
            question="test",
        )

        mock_fileintel.query.return_value = empty_response
        mock_llm.invert_claim.return_value = "Inverted"

        report = await generator.generate(
            claim="Test",
            collection="test",
        )

        assert len(report.supporting_evidence) == 0
        assert len(report.contradicting_evidence) == 0

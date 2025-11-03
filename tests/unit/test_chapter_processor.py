"""Unit tests for chapter processor."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from acadwrite.models import AcademicSection, Citation, CitationStyle, WritingStyle
from acadwrite.models.outline import Outline, OutlineItem
from acadwrite.workflows import ChapterProcessor


class TestChapterProcessor:
    """Tests for ChapterProcessor."""

    @pytest.fixture
    def mock_section_generator(self) -> AsyncMock:
        """Create mocked section generator."""
        return AsyncMock()

    @pytest.fixture
    def mock_formatter(self) -> MagicMock:
        """Create mocked formatter."""
        mock = MagicMock()
        # Default deduplication behavior (no duplicates)
        mock.deduplicate_citations.return_value = ([], {})
        mock.renumber_citations_in_content.return_value = "test content"
        mock.generate_footnotes.return_value = ""
        return mock

    @pytest.fixture
    def processor(
        self, mock_section_generator: AsyncMock, mock_formatter: MagicMock
    ) -> ChapterProcessor:
        """Create chapter processor."""
        return ChapterProcessor(mock_section_generator, mock_formatter)

    @pytest.fixture
    def sample_outline(self) -> Outline:
        """Create sample outline."""
        items = [
            OutlineItem(heading="Introduction", level=2, children=[]),
            OutlineItem(heading="Background", level=2, children=[]),
        ]
        return Outline(title="Test Chapter", items=items)

    @pytest.fixture
    def sample_section(self) -> AcademicSection:
        """Create sample section."""
        return AcademicSection(
            heading="Test Section",
            level=2,
            content="Test content",
            citations=[
                Citation(
                    id=1,
                    author="Smith",
                    title="Test",
                    year="2020",
                    page=5,
                    full_citation="Smith (2020). Test.",
                )
            ],
        )

    @pytest.mark.asyncio
    async def test_process_simple_outline(
        self,
        processor: ChapterProcessor,
        mock_section_generator: AsyncMock,
        mock_formatter: MagicMock,
        sample_outline: Outline,
        sample_section: AcademicSection,
    ) -> None:
        """Test processing simple outline without subsections."""
        # Mock section generator to return sample sections
        mock_section_generator.generate.return_value = sample_section

        # Mock deduplication
        mock_formatter.deduplicate_citations.return_value = (
            sample_section.citations,
            {1: 1},
        )

        chapter = await processor.process(
            outline=sample_outline,
            collection="test",
        )

        assert chapter.title == "Test Chapter"
        assert len(chapter.sections) == 2
        assert chapter.metadata.total_sections == 2

        # Verify section generator was called for each item
        assert mock_section_generator.generate.call_count == 2

    @pytest.mark.asyncio
    async def test_process_with_subsections(
        self,
        processor: ChapterProcessor,
        mock_section_generator: AsyncMock,
        mock_formatter: MagicMock,
        sample_section: AcademicSection,
    ) -> None:
        """Test processing outline with subsections."""
        # Create outline with subsections
        outline = Outline(
            title="Test",
            items=[
                OutlineItem(
                    heading="Main",
                    level=2,
                    children=[
                        OutlineItem(heading="Sub 1", level=3, children=[]),
                        OutlineItem(heading="Sub 2", level=3, children=[]),
                    ],
                )
            ],
        )

        mock_section_generator.generate.return_value = sample_section
        mock_formatter.deduplicate_citations.return_value = ([], {})

        chapter = await processor.process(outline=outline, collection="test")

        # Should have main section + 2 subsections = 3 total
        assert len(chapter.sections) == 3
        assert mock_section_generator.generate.call_count == 3

    @pytest.mark.asyncio
    async def test_process_with_context(
        self,
        processor: ChapterProcessor,
        mock_section_generator: AsyncMock,
        mock_formatter: MagicMock,
        sample_outline: Outline,
        sample_section: AcademicSection,
    ) -> None:
        """Test that context is passed between sections."""
        mock_section_generator.generate.return_value = sample_section
        mock_formatter.deduplicate_citations.return_value = ([], {})

        await processor.process(outline=sample_outline, collection="test")

        # First section should have no context
        first_call = mock_section_generator.generate.call_args_list[0]
        assert first_call[1]["context"] is None

        # Second section should have context from first
        second_call = mock_section_generator.generate.call_args_list[1]
        assert second_call[1]["context"] is not None
        assert "Test Section" in second_call[1]["context"]

    @pytest.mark.asyncio
    async def test_citation_deduplication(
        self,
        processor: ChapterProcessor,
        mock_section_generator: AsyncMock,
        mock_formatter: MagicMock,
        sample_outline: Outline,
    ) -> None:
        """Test citation deduplication across sections."""
        # Create sections with duplicate citations
        citation1 = Citation(
            id=1, author="Smith", title="Test", year="2020", page=5, full_citation="Smith"
        )
        citation2 = Citation(
            id=2, author="Smith", title="Test", year="2020", page=5, full_citation="Smith"
        )

        section1 = AcademicSection(
            heading="Section 1", level=2, content="Content", citations=[citation1]
        )
        section2 = AcademicSection(
            heading="Section 2", level=2, content="Content", citations=[citation2]
        )

        mock_section_generator.generate.side_effect = [section1, section2]

        # Mock deduplication to merge citations
        unique_citation = Citation(
            id=1, author="Smith", title="Test", year="2020", page=5, full_citation="Smith"
        )
        mock_formatter.deduplicate_citations.return_value = (
            [unique_citation],
            {1: 1, 2: 1},  # Both map to ID 1
        )

        chapter = await processor.process(outline=sample_outline, collection="test")

        # Should have called deduplicate with all citations
        mock_formatter.deduplicate_citations.assert_called_once()
        assert len(chapter.citations) == 1

    @pytest.mark.asyncio
    async def test_continue_on_error(self) -> None:
        """Test continue_on_error flag."""
        # Create fresh mocks for this test
        mock_gen = AsyncMock()
        mock_fmt = MagicMock()

        # Create outline with 2 sections
        outline = Outline(
            title="Test",
            items=[
                OutlineItem(heading="Section 1", level=2, children=[]),
                OutlineItem(heading="Section 2", level=2, children=[]),
            ],
        )

        # First section fails, second succeeds
        success_section = AcademicSection(
            heading="Section 2", level=2, content="Success", citations=[]
        )

        # Mock to raise exception on first call, return section on second
        call_count = [0]

        async def mock_generate(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("Test error")
            return success_section

        mock_gen.generate.side_effect = mock_generate
        mock_fmt.deduplicate_citations.return_value = ([], {})
        # Make renumber return the original content unchanged
        mock_fmt.renumber_citations_in_content.side_effect = lambda content, mapping: content
        mock_fmt.generate_footnotes.return_value = ""

        processor = ChapterProcessor(mock_gen, mock_fmt)

        chapter = await processor.process(
            outline=outline,
            collection="test",
            continue_on_error=True,
        )

        # Should have 2 sections (one error placeholder, one real)
        assert len(chapter.sections) == 2
        assert "Error generating section" in chapter.sections[0].content
        assert chapter.sections[1].content == "Success"

    @pytest.mark.asyncio
    async def test_stop_on_error(
        self,
        processor: ChapterProcessor,
        mock_section_generator: AsyncMock,
        sample_outline: Outline,
    ) -> None:
        """Test that errors propagate when continue_on_error=False."""
        mock_section_generator.generate.side_effect = Exception("Test error")

        with pytest.raises(Exception) as exc_info:
            await processor.process(
                outline=sample_outline,
                collection="test",
                continue_on_error=False,
            )

        assert "Test error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_calculate_metadata(
        self,
        processor: ChapterProcessor,
        sample_section: AcademicSection,
    ) -> None:
        """Test metadata calculation."""
        sections = [sample_section, sample_section]
        citations = [sample_section.citations[0]]

        metadata = processor._calculate_metadata(
            title="Test",
            sections=sections,
            unique_citations=citations,
        )

        assert metadata.title == "Test"
        assert metadata.total_sections == 2
        assert metadata.unique_citations == 1
        assert metadata.total_citations == 2  # 2 sections, 1 citation each
        assert len(metadata.sections_list) == 2

    def test_save_chapter_single_file(
        self,
        processor: ChapterProcessor,
        sample_section: AcademicSection,
        tmp_path: Path,
    ) -> None:
        """Test saving chapter as single file."""
        from acadwrite.workflows import Chapter, ChapterMetadata

        chapter = Chapter(
            title="Test Chapter",
            sections=[sample_section],
            citations=sample_section.citations,
            metadata=ChapterMetadata(
                title="Test",
                total_sections=1,
                total_word_count=2,
                total_citations=1,
                unique_citations=1,
            ),
        )

        saved_files = processor.save_chapter(
            chapter=chapter,
            output_dir=tmp_path,
            single_file=True,
        )

        assert "chapter" in saved_files
        assert "bibliography" in saved_files
        assert "metadata" in saved_files

        # Verify files exist
        assert saved_files["chapter"].exists()
        assert saved_files["bibliography"].exists()
        assert saved_files["metadata"].exists()

    def test_save_chapter_multiple_files(
        self,
        processor: ChapterProcessor,
        sample_section: AcademicSection,
        tmp_path: Path,
    ) -> None:
        """Test saving chapter as multiple files."""
        from acadwrite.workflows import Chapter, ChapterMetadata

        chapter = Chapter(
            title="Test Chapter",
            sections=[sample_section, sample_section],
            citations=sample_section.citations,
            metadata=ChapterMetadata(
                title="Test",
                total_sections=2,
                total_word_count=4,
                total_citations=2,
                unique_citations=1,
            ),
        )

        saved_files = processor.save_chapter(
            chapter=chapter,
            output_dir=tmp_path,
            single_file=False,
        )

        assert "section_1" in saved_files
        assert "section_2" in saved_files
        assert "bibliography" in saved_files
        assert "metadata" in saved_files

    def test_sanitize_filename(self, processor: ChapterProcessor) -> None:
        """Test filename sanitization."""
        assert processor._sanitize_filename("Test Section") == "test_section"
        assert processor._sanitize_filename("Test & Special! Chars?") == "test_special_chars"
        assert processor._sanitize_filename("A" * 100)[:50] == "a" * 50

    def test_generate_bibtex(
        self, processor: ChapterProcessor, sample_section: AcademicSection
    ) -> None:
        """Test BibTeX generation."""
        bib = processor._generate_bibtex(sample_section.citations)

        assert "@article" in bib or "@book" in bib
        assert "Smith" in bib

    def test_generate_bibtex_empty(self, processor: ChapterProcessor) -> None:
        """Test BibTeX generation with no citations."""
        bib = processor._generate_bibtex([])
        assert bib == ""

    @pytest.mark.asyncio
    async def test_max_words_per_section(
        self,
        processor: ChapterProcessor,
        mock_section_generator: AsyncMock,
        mock_formatter: MagicMock,
        sample_outline: Outline,
        sample_section: AcademicSection,
    ) -> None:
        """Test max words limit is passed to section generator."""
        mock_section_generator.generate.return_value = sample_section
        mock_formatter.deduplicate_citations.return_value = ([], {})

        await processor.process(
            outline=sample_outline,
            collection="test",
            max_words_per_section=500,
        )

        # Verify max_words was passed
        call_args = mock_section_generator.generate.call_args_list[0]
        assert call_args[1]["max_words"] == 500

    @pytest.mark.asyncio
    async def test_style_parameters(
        self,
        processor: ChapterProcessor,
        mock_section_generator: AsyncMock,
        mock_formatter: MagicMock,
        sample_outline: Outline,
        sample_section: AcademicSection,
    ) -> None:
        """Test style parameters are passed correctly."""
        mock_section_generator.generate.return_value = sample_section
        mock_formatter.deduplicate_citations.return_value = ([], {})

        await processor.process(
            outline=sample_outline,
            collection="test",
            style=WritingStyle.TECHNICAL,
            citation_style=CitationStyle.FOOTNOTE,
        )

        call_args = mock_section_generator.generate.call_args_list[0]
        assert call_args[1]["style"] == WritingStyle.TECHNICAL
        assert call_args[1]["citation_style"] == CitationStyle.FOOTNOTE

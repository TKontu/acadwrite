"""Unit tests for formatter service."""

import pytest

from acadwrite.models import AcademicSection, Citation, CitationStyle
from acadwrite.services import FormatterService


class TestFormatterService:
    """Tests for FormatterService."""

    @pytest.fixture
    def formatter(self) -> FormatterService:
        """Create FormatterService instance."""
        return FormatterService()

    def test_format_section_inline(self, formatter: FormatterService) -> None:
        """Test formatting section with inline citations."""
        section = AcademicSection(
            heading="Introduction",
            level=2,
            content="This is content [Author, 2020, p. 5].",
        )

        result = formatter.format_section(section, CitationStyle.INLINE)

        assert "## Introduction" in result
        assert "This is content [Author, 2020, p. 5]." in result

    def test_format_section_footnote(self, formatter: FormatterService) -> None:
        """Test formatting section with footnote citations."""
        citation = Citation(
            id=1,
            author="Smith",
            title="Test Article",
            year="2020",
            page=5,
            full_citation="Smith (2020). Test Article.",
        )

        section = AcademicSection(
            heading="Introduction",
            level=2,
            content="Content [^1]",
            citations=[citation],
        )

        result = formatter.format_section(section, CitationStyle.FOOTNOTE)

        assert "## Introduction" in result
        assert "Content [^1]" in result
        assert "[^1]: Smith (2020). Test Article. p.5" in result

    def test_convert_inline_to_footnotes_simple(self, formatter: FormatterService) -> None:
        """Test converting inline citations to footnotes."""
        content = "This is a claim [Author, 2020, p. 5]. Another claim [Jones, 2021]."
        citations = [
            Citation(
                id=1, author="Author", title="Article 1", year="2020", full_citation="Author (2020)"
            ),
            Citation(
                id=2, author="Jones", title="Article 2", year="2021", full_citation="Jones (2021)"
            ),
        ]

        result = formatter.convert_inline_to_footnotes(content, citations)

        assert "[^1]" in result
        assert "[^2]" in result
        assert "[Author, 2020, p. 5]" not in result
        assert "[Jones, 2021]" not in result

    def test_convert_inline_to_footnotes_duplicate(self, formatter: FormatterService) -> None:
        """Test converting with duplicate citations."""
        content = "First [Author, 2020]. Second [Author, 2020]. Third [Author, 2020]."
        citations = []

        result = formatter.convert_inline_to_footnotes(content, citations)

        # Same citation should get same number
        assert result.count("[^1]") == 3

    def test_convert_inline_to_footnotes_short_format(self, formatter: FormatterService) -> None:
        """Test converting short citation format [Author]."""
        content = "This uses short format [SEBoK]."
        citations = []

        result = formatter.convert_inline_to_footnotes(content, citations)

        assert "[^1]" in result
        assert "[SEBoK]" not in result

    def test_generate_footnotes(self, formatter: FormatterService) -> None:
        """Test generating footnote bibliography."""
        citations = [
            Citation(
                id=1,
                author="Smith",
                title="Article 1",
                year="2020",
                page=5,
                full_citation="Smith (2020). Article 1.",
            ),
            Citation(
                id=2,
                author="Jones",
                title="Article 2",
                year="2021",
                full_citation="Jones (2021). Article 2.",
            ),
        ]

        result = formatter.generate_footnotes(citations)

        assert "---" in result
        assert "[^1]: Smith (2020). Article 1. p.5" in result
        assert "[^2]: Jones (2021). Article 2." in result

    def test_generate_footnotes_empty(self, formatter: FormatterService) -> None:
        """Test generating footnotes with no citations."""
        result = formatter.generate_footnotes([])
        assert result == ""

    def test_deduplicate_citations(self, formatter: FormatterService) -> None:
        """Test deduplicating citations."""
        citations = [
            Citation(
                id=1, author="Smith", title="Article", year="2020", page=5, full_citation="Smith"
            ),
            Citation(id=2, author="Jones", title="Other", year="2021", full_citation="Jones"),
            Citation(
                id=3, author="Smith", title="Article", year="2020", page=5, full_citation="Smith"
            ),  # Duplicate of #1
        ]

        unique, id_mapping = formatter.deduplicate_citations(citations)

        assert len(unique) == 2
        assert unique[0].author == "Smith"
        assert unique[1].author == "Jones"

        # Check ID mapping
        assert id_mapping[1] == 1  # First citation stays as #1
        assert id_mapping[2] == 2  # Second citation becomes #2
        assert id_mapping[3] == 1  # Third citation (duplicate) maps to #1

    def test_deduplicate_citations_different_pages(self, formatter: FormatterService) -> None:
        """Test that same source with different pages are kept separate."""
        citations = [
            Citation(
                id=1, author="Smith", title="Article", year="2020", page=5, full_citation="Smith"
            ),
            Citation(
                id=2, author="Smith", title="Article", year="2020", page=10, full_citation="Smith"
            ),
        ]

        unique, id_mapping = formatter.deduplicate_citations(citations)

        # Different pages should be separate citations
        assert len(unique) == 2
        assert unique[0].page == 5
        assert unique[1].page == 10

    def test_renumber_citations_in_content(self, formatter: FormatterService) -> None:
        """Test renumbering citation markers."""
        content = "First [^1]. Second [^2]. Third [^3]."
        id_mapping = {1: 1, 2: 3, 3: 1}  # #2 becomes #3, #3 becomes #1

        result = formatter.renumber_citations_in_content(content, id_mapping)

        assert "First [^1]" in result
        assert "Second [^3]" in result
        assert "Third [^1]" in result

    def test_format_section_with_subsections(self, formatter: FormatterService) -> None:
        """Test formatting section with subsections."""
        subsection = AcademicSection(
            heading="Subsection",
            level=3,
            content="Subsection content.",
        )

        section = AcademicSection(
            heading="Main",
            level=2,
            content="Main content.",
            subsections=[subsection],
        )

        result = formatter.format_section(section, CitationStyle.INLINE)

        assert "## Main" in result
        assert "Main content." in result
        assert "### Subsection" in result
        assert "Subsection content." in result

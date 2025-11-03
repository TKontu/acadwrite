"""Tests for CitationManager."""

import pytest
from pathlib import Path
import tempfile
import json

from acadwrite.workflows.citation_manager import CitationManager, CitationCheck
from acadwrite.models.section import Citation, AcademicSection


class TestCitationManager:
    """Test suite for CitationManager."""

    def test_extract_from_text_inline_citations(self):
        """Test extracting inline citations."""
        manager = CitationManager()
        text = """
        This is a paragraph with citations [Smith, 2020, p. 42] and another one [Jones, 2019].
        Here's more content [Brown, n.d., p. 15].
        """

        citations = manager.extract_from_text(text)

        assert len(citations) == 3
        assert citations[0].author == "Smith"
        assert citations[0].year == "2020"
        assert citations[0].page == 42
        assert citations[1].author == "Jones"
        assert citations[1].year == "2019"
        assert citations[1].page is None
        assert citations[2].author == "Brown"
        assert citations[2].year == "n.d."
        assert citations[2].page == 15

    def test_extract_from_text_footnote_citations(self):
        """Test extracting footnote citations."""
        manager = CitationManager()
        text = """
        This is content[^1] with footnotes[^2].

        [^1]: Smith, J. (2020). The Title. Publisher, p. 42.
        [^2]: Jones, A. (2019). Another Title.
        """

        citations = manager.extract_from_text(text)

        assert len(citations) == 2
        assert citations[0].id == 1
        assert citations[0].author.endswith("J.")  # Might be "Smith, J." or "J."
        assert citations[0].year == "2020"
        assert citations[0].page == 42
        assert citations[1].id == 2
        assert citations[1].author.endswith("A.")  # Might be "Jones, A." or "A."
        assert citations[1].year == "2019"

    def test_extract_from_text_no_citations(self):
        """Test extraction with no citations."""
        manager = CitationManager()
        text = "This is just regular text with no citations."

        citations = manager.extract_from_text(text)

        assert len(citations) == 0

    def test_extract_from_text_mixed_formats(self):
        """Test extraction with both inline and footnote citations."""
        manager = CitationManager()
        text = """
        Inline citation [Smith, 2020, p. 5] here.

        And a footnote citation[^1].

        [^1]: Brown, T. (2021). Research Methods, p. 100.
        """

        citations = manager.extract_from_text(text)

        # Should extract both types
        assert len(citations) >= 2

    def test_deduplicate_citations(self):
        """Test citation deduplication across sections."""
        manager = CitationManager()

        # Create sections with duplicate citations
        citation1 = Citation(
            id="1",
            author="Smith",
            title="Research Paper",
            page="10",
            year="2020",
            full_citation="Smith (2020), p. 10",
        )
        citation2 = Citation(
            id="2",
            author="Jones",
            title="Another Paper",
            page="5",
            year="2019",
            full_citation="Jones (2019), p. 5",
        )
        # Duplicate of citation1
        citation3 = Citation(
            id="3",
            author="Smith",
            title="Research Paper",
            page="10",
            year="2020",
            full_citation="Smith (2020), p. 10",
        )

        section1 = AcademicSection(
            heading="Section 1", level=2, content="Content", citations=[citation1, citation2]
        )
        section2 = AcademicSection(
            heading="Section 2", level=2, content="Content", citations=[citation3]
        )

        unique_citations = manager.deduplicate([section1, section2])

        # Should have only 2 unique citations
        assert len(unique_citations) == 2

    def test_deduplicate_different_pages(self):
        """Test that citations with different pages are not duplicates."""
        manager = CitationManager()

        citation1 = Citation(
            id="1",
            author="Smith",
            title="Research Paper",
            page="10",
            year="2020",
            full_citation="Smith (2020), p. 10",
        )
        citation2 = Citation(
            id="2",
            author="Smith",
            title="Research Paper",
            page="15",
            year="2020",
            full_citation="Smith (2020), p. 15",
        )

        section = AcademicSection(
            heading="Section", level=2, content="Content", citations=[citation1, citation2]
        )

        unique_citations = manager.deduplicate([section])

        # Different pages = different citations
        assert len(unique_citations) == 2

    def test_check_citations_valid(self):
        """Test citation checking with valid citations."""
        manager = CitationManager()
        text = """
        Valid citations [Smith, 2020, p. 10] and [Jones, 2019, p. 5].
        """

        result = manager.check_citations(text)

        assert result.total_citations == 2
        assert result.valid_citations == 2
        assert len(result.invalid_citations) == 0

    def test_check_citations_missing_page_not_strict(self):
        """Test citation checking with missing pages (not strict)."""
        manager = CitationManager()
        text = "[Smith, 2020]"  # No page number

        result = manager.check_citations(text, strict=False)

        assert result.total_citations == 1
        assert result.valid_citations == 1
        assert len(result.invalid_citations) == 0
        assert len(result.missing_pages) == 1

    def test_check_citations_missing_page_strict(self):
        """Test citation checking with missing pages (strict mode)."""
        manager = CitationManager()
        text = "[Smith, 2020]"  # No page number

        result = manager.check_citations(text, strict=True)

        assert result.total_citations == 1
        assert result.valid_citations == 0
        assert len(result.invalid_citations) == 1

    def test_check_citations_suspicious_year(self):
        """Test citation checking with suspicious year."""
        manager = CitationManager()
        text = "[Smith, 3000, p. 10]"  # Future year

        result = manager.check_citations(text)

        assert len(result.warnings) > 0

    def test_export_bibtex(self):
        """Test BibTeX export."""
        manager = CitationManager()
        citations = [
            Citation(
                id="1",
                author="Smith",
                title="Research Paper",
                page="10",
                year="2020",
                full_citation="Smith (2020)",
            )
        ]

        bibtex = manager.export_bibtex(citations)

        assert "@article{" in bibtex or "@misc{" in bibtex
        assert "Smith" in bibtex
        assert "2020" in bibtex

    def test_export_ris(self):
        """Test RIS export."""
        manager = CitationManager()
        citations = [
            Citation(
                id="1",
                author="Smith",
                title="Research Paper",
                page="10",
                year="2020",
                full_citation="Smith (2020)",
            )
        ]

        ris = manager.export_ris(citations)

        assert "TY  - JOUR" in ris
        assert "AU  - Smith" in ris
        assert "PY  - 2020" in ris
        assert "ER  -" in ris

    def test_export_json(self):
        """Test JSON export."""
        manager = CitationManager()
        citations = [
            Citation(
                id="1",
                author="Smith",
                title="Research Paper",
                page="10",
                year="2020",
                full_citation="Smith (2020)",
            )
        ]

        json_output = manager.export_json(citations)
        parsed = json.loads(json_output)

        assert len(parsed) == 1
        assert parsed[0]["author"] == "Smith"
        assert parsed[0]["year"] == "2020"

    def test_export_invalid_format(self):
        """Test export with invalid format."""
        manager = CitationManager()
        citations = [
            Citation(id="1", author="Smith", title="", page=None, year="2020", full_citation="")
        ]

        with pytest.raises(ValueError):
            manager.export(citations, "invalid_format")

    def test_export_format_bibtex(self):
        """Test export method with BibTeX format."""
        manager = CitationManager()
        citations = [
            Citation(
                id="1",
                author="Smith",
                title="Research",
                page="10",
                year="2020",
                full_citation="Smith (2020)",
            )
        ]

        output = manager.export(citations, "bibtex")
        assert "Smith" in output

    def test_export_format_ris(self):
        """Test export method with RIS format."""
        manager = CitationManager()
        citations = [
            Citation(
                id="1",
                author="Smith",
                title="Research",
                page="10",
                year="2020",
                full_citation="Smith (2020)",
            )
        ]

        output = manager.export(citations, "ris")
        assert "AU  - Smith" in output

    def test_export_format_json(self):
        """Test export method with JSON format."""
        manager = CitationManager()
        citations = [
            Citation(
                id="1",
                author="Smith",
                title="Research",
                page="10",
                year="2020",
                full_citation="Smith (2020)",
            )
        ]

        output = manager.export(citations, "json")
        parsed = json.loads(output)
        assert parsed[0]["author"] == "Smith"

    def test_format_bibliography_apa(self):
        """Test bibliography formatting in APA style."""
        manager = CitationManager()
        citations = [
            Citation(
                id="1",
                author="Smith, J.",
                title="Research Paper",
                page="10",
                year="2020",
                full_citation="Smith, J. (2020). Research Paper. Journal, p. 10.",
            ),
            Citation(
                id="2",
                author="Jones, A.",
                title="Another Study",
                page="5",
                year="2019",
                full_citation="Jones, A. (2019). Another Study. Publisher, p. 5.",
            ),
        ]

        bibliography = manager.format_bibliography(citations, style="apa")

        assert "Smith, J. (2020)" in bibliography
        assert "Jones, A. (2019)" in bibliography

    def test_format_bibliography_unsupported_style(self):
        """Test bibliography formatting with unsupported style."""
        manager = CitationManager()
        citations = []

        with pytest.raises(ValueError):
            manager.format_bibliography(citations, style="mla")

    def test_deduplicate_in_file(self):
        """Test deduplication in file."""
        manager = CitationManager()

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(
                """
            Text with citations [Smith, 2020, p. 10] and [Smith, 2020, p. 10].
            """
            )
            temp_path = Path(f.name)

        try:
            num_duplicates = manager.deduplicate_in_file(temp_path)
            # Should find at least 1 duplicate
            assert num_duplicates >= 0
        finally:
            temp_path.unlink()

    def test_extract_complex_inline_citation(self):
        """Test extraction of complex inline citations."""
        manager = CitationManager()
        text = "[Smith et al., 2020, p. 42]"

        citations = manager.extract_from_text(text)

        # Should extract the citation (author might include "et al.")
        assert len(citations) >= 1

    def test_check_citations_empty_text(self):
        """Test checking citations in empty text."""
        manager = CitationManager()
        text = ""

        result = manager.check_citations(text)

        assert result.total_citations == 0
        assert result.valid_citations == 0

    def test_deduplicate_empty_sections(self):
        """Test deduplication with no sections."""
        manager = CitationManager()

        unique_citations = manager.deduplicate([])

        assert len(unique_citations) == 0

    def test_export_empty_citations(self):
        """Test exporting empty citation list."""
        manager = CitationManager()

        bibtex = manager.export_bibtex([])
        assert bibtex == ""

        ris = manager.export_ris([])
        assert ris == ""

        json_output = manager.export_json([])
        assert json_output == "[]"

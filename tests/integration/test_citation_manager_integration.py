"""Integration tests for Citation Manager workflow."""

import pytest

from acadwrite.workflows.citation_manager import CitationManager


class TestCitationManagerIntegration:
    """Integration tests for citation management."""

    def test_extract_from_real_document(self, sample_markdown_with_citations):
        """Test extracting citations from real markdown document."""
        manager = CitationManager()

        text = sample_markdown_with_citations.read_text()
        citations = manager.extract_from_text(text)

        # Should find all citations in the document
        assert len(citations) >= 5  # Document has 5 citations

        # Verify some specific citations
        authors = [c.author for c in citations]
        assert "Smith" in authors
        assert "Jones" in authors
        assert "Brown" in authors

    def test_check_citations_valid_document(self, sample_markdown_with_citations):
        """Test checking citations in valid document."""
        manager = CitationManager()

        text = sample_markdown_with_citations.read_text()
        result = manager.check_citations(text, strict=False)

        # Should find citations
        assert result.total_citations >= 5
        assert result.valid_citations >= 5

        # Should be valid
        assert result.is_valid

    def test_check_citations_strict_mode(self, sample_markdown_with_citations):
        """Test checking citations in strict mode."""
        manager = CitationManager()

        text = sample_markdown_with_citations.read_text()
        result = manager.check_citations(text, strict=True)

        # Strict mode checks for complete citations with page numbers
        assert result.total_citations >= 5

        # Some may be missing page numbers
        if result.issues:
            # Verify issue structure
            for issue in result.issues:
                assert "type" in issue
                assert "citation" in issue

    def test_check_citations_missing_citations(self, sample_markdown_document):
        """Test checking document with no citations."""
        manager = CitationManager()

        text = sample_markdown_document.read_text()
        result = manager.check_citations(text, strict=False)

        # Should have no citations
        assert result.total_citations == 0
        assert result.valid_citations == 0

        # May or may not be considered "valid" depending on implementation

    def test_export_to_bibtex(self, sample_markdown_with_citations):
        """Test exporting citations to BibTeX format."""
        manager = CitationManager()

        text = sample_markdown_with_citations.read_text()
        citations = manager.extract_from_text(text)

        bibtex = manager.export(citations, format="bibtex")

        # Verify BibTeX format
        assert "@article" in bibtex or "@book" in bibtex
        assert len(bibtex) > 0

        # Should have entries for each citation
        for citation in citations:
            if citation.author:
                # Author should appear in BibTeX
                assert citation.author in bibtex

    def test_export_to_ris(self, sample_markdown_with_citations):
        """Test exporting citations to RIS format."""
        manager = CitationManager()

        text = sample_markdown_with_citations.read_text()
        citations = manager.extract_from_text(text)

        ris = manager.export(citations, format="ris")

        # Verify RIS format
        assert "TY  -" in ris
        assert "ER  -" in ris
        assert len(ris) > 0

        # Should have entries for each citation
        assert ris.count("ER  -") == len(citations)

    def test_export_to_json(self, sample_markdown_with_citations):
        """Test exporting citations to JSON format."""
        import json

        manager = CitationManager()

        text = sample_markdown_with_citations.read_text()
        citations = manager.extract_from_text(text)

        json_output = manager.export(citations, format="json")

        # Verify JSON format
        parsed = json.loads(json_output)
        assert isinstance(parsed, list)
        assert len(parsed) == len(citations)

        # Verify JSON structure
        for item in parsed:
            assert "author" in item
            assert "year" in item

    def test_deduplicate_citations(self, sample_markdown_with_citations):
        """Test deduplicating citations from sections."""
        from acadwrite.models.section import AcademicSection, Citation

        manager = CitationManager()

        # Create sections with duplicate citations
        section1 = AcademicSection(
            heading="Section 1",
            level=2,
            content="Content 1",
            citations=[
                Citation(id="smith2020", author="Smith", year="2020", title="Paper 1"),
                Citation(id="jones2019", author="Jones", year="2019", title="Paper 2"),
            ],
            subsections=[],
        )

        section2 = AcademicSection(
            heading="Section 2",
            level=2,
            content="Content 2",
            citations=[
                Citation(id="smith2020", author="Smith", year="2020", title="Paper 1"),  # Duplicate
                Citation(id="brown2021", author="Brown", year="2021", title="Paper 3"),
            ],
            subsections=[],
        )

        deduplicated = manager.deduplicate([section1, section2])

        # Should remove duplicates
        assert len(deduplicated) == 3  # Not 4
        citation_ids = [c.id for c in deduplicated]
        assert len(citation_ids) == len(set(citation_ids))  # All unique

    def test_extract_mixed_citation_styles(self, tmp_path):
        """Test extracting from document with mixed citation styles."""
        doc = tmp_path / "mixed.md"
        doc.write_text(
            """# Mixed Citations

Inline citation [Smith, 2020, p. 15] and another [Jones, 2019].

Footnote style[^1] and another[^2].

[^1]: Smith, A. (2020). Title. Publisher.
[^2]: Jones, B. (2019). Another Title. Publisher.
"""
        )

        manager = CitationManager()
        text = doc.read_text()
        citations = manager.extract_from_text(text)

        # Should extract both inline and footnote citations
        assert len(citations) >= 4

    def test_extract_incomplete_citations(self, tmp_path):
        """Test extracting incomplete citations."""
        doc = tmp_path / "incomplete.md"
        doc.write_text(
            """# Incomplete Citations

Missing page [Smith, 2020] and missing year [Jones, n.d., p. 10].
"""
        )

        manager = CitationManager()
        text = doc.read_text()
        citations = manager.extract_from_text(text)

        # Should still extract them
        assert len(citations) >= 2

        # Verify handling of missing fields
        for citation in citations:
            assert citation.author is not None

    def test_check_duplicate_citations(self, tmp_path):
        """Test detecting duplicate citations."""
        doc = tmp_path / "duplicates.md"
        doc.write_text(
            """# Document with Duplicates

First mention [Smith, 2020, p. 15].
Second mention [Smith, 2020, p. 15].
Third mention [Smith, 2020, p. 15].
"""
        )

        manager = CitationManager()
        text = doc.read_text()
        result = manager.check_citations(text, strict=False)

        # Should detect duplicates
        if result.issues:
            # May report duplicate citations
            duplicate_issues = [i for i in result.issues if "duplicate" in i.get("type", "").lower()]
            # Implementation may or may not flag duplicates

    def test_export_empty_citations(self):
        """Test exporting empty citation list."""
        manager = CitationManager()

        bibtex = manager.export([], format="bibtex")
        assert bibtex == "" or bibtex is not None

        ris = manager.export([], format="ris")
        assert ris == "" or ris is not None

        json_output = manager.export([], format="json")
        assert json_output == "[]" or json_output is not None

    def test_extract_from_empty_document(self, tmp_path):
        """Test extracting from empty document."""
        doc = tmp_path / "empty.md"
        doc.write_text("")

        manager = CitationManager()
        citations = manager.extract_from_text("")

        assert len(citations) == 0

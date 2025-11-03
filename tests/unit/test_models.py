"""Unit tests for data models."""

from pathlib import Path

import pytest

from acadwrite.models import (
    AcademicSection,
    Citation,
    CitationStyle,
    Outline,
    OutlineItem,
    QueryResponse,
    Source,
    WritingStyle,
)


class TestCitation:
    """Tests for Citation model."""

    def test_to_footnote(self) -> None:
        """Test footnote formatting."""
        citation = Citation(
            id=1,
            author="Smith",
            title="Test Article",
            year="2020",
            page=42,
            full_citation="Smith (2020). Test Article.",
        )

        footnote = citation.to_footnote()
        assert footnote == "[^1]: Smith (2020). Test Article. p.42"

    def test_to_footnote_no_page(self) -> None:
        """Test footnote without page number."""
        citation = Citation(
            id=2,
            author="Jones",
            title="Another Article",
            year="2021",
            full_citation="Jones (2021). Another Article.",
        )

        footnote = citation.to_footnote()
        assert "[^2]: Jones (2021). Another Article." in footnote
        assert "p." not in footnote

    def test_to_footnote_no_year(self) -> None:
        """Test footnote without year."""
        citation = Citation(
            id=3,
            author="Brown",
            title="Old Article",
            full_citation="Brown. Old Article.",
        )

        footnote = citation.to_footnote()
        assert "[^3]: Brown. Old Article." in footnote

    def test_to_bibtex(self) -> None:
        """Test BibTeX formatting."""
        citation = Citation(
            id=1,
            author="Smith, J.",
            title="Test Article",
            year="2020",
            page=42,
            full_citation="Smith (2020). Test Article.",
        )

        bibtex = citation.to_bibtex()
        assert "@article{" in bibtex
        assert "author = {Smith, J.}" in bibtex
        assert "title = {Test Article}" in bibtex
        assert "year = {2020}" in bibtex
        assert "pages = {42}" in bibtex

    def test_to_bibtex_custom_key(self) -> None:
        """Test BibTeX with custom key."""
        citation = Citation(
            id=1,
            author="Smith",
            title="Test",
            year="2020",
            full_citation="Smith (2020). Test.",
        )

        bibtex = citation.to_bibtex(key="smith2020custom")
        assert "@article{smith2020custom," in bibtex


class TestAcademicSection:
    """Tests for AcademicSection model."""

    def test_word_count(self) -> None:
        """Test word count calculation."""
        section = AcademicSection(
            heading="Introduction",
            level=2,
            content="This is a test section with ten words total.",
        )

        assert section.word_count() == 9

    def test_word_count_empty(self) -> None:
        """Test word count for empty content."""
        section = AcademicSection(heading="Empty", level=2, content="")

        assert section.word_count() == 0

    def test_all_citations(self) -> None:
        """Test citation collection including subsections."""
        citation1 = Citation(id=1, author="A", title="T1", full_citation="A. T1.")
        citation2 = Citation(id=2, author="B", title="T2", full_citation="B. T2.")
        citation3 = Citation(id=3, author="C", title="T3", full_citation="C. T3.")

        subsection = AcademicSection(
            heading="Sub", level=3, content="Content", citations=[citation3]
        )

        section = AcademicSection(
            heading="Main",
            level=2,
            content="Content",
            citations=[citation1, citation2],
            subsections=[subsection],
        )

        all_cit = section.all_citations()
        assert len(all_cit) == 3
        assert citation1 in all_cit
        assert citation2 in all_cit
        assert citation3 in all_cit

    def test_to_markdown_inline(self) -> None:
        """Test markdown rendering with inline citations."""
        section = AcademicSection(
            heading="Test",
            level=2,
            content="Some content here.",
        )

        markdown = section.to_markdown(CitationStyle.INLINE)
        assert "## Test" in markdown
        assert "Some content here." in markdown

    def test_to_markdown_footnote(self) -> None:
        """Test markdown rendering with footnote citations."""
        citation = Citation(
            id=1,
            author="Smith",
            title="Article",
            year="2020",
            full_citation="Smith (2020). Article.",
        )

        section = AcademicSection(
            heading="Test",
            level=2,
            content="Content [^1]",
            citations=[citation],
        )

        markdown = section.to_markdown(CitationStyle.FOOTNOTE)
        assert "## Test" in markdown
        assert "Content [^1]" in markdown
        assert "[^1]: Smith (2020). Article." in markdown


class TestOutlineItem:
    """Tests for OutlineItem model."""

    def test_is_leaf_true(self) -> None:
        """Test is_leaf for item without children."""
        item = OutlineItem(heading="Leaf", level=2)
        assert item.is_leaf() is True

    def test_is_leaf_false(self) -> None:
        """Test is_leaf for item with children."""
        child = OutlineItem(heading="Child", level=3)
        item = OutlineItem(heading="Parent", level=2, children=[child])
        assert item.is_leaf() is False

    def test_all_items(self) -> None:
        """Test flattening of item tree."""
        child1 = OutlineItem(heading="Child1", level=3)
        child2 = OutlineItem(heading="Child2", level=3)
        parent = OutlineItem(heading="Parent", level=2, children=[child1, child2])

        items = parent.all_items()
        assert len(items) == 3
        assert parent in items
        assert child1 in items
        assert child2 in items


class TestOutline:
    """Tests for Outline model."""

    def test_from_yaml(self, tmp_path: Path) -> None:
        """Test loading outline from YAML."""
        yaml_content = """
title: "Test Chapter"
sections:
  - heading: "Introduction"
    level: 2
    subsections:
      - heading: "Background"
        level: 3
  - heading: "Methods"
    level: 2
"""
        yaml_file = tmp_path / "outline.yaml"
        yaml_file.write_text(yaml_content)

        outline = Outline.from_yaml(yaml_file)

        assert outline.title == "Test Chapter"
        assert len(outline.items) == 2
        assert outline.items[0].heading == "Introduction"
        assert outline.items[0].level == 2
        assert len(outline.items[0].children) == 1
        assert outline.items[0].children[0].heading == "Background"
        assert outline.items[1].heading == "Methods"

    def test_from_markdown(self, tmp_path: Path) -> None:
        """Test loading outline from Markdown."""
        md_content = """# Test Chapter

## Introduction
### Background
### Related Work

## Methods
### Data Collection
"""
        md_file = tmp_path / "outline.md"
        md_file.write_text(md_content)

        outline = Outline.from_markdown(md_file)

        assert outline.title == "Test Chapter"
        assert len(outline.items) == 2
        assert outline.items[0].heading == "Introduction"
        assert outline.items[0].level == 2
        assert len(outline.items[0].children) == 2
        assert outline.items[0].children[0].heading == "Background"
        assert outline.items[0].children[0].level == 3

    def test_from_markdown_empty(self, tmp_path: Path) -> None:
        """Test loading empty markdown outline."""
        md_file = tmp_path / "empty.md"
        md_file.write_text("# Title Only\n")

        outline = Outline.from_markdown(md_file)

        assert outline.title == "Title Only"
        assert len(outline.items) == 0


class TestSource:
    """Tests for Source model."""

    def test_from_dict(self) -> None:
        """Test creating Source from API response dict."""
        data = {
            "document_id": "doc-123",
            "chunk_id": "chunk-456",
            "filename": "test.pdf",
            "citation": "Smith (2020). Test Article.",
            "in_text_citation": "(Smith, 2020, p. 42)",
            "text": "This is a test excerpt.",
            "similarity_score": 0.95,
            "relevance_score": 0.95,
            "chunk_metadata": {"page_number": 42},
            "document_metadata": {
                "title": "Test Article",
                "authors": ["Smith, J."],
                "publication_date": "2020",
            },
        }

        source = Source.from_dict(data)

        assert source.document_id == "doc-123"
        assert source.chunk_id == "chunk-456"
        assert source.filename == "test.pdf"
        assert source.citation == "Smith (2020). Test Article."
        assert source.in_text_citation == "(Smith, 2020, p. 42)"
        assert source.chunk_metadata.page_number == 42
        assert source.document_metadata.title == "Test Article"


class TestQueryResponse:
    """Tests for QueryResponse model."""

    def test_from_fileintel_response(self) -> None:
        """Test creating QueryResponse from API response."""
        data = {
            "answer": "This is the answer [Smith, 2020, p. 42].",
            "sources": [
                {
                    "document_id": "doc-1",
                    "chunk_id": "chunk-1",
                    "filename": "test.pdf",
                    "citation": "Smith (2020). Test.",
                    "in_text_citation": "(Smith, 2020, p. 42)",
                    "text": "Excerpt",
                    "similarity_score": 0.9,
                    "relevance_score": 0.9,
                    "chunk_metadata": {},
                    "document_metadata": {"title": "Test", "authors": []},
                }
            ],
            "query_type": "vector",
            "collection_id": "coll-123",
            "question": "What is the test?",
            "processing_time_ms": 1500,
        }

        response = QueryResponse.from_fileintel_response(data)

        assert response.answer == "This is the answer [Smith, 2020, p. 42]."
        assert len(response.sources) == 1
        assert response.sources[0].document_id == "doc-1"
        assert response.query_type == "vector"
        assert response.collection_id == "coll-123"
        assert response.question == "What is the test?"
        assert response.processing_time_ms == 1500

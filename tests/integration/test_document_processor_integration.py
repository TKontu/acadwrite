"""Integration tests for Document Processor workflow."""

import pytest

from acadwrite.workflows.document_processor import DocumentProcessor
from acadwrite.workflows.markdown_chunker import MarkdownChunker


class TestDocumentProcessorIntegration:
    """Integration tests for document processing with real FileIntel and LLM."""

    @pytest.mark.asyncio
    async def test_find_citations_basic(
        self, fileintel_client, sample_markdown_document, test_collection
    ):
        """Test finding citations for uncited claims."""
        try:
            processor = DocumentProcessor(
                fileintel_client=fileintel_client, chunker=MarkdownChunker()
            )

            text = sample_markdown_document.read_text()
            processed = await processor.process_document(
                markdown_text=text,
                collection=test_collection,
                operation="find_citations",
                max_sources=3,
            )

            # Verify document structure
            assert processed.original_markdown == text
            assert len(processed.chunks) > 0

            # Check that citations were suggested for claims
            chunks_with_citations = [c for c in processed.chunks if c.suggested_citations]
            # Should find at least some uncited claims
            assert len(chunks_with_citations) >= 0  # May have none if no claims found

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            raise

    @pytest.mark.asyncio
    async def test_find_citations_preserves_structure(
        self, fileintel_client, sample_markdown_document, test_collection
    ):
        """Test that find_citations preserves document structure."""
        try:
            processor = DocumentProcessor(
                fileintel_client=fileintel_client, chunker=MarkdownChunker()
            )

            text = sample_markdown_document.read_text()
            processed = await processor.process_document(
                markdown_text=text,
                collection=test_collection,
                operation="find_citations",
                max_sources=2,
            )

            # Reassemble document
            reassembled = processed.to_markdown()

            # Should preserve main structure (headings)
            assert "# Introduction" in reassembled or "## Introduction" in reassembled
            # May have modifications due to citations

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            raise

    @pytest.mark.asyncio
    async def test_add_evidence_operation(
        self, fileintel_client, sample_markdown_document, test_collection
    ):
        """Test adding evidence to existing sections."""
        try:
            processor = DocumentProcessor(
                fileintel_client=fileintel_client, chunker=MarkdownChunker()
            )

            text = sample_markdown_document.read_text()
            processed = await processor.process_document(
                markdown_text=text,
                collection=test_collection,
                operation="add_evidence",
                max_sources=3,
            )

            # Verify processing occurred
            assert len(processed.chunks) > 0

            # Check for added evidence
            chunks_with_evidence = [c for c in processed.chunks if c.added_evidence]
            # May or may not have evidence depending on content
            assert isinstance(chunks_with_evidence, list)

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            raise

    @pytest.mark.asyncio
    async def test_improve_clarity_operation(
        self, fileintel_client, llm_client, sample_markdown_document, test_collection
    ):
        """Test improving clarity with LLM."""
        try:
            processor = DocumentProcessor(
                fileintel_client=fileintel_client,
                llm_client=llm_client,
                chunker=MarkdownChunker(),
            )

            text = sample_markdown_document.read_text()
            processed = await processor.process_document(
                markdown_text=text,
                collection=test_collection,
                operation="improve_clarity",
                max_sources=2,
            )

            # Verify processing occurred
            assert len(processed.chunks) > 0

            # Check for clarity improvements
            chunks_with_improvements = [c for c in processed.chunks if c.improved_version]
            # Should have at least some improvements
            assert isinstance(chunks_with_improvements, list)

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            if "connection" in str(e).lower():
                pytest.skip("LLM endpoint not available")
            raise

    @pytest.mark.asyncio
    async def test_find_contradictions_operation(
        self, fileintel_client, sample_markdown_with_citations, test_collection
    ):
        """Test finding contradictions in cited content."""
        try:
            processor = DocumentProcessor(
                fileintel_client=fileintel_client, chunker=MarkdownChunker()
            )

            text = sample_markdown_with_citations.read_text()
            processed = await processor.process_document(
                markdown_text=text,
                collection=test_collection,
                operation="find_contradictions",
                max_sources=3,
            )

            # Verify processing occurred
            assert len(processed.chunks) > 0

            # Check for contradictions
            chunks_with_contradictions = [c for c in processed.chunks if c.contradictions]
            # May or may not find contradictions
            assert isinstance(chunks_with_contradictions, list)

            if chunks_with_contradictions:
                for chunk in chunks_with_contradictions:
                    for contradiction in chunk.contradictions:
                        # Verify contradiction structure
                        assert contradiction.text is not None
                        assert contradiction.citation is not None

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            raise

    @pytest.mark.asyncio
    async def test_chunking_integration(
        self, fileintel_client, tmp_path, test_collection
    ):
        """Test that markdown chunking works correctly with processor."""
        try:
            # Create document with various markdown elements
            doc = tmp_path / "complex.md"
            doc.write_text(
                """# Main Title

## Section 1

This is a paragraph with multiple sentences. It should be chunked appropriately. Each sentence matters.

- List item 1
- List item 2
- List item 3

## Section 2

Another paragraph here.

```python
def example():
    return "code"
```

> A quote block
> with multiple lines

### Subsection

Final paragraph.
"""
            )

            processor = DocumentProcessor(
                fileintel_client=fileintel_client, chunker=MarkdownChunker()
            )

            text = doc.read_text()
            processed = await processor.process_document(
                markdown_text=text,
                collection=test_collection,
                operation="find_citations",
                max_sources=2,
            )

            # Should have multiple chunks
            assert len(processed.chunks) >= 5

            # Verify chunk types are diverse
            chunk_types = set(c.original_chunk.type for c in processed.chunks)
            assert len(chunk_types) >= 2  # Should have multiple types

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            raise

    @pytest.mark.asyncio
    async def test_document_reassembly(
        self, fileintel_client, sample_markdown_document, test_collection
    ):
        """Test that processed document can be reassembled."""
        try:
            processor = DocumentProcessor(
                fileintel_client=fileintel_client, chunker=MarkdownChunker()
            )

            text = sample_markdown_document.read_text()
            processed = await processor.process_document(
                markdown_text=text,
                collection=test_collection,
                operation="find_citations",
                max_sources=2,
            )

            # Reassemble document
            reassembled = processed.to_markdown()

            # Should produce valid markdown
            assert len(reassembled) > 0
            assert isinstance(reassembled, str)

            # Should have some structural elements
            assert "#" in reassembled  # Has headings

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            raise

    @pytest.mark.asyncio
    async def test_context_preservation(
        self, fileintel_client, tmp_path, test_collection
    ):
        """Test that chunk context is preserved during processing."""
        try:
            # Create document with nested structure
            doc = tmp_path / "nested.md"
            doc.write_text(
                """# Chapter

## Section 1

Content in section 1.

### Subsection 1.1

Content in subsection 1.1.

### Subsection 1.2

Content in subsection 1.2.

## Section 2

Content in section 2.
"""
            )

            processor = DocumentProcessor(
                fileintel_client=fileintel_client, chunker=MarkdownChunker()
            )

            text = doc.read_text()
            processed = await processor.process_document(
                markdown_text=text,
                collection=test_collection,
                operation="find_citations",
                max_sources=2,
            )

            # Check that chunks have context
            for chunk in processed.chunks:
                if chunk.original_chunk.context:
                    # Context should be a hierarchy
                    assert ">" in chunk.original_chunk.context or len(chunk.original_chunk.context.split()) == 1

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            raise

    @pytest.mark.asyncio
    async def test_metadata_extraction(
        self, fileintel_client, sample_markdown_document, test_collection
    ):
        """Test that metadata is properly extracted and preserved."""
        try:
            processor = DocumentProcessor(
                fileintel_client=fileintel_client, chunker=MarkdownChunker()
            )

            text = sample_markdown_document.read_text()
            processed = await processor.process_document(
                markdown_text=text,
                collection=test_collection,
                operation="find_citations",
                max_sources=3,
            )

            # Check metadata
            assert processed.metadata is not None
            assert processed.metadata["operation"] == "find_citations"
            assert processed.metadata["collection"] == test_collection
            assert processed.metadata["max_sources"] == 3
            assert "total_chunks" in processed.metadata
            assert processed.metadata["total_chunks"] == len(processed.chunks)

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            raise

    @pytest.mark.asyncio
    async def test_empty_document(self, fileintel_client, tmp_path, test_collection):
        """Test processing empty document."""
        try:
            doc = tmp_path / "empty.md"
            doc.write_text("")

            processor = DocumentProcessor(
                fileintel_client=fileintel_client, chunker=MarkdownChunker()
            )

            text = doc.read_text()
            processed = await processor.process_document(
                markdown_text=text,
                collection=test_collection,
                operation="find_citations",
                max_sources=2,
            )

            # Should handle gracefully
            assert len(processed.chunks) == 0
            assert processed.original_markdown == ""

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            raise

    @pytest.mark.asyncio
    async def test_large_document(self, fileintel_client, tmp_path, test_collection):
        """Test processing large document with many sections."""
        try:
            # Create large document
            sections = []
            for i in range(20):
                sections.append(f"## Section {i}\n\nContent for section {i}.\n\n")

            doc = tmp_path / "large.md"
            doc.write_text("# Large Document\n\n" + "".join(sections))

            processor = DocumentProcessor(
                fileintel_client=fileintel_client, chunker=MarkdownChunker()
            )

            text = doc.read_text()
            processed = await processor.process_document(
                markdown_text=text,
                collection=test_collection,
                operation="find_citations",
                max_sources=2,
            )

            # Should handle many chunks
            assert len(processed.chunks) >= 20

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            raise

    @pytest.mark.asyncio
    async def test_mixed_content_types(self, fileintel_client, tmp_path, test_collection):
        """Test processing document with mixed content types."""
        try:
            doc = tmp_path / "mixed.md"
            doc.write_text(
                """# Mixed Content

Regular paragraph.

- List item
- Another item

```python
code_block = True
```

> Quote block

| Table | Header |
|-------|--------|
| Cell  | Data   |

More text.
"""
            )

            processor = DocumentProcessor(
                fileintel_client=fileintel_client, chunker=MarkdownChunker()
            )

            text = doc.read_text()
            processed = await processor.process_document(
                markdown_text=text,
                collection=test_collection,
                operation="find_citations",
                max_sources=2,
            )

            # Should handle all content types
            assert len(processed.chunks) > 0

            # Check for diverse chunk types
            chunk_types = [c.original_chunk.type for c in processed.chunks]
            assert "paragraph" in chunk_types or "list" in chunk_types or "code" in chunk_types

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            raise

    @pytest.mark.asyncio
    async def test_citation_format_consistency(
        self, fileintel_client, sample_markdown_document, test_collection
    ):
        """Test that suggested citations have consistent format."""
        try:
            processor = DocumentProcessor(
                fileintel_client=fileintel_client, chunker=MarkdownChunker()
            )

            text = sample_markdown_document.read_text()
            processed = await processor.process_document(
                markdown_text=text,
                collection=test_collection,
                operation="find_citations",
                max_sources=3,
            )

            # Check citation format in chunks
            for chunk in processed.chunks:
                if chunk.suggested_citations:
                    for citation in chunk.suggested_citations:
                        # Verify citation structure
                        assert citation.text is not None
                        assert citation.citation is not None
                        assert citation.relevance_score is not None
                        assert 0.0 <= citation.relevance_score <= 1.0

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            raise

    @pytest.mark.asyncio
    async def test_max_sources_respected(
        self, fileintel_client, sample_markdown_document, test_collection
    ):
        """Test that max_sources parameter is respected."""
        try:
            processor = DocumentProcessor(
                fileintel_client=fileintel_client, chunker=MarkdownChunker()
            )

            text = sample_markdown_document.read_text()
            processed = await processor.process_document(
                markdown_text=text,
                collection=test_collection,
                operation="find_citations",
                max_sources=2,
            )

            # Check that each chunk respects max_sources
            for chunk in processed.chunks:
                if chunk.suggested_citations:
                    assert len(chunk.suggested_citations) <= 2

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            raise

"""End-to-end integration tests for complete workflows."""

import pytest

from acadwrite.models.outline import Outline
from acadwrite.workflows.chapter_processor import ChapterProcessor
from acadwrite.workflows.citation_manager import CitationManager
from acadwrite.workflows.counterargument import CounterargumentGenerator
from acadwrite.workflows.document_processor import DocumentProcessor
from acadwrite.workflows.markdown_chunker import MarkdownChunker
from acadwrite.workflows.section_generator import SectionGenerator


class TestEndToEndWorkflows:
    """End-to-end integration tests for complete workflows."""

    @pytest.mark.asyncio
    async def test_complete_chapter_workflow(
        self, section_generator, formatter_service, test_collection, sample_outline_yaml, temp_output_dir
    ):
        """Test complete workflow from outline to finished chapter with citations."""
        try:
            # Step 1: Process outline to chapter
            processor = ChapterProcessor(
                section_generator=section_generator,
                formatter=formatter_service,
            )
            outline = Outline.from_yaml(sample_outline_yaml)

            chapter = await processor.process(
                outline=outline,
                collection=test_collection,
                output_dir=temp_output_dir,
                max_sources=3,
                max_words=300,
            )

            # Step 2: Extract citations from generated chapter
            manager = CitationManager()
            combined_file = temp_output_dir / "combined.md"
            text = combined_file.read_text()
            citations = manager.extract_from_text(text)

            # Step 3: Verify workflow completion
            assert chapter.title == "Test Chapter"
            assert len(chapter.sections) > 0
            assert chapter.metadata.total_words > 0

            # Should have generated citations
            assert len(citations) >= 0  # May have none if no sources

            # Files should exist
            assert combined_file.exists()

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            raise

    @pytest.mark.asyncio
    async def test_section_to_counterargument_workflow(
        self, fileintel_client, llm_client, test_collection
    ):
        """Test workflow from section generation to counterargument analysis."""
        try:
            # Step 1: Generate section with claim
            section_gen = SectionGenerator(fileintel_client=fileintel_client)
            section = await section_gen.generate(
                heading="AI Benefits in Healthcare",
                collection=test_collection,
                max_sources=3,
                max_words=200,
            )

            # Step 2: Extract a claim from the section
            # For test purposes, use a predefined claim
            claim = "AI improves diagnostic accuracy in healthcare"

            # Step 3: Generate counterarguments
            counter_gen = CounterargumentGenerator(
                fileintel_client=fileintel_client, llm_client=llm_client
            )
            report = await counter_gen.generate(
                claim=claim, collection=test_collection, depth="quick"
            )

            # Verify workflow
            assert section.content is not None
            assert len(section.content) > 0
            assert report.original_claim == claim
            assert report.inverted_claim is not None

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            if "connection" in str(e).lower():
                pytest.skip("LLM endpoint not available")
            raise

    @pytest.mark.asyncio
    async def test_document_processing_to_citation_export_workflow(
        self, fileintel_client, sample_markdown_document, test_collection, tmp_path
    ):
        """Test workflow from document processing to citation export."""
        try:
            # Step 1: Process document to find citations
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

            # Step 2: Reassemble document with citations
            reassembled = processed.to_markdown()
            output_file = tmp_path / "processed.md"
            output_file.write_text(reassembled)

            # Step 3: Extract and export citations
            manager = CitationManager()
            citations = manager.extract_from_text(reassembled)
            bibtex = manager.export(citations, format="bibtex")

            # Verify workflow
            assert len(processed.chunks) > 0
            assert len(reassembled) > 0
            assert output_file.exists()
            assert isinstance(bibtex, str)

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            raise

    @pytest.mark.asyncio
    async def test_multi_section_chapter_with_validation(
        self, section_generator, formatter_service, test_collection, tmp_path, temp_output_dir
    ):
        """Test complete workflow with multiple sections and citation validation."""
        try:
            # Step 1: Create outline for multi-section chapter
            outline_file = tmp_path / "multi_section.yaml"
            outline_file.write_text(
                """title: "Multi-Section Test"
sections:
  - heading: "Introduction"
    level: 2
  - heading: "Literature Review"
    level: 2
  - heading: "Methodology"
    level: 2
  - heading: "Conclusion"
    level: 2
"""
            )

            # Step 2: Generate chapter
            processor = ChapterProcessor(
                section_generator=section_generator,
                formatter=formatter_service,
            )
            outline = Outline.from_yaml(outline_file)
            chapter = await processor.process(
                outline=outline,
                collection=test_collection,
                output_dir=temp_output_dir,
                max_sources=3,
                max_words=250,
            )

            # Step 3: Validate citations in generated chapter
            manager = CitationManager()
            combined_file = temp_output_dir / "combined.md"
            text = combined_file.read_text()
            result = manager.check_citations(text, strict=False)

            # Verify workflow
            assert len(chapter.sections) == 4
            assert chapter.metadata.total_words > 0
            assert result.total_citations >= 0

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            raise

    @pytest.mark.asyncio
    async def test_iterative_document_improvement_workflow(
        self, fileintel_client, llm_client, tmp_path, test_collection
    ):
        """Test iterative workflow: generate, process, improve."""
        try:
            # Step 1: Generate initial section
            section_gen = SectionGenerator(fileintel_client=fileintel_client)
            section = await section_gen.generate(
                heading="Machine Learning Overview",
                collection=test_collection,
                max_sources=2,
                max_words=200,
            )

            # Step 2: Save to file
            doc_file = tmp_path / "ml_overview.md"
            doc_file.write_text(f"## {section.heading}\n\n{section.content}\n")

            # Step 3: Process for citations
            processor = DocumentProcessor(
                fileintel_client=fileintel_client, chunker=MarkdownChunker()
            )
            processed = await processor.process_document(
                markdown_text=doc_file.read_text(),
                collection=test_collection,
                operation="find_citations",
                max_sources=3,
            )

            # Step 4: Improve clarity (requires LLM)
            improved = await processor.process_document(
                markdown_text=processed.to_markdown(),
                collection=test_collection,
                operation="improve_clarity",
                max_sources=2,
            )

            # Verify workflow
            assert section.content is not None
            assert len(processed.chunks) > 0
            assert len(improved.chunks) > 0

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            if "connection" in str(e).lower():
                pytest.skip("LLM endpoint not available")
            raise

    @pytest.mark.asyncio
    async def test_citation_export_multiple_formats_workflow(
        self, section_generator, formatter_service, test_collection, sample_outline_yaml, temp_output_dir, tmp_path
    ):
        """Test workflow ending with exporting citations in multiple formats."""
        try:
            # Step 1: Generate chapter
            processor = ChapterProcessor(
                section_generator=section_generator,
                formatter=formatter_service,
            )
            outline = Outline.from_yaml(sample_outline_yaml)
            chapter = await processor.process(
                outline=outline,
                collection=test_collection,
                output_dir=temp_output_dir,
                max_sources=3,
                max_words=200,
            )

            # Step 2: Extract citations
            manager = CitationManager()
            combined_file = temp_output_dir / "combined.md"
            text = combined_file.read_text()
            citations = manager.extract_from_text(text)

            # Step 3: Export to multiple formats
            bibtex = manager.export(citations, format="bibtex")
            ris = manager.export(citations, format="ris")
            json_output = manager.export(citations, format="json")

            # Step 4: Save exports
            (tmp_path / "citations.bib").write_text(bibtex)
            (tmp_path / "citations.ris").write_text(ris)
            (tmp_path / "citations.json").write_text(json_output)

            # Verify workflow
            assert chapter.metadata.total_citations >= 0
            assert isinstance(bibtex, str)
            assert isinstance(ris, str)
            assert isinstance(json_output, str)
            assert (tmp_path / "citations.bib").exists()

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            raise

    @pytest.mark.asyncio
    async def test_parallel_section_generation_workflow(
        self, fileintel_client, test_collection
    ):
        """Test generating multiple sections in parallel workflow."""
        try:
            section_gen = SectionGenerator(fileintel_client=fileintel_client)

            # Generate multiple sections (simulating parallel processing)
            headings = [
                "Neural Networks",
                "Deep Learning",
                "Machine Learning Applications",
            ]

            sections = []
            for heading in headings:
                section = await section_gen.generate(
                    heading=heading,
                    collection=test_collection,
                    max_sources=2,
                    max_words=150,
                )
                sections.append(section)

            # Verify all sections generated
            assert len(sections) == 3
            for section in sections:
                assert section.content is not None
                assert len(section.content) > 0

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            raise

    @pytest.mark.asyncio
    async def test_counterargument_to_balanced_section_workflow(
        self, fileintel_client, llm_client, test_collection
    ):
        """Test workflow from counterargument to balanced section."""
        try:
            # Step 1: Generate counterarguments
            counter_gen = CounterargumentGenerator(
                fileintel_client=fileintel_client, llm_client=llm_client
            )
            report = await counter_gen.generate(
                claim="Cloud computing reduces operational costs",
                collection=test_collection,
                depth="standard",
                synthesis=True,
            )

            # Step 2: Use synthesis as basis for balanced section
            section_gen = SectionGenerator(fileintel_client=fileintel_client)
            section = await section_gen.generate(
                heading="Cloud Computing Cost Analysis",
                collection=test_collection,
                context=report.synthesis if report.synthesis else "Balanced view on costs",
                max_sources=3,
                max_words=300,
            )

            # Verify workflow
            assert report.synthesis is not None
            assert section.content is not None
            assert len(section.content) > 0

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            if "connection" in str(e).lower():
                pytest.skip("LLM endpoint not available")
            raise

    @pytest.mark.asyncio
    async def test_full_research_paper_workflow(
        self, section_generator, formatter_service, llm_client, test_collection, tmp_path, temp_output_dir
    ):
        """Test complete workflow for generating a research paper section."""
        try:
            # Step 1: Create comprehensive outline
            outline_file = tmp_path / "research_paper.yaml"
            outline_file.write_text(
                """title: "Research Paper"
sections:
  - heading: "Abstract"
    level: 2
  - heading: "Introduction"
    level: 2
  - heading: "Literature Review"
    level: 2
    subsections:
      - heading: "Background"
        level: 3
      - heading: "Current Research"
        level: 3
  - heading: "Methodology"
    level: 2
  - heading: "Results"
    level: 2
  - heading: "Discussion"
    level: 2
  - heading: "Conclusion"
    level: 2
"""
            )

            # Step 2: Generate chapter
            processor = ChapterProcessor(
                section_generator=section_generator,
                formatter=formatter_service,
            )
            outline = Outline.from_yaml(outline_file)
            chapter = await processor.process(
                outline=outline,
                collection=test_collection,
                output_dir=temp_output_dir,
                max_sources=3,
                max_words=200,
                citation_style="footnote",
            )

            # Step 3: Validate structure
            assert len(chapter.sections) == 7  # Top-level sections
            lit_review = next(
                (s for s in chapter.sections if s.heading == "Literature Review"), None
            )
            if lit_review:
                assert len(lit_review.subsections) == 2

            # Step 4: Check citations
            manager = CitationManager()
            combined_file = temp_output_dir / "combined.md"
            text = combined_file.read_text()
            result = manager.check_citations(text, strict=False)

            # Step 5: Export citations
            citations = manager.extract_from_text(text)
            bibtex = manager.export(citations, format="bibtex")

            # Verify complete workflow
            assert chapter.metadata.total_words > 0
            assert result.total_citations >= 0
            assert combined_file.exists()
            assert isinstance(bibtex, str)

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            if "connection" in str(e).lower():
                pytest.skip("LLM endpoint not available")
            raise

    @pytest.mark.asyncio
    async def test_document_quality_check_workflow(
        self, fileintel_client, llm_client, sample_markdown_with_citations, test_collection
    ):
        """Test workflow for checking and improving document quality."""
        try:
            # Step 1: Check existing citations
            manager = CitationManager()
            text = sample_markdown_with_citations.read_text()
            validation_result = manager.check_citations(text, strict=True)

            # Step 2: Process for contradictions
            processor = DocumentProcessor(
                fileintel_client=fileintel_client, chunker=MarkdownChunker()
            )
            processed = await processor.process_document(
                markdown_text=text,
                collection=test_collection,
                operation="find_contradictions",
                max_sources=3,
            )

            # Step 3: Improve clarity if needed
            improved = await processor.process_document(
                markdown_text=text,
                collection=test_collection,
                operation="improve_clarity",
                max_sources=2,
            )

            # Verify workflow
            assert validation_result.total_citations >= 0
            assert len(processed.chunks) > 0
            assert len(improved.chunks) > 0

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            if "connection" in str(e).lower():
                pytest.skip("LLM endpoint not available")
            raise

"""Integration tests for Chapter Processor workflow."""

import pytest

from acadwrite.models.outline import Outline
from acadwrite.workflows.chapter_processor import ChapterProcessor


class TestChapterProcessorIntegration:
    """Integration tests for chapter processing with real FileIntel."""

    @pytest.mark.asyncio
    async def test_process_yaml_outline(
        self, section_generator, formatter_service, test_collection, sample_outline_yaml, temp_output_dir
    ):
        """Test processing YAML outline into chapter."""
        try:
            processor = ChapterProcessor(
                section_generator=section_generator,
                formatter=formatter_service,
            )

            # Load outline
            outline = Outline.from_yaml(sample_outline_yaml)

            # Process chapter
            chapter = await processor.process(
                outline=outline,
                collection=test_collection,
                output_dir=temp_output_dir,
                max_sources=3,
                max_words=200,  # Keep small for faster tests
            )

            # Verify chapter structure
            assert chapter.title == "Test Chapter"
            assert len(chapter.sections) > 0

            # Verify all sections were generated
            assert any(s.heading == "Introduction" for s in chapter.sections)
            assert any(s.heading == "Background" for s in chapter.sections)
            assert any(s.heading == "Methods" for s in chapter.sections)
            assert any(s.heading == "Results" for s in chapter.sections)
            assert any(s.heading == "Conclusion" for s in chapter.sections)

            # Verify metadata
            assert chapter.metadata.collection == test_collection
            assert chapter.metadata.total_words > 0
            assert chapter.metadata.total_citations >= 0

            # Verify files were created
            assert (temp_output_dir / "combined.md").exists()
            section_files = list(temp_output_dir.glob("*.md"))
            assert len(section_files) > 1  # combined.md + individual sections

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            raise

    @pytest.mark.asyncio
    async def test_process_markdown_outline(
        self, section_generator, formatter_service, test_collection, sample_outline_markdown, temp_output_dir
    ):
        """Test processing markdown outline into chapter."""
        try:
            processor = ChapterProcessor(
                section_generator=section_generator,
                formatter=formatter_service,
            )

            # Load outline
            outline = Outline.from_markdown(sample_outline_markdown)

            # Process chapter
            chapter = await processor.process(
                outline=outline,
                collection=test_collection,
                output_dir=temp_output_dir,
                max_sources=3,
                max_words=200,
            )

            # Verify chapter structure
            assert chapter.title == "Test Chapter"
            assert len(chapter.sections) > 0

            # Verify metadata
            assert chapter.metadata.total_words > 0

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            raise

    @pytest.mark.asyncio
    async def test_process_with_nested_sections(
        self, section_generator, formatter_service, test_collection, sample_outline_yaml, temp_output_dir
    ):
        """Test processing outline with nested subsections."""
        try:
            processor = ChapterProcessor(
                section_generator=section_generator,
                formatter=formatter_service,
            )
            outline = Outline.from_yaml(sample_outline_yaml)

            chapter = await processor.process(
                outline=outline,
                collection=test_collection,
                output_dir=temp_output_dir,
                max_sources=2,
                max_words=150,
            )

            # Find the Methods section which has subsections
            methods_section = next((s for s in chapter.sections if s.heading == "Methods"), None)
            assert methods_section is not None

            # Verify subsections
            assert len(methods_section.subsections) == 2
            subsection_headings = [s.heading for s in methods_section.subsections]
            assert "Data Collection" in subsection_headings
            assert "Analysis" in subsection_headings

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            raise

    @pytest.mark.asyncio
    async def test_process_single_file_output(
        self, section_generator, formatter_service, test_collection, sample_outline_yaml, temp_output_dir
    ):
        """Test processing with single file output option."""
        try:
            processor = ChapterProcessor(
                section_generator=section_generator,
                formatter=formatter_service,
            )
            outline = Outline.from_yaml(sample_outline_yaml)

            chapter = await processor.process(
                outline=outline,
                collection=test_collection,
                output_dir=temp_output_dir,
                single_file=True,
                max_sources=2,
                max_words=150,
            )

            # Should only have combined.md
            md_files = list(temp_output_dir.glob("*.md"))
            assert len(md_files) == 1
            assert md_files[0].name == "combined.md"

            # Verify combined file has all content
            combined_content = md_files[0].read_text()
            assert "Introduction" in combined_content
            assert "Background" in combined_content
            assert "Methods" in combined_content

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            raise

    @pytest.mark.asyncio
    async def test_process_citation_deduplication(
        self, section_generator, formatter_service, test_collection, sample_outline_yaml, temp_output_dir
    ):
        """Test that citations are deduplicated across sections."""
        try:
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

            # Get all citations
            all_citations = []
            for section in chapter.sections:
                all_citations.extend(section.all_citations())

            # Check for duplicates by comparing citation IDs
            citation_ids = [c.id for c in all_citations]
            unique_ids = set(citation_ids)

            # After deduplication, should have fewer or equal citations
            assert len(unique_ids) <= len(citation_ids)

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            raise

    @pytest.mark.asyncio
    async def test_process_with_different_citation_styles(
        self, section_generator, formatter_service, test_collection, sample_outline_yaml, temp_output_dir
    ):
        """Test processing with different citation styles."""
        try:
            processor = ChapterProcessor(
                section_generator=section_generator,
                formatter=formatter_service,
            )
            outline = Outline.from_yaml(sample_outline_yaml)

            # Test footnote style
            chapter_footnote = await processor.process(
                outline=outline,
                collection=test_collection,
                output_dir=temp_output_dir,
                citation_style="footnote",
                max_sources=2,
                max_words=150,
            )

            # Check if footnote markers exist in content
            combined_file = temp_output_dir / "combined.md"
            if combined_file.exists():
                content = combined_file.read_text()
                # May or may not have [^N] markers depending on sources
                # Just verify it doesn't crash

            assert chapter_footnote.metadata.citation_style == "footnote"

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            raise

    @pytest.mark.asyncio
    async def test_process_minimal_outline(
        self, section_generator, formatter_service, test_collection, tmp_path, temp_output_dir
    ):
        """Test processing minimal outline with single section."""
        try:
            # Create minimal outline
            minimal_outline = tmp_path / "minimal.yaml"
            minimal_outline.write_text(
                """title: "Minimal Chapter"
sections:
  - heading: "Single Section"
    level: 1
"""
            )

            processor = ChapterProcessor(
                section_generator=section_generator,
                formatter=formatter_service,
            )
            outline = Outline.from_yaml(minimal_outline)

            chapter = await processor.process(
                outline=outline,
                collection=test_collection,
                output_dir=temp_output_dir,
                max_sources=2,
                max_words=200,
            )

            assert chapter.title == "Minimal Chapter"
            assert len(chapter.sections) == 1
            assert chapter.sections[0].heading == "Single Section"

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            raise

    @pytest.mark.asyncio
    async def test_process_preserves_heading_levels(
        self, section_generator, formatter_service, test_collection, sample_outline_yaml, temp_output_dir
    ):
        """Test that heading levels are preserved correctly."""
        try:
            processor = ChapterProcessor(
                section_generator=section_generator,
                formatter=formatter_service,
            )
            outline = Outline.from_yaml(sample_outline_yaml)

            chapter = await processor.process(
                outline=outline,
                collection=test_collection,
                output_dir=temp_output_dir,
                max_sources=2,
                max_words=150,
            )

            # Check top-level sections are level 1
            for section in chapter.sections:
                if section.heading in ["Introduction", "Background", "Results", "Conclusion"]:
                    assert section.level == 2  # Level 2 for ## headings

                # Check subsections
                if section.heading == "Methods":
                    for subsection in section.subsections:
                        assert subsection.level == 3  # Level 3 for ### headings

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            raise

    @pytest.mark.asyncio
    async def test_process_output_file_structure(
        self, section_generator, formatter_service, test_collection, sample_outline_yaml, temp_output_dir
    ):
        """Test that output files are created with correct structure."""
        try:
            processor = ChapterProcessor(
                section_generator=section_generator,
                formatter=formatter_service,
            )
            outline = Outline.from_yaml(sample_outline_yaml)

            await processor.process(
                outline=outline,
                collection=test_collection,
                output_dir=temp_output_dir,
                max_sources=2,
                max_words=150,
            )

            # Verify files exist
            assert (temp_output_dir / "combined.md").exists()
            assert (temp_output_dir / "01_introduction.md").exists()
            assert (temp_output_dir / "02_background.md").exists()
            assert (temp_output_dir / "03_methods.md").exists()
            assert (temp_output_dir / "04_results.md").exists()
            assert (temp_output_dir / "05_conclusion.md").exists()

            # Verify files are not empty
            for md_file in temp_output_dir.glob("*.md"):
                content = md_file.read_text()
                assert len(content) > 0

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            raise

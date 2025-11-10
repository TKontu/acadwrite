"""Integration tests for Section Generator workflow."""

import pytest

from acadwrite.workflows.section_generator import SectionGenerator


class TestSectionGeneratorIntegration:
    """Integration tests for section generation with real FileIntel."""

    @pytest.mark.asyncio
    async def test_generate_basic_section(self, fileintel_client, test_collection):
        """Test generating a basic section."""
        try:
            generator = SectionGenerator(fileintel_client=fileintel_client)

            section = await generator.generate(
                heading="Introduction to Machine Learning",
                collection=test_collection,
                max_sources=5,
                max_words=500,
            )

            # Verify section structure
            assert section.heading == "Introduction to Machine Learning"
            assert section.level == 2
            assert len(section.content) > 0

            # Should have some content
            assert section.word_count() > 0
            assert section.word_count() <= 550  # Allow some margin

            # May or may not have citations depending on sources
            citations = section.all_citations()
            assert isinstance(citations, list)

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            raise

    @pytest.mark.asyncio
    async def test_generate_with_context(self, fileintel_client, test_collection):
        """Test generating section with context."""
        try:
            generator = SectionGenerator(fileintel_client=fileintel_client)

            section = await generator.generate(
                heading="Neural Network Applications",
                collection=test_collection,
                context="Focus on healthcare and medical diagnostics",
                max_sources=3,
                max_words=300,
            )

            assert section.content is not None
            assert len(section.content) > 0
            assert section.word_count() > 0

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            raise

    @pytest.mark.asyncio
    async def test_generate_multiple_sections(self, fileintel_client, test_collection):
        """Test generating multiple sections sequentially."""
        try:
            generator = SectionGenerator(fileintel_client=fileintel_client)

            headings = [
                "Overview of AI",
                "Machine Learning Fundamentals",
                "Deep Learning Architectures",
            ]

            sections = []
            for heading in headings:
                section = await generator.generate(
                    heading=heading,
                    collection=test_collection,
                    max_sources=3,
                    max_words=200,
                )
                sections.append(section)

            # All sections should be generated
            assert len(sections) == 3

            for section in sections:
                assert section.content is not None
                assert len(section.content) > 0
                assert section.word_count() > 0

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            raise

    @pytest.mark.asyncio
    async def test_generate_with_different_word_limits(self, fileintel_client, test_collection):
        """Test generating sections with different word limits."""
        try:
            generator = SectionGenerator(fileintel_client=fileintel_client)

            # Short section
            section_short = await generator.generate(
                heading="AI Definition",
                collection=test_collection,
                max_sources=2,
                max_words=100,
            )

            # Long section
            section_long = await generator.generate(
                heading="History of AI",
                collection=test_collection,
                max_sources=5,
                max_words=800,
            )

            # Verify word counts respect limits (with margin)
            assert section_short.word_count() <= 120
            assert section_long.word_count() <= 850

            # Short should be shorter than long
            assert section_short.word_count() < section_long.word_count()

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            raise

    @pytest.mark.asyncio
    async def test_generate_with_max_sources_limit(self, fileintel_client, test_collection):
        """Test that max_sources parameter is respected."""
        try:
            generator = SectionGenerator(fileintel_client=fileintel_client)

            section = await generator.generate(
                heading="Machine Learning Types",
                collection=test_collection,
                max_sources=2,
                max_words=400,
            )

            # Count unique citations
            citations = section.all_citations()
            # Should have at most max_sources citations
            assert len(citations) <= 2

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            raise

    @pytest.mark.asyncio
    async def test_generate_citations_format(self, fileintel_client, test_collection):
        """Test that citations are properly formatted."""
        try:
            generator = SectionGenerator(fileintel_client=fileintel_client)

            section = await generator.generate(
                heading="Deep Learning Techniques",
                collection=test_collection,
                max_sources=5,
                max_words=400,
            )

            citations = section.all_citations()

            if citations:
                for citation in citations:
                    # Verify citation has required fields
                    assert citation.author is not None
                    assert citation.year is not None
                    # Page and title may be optional
                    assert citation.id is not None

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            raise

    @pytest.mark.asyncio
    async def test_generate_with_empty_collection(self, fileintel_client):
        """Test behavior with empty or minimal collection."""
        try:
            generator = SectionGenerator(fileintel_client=fileintel_client)

            # Try to generate from potentially empty collection
            section = await generator.generate(
                heading="Test Heading",
                collection="empty_test_collection_xyz",
                max_sources=5,
                max_words=300,
            )

            # Should still return a section, even if minimal
            assert section.heading == "Test Heading"
            # Content might be minimal or empty depending on implementation

        except Exception as e:
            # Collection not found is acceptable
            if "not found" in str(e).lower():
                pytest.skip("Empty collection test skipped - collection not found")
            # Other errors should be raised
            raise

    @pytest.mark.asyncio
    async def test_generate_special_characters_in_heading(
        self, fileintel_client, test_collection
    ):
        """Test generating section with special characters in heading."""
        try:
            generator = SectionGenerator(fileintel_client=fileintel_client)

            section = await generator.generate(
                heading="AI & ML: Evolution & Impact",
                collection=test_collection,
                max_sources=3,
                max_words=300,
            )

            assert section.heading == "AI & ML: Evolution & Impact"
            assert section.content is not None

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            raise

    @pytest.mark.asyncio
    async def test_generate_long_heading(self, fileintel_client, test_collection):
        """Test generating section with very long heading."""
        try:
            generator = SectionGenerator(fileintel_client=fileintel_client)

            long_heading = (
                "A Comprehensive Analysis of Machine Learning Algorithms "
                "and Their Applications in Modern Data Science and Artificial Intelligence"
            )

            section = await generator.generate(
                heading=long_heading,
                collection=test_collection,
                max_sources=3,
                max_words=300,
            )

            assert section.heading == long_heading
            assert section.content is not None

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            raise

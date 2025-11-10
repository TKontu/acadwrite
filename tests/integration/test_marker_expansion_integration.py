"""Integration tests for marker expansion functionality."""

import tempfile
from pathlib import Path

import pytest

from acadwrite.config import Settings
from acadwrite.services.fileintel import FileIntelClient
from acadwrite.services.llm import LLMClient
from acadwrite.workflows.marker_expander import MarkerExpander


@pytest.mark.asyncio
@pytest.mark.integration
class TestMarkerExpansionIntegration:
    """Integration tests for marker expansion with real FileIntel."""

    async def test_expand_simple_marker(self, fileintel_client, test_collection):
        """Test expanding a simple expand marker."""
        # Create test file
        markdown_content = """# Test Document

## Introduction

<!-- ACADWRITE: expand -->
- Topic: Concurrent engineering principles
- Focus: Core benefits and applications
<!-- END ACADWRITE -->

## Conclusion

Some concluding text.
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write(markdown_content)
            temp_path = Path(f.name)

        try:
            # Expand markers
            settings = Settings()
            expander = MarkerExpander(
                fileintel_client=fileintel_client, settings=settings
            )

            expanded_text, expansions = await expander.expand_file(
                file_path=temp_path, collection=test_collection
            )

            # Verify expansion
            assert len(expansions) == 1
            assert expansions[0].success
            assert len(expansions[0].generated_content) > 0
            assert "concurrent engineering" in expanded_text.lower()
            assert "<!-- ACADWRITE: expand -->" not in expanded_text
            assert "<!-- END ACADWRITE -->" not in expanded_text

            # Verify structure preserved
            assert "# Test Document" in expanded_text
            assert "## Introduction" in expanded_text
            assert "## Conclusion" in expanded_text
            assert "Some concluding text" in expanded_text

        finally:
            # Cleanup
            temp_path.unlink()

    async def test_expand_multiple_markers(self, fileintel_client, test_collection):
        """Test expanding multiple markers in one file."""
        markdown_content = """# Research Paper

## Background

<!-- ACADWRITE: expand -->
- Topic: Product development methodologies
<!-- END ACADWRITE -->

## Methods

<!-- ACADWRITE: expand -->
- Topic: Research methodology
- Focus: Case study approach
<!-- END ACADWRITE -->
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write(markdown_content)
            temp_path = Path(f.name)

        try:
            settings = Settings()
            expander = MarkerExpander(
                fileintel_client=fileintel_client, settings=settings
            )

            expanded_text, expansions = await expander.expand_file(
                file_path=temp_path, collection=test_collection
            )

            # Verify both markers expanded
            assert len(expansions) == 2
            assert all(exp.success for exp in expansions)
            assert "<!-- ACADWRITE" not in expanded_text

            # Verify content generated for both sections
            lines = expanded_text.split("\n")
            background_idx = next(
                i for i, line in enumerate(lines) if "## Background" in line
            )
            methods_idx = next(
                i for i, line in enumerate(lines) if "## Methods" in line
            )

            # There should be content between the headings
            assert methods_idx > background_idx + 5

        finally:
            temp_path.unlink()

    async def test_expand_with_citations(self, fileintel_client, test_collection):
        """Test that expanded content includes citations."""
        markdown_content = """# Paper

## Section

<!-- ACADWRITE: expand -->
- Topic: Design for manufacturing principles
<!-- END ACADWRITE -->
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write(markdown_content)
            temp_path = Path(f.name)

        try:
            settings = Settings()
            expander = MarkerExpander(
                fileintel_client=fileintel_client, settings=settings
            )

            expanded_text, expansions = await expander.expand_file(
                file_path=temp_path, collection=test_collection
            )

            # Verify citations present
            assert len(expansions) == 1
            assert expansions[0].success
            assert len(expansions[0].citations) > 0

            # Check for citation markers in text (inline format)
            assert "(" in expanded_text and ")" in expanded_text

        finally:
            temp_path.unlink()

    async def test_expand_evidence_operation(self, fileintel_client, test_collection):
        """Test evidence operation that adds supporting evidence."""
        markdown_content = """# Paper

## Analysis

<!-- ACADWRITE: evidence -->
Concurrent engineering can reduce time-to-market.
<!-- END ACADWRITE -->
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write(markdown_content)
            temp_path = Path(f.name)

        try:
            settings = Settings()
            expander = MarkerExpander(
                fileintel_client=fileintel_client, settings=settings
            )

            expanded_text, expansions = await expander.expand_file(
                file_path=temp_path, collection=test_collection
            )

            # Verify evidence added
            assert len(expansions) == 1
            assert expansions[0].success
            # Original text should be preserved
            assert "reduce time-to-market" in expanded_text
            # Evidence should be added
            assert len(expanded_text) > len(markdown_content)

        finally:
            temp_path.unlink()

    async def test_expand_with_max_words_param(
        self, fileintel_client, test_collection
    ):
        """Test that max_words parameter is respected."""
        markdown_content = """# Paper

## Section

<!-- ACADWRITE: expand max_words=100 -->
- Topic: Concurrent engineering
<!-- END ACADWRITE -->
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write(markdown_content)
            temp_path = Path(f.name)

        try:
            settings = Settings()
            expander = MarkerExpander(
                fileintel_client=fileintel_client, settings=settings
            )

            expanded_text, expansions = await expander.expand_file(
                file_path=temp_path, collection=test_collection
            )

            # Verify expansion
            assert len(expansions) == 1
            assert expansions[0].success

            # Check word count is roughly within limit
            content = expansions[0].generated_content
            word_count = len(content.split())
            # Allow some flexibility (max_words is a target, not strict limit)
            assert word_count <= 150  # 50% tolerance

        finally:
            temp_path.unlink()

    async def test_dry_run_mode(self, fileintel_client, test_collection):
        """Test dry run mode doesn't modify anything."""
        markdown_content = """# Paper

<!-- ACADWRITE: expand -->
- Topic: Test
<!-- END ACADWRITE -->
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write(markdown_content)
            temp_path = Path(f.name)

        try:
            original_content = temp_path.read_text()

            settings = Settings()
            expander = MarkerExpander(
                fileintel_client=fileintel_client, settings=settings
            )

            expanded_text, expansions = await expander.expand_file(
                file_path=temp_path, collection=test_collection, dry_run=True
            )

            # Verify expansion was processed
            assert len(expansions) == 1

            # Verify file wasn't modified
            assert temp_path.read_text() == original_content

        finally:
            temp_path.unlink()

    async def test_no_markers_in_file(self, fileintel_client, test_collection):
        """Test handling of file with no markers."""
        markdown_content = """# Paper

## Introduction

Just regular markdown with no markers.
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write(markdown_content)
            temp_path = Path(f.name)

        try:
            settings = Settings()
            expander = MarkerExpander(
                fileintel_client=fileintel_client, settings=settings
            )

            expanded_text, expansions = await expander.expand_file(
                file_path=temp_path, collection=test_collection
            )

            # Should return original text unchanged
            assert expanded_text == markdown_content
            assert len(expansions) == 0

        finally:
            temp_path.unlink()


@pytest.fixture
async def fileintel_client():
    """Create FileIntel client for testing."""
    settings = Settings()
    async with FileIntelClient(
        base_url=settings.fileintel.base_url,
        api_key=settings.fileintel.api_key,
        timeout=settings.fileintel.timeout
    ) as client:
        yield client


@pytest.fixture
def test_collection():
    """Get test collection name from settings."""
    # Use the first available collection or a default
    # In real tests, you'd configure this via environment
    return "test_collection"  # Replace with actual test collection name

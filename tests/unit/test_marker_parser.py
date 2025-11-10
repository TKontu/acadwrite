"""Unit tests for marker parser."""

import pytest

from acadwrite.models.section import MarkerOperation
from acadwrite.workflows.marker_parser import MarkerParser


class TestMarkerParser:
    """Test marker parser functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = MarkerParser()

    def test_parse_simple_expand_marker(self):
        """Test parsing a simple expand marker."""
        text = """## Introduction

<!-- ACADWRITE: expand -->
- Topic: Concurrent engineering
- Focus: Benefits
<!-- END ACADWRITE -->

More text here.
"""
        markers = self.parser.parse_markers(text)

        assert len(markers) == 1
        marker = markers[0]
        assert marker.operation == MarkerOperation.EXPAND
        assert marker.heading == "Introduction"
        assert marker.heading_level == 2
        assert "Topic: Concurrent engineering" in marker.content
        assert "Focus: Benefits" in marker.content

    def test_parse_multiple_markers(self):
        """Test parsing multiple markers in one document."""
        text = """## Section 1

<!-- ACADWRITE: expand -->
- Topic A
<!-- END ACADWRITE -->

## Section 2

<!-- ACADWRITE: evidence -->
Existing text that needs evidence
<!-- END ACADWRITE -->

## Section 3

<!-- ACADWRITE: citations -->
Text needing citations
<!-- END ACADWRITE -->
"""
        markers = self.parser.parse_markers(text)

        assert len(markers) == 3
        assert markers[0].operation == MarkerOperation.EXPAND
        assert markers[0].heading == "Section 1"
        assert markers[1].operation == MarkerOperation.EVIDENCE
        assert markers[1].heading == "Section 2"
        assert markers[2].operation == MarkerOperation.CITATIONS
        assert markers[2].heading == "Section 3"

    def test_parse_marker_with_params(self):
        """Test parsing marker with parameters."""
        text = """## Test

<!-- ACADWRITE: expand max_words=300 style=formal -->
- Content
<!-- END ACADWRITE -->
"""
        markers = self.parser.parse_markers(text)

        assert len(markers) == 1
        marker = markers[0]
        assert marker.params.get("max_words") == "300"
        assert marker.params.get("style") == "formal"

    def test_parse_marker_without_heading(self):
        """Test parsing marker without preceding heading."""
        text = """Some intro text.

<!-- ACADWRITE: expand -->
- Topic
<!-- END ACADWRITE -->
"""
        markers = self.parser.parse_markers(text)

        assert len(markers) == 1
        marker = markers[0]
        assert marker.heading is None
        assert marker.heading_level == 1

    def test_parse_nested_headings(self):
        """Test marker parsing with nested headings."""
        text = """# Chapter

## Section

### Subsection

<!-- ACADWRITE: expand -->
- Content
<!-- END ACADWRITE -->
"""
        markers = self.parser.parse_markers(text)

        assert len(markers) == 1
        marker = markers[0]
        assert marker.heading == "Subsection"
        assert marker.heading_level == 3

    def test_parse_different_operations(self):
        """Test parsing all operation types."""
        operations = ["expand", "evidence", "citations", "clarity", "contradict"]

        for op in operations:
            text = f"""## Test

<!-- ACADWRITE: {op} -->
Content
<!-- END ACADWRITE -->
"""
            markers = self.parser.parse_markers(text)
            assert len(markers) == 1
            assert markers[0].operation == MarkerOperation(op)

    def test_parse_case_insensitive(self):
        """Test that marker parsing is case-insensitive."""
        text = """## Test

<!-- acadwrite: EXPAND -->
Content
<!-- end ACADWRITE -->
"""
        markers = self.parser.parse_markers(text)
        assert len(markers) == 1
        assert markers[0].operation == MarkerOperation.EXPAND

    def test_parse_malformed_marker_missing_end(self):
        """Test handling of marker without END tag."""
        text = """## Test

<!-- ACADWRITE: expand -->
Content without end marker

## Next Section
"""
        markers = self.parser.parse_markers(text)
        # Should skip malformed marker
        assert len(markers) == 0

    def test_parse_unknown_operation_defaults_to_expand(self):
        """Test that unknown operations default to expand."""
        text = """## Test

<!-- ACADWRITE: unknown_op -->
Content
<!-- END ACADWRITE -->
"""
        markers = self.parser.parse_markers(text)
        assert len(markers) == 1
        assert markers[0].operation == MarkerOperation.EXPAND

    def test_extract_context(self):
        """Test extracting context around a marker."""
        text = """## Introduction

This is some previous content.
It has multiple lines.

More context here.

<!-- ACADWRITE: expand -->
- Topic
<!-- END ACADWRITE -->
"""
        markers = self.parser.parse_markers(text)
        context = self.parser.extract_context(text, markers[0], context_lines=5)

        assert "previous content" in context
        assert "More context here" in context

    def test_replace_marker_with_content(self):
        """Test replacing a marker with generated content."""
        text = """## Test

<!-- ACADWRITE: expand -->
- Topic
<!-- END ACADWRITE -->

More text.
"""
        markers = self.parser.parse_markers(text)
        new_content = "Generated content here."

        result = self.parser.replace_marker_with_content(text, markers[0], new_content)

        assert "Generated content here." in result
        assert "<!-- ACADWRITE: expand -->" not in result
        assert "<!-- END ACADWRITE -->" not in result
        assert "More text." in result

    def test_replace_multiple_markers(self):
        """Test replacing multiple markers in order."""
        text = """## Section 1

<!-- ACADWRITE: expand -->
- A
<!-- END ACADWRITE -->

## Section 2

<!-- ACADWRITE: expand -->
- B
<!-- END ACADWRITE -->
"""
        markers = self.parser.parse_markers(text)
        expansions = [
            (markers[0], "Content A"),
            (markers[1], "Content B"),
        ]

        result = self.parser.replace_all_markers(text, expansions)

        assert "Content A" in result
        assert "Content B" in result
        assert "<!-- ACADWRITE" not in result

    def test_multiline_marker_content(self):
        """Test marker with multiline content."""
        text = """## Test

<!-- ACADWRITE: expand -->
- First bullet
- Second bullet
- Third bullet with
  continuation line
<!-- END ACADWRITE -->
"""
        markers = self.parser.parse_markers(text)

        assert len(markers) == 1
        marker = markers[0]
        assert "First bullet" in marker.content
        assert "Second bullet" in marker.content
        assert "Third bullet" in marker.content
        assert "continuation line" in marker.content

    def test_marker_with_empty_content(self):
        """Test marker with no content between tags."""
        text = """## Test

<!-- ACADWRITE: expand -->
<!-- END ACADWRITE -->
"""
        markers = self.parser.parse_markers(text)

        assert len(markers) == 1
        marker = markers[0]
        assert marker.content == ""

    def test_line_numbers_are_correct(self):
        """Test that line numbers are tracked correctly."""
        text = """Line 0
Line 1
## Heading on line 2
Line 3
<!-- ACADWRITE: expand -->
Line 5 content
<!-- END ACADWRITE -->
Line 7
"""
        markers = self.parser.parse_markers(text)

        assert len(markers) == 1
        marker = markers[0]
        # Line numbers are 0-indexed
        assert marker.start_line == 4  # "<!-- ACADWRITE: expand -->"
        assert marker.end_line == 6    # "<!-- END ACADWRITE -->"

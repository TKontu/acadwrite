"""Parser for AcadWrite expansion markers in markdown files."""

import re
from typing import List, Optional, Tuple

from acadwrite.models.section import ExpansionMarker, MarkerOperation


class MarkerParser:
    """Parse AcadWrite expansion markers from markdown text."""

    # Regex patterns for markers
    START_PATTERN = re.compile(
        r"<!--\s*ACADWRITE:\s*(\w+)(?:\s+(.+?))?\s*-->", re.IGNORECASE
    )
    END_PATTERN = re.compile(r"<!--\s*END\s+ACADWRITE\s*-->", re.IGNORECASE)
    HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$")

    def parse_markers(self, text: str) -> List[ExpansionMarker]:
        """Parse all expansion markers from markdown text.

        Args:
            text: Markdown content

        Returns:
            List of ExpansionMarker objects

        Example:
            >>> parser = MarkerParser()
            >>> text = '''
            ... ## Introduction
            ... <!-- ACADWRITE: expand -->
            ... - Topic: AI in healthcare
            ... - Focus: diagnostics
            ... <!-- END ACADWRITE -->
            ... '''
            >>> markers = parser.parse_markers(text)
            >>> len(markers)
            1
        """
        lines = text.split("\n")
        markers: List[ExpansionMarker] = []
        current_heading: Optional[str] = None
        current_heading_level: int = 1
        i = 0

        while i < len(lines):
            line = lines[i]

            # Track current heading
            heading_match = self.HEADING_PATTERN.match(line)
            if heading_match:
                current_heading_level = len(heading_match.group(1))
                current_heading = heading_match.group(2).strip()
                i += 1
                continue

            # Look for start marker
            start_match = self.START_PATTERN.match(line.strip())
            if start_match:
                operation_str = start_match.group(1).lower()
                params_str = start_match.group(2)

                # Parse operation
                try:
                    operation = MarkerOperation(operation_str)
                except ValueError:
                    # Default to expand if operation unknown
                    operation = MarkerOperation.EXPAND

                # Parse params
                params = self._parse_params(params_str) if params_str else {}

                # Find end marker
                start_line = i
                content_lines = []
                i += 1

                while i < len(lines):
                    if self.END_PATTERN.match(lines[i].strip()):
                        end_line = i
                        # Create marker
                        marker = ExpansionMarker(
                            operation=operation,
                            start_line=start_line,
                            end_line=end_line,
                            content="\n".join(content_lines).strip(),
                            heading=current_heading,
                            heading_level=current_heading_level,
                            params=params,
                        )
                        markers.append(marker)
                        break
                    else:
                        content_lines.append(lines[i])
                        i += 1
                else:
                    # No end marker found - skip this marker
                    pass

            i += 1

        return markers

    def _parse_params(self, params_str: str) -> dict:
        """Parse parameters from marker comment.

        Args:
            params_str: Parameter string like 'max_words=500 style=formal'

        Returns:
            Dictionary of parameters
        """
        params = {}
        # Simple key=value parsing
        parts = params_str.split()
        for part in parts:
            if "=" in part:
                key, value = part.split("=", 1)
                params[key.strip()] = value.strip()
        return params

    def extract_context(
        self, text: str, marker: ExpansionMarker, context_lines: int = 5
    ) -> str:
        """Extract surrounding context for a marker.

        Args:
            text: Full markdown text
            marker: The marker to get context for
            context_lines: Number of lines before marker to include

        Returns:
            Context text (e.g., previous paragraphs)
        """
        lines = text.split("\n")
        start_idx = max(0, marker.start_line - context_lines)

        # Get lines before marker, excluding the marker itself
        context_lines_text = lines[start_idx : marker.start_line]

        # Filter out empty lines and other markers
        context = []
        for line in context_lines_text:
            if line.strip() and not self.START_PATTERN.match(
                line.strip()
            ) and not self.END_PATTERN.match(line.strip()):
                context.append(line)

        return "\n".join(context)

    def find_markers_in_file(self, file_path: str) -> Tuple[str, List[ExpansionMarker]]:
        """Parse markers from a file.

        Args:
            file_path: Path to markdown file

        Returns:
            Tuple of (file_content, list_of_markers)
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        markers = self.parse_markers(content)
        return content, markers

    def replace_marker_with_content(
        self, text: str, marker: ExpansionMarker, new_content: str
    ) -> str:
        """Replace a marker in text with expanded content.

        Args:
            text: Original markdown text
            marker: The marker to replace
            new_content: Generated content to insert

        Returns:
            Updated text with marker replaced
        """
        lines = text.split("\n")

        # Replace lines from start_line to end_line (inclusive) with new content
        before = lines[: marker.start_line]
        after = lines[marker.end_line + 1 :]

        # Insert new content (preserve indentation if needed)
        new_lines = before + [new_content] + after

        return "\n".join(new_lines)

    def replace_all_markers(
        self, text: str, expansions: List[Tuple[ExpansionMarker, str]]
    ) -> str:
        """Replace multiple markers in text.

        Args:
            text: Original markdown text
            expansions: List of (marker, expanded_content) tuples

        Returns:
            Text with all markers replaced

        Note:
            Replacements happen in reverse order (from end to start) to preserve
            line numbers during replacement.
        """
        # Sort by start_line in reverse order
        sorted_expansions = sorted(
            expansions, key=lambda x: x[0].start_line, reverse=True
        )

        result = text
        for marker, content in sorted_expansions:
            result = self.replace_marker_with_content(result, marker, content)

        return result

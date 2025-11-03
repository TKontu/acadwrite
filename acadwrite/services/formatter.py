"""Formatting service for academic content."""

import re
from typing import List, Tuple

from acadwrite.models import AcademicSection, Citation, CitationStyle


class FormatterService:
    """Service for formatting academic content and citations.

    Handles conversion between citation formats and markdown generation.
    """

    def format_section(
        self,
        section: AcademicSection,
        citation_style: CitationStyle = CitationStyle.INLINE,
    ) -> str:
        """Format an academic section as markdown.

        Args:
            section: Section to format
            citation_style: Citation style to use

        Returns:
            Markdown-formatted string
        """
        return section.to_markdown(citation_style)

    def convert_inline_to_footnotes(
        self,
        content: str,
        sources: List[Citation],
    ) -> str:
        """Convert inline citations to footnote format.

        Parses citations in the format [Author, Year, p.X] or [Author, Year]
        and converts them to [^N] footnote markers.

        Args:
            content: Content with inline citations like [Author, 2020, p.5]
            sources: List of Citation objects

        Returns:
            Content with footnote markers [^1], [^2], etc.
        """
        # Pattern to match inline citations: [Author, Year, p.X] or [Author]
        # This matches FileIntel's citation format
        citation_pattern = r"\[([^\]]+?(?:,\s*\d{4})?(?:,\s*p\.\s*\d+)?)\]"

        result = content
        footnote_map: dict[str, int] = {}
        next_number = 1

        def replace_citation(match: re.Match[str]) -> str:
            """Replace inline citation with footnote marker."""
            nonlocal next_number
            citation_text = match.group(1)

            # Check if we've seen this citation before
            if citation_text in footnote_map:
                number = footnote_map[citation_text]
            else:
                number = next_number
                footnote_map[citation_text] = number
                next_number += 1

            return f"[^{number}]"

        # Replace all inline citations with footnote markers
        result = re.sub(citation_pattern, replace_citation, result)

        return result

    def generate_footnotes(
        self,
        sources: List[Citation],
    ) -> str:
        """Generate footnote bibliography from citations.

        Args:
            sources: List of citations

        Returns:
            Formatted footnotes section
        """
        if not sources:
            return ""

        lines = ["---", ""]
        for i, citation in enumerate(sources, 1):
            lines.append(citation.to_footnote(i))

        return "\n".join(lines)

    def deduplicate_citations(
        self,
        citations: List[Citation],
    ) -> Tuple[List[Citation], dict[int, int]]:
        """Deduplicate citations and create ID mapping.

        Citations are considered duplicates if they have the same author,
        title, and page number.

        Args:
            citations: List of citations to deduplicate

        Returns:
            Tuple of (unique citations, mapping from old ID to new ID)
        """
        seen: dict[tuple[str, str, int | None], int] = {}
        unique: List[Citation] = []
        id_mapping: dict[int, int] = {}

        for citation in citations:
            key = (citation.author, citation.title, citation.page)

            if key in seen:
                # Duplicate - map old ID to existing ID
                id_mapping[citation.id] = seen[key]
            else:
                # New citation
                new_id = len(unique) + 1
                seen[key] = new_id
                id_mapping[citation.id] = new_id

                # Create new citation with updated ID
                unique.append(
                    Citation(
                        id=new_id,
                        author=citation.author,
                        title=citation.title,
                        year=citation.year,
                        page=citation.page,
                        full_citation=citation.full_citation,
                    )
                )

        return unique, id_mapping

    def renumber_citations_in_content(
        self,
        content: str,
        id_mapping: dict[int, int],
    ) -> str:
        """Renumber citation markers in content.

        Args:
            content: Content with [^N] markers
            id_mapping: Mapping from old ID to new ID

        Returns:
            Content with updated citation numbers
        """

        def replace_marker(match: re.Match[str]) -> str:
            old_id = int(match.group(1))
            new_id = id_mapping.get(old_id, old_id)
            return f"[^{new_id}]"

        # Pattern to match footnote markers [^1], [^2], etc.
        marker_pattern = r"\[\^(\d+)\]"
        return re.sub(marker_pattern, replace_marker, content)

"""Section generator workflow for academic content."""

import re
from typing import List, Optional

from acadwrite.models import AcademicSection, Citation, CitationStyle, WritingStyle
from acadwrite.models.query import QueryResponse, Source
from acadwrite.services import FileIntelClient, FormatterService


class SectionGenerator:
    """Generate academic sections with citations from FileIntel queries.

    This workflow:
    1. Queries FileIntel with the section heading
    2. Extracts citations from sources
    3. Creates formatted academic section
    4. Handles word count limits

    Example:
        async with FileIntelClient("http://localhost:8000") as client:
            formatter = FormatterService()
            generator = SectionGenerator(client, formatter)

            section = await generator.generate(
                heading="Definition of Concurrent Engineering",
                collection="thesis_sources",
                max_words=500,
            )

            print(section.to_markdown(CitationStyle.FOOTNOTE))
    """

    def __init__(
        self,
        fileintel: FileIntelClient,
        formatter: FormatterService,
    ) -> None:
        """Initialize section generator.

        Args:
            fileintel: FileIntel client for querying documents
            formatter: Formatter service for citation conversion
        """
        self.client = fileintel
        self.formatter = formatter

    async def generate(
        self,
        heading: str,
        collection: str,
        context: Optional[str] = None,
        style: WritingStyle = WritingStyle.FORMAL,
        citation_style: CitationStyle = CitationStyle.INLINE,
        max_words: Optional[int] = None,
        max_sources: Optional[int] = None,
    ) -> AcademicSection:
        """Generate an academic section with citations.

        Args:
            heading: Section heading/topic
            collection: FileIntel collection name
            context: Optional context to guide the query
            style: Writing style (currently not used, for future enhancement)
            citation_style: Citation format (INLINE or FOOTNOTE)
            max_words: Optional word count limit
            max_sources: Optional limit on number of sources

        Returns:
            AcademicSection with content and citations

        Raises:
            FileIntelError: If query fails
        """
        # Build query from heading and context
        query = self._build_query(heading, context)

        # Query FileIntel
        response = await self.client.query(
            collection=collection,
            question=query,
            rag_type="vector",
            max_sources=max_sources,
        )

        # Extract content and citations
        content = response.answer
        citations = self._extract_citations(response.sources)

        # Handle word count limits if needed
        if max_words and self._count_words(content) > max_words:
            content = self._truncate_to_word_limit(content, max_words)

        # Create section
        section = AcademicSection(
            heading=heading,
            level=2,  # Default to level 2 (##)
            content=content,
            citations=citations,
        )

        return section

    def _build_query(self, heading: str, context: Optional[str] = None) -> str:
        """Build query text from heading and optional context.

        Args:
            heading: Section heading
            context: Optional additional context

        Returns:
            Query string for FileIntel
        """
        if context:
            return f"{heading}. Context: {context}"
        return heading

    def _extract_citations(self, sources: List[Source]) -> List[Citation]:
        """Extract Citation objects from FileIntel sources.

        Args:
            sources: List of Source objects from FileIntel

        Returns:
            List of Citation objects
        """
        citations = []

        for i, source in enumerate(sources, 1):
            # Extract page number from in_text_citation if present
            page = self._extract_page_number(source.in_text_citation)

            # Get author from document metadata if available
            author = "Unknown"
            if source.document_metadata.authors:
                author = source.document_metadata.authors[0]
            elif source.document_metadata.title:
                # Use title as fallback
                author = source.document_metadata.title

            # Get year from publication date
            year = ""
            if source.document_metadata.publication_date:
                # Extract year from date string (e.g., "2020-01-01" -> "2020")
                year = source.document_metadata.publication_date[:4]

            citation = Citation(
                id=i,
                author=author,
                title=source.document_metadata.title or source.filename,
                year=year,
                page=page,
                full_citation=source.citation,
            )
            citations.append(citation)

        return citations

    def _extract_page_number(self, in_text_citation: str) -> Optional[int]:
        """Extract page number from in-text citation.

        Args:
            in_text_citation: Citation string like "(Author, 2020, p.5)"

        Returns:
            Page number if found, None otherwise
        """
        # Pattern to match p.X or p. X
        page_pattern = r"p\.\s*(\d+)"
        match = re.search(page_pattern, in_text_citation)
        if match:
            return int(match.group(1))
        return None

    def _count_words(self, text: str) -> int:
        """Count words in text.

        Args:
            text: Text to count

        Returns:
            Word count
        """
        # Simple word count - split on whitespace
        return len(text.split())

    def _truncate_to_word_limit(self, text: str, max_words: int) -> str:
        """Truncate text to word limit while preserving sentence boundaries.

        Args:
            text: Text to truncate
            max_words: Maximum word count

        Returns:
            Truncated text
        """
        words = text.split()
        if len(words) <= max_words:
            return text

        # Take first max_words words
        truncated_words = words[:max_words]
        truncated_text = " ".join(truncated_words)

        # Try to end at a sentence boundary
        # Find last period, question mark, or exclamation mark
        last_sentence = max(
            truncated_text.rfind("."),
            truncated_text.rfind("?"),
            truncated_text.rfind("!"),
        )

        if last_sentence > len(truncated_text) * 0.7:  # If we found a sentence end in last 30%
            return truncated_text[: last_sentence + 1]

        # Otherwise just add ellipsis
        return truncated_text + "..."

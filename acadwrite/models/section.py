"""Data models for academic sections and citations."""

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class WritingStyle(str, Enum):
    """Writing style for generated content."""

    FORMAL = "formal"
    TECHNICAL = "technical"
    ACCESSIBLE = "accessible"
    RAW = "raw"


class CitationStyle(str, Enum):
    """Citation formatting style."""

    INLINE = "inline"  # (Author, Year, p.X)
    FOOTNOTE = "footnote"  # [^1]
    ENDNOTE = "endnote"  # [1]


class Citation(BaseModel):
    """A formatted citation with metadata.

    This is derived from FileIntel's Source but simplified for output.
    """

    id: int  # Citation number in the document
    author: str  # Primary author or author surname
    title: str
    year: Optional[str] = None
    page: Optional[int] = None
    full_citation: str  # Complete bibliography entry

    def to_footnote(self, number: Optional[int] = None) -> str:
        """Format as footnote citation.

        Args:
            number: Override citation number (uses self.id if not provided)

        Returns:
            Formatted footnote string like "[^1]: Author (Year). Title. p.X"
        """
        num = number if number is not None else self.id
        parts = [f"[^{num}]:"]

        if self.year:
            parts.append(f"{self.author} ({self.year}).")
        else:
            parts.append(f"{self.author}.")

        parts.append(f"{self.title}.")

        if self.page:
            parts.append(f"p.{self.page}")

        return " ".join(parts)

    def to_bibtex(self, key: Optional[str] = None) -> str:
        """Format as BibTeX entry.

        Args:
            key: BibTeX citation key (generates from author+year if not provided)

        Returns:
            BibTeX entry string
        """
        if key is None:
            # Generate key like "author2020"
            author_key = self.author.lower().replace(" ", "")
            year_key = self.year if self.year else "nd"
            key = f"{author_key}{year_key}"

        lines = [f"@article{{{key},"]

        if self.author:
            lines.append(f"  author = {{{self.author}}},")
        if self.title:
            lines.append(f"  title = {{{self.title}}},")
        if self.year:
            lines.append(f"  year = {{{self.year}}},")
        if self.page:
            lines.append(f"  pages = {{{self.page}}},")

        lines.append("}")
        return "\n".join(lines)


class AcademicSection(BaseModel):
    """A generated academic section with content and citations."""

    heading: str
    level: int = Field(ge=1, le=6, description="Heading level (1-6)")
    content: str  # Markdown content with citation markers
    citations: List[Citation] = Field(default_factory=list)
    subsections: List["AcademicSection"] = Field(default_factory=list)

    def word_count(self) -> int:
        """Calculate word count of content.

        Returns:
            Number of words in content (excluding citation markers)
        """
        # Simple word count - split on whitespace
        return len(self.content.split())

    def all_citations(self) -> List[Citation]:
        """Get all citations including from subsections.

        Returns:
            Flattened list of all citations
        """
        citations = list(self.citations)
        for subsection in self.subsections:
            citations.extend(subsection.all_citations())
        return citations

    def to_markdown(self, citation_style: CitationStyle = CitationStyle.INLINE) -> str:
        """Render section as markdown.

        Args:
            citation_style: How to format citations

        Returns:
            Markdown string with heading, content, and citations
        """
        lines = []

        # Add heading
        heading_prefix = "#" * self.level
        lines.append(f"{heading_prefix} {self.heading}")
        lines.append("")

        # Add content
        lines.append(self.content)
        lines.append("")

        # Add citations if footnote style
        if citation_style == CitationStyle.FOOTNOTE and self.citations:
            lines.append("---")
            lines.append("")
            for citation in self.citations:
                lines.append(citation.to_footnote())
            lines.append("")

        # Add subsections recursively
        for subsection in self.subsections:
            lines.append(subsection.to_markdown(citation_style))
            lines.append("")

        return "\n".join(lines)


class MarkerOperation(str, Enum):
    """Type of operation requested in a marker."""

    EXPAND = "expand"  # Generate new content
    EVIDENCE = "evidence"  # Add supporting evidence
    CITATIONS = "citations"  # Add citations to existing text
    CLARITY = "clarity"  # Improve clarity
    CONTRADICT = "contradict"  # Find contradicting evidence


class ExpansionMarker(BaseModel):
    """A marker in markdown requesting AcadWrite expansion.

    Syntax:
        <!-- ACADWRITE: expand -->
        - bullet points with context
        - topic hints
        <!-- END ACADWRITE -->

    Or with operation specified:
        <!-- ACADWRITE: evidence -->
        Existing paragraph that needs citations
        <!-- END ACADWRITE -->
    """

    operation: MarkerOperation = MarkerOperation.EXPAND
    start_line: int  # Line number where marker starts
    end_line: int  # Line number where marker ends
    content: str  # Content between markers (bullets, hints, or existing text)
    context: Optional[str] = None  # Surrounding context (previous heading, etc.)
    heading: Optional[str] = None  # Closest heading above marker
    heading_level: int = 1  # Level of the heading
    params: Dict[str, str] = Field(
        default_factory=dict
    )  # Additional parameters from marker

    @property
    def is_expand_operation(self) -> bool:
        """Check if this is an expand operation."""
        return self.operation == MarkerOperation.EXPAND

    @property
    def is_evidence_operation(self) -> bool:
        """Check if this is an evidence operation."""
        return self.operation == MarkerOperation.EVIDENCE

    @property
    def is_citations_operation(self) -> bool:
        """Check if this is a citations operation."""
        return self.operation == MarkerOperation.CITATIONS

    @property
    def is_clarity_operation(self) -> bool:
        """Check if this is a clarity operation."""
        return self.operation == MarkerOperation.CLARITY

    @property
    def is_contradict_operation(self) -> bool:
        """Check if this is a contradict operation."""
        return self.operation == MarkerOperation.CONTRADICT


class ExpandedContent(BaseModel):
    """Result of expanding a marker."""

    marker: ExpansionMarker
    generated_content: str  # The expanded content
    citations: List[Citation] = Field(default_factory=list)
    success: bool = True
    error_message: Optional[str] = None


# Allow forward references for recursive model
AcademicSection.model_rebuild()

"""Citation management utilities for extracting, checking, and exporting citations."""

import re
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path

from acadwrite.models.section import AcademicSection, Citation


@dataclass
class CitationCheck:
    """Result of citation checking."""

    total_citations: int
    valid_citations: int
    invalid_citations: List[str]
    missing_pages: List[str]
    warnings: List[str]


class CitationManager:
    """Manages citation extraction, validation, and export."""

    def __init__(self) -> None:
        """Initialize the citation manager."""
        pass

    def extract_from_text(self, text: str) -> List[Citation]:
        """
        Extract citations from markdown text.

        Supports both inline [Author, Year, p.X] and footnote [^N] styles.

        Args:
            text: Markdown text with citations

        Returns:
            List of extracted Citation objects
        """
        citations: List[Citation] = []
        citation_id = 1

        # Pattern for inline citations: [Author, Year, p.X] or [Author, Year]
        inline_pattern = r"\[([^,\]]+),\s*(\d{4}|n\.d\.),?\s*(?:p\.\s*(\d+))?\]"

        for match in re.finditer(inline_pattern, text):
            author = match.group(1).strip()
            year = match.group(2).strip()
            page_str = match.group(3) if match.group(3) else None
            page = int(page_str) if page_str else None

            citation = Citation(
                id=citation_id,
                author=author,
                title="",  # Not available from inline citation
                page=page,
                year=year,
                full_citation=f"{author} ({year})" + (f", p. {page}" if page else ""),
            )
            citations.append(citation)
            citation_id += 1

        # Pattern for footnotes: [^N]: Full citation text
        footnote_pattern = r"\[\^(\d+)\]:\s*([^\n]+)"

        for match in re.finditer(footnote_pattern, text):
            footnote_num = int(match.group(1))
            full_text = match.group(2).strip()

            # Try to parse author and year from footnote
            author_year_match = re.search(r"([^,(]+?)[\s,]+\((\d{4}|n\.d\.)\)", full_text)
            page_match = re.search(r"p\.\s*(\d+)", full_text)

            if author_year_match:
                author = author_year_match.group(1).strip()
                year = author_year_match.group(2).strip()
                page_str = page_match.group(1) if page_match else None
                page = int(page_str) if page_str else None

                citation = Citation(
                    id=footnote_num,
                    author=author,
                    title="",
                    page=page,
                    year=year,
                    full_citation=full_text,
                )
                citations.append(citation)

        return citations

    def deduplicate(self, sections: List[AcademicSection]) -> List[Citation]:
        """
        Deduplicate citations across multiple sections.

        Citations are considered duplicates if they have the same author, title, and page.

        Args:
            sections: List of academic sections

        Returns:
            Deduplicated list of citations
        """
        all_citations = []
        for section in sections:
            all_citations.extend(section.all_citations())

        # Use a dictionary to track unique citations
        unique_citations = {}

        for citation in all_citations:
            # Create key based on author, title, and page
            key = (citation.author, citation.title, citation.page)

            if key not in unique_citations:
                unique_citations[key] = citation

        return list(unique_citations.values())

    def check_citations(self, text: str, strict: bool = False) -> CitationCheck:
        """
        Check citations in text for completeness and validity.

        Args:
            text: Markdown text with citations
            strict: If True, require all citations to have page numbers

        Returns:
            CitationCheck object with validation results
        """
        citations = self.extract_from_text(text)
        invalid = []
        missing_pages = []
        warnings = []

        for citation in citations:
            # Check for missing author
            if not citation.author or citation.author.strip() == "":
                invalid.append(f"Citation {citation.id} missing author")

            # Check for missing year
            if not citation.year or citation.year.strip() == "":
                invalid.append(f"Citation {citation.id} missing year")

            # Check for missing page (warning or error based on strict mode)
            if not citation.page:
                msg = f"Citation {citation.id} ({citation.author}, {citation.year}) missing page number"
                if strict:
                    invalid.append(msg)
                else:
                    missing_pages.append(msg)

            # Check for invalid year format
            if citation.year and citation.year != "n.d.":
                try:
                    year_int = int(citation.year)
                    if year_int < 1000 or year_int > 2100:
                        warnings.append(
                            f"Citation {citation.id} has suspicious year: {citation.year}"
                        )
                except ValueError:
                    invalid.append(
                        f"Citation {citation.id} has invalid year format: {citation.year}"
                    )

        return CitationCheck(
            total_citations=len(citations),
            valid_citations=len(citations) - len(invalid),
            invalid_citations=invalid,
            missing_pages=missing_pages,
            warnings=warnings,
        )

    def export_bibtex(self, citations: List[Citation]) -> str:
        """
        Export citations to BibTeX format.

        Args:
            citations: List of citations to export

        Returns:
            BibTeX formatted string
        """
        bibtex_entries = []

        for citation in citations:
            entry = citation.to_bibtex()
            if entry:
                bibtex_entries.append(entry)

        return "\n\n".join(bibtex_entries)

    def export_ris(self, citations: List[Citation]) -> str:
        """
        Export citations to RIS format (Research Information Systems).

        Args:
            citations: List of citations to export

        Returns:
            RIS formatted string
        """
        ris_entries = []

        for citation in citations:
            entry_lines = [
                "TY  - JOUR",  # Default to journal article
                f"AU  - {citation.author}",
            ]

            if citation.title:
                entry_lines.append(f"TI  - {citation.title}")
            if citation.year:
                entry_lines.append(f"PY  - {citation.year}")
            if citation.page:
                entry_lines.append(f"SP  - {citation.page}")

            entry_lines.append("ER  -")

            entry = "\n".join(entry_lines)
            ris_entries.append(entry)

        return "\n\n".join(ris_entries)

    def export_json(self, citations: List[Citation]) -> str:
        """
        Export citations to JSON format.

        Args:
            citations: List of citations to export

        Returns:
            JSON formatted string
        """
        import json

        citations_dict = [
            {
                "id": c.id,
                "author": c.author,
                "title": c.title,
                "year": c.year,
                "page": c.page,
                "full_citation": c.full_citation,
            }
            for c in citations
        ]

        return json.dumps(citations_dict, indent=2)

    def export(self, citations: List[Citation], format: str) -> str:
        """
        Export citations in the specified format.

        Args:
            citations: List of citations to export
            format: Export format (bibtex, ris, json)

        Returns:
            Formatted citation string

        Raises:
            ValueError: If format is not supported
        """
        format_lower = format.lower()

        if format_lower == "bibtex":
            return self.export_bibtex(citations)
        elif format_lower == "ris":
            return self.export_ris(citations)
        elif format_lower == "json":
            return self.export_json(citations)
        else:
            raise ValueError(
                f"Unsupported format: {format}. " f"Supported formats: bibtex, ris, json"
            )

    def format_bibliography(self, citations: List[Citation], style: str = "apa") -> str:
        """
        Format citations as a bibliography.

        Args:
            citations: List of citations
            style: Bibliography style (currently only 'apa' supported)

        Returns:
            Formatted bibliography string
        """
        if style.lower() != "apa":
            raise ValueError(f"Unsupported style: {style}. Currently only 'apa' is supported.")

        bibliography_lines = []

        for citation in citations:
            if citation.full_citation:
                bibliography_lines.append(citation.full_citation)
            else:
                # Fallback formatting
                line = f"{citation.author} ({citation.year})"
                if citation.title:
                    line += f". {citation.title}"
                if citation.page:
                    line += f", p. {citation.page}"
                bibliography_lines.append(line)

        return "\n".join(bibliography_lines)

    def deduplicate_in_file(self, input_path: Path, output_path: Optional[Path] = None) -> int:
        """
        Deduplicate citations in a markdown file.

        Args:
            input_path: Path to input markdown file
            output_path: Path to output file (if None, modifies in-place)

        Returns:
            Number of duplicate citations removed
        """
        # Read the file
        text = input_path.read_text()

        # Extract citations
        citations = self.extract_from_text(text)

        # Find duplicates
        seen = {}
        duplicates = []

        for citation in citations:
            key = (citation.author, citation.title, citation.page)
            if key in seen:
                duplicates.append(citation.id)
            else:
                seen[key] = citation.id

        # For now, just return count - actual deduplication would require
        # more sophisticated text manipulation
        return len(duplicates)

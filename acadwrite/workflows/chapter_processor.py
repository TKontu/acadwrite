"""Chapter processor workflow for multi-section generation."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from acadwrite.models import AcademicSection, Citation, CitationStyle, WritingStyle
from acadwrite.models.outline import Outline, OutlineItem
from acadwrite.services import FormatterService
from acadwrite.workflows.section_generator import SectionGenerator


@dataclass
class ChapterMetadata:
    """Metadata about a generated chapter."""

    title: str
    total_sections: int
    total_word_count: int
    total_citations: int
    unique_citations: int
    sections_list: List[str] = field(default_factory=list)


@dataclass
class Chapter:
    """Complete chapter with sections and metadata."""

    title: str
    sections: List[AcademicSection]
    citations: List[Citation]  # Deduplicated citations
    metadata: ChapterMetadata


class ChapterProcessor:
    """Process outlines into complete chapters with multiple sections.

    This workflow:
    1. Parses outline from YAML or Markdown
    2. Generates sections recursively (including subsections)
    3. Tracks context between sections for coherence
    4. Deduplicates citations across all sections
    5. Generates unified bibliography

    Example:
        async with FileIntelClient("http://localhost:8000") as client:
            formatter = FormatterService()
            section_gen = SectionGenerator(client, formatter)
            processor = ChapterProcessor(section_gen, formatter)

            outline = Outline.from_yaml(Path("outline.yaml"))
            chapter = await processor.process(
                outline=outline,
                collection="thesis_sources",
            )

            print(f"Generated {len(chapter.sections)} sections")
            print(f"Total citations: {len(chapter.citations)}")
    """

    def __init__(
        self,
        section_generator: SectionGenerator,
        formatter: FormatterService,
    ) -> None:
        """Initialize chapter processor.

        Args:
            section_generator: SectionGenerator for creating sections
            formatter: FormatterService for citation handling
        """
        self.section_generator = section_generator
        self.formatter = formatter

    async def process(
        self,
        outline: Outline,
        collection: str,
        style: WritingStyle = WritingStyle.FORMAL,
        citation_style: CitationStyle = CitationStyle.INLINE,
        max_words_per_section: Optional[int] = None,
        continue_on_error: bool = True,
    ) -> Chapter:
        """Process outline into complete chapter.

        Args:
            outline: Outline to process
            collection: FileIntel collection name
            style: Writing style
            citation_style: Citation format
            max_words_per_section: Optional word limit per section
            continue_on_error: Whether to continue if section generation fails

        Returns:
            Chapter with all sections and deduplicated citations

        Raises:
            FileIntelError: If queries fail and continue_on_error=False
        """
        sections: List[AcademicSection] = []
        context = ""  # Running context from previous sections

        # Process each top-level outline item
        for item in outline.items:
            section_results = await self._process_item(
                item=item,
                collection=collection,
                context=context,
                style=style,
                citation_style=citation_style,
                max_words_per_section=max_words_per_section,
                continue_on_error=continue_on_error,
            )
            sections.extend(section_results)

            # Update context with last generated section's heading
            if section_results:
                last_section = section_results[-1]
                context = f"Previous section: {last_section.heading}"

        # Deduplicate citations across all sections
        all_citations = []
        for section in sections:
            all_citations.extend(section.all_citations())

        unique_citations, id_mapping = self.formatter.deduplicate_citations(all_citations)

        # Renumber citation markers in all sections
        for section in sections:
            section.content = self.formatter.renumber_citations_in_content(
                section.content, id_mapping
            )
            # Update citation IDs in section's citation list
            section.citations = [
                cit for cit in unique_citations if cit.id in [c.id for c in section.citations]
            ]

        # Calculate metadata
        metadata = self._calculate_metadata(
            title=outline.title,
            sections=sections,
            unique_citations=unique_citations,
        )

        return Chapter(
            title=outline.title,
            sections=sections,
            citations=unique_citations,
            metadata=metadata,
        )

    async def _process_item(
        self,
        item: OutlineItem,
        collection: str,
        context: str,
        style: WritingStyle,
        citation_style: CitationStyle,
        max_words_per_section: Optional[int],
        continue_on_error: bool,
    ) -> List[AcademicSection]:
        """Process a single outline item recursively.

        Args:
            item: OutlineItem to process
            collection: FileIntel collection
            context: Context from previous sections
            style: Writing style
            citation_style: Citation format
            max_words_per_section: Optional word limit
            continue_on_error: Whether to continue on errors

        Returns:
            List of generated sections (may include subsections)
        """
        sections = []

        # Generate this section
        try:
            section = await self.section_generator.generate(
                heading=item.heading,
                collection=collection,
                context=context if context else None,
                style=style,
                citation_style=citation_style,
                max_words=max_words_per_section,
            )
            section.level = item.level
            sections.append(section)

            # Update context for subsections
            section_context = f"Parent section: {item.heading}"

            # Process subsections recursively
            if item.children:
                for child in item.children:
                    child_sections = await self._process_item(
                        item=child,
                        collection=collection,
                        context=section_context,
                        style=style,
                        citation_style=citation_style,
                        max_words_per_section=max_words_per_section,
                        continue_on_error=continue_on_error,
                    )
                    # Add subsections to parent but don't add them to sections list
                    # (they're already in child_sections which gets added to sections)
                    sections.extend(child_sections)

        except Exception as e:
            if not continue_on_error:
                raise
            # Create placeholder section on error
            section = AcademicSection(
                heading=item.heading,
                level=item.level,
                content=f"Error generating section: {e}",
                citations=[],
            )
            sections.append(section)

        return sections

    def _calculate_metadata(
        self,
        title: str,
        sections: List[AcademicSection],
        unique_citations: List[Citation],
    ) -> ChapterMetadata:
        """Calculate chapter metadata.

        Args:
            title: Chapter title
            sections: All sections
            unique_citations: Deduplicated citations

        Returns:
            ChapterMetadata
        """
        total_words = sum(section.word_count() for section in sections)
        section_headings = [section.heading for section in sections]

        # Count total citations (including duplicates)
        total_citations = sum(len(section.all_citations()) for section in sections)

        return ChapterMetadata(
            title=title,
            total_sections=len(sections),
            total_word_count=total_words,
            total_citations=total_citations,
            unique_citations=len(unique_citations),
            sections_list=section_headings,
        )

    def save_chapter(
        self,
        chapter: Chapter,
        output_dir: Path,
        citation_style: CitationStyle = CitationStyle.INLINE,
        single_file: bool = False,
    ) -> Dict[str, Path]:
        """Save chapter to files.

        Args:
            chapter: Chapter to save
            output_dir: Output directory
            citation_style: Citation format
            single_file: Whether to combine all sections into one file

        Returns:
            Dictionary mapping file type to saved path
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        saved_files = {}

        if single_file:
            # Save all sections to one file
            chapter_path = output_dir / f"{self._sanitize_filename(chapter.title)}.md"
            content_parts = [f"# {chapter.title}\n"]

            for section in chapter.sections:
                content_parts.append(section.to_markdown(citation_style))
                content_parts.append("\n")

            # Add bibliography
            if chapter.citations:
                content_parts.append("---\n\n")
                content_parts.append("## References\n\n")
                footnotes = self.formatter.generate_footnotes(chapter.citations)
                content_parts.append(footnotes)

            chapter_path.write_text("\n".join(content_parts))
            saved_files["chapter"] = chapter_path

        else:
            # Save each section to individual file
            for i, section in enumerate(chapter.sections, 1):
                section_filename = f"{i:02d}_{self._sanitize_filename(section.heading)}.md"
                section_path = output_dir / section_filename

                content = section.to_markdown(citation_style)
                section_path.write_text(content)

                saved_files[f"section_{i}"] = section_path

        # Save bibliography
        bib_path = output_dir / "bibliography.bib"
        bib_content = self._generate_bibtex(chapter.citations)
        bib_path.write_text(bib_content)
        saved_files["bibliography"] = bib_path

        # Save metadata
        metadata_path = output_dir / "metadata.json"
        metadata_dict = {
            "title": chapter.metadata.title,
            "total_sections": chapter.metadata.total_sections,
            "total_word_count": chapter.metadata.total_word_count,
            "total_citations": chapter.metadata.total_citations,
            "unique_citations": chapter.metadata.unique_citations,
            "sections": chapter.metadata.sections_list,
        }
        metadata_path.write_text(json.dumps(metadata_dict, indent=2))
        saved_files["metadata"] = metadata_path

        return saved_files

    def _sanitize_filename(self, text: str) -> str:
        """Sanitize text for use in filename.

        Args:
            text: Text to sanitize

        Returns:
            Sanitized filename
        """
        # Remove or replace problematic characters
        sanitized = text.lower()
        # Replace spaces with underscores
        sanitized = sanitized.replace(" ", "_")
        # Keep only alphanumeric and underscores
        sanitized = "".join(c if c.isalnum() or c == "_" else "_" for c in sanitized)
        # Remove consecutive underscores
        while "__" in sanitized:
            sanitized = sanitized.replace("__", "_")
        # Remove leading/trailing underscores
        sanitized = sanitized.strip("_")
        return sanitized[:50]  # Limit length

    def _generate_bibtex(self, citations: List[Citation]) -> str:
        """Generate BibTeX bibliography.

        Args:
            citations: List of citations

        Returns:
            BibTeX formatted string
        """
        if not citations:
            return ""

        bib_entries = []
        for citation in citations:
            bib_entries.append(citation.to_bibtex())

        return "\n\n".join(bib_entries)

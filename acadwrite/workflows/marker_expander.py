"""Expander for AcadWrite markers in markdown files."""

import asyncio
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from acadwrite.config import Settings
from acadwrite.models.section import (
    Citation,
    ExpandedContent,
    ExpansionMarker,
    MarkerOperation,
)
from acadwrite.services.fileintel import FileIntelClient
from acadwrite.services.formatter import FormatterService
from acadwrite.services.llm import LLMClient
from acadwrite.workflows.counterargument import CounterargumentGenerator
from acadwrite.workflows.marker_parser import MarkerParser
from acadwrite.workflows.section_generator import SectionGenerator


class MarkerExpander:
    """Expand AcadWrite markers in markdown files."""

    def __init__(
        self,
        fileintel_client: FileIntelClient,
        llm_client: Optional[LLMClient] = None,
        settings: Optional[Settings] = None,
        console: Optional[Console] = None,
    ):
        """Initialize marker expander.

        Args:
            fileintel_client: FileIntel client for querying
            llm_client: LLM client (optional, for clarity operations)
            settings: Application settings
            console: Rich console for output
        """
        self.fileintel = fileintel_client
        self.llm = llm_client
        self.settings = settings or Settings()
        self.console = console or Console()
        self.parser = MarkerParser()
        self.formatter = FormatterService()
        self.section_generator = SectionGenerator(fileintel_client, self.formatter)

    async def expand_file(
        self,
        file_path: Path,
        collection: str,
        dry_run: bool = False,
        default_search_type: Optional[str] = None,
        default_answer_format: Optional[str] = None,
    ) -> tuple[str, List[ExpandedContent]]:
        """Expand all markers in a markdown file.

        Args:
            file_path: Path to markdown file
            collection: FileIntel collection to query
            dry_run: If True, don't modify file, just return what would be done
            default_search_type: Default search type for markers without explicit type
            default_answer_format: Default answer format for markers without explicit format

        Returns:
            Tuple of (expanded_text, list_of_expansions)
        """
        # Parse file
        original_text, markers = self.parser.find_markers_in_file(str(file_path))

        if not markers:
            self.console.print(f"[yellow]No markers found in {file_path}[/yellow]")
            return original_text, []

        # Apply default parameters to markers that don't have them
        if default_search_type or default_answer_format:
            for marker in markers:
                if default_search_type and 'type' not in marker.params and 'search_type' not in marker.params:
                    marker.params['type'] = default_search_type
                if default_answer_format and 'format' not in marker.params and 'answer_format' not in marker.params:
                    marker.params['format'] = default_answer_format

        self.console.print(
            f"[cyan]Found {len(markers)} marker(s) in {file_path}[/cyan]"
        )

        # Expand each marker
        expansions: List[ExpandedContent] = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            for i, marker in enumerate(markers, 1):
                task = progress.add_task(
                    f"Expanding marker {i}/{len(markers)} ({marker.operation.value})...",
                    total=None,
                )

                try:
                    expanded = await self.expand_marker(marker, collection, original_text)
                    expansions.append(expanded)
                    progress.update(
                        task,
                        description=f"✓ Expanded marker {i}/{len(markers)}",
                        completed=True,
                    )
                except Exception as e:
                    self.console.print(
                        f"[red]Error expanding marker {i}: {str(e)}[/red]"
                    )
                    expansions.append(
                        ExpandedContent(
                            marker=marker,
                            generated_content="",
                            success=False,
                            error_message=str(e),
                        )
                    )

        # Replace markers with expanded content
        replacements = [
            (exp.marker, exp.generated_content)
            for exp in expansions
            if exp.success
        ]

        if replacements:
            expanded_text = self.parser.replace_all_markers(original_text, replacements)
        else:
            expanded_text = original_text

        return expanded_text, expansions

    async def expand_marker(
        self, marker: ExpansionMarker, collection: str, full_text: str
    ) -> ExpandedContent:
        """Expand a single marker.

        Args:
            marker: The marker to expand
            collection: FileIntel collection to query
            full_text: Full document text for context

        Returns:
            ExpandedContent with generated content and citations
        """
        # Get surrounding context
        context = self.parser.extract_context(full_text, marker, context_lines=10)

        # Dispatch based on operation
        if marker.is_expand_operation:
            return await self._expand_generate(marker, collection, context)
        elif marker.is_evidence_operation:
            return await self._expand_evidence(marker, collection, context)
        elif marker.is_citations_operation:
            return await self._expand_citations(marker, collection)
        elif marker.is_clarity_operation:
            return await self._expand_clarity(marker)
        elif marker.is_contradict_operation:
            return await self._expand_contradict(marker, collection)
        else:
            raise ValueError(f"Unknown operation: {marker.operation}")

    async def _expand_generate(
        self, marker: ExpansionMarker, collection: str, context: str
    ) -> ExpandedContent:
        """Expand a generate/expand marker.

        Creates new content based on bullet points or hints.
        """
        # Build query from marker content
        query = self._build_query_from_marker(marker)

        # Get max words from params or settings
        max_words = int(
            marker.params.get(
                "max_words", self.settings.writing.max_words_per_section
            )
        )

        # Generate section
        section = await self.section_generator.generate(
            heading=marker.heading or "Content",
            collection=collection,
            context=context,
            max_words=max_words,
        )

        # Format as markdown (without heading since it's inline)
        content = section.content

        # Convert citations
        citations = self._convert_section_citations(section)

        return ExpandedContent(
            marker=marker, generated_content=content, citations=citations, success=True
        )

    async def _expand_evidence(
        self, marker: ExpansionMarker, collection: str, context: str
    ) -> ExpandedContent:
        """Expand an evidence marker.

        Adds supporting evidence to existing text.

        Supports marker parameters:
        - type: Search type (vector, graph, adaptive, global, local)
        - format: Answer format (default, table, list, json, essay, markdown)
        """
        # Query FileIntel for evidence
        query_text = marker.content[:200]  # Use first 200 chars as query

        # Extract parameters from marker
        search_type = marker.params.get('type', marker.params.get('search_type', 'adaptive'))
        answer_format = marker.params.get('format', marker.params.get('answer_format', 'default'))

        response = await self.fileintel.query(
            collection=collection,
            question=query_text,
            search_type=search_type,
            answer_format=answer_format
        )

        # Validate response
        if not response.answer or not response.answer.strip():
            return ExpandedContent(
                marker=marker,
                generated_content=marker.content,
                success=False,
                error_message="FileIntel returned empty response - no evidence found",
            )

        # Format evidence as additional paragraph
        evidence_text = f"\n\n{response.answer}\n"

        # Extract citations
        citations = [
            Citation(
                id=i + 1,
                author=source.document_metadata.author_surnames[0]
                if source.document_metadata.author_surnames
                else "Unknown",
                title=source.document_metadata.title,
                year=source.document_metadata.publication_date,
                page=source.chunk_metadata.page_number,
                full_citation=source.citation,
            )
            for i, source in enumerate(response.sources[:5])
        ]

        return ExpandedContent(
            marker=marker,
            generated_content=marker.content + evidence_text,
            citations=citations,
            success=True,
        )

    async def _expand_citations(
        self, marker: ExpansionMarker, collection: str
    ) -> ExpandedContent:
        """Expand a citations marker.

        Adds inline citations to existing text.

        Supports marker parameters:
        - type: Search type (vector, graph, adaptive, global, local)
        - format: Answer format (default, table, list, json, essay, markdown)
        """
        # Query FileIntel with the text
        query_text = marker.content

        # Extract parameters from marker
        search_type = marker.params.get('type', marker.params.get('search_type', 'adaptive'))
        answer_format = marker.params.get('format', marker.params.get('answer_format', 'default'))

        response = await self.fileintel.query(
            collection=collection,
            question=query_text,
            search_type=search_type,
            answer_format=answer_format
        )

        # Validate response
        if not response.answer or not response.answer.strip():
            return ExpandedContent(
                marker=marker,
                generated_content=marker.content,
                success=False,
                error_message="FileIntel returned empty response - no citations found",
            )

        # Use FileIntel's answer which already has citations
        # Or keep original and add citation markers
        content_with_citations = response.answer

        # Extract citations
        citations = [
            Citation(
                id=i + 1,
                author=source.document_metadata.author_surnames[0]
                if source.document_metadata.author_surnames
                else "Unknown",
                title=source.document_metadata.title,
                year=source.document_metadata.publication_date,
                page=source.chunk_metadata.page_number,
                full_citation=source.citation,
            )
            for i, source in enumerate(response.sources[:3])
        ]

        return ExpandedContent(
            marker=marker,
            generated_content=content_with_citations,
            citations=citations,
            success=True,
        )

    async def _expand_clarity(self, marker: ExpansionMarker) -> ExpandedContent:
        """Expand a clarity marker.

        Uses LLM to improve text clarity.
        """
        if not self.llm:
            return ExpandedContent(
                marker=marker,
                generated_content=marker.content,
                success=False,
                error_message="LLM client required for clarity operation",
            )

        # Use LLM to improve clarity
        prompt = f"""Improve the clarity of the following academic text while maintaining its meaning and citations:

{marker.content}

Return only the improved text, preserving all citations exactly as they appear."""

        improved_text = await self.llm.generate(prompt, max_tokens=2000)

        return ExpandedContent(
            marker=marker, generated_content=improved_text, success=True
        )

    async def _expand_contradict(
        self, marker: ExpansionMarker, collection: str
    ) -> ExpandedContent:
        """Expand a contradict marker.

        Finds contradicting evidence.
        """
        if not self.llm:
            return ExpandedContent(
                marker=marker,
                generated_content=marker.content,
                success=False,
                error_message="LLM client required for contradict operation",
            )

        # Use counterargument generator
        from acadwrite.workflows.counterargument import AnalysisDepth
        generator = CounterargumentGenerator(self.fileintel, self.llm)
        report = await generator.generate(
            claim=marker.content,
            collection=collection,
            depth=AnalysisDepth.STANDARD,
            include_synthesis=True,
        )

        # Format as markdown section using the report
        content_parts = [marker.content, "", "**Contradicting Evidence:**", ""]

        for i, evidence in enumerate(report.contradicting_evidence[:3], 1):
            content_parts.append(f"{i}. {evidence.snippet}")
            content_parts.append(f"   - {evidence.citation}")
            content_parts.append("")

        if report.synthesis:
            content_parts.append("**Analysis:**")
            content_parts.append(report.synthesis)

        content = "\n".join(content_parts)

        # Extract citations from contradicting evidence
        citations = []
        for i, ev in enumerate(report.contradicting_evidence[:3], 1):
            # Create citation from evidence (using property methods)
            author = "Unknown"
            if ev.source.document_metadata.author_surnames:
                author = ev.source.document_metadata.author_surnames[0]

            citations.append(
                Citation(
                    id=i,
                    author=author,
                    title=ev.title,
                    year=ev.year,
                    page=ev.page,
                    full_citation=ev.citation,
                )
            )

        return ExpandedContent(
            marker=marker, generated_content=content, citations=citations, success=True
        )

    def _build_query_from_marker(self, marker: ExpansionMarker) -> str:
        """Build a query string from marker content.

        Args:
            marker: Expansion marker

        Returns:
            Query string for FileIntel
        """
        # If content has bullet points, extract key topics
        lines = marker.content.split("\n")
        topics = []

        for line in lines:
            line = line.strip()
            if line.startswith("-") or line.startswith("*"):
                # Extract bullet content
                topic = line.lstrip("-*").strip()
                topics.append(topic)

        if topics:
            # Combine with heading
            if marker.heading:
                return f"{marker.heading}: {', '.join(topics)}"
            return ", ".join(topics)

        # Otherwise use content as-is (up to 200 chars)
        return marker.content[:200]

    def _convert_section_citations(self, section) -> List[Citation]:
        """Convert section citations to Citation models.

        Args:
            section: AcademicSection with citations

        Returns:
            List of Citation objects
        """
        # Section already has citations as Citation objects
        return section.citations

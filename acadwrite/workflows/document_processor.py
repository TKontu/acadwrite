"""
Document Processor - Process existing markdown files with smart operations.

Supports operations like:
- find_citations: Add missing citations to text
- add_evidence: Add supporting evidence from sources
- improve_clarity: Simplify complex text
- find_contradictions: Find contradicting evidence
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from acadwrite.models.query import QueryResponse, Source
from acadwrite.models.section import Citation
from acadwrite.services.fileintel import FileIntelClient
from acadwrite.services.llm import LLMClient
from acadwrite.workflows.markdown_chunker import Chunk, ChunkType, MarkdownChunker


@dataclass
class ProcessedChunk:
    """Result of processing a chunk."""

    original: Chunk
    processed_text: str
    operation: str
    citations_added: List[dict] = field(default_factory=list)
    evidence_added: List[Source] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)
    contradictions: List[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class ProcessedDocument:
    """Result of processing entire document."""

    original_text: str
    processed_text: str
    operation: str
    chunks_processed: int
    citations_added: int = 0
    evidence_added: int = 0
    improvements: int = 0
    contradictions_found: int = 0
    metadata: dict = field(default_factory=dict)


class DocumentProcessor:
    """
    Process markdown documents with smart chunking and operations.

    Uses MarkdownChunker to split documents into semantic chunks,
    then applies operations like citation finding, evidence addition, etc.
    """

    def __init__(
        self,
        fileintel_client: Optional[FileIntelClient] = None,
        llm_client: Optional[LLMClient] = None,
        chunker: Optional[MarkdownChunker] = None,
    ):
        """
        Initialize processor.

        Args:
            fileintel_client: FileIntel client for RAG queries
            llm_client: LLM client for text generation
            chunker: Markdown chunker (creates default if not provided)
        """
        self.fileintel = fileintel_client
        self.llm = llm_client
        self.chunker = chunker or MarkdownChunker(target_tokens=300, max_tokens=500)

    async def process_document(
        self,
        markdown_path: Path,
        operation: str,
        collection: str,
        **kwargs,
    ) -> ProcessedDocument:
        """
        Process entire document with operation.

        Args:
            markdown_path: Path to markdown file
            operation: Operation name (find_citations, add_evidence, etc.)
            collection: FileIntel collection
            **kwargs: Operation-specific parameters

        Returns:
            ProcessedDocument with results
        """
        # Read document
        markdown_text = markdown_path.read_text(encoding="utf-8")

        # Chunk document
        chunks = self.chunker.chunk_markdown(markdown_text)

        # Process each chunk
        processed_chunks = []
        for chunk in chunks:
            # Skip non-content chunks
            if chunk.type == ChunkType.HEADING:
                processed_chunks.append(
                    ProcessedChunk(original=chunk, processed_text=chunk.text, operation=operation)
                )
                continue

            result = await self._process_chunk(chunk, operation, collection, **kwargs)
            processed_chunks.append(result)

        # Reassemble document
        processed_doc = self._reassemble_document(markdown_text, processed_chunks, operation)

        return processed_doc

    async def _process_chunk(
        self,
        chunk: Chunk,
        operation: str,
        collection: str,
        **kwargs,
    ) -> ProcessedChunk:
        """Process single chunk with operation."""
        if operation == "find_citations":
            return await self._find_citations(chunk, collection)
        elif operation == "add_evidence":
            return await self._add_evidence(chunk, collection)
        elif operation == "improve_clarity":
            return await self._improve_clarity(chunk)
        elif operation == "find_contradictions":
            return await self._find_contradictions(chunk, collection)
        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def _find_citations(self, chunk: Chunk, collection: str) -> ProcessedChunk:
        """
        Find missing citations in chunk.

        Strategy:
        1. Identify factual claims in chunk
        2. Query FileIntel for each claim
        3. Insert citations where needed
        4. Preserve existing citations
        """
        if not self.fileintel:
            raise ValueError("FileIntel client required for find_citations operation")

        # Extract claims that need citations
        claims = self._extract_claims(chunk.text)

        processed_text = chunk.text
        citations_added = []

        for claim in claims:
            # Check if claim already has citation
            if self._has_citation(claim, chunk.text):
                continue

            # Query FileIntel for supporting evidence
            question = f"{chunk.context}: {claim}" if chunk.context else claim

            try:
                response = await self.fileintel.query(
                    collection=collection, question=question, max_results=2
                )

                if response.sources:
                    # Add citation to claim
                    best_source = response.sources[0]
                    citation = self._format_inline_citation(best_source)

                    # Insert citation after claim (first occurrence only)
                    processed_text = processed_text.replace(
                        claim, claim + f" {citation}", 1  # Only first occurrence
                    )

                    # Extract author and date from document metadata (with null checks)
                    authors = (
                        best_source.document_metadata.authors
                        if best_source.document_metadata.authors
                        else []
                    )
                    author = authors[0] if authors else "Unknown"
                    year = (
                        best_source.document_metadata.publication_date
                        if best_source.document_metadata.publication_date
                        else "n.d."
                    )
                    page = (
                        best_source.chunk_metadata.page_number
                        if best_source.chunk_metadata.page_number
                        else None
                    )

                    citations_added.append(
                        {
                            "claim": claim,
                            "citation": citation,
                            "source": {
                                "author": author,
                                "year": year,
                                "page": page,
                            },
                        }
                    )
            except Exception as e:
                # Continue processing even if one query fails
                print(f"Warning: Failed to query for claim '{claim[:50]}...': {e}")
                continue

        return ProcessedChunk(
            original=chunk,
            processed_text=processed_text,
            citations_added=citations_added,
            operation="find_citations",
        )

    async def _add_evidence(self, chunk: Chunk, collection: str) -> ProcessedChunk:
        """
        Add supporting evidence to arguments.

        Strategy:
        1. Identify main arguments in chunk
        2. Query FileIntel for supporting evidence
        3. Insert evidence paragraphs
        """
        if not self.fileintel:
            raise ValueError("FileIntel client required for add_evidence operation")

        # Identify topic sentence (usually first sentence)
        sentences = self.chunker._split_into_sentences(chunk.text)
        if not sentences:
            return ProcessedChunk(
                original=chunk, processed_text=chunk.text, operation="add_evidence"
            )

        topic = sentences[0]

        # Query for supporting evidence
        question = f"Evidence supporting: {topic}"

        try:
            response = await self.fileintel.query(
                collection=collection, question=question, max_results=3
            )

            if not response.sources:
                return ProcessedChunk(
                    original=chunk, processed_text=chunk.text, operation="add_evidence"
                )

            # Build evidence paragraph
            evidence_lines = ["\n\nSupporting evidence:"]

            for i, source in enumerate(response.sources[:3], 1):
                # Extract key point from source
                key_point = source.text[:200] + "..." if len(source.text) > 200 else source.text
                citation = self._format_inline_citation(source)

                evidence_lines.append(f"{i}. {citation}: {key_point}")

            evidence_text = "\n".join(evidence_lines)

            # Insert evidence after chunk
            processed_text = chunk.text + evidence_text

            return ProcessedChunk(
                original=chunk,
                processed_text=processed_text,
                evidence_added=response.sources,
                operation="add_evidence",
            )

        except Exception as e:
            print(f"Warning: Failed to add evidence: {e}")
            return ProcessedChunk(
                original=chunk, processed_text=chunk.text, operation="add_evidence"
            )

    async def _improve_clarity(self, chunk: Chunk) -> ProcessedChunk:
        """
        Improve clarity of complex text.

        Strategy:
        1. Identify complex sentences
        2. Use LLM to suggest simplifications
        3. Return suggestions
        """
        if not self.llm:
            raise ValueError("LLM client required for improve_clarity operation")

        # Check if chunk is complex
        sentences = self.chunker._split_into_sentences(chunk.text)
        avg_sentence_length = len(chunk.text.split()) / max(1, len(sentences)) if sentences else 0

        if avg_sentence_length < 25:  # Not complex enough
            return ProcessedChunk(
                original=chunk, processed_text=chunk.text, operation="improve_clarity"
            )

        # Use LLM to clarify
        prompt = f"""Improve the clarity of this academic text while maintaining accuracy:

{chunk.text}

Provide a clearer version that:
- Uses simpler sentence structures
- Defines technical terms
- Maintains all factual content

Return only the improved text without explanations."""

        try:
            clarified = await self.llm.generate(prompt)

            return ProcessedChunk(
                original=chunk,
                processed_text=clarified,
                improvements=["clarity"],
                operation="improve_clarity",
            )

        except Exception as e:
            print(f"Warning: Failed to improve clarity: {e}")
            return ProcessedChunk(
                original=chunk, processed_text=chunk.text, operation="improve_clarity"
            )

    async def _find_contradictions(self, chunk: Chunk, collection: str) -> ProcessedChunk:
        """
        Find contradicting evidence.

        Strategy:
        1. Extract claims from chunk
        2. Invert each claim
        3. Query for contradicting evidence
        4. Report contradictions
        """
        if not self.fileintel:
            raise ValueError("FileIntel client required for find_contradictions operation")
        if not self.llm:
            raise ValueError("LLM client required for find_contradictions operation")

        claims = self._extract_claims(chunk.text)
        contradictions = []

        for claim in claims:
            # Invert claim using LLM
            try:
                inverted = await self.llm.invert_claim(claim)

                # Query for evidence supporting inverted claim
                response = await self.fileintel.query(
                    collection=collection, question=inverted, max_results=2
                )

                if response.sources:
                    contradictions.append(
                        {
                            "original_claim": claim,
                            "inverted_claim": inverted,
                            "contradicting_sources": [
                                {
                                    "author": (
                                        s.document_metadata.authors[0]
                                        if (
                                            s.document_metadata.authors
                                            and len(s.document_metadata.authors) > 0
                                        )
                                        else "Unknown"
                                    ),
                                    "year": (
                                        s.document_metadata.publication_date
                                        if s.document_metadata.publication_date
                                        else "n.d."
                                    ),
                                    "text": s.text[:200] + "..." if len(s.text) > 200 else s.text,
                                }
                                for s in response.sources
                            ],
                        }
                    )
            except Exception as e:
                print(f"Warning: Failed to check contradiction for claim '{claim[:50]}...': {e}")
                continue

        return ProcessedChunk(
            original=chunk,
            processed_text=chunk.text,  # No modification, just report
            contradictions=contradictions,
            operation="find_contradictions",
        )

    def _extract_claims(self, text: str) -> List[str]:
        """
        Extract factual claims that need citations.

        Simple heuristic:
        - Sentences with statistics/numbers
        - Definitive statements ("is", "are", "has been shown")
        - Comparative statements ("better", "faster", "more effective")
        """
        claims = []
        sentences = self.chunker._split_into_sentences(text)

        for sentence in sentences:
            # Check for patterns that indicate factual claims
            if any(
                [
                    re.search(r"\d+%", sentence),  # Percentages
                    re.search(r"\d+\.\d+", sentence),  # Decimals/stats
                    "research shows" in sentence.lower(),
                    "studies indicate" in sentence.lower(),
                    "has been shown" in sentence.lower(),
                    "is known" in sentence.lower(),
                    re.search(r"\b(better|faster|more|less)\s+\w+\s+than\b", sentence, re.I),
                ]
            ):
                claims.append(sentence)

        return claims

    def _has_citation(self, claim: str, text: str) -> bool:
        """Check if a claim already has a citation."""
        # Look for citation patterns near the claim
        # Inline: [Author, Year, p.X]
        # Footnote: [^N]

        # Find claim position
        claim_pos = text.find(claim)
        if claim_pos == -1:
            return False

        # Check ~50 characters after claim for citation
        search_window = text[claim_pos : claim_pos + len(claim) + 50]

        inline_pattern = r"\[([^,\]]+),\s*(\d{4}|n\.d\.)"
        footnote_pattern = r"\[\^\d+\]"

        return bool(
            re.search(inline_pattern, search_window) or re.search(footnote_pattern, search_window)
        )

    def _format_inline_citation(self, source: Source) -> str:
        """Format a source as an inline citation."""
        # Extract author from document metadata (with null checks)
        authors = source.document_metadata.authors if source.document_metadata.authors else []
        author = authors[0] if authors else "Unknown"

        # Extract date from document metadata
        year = (
            source.document_metadata.publication_date
            if source.document_metadata.publication_date
            else "n.d."
        )

        # Extract page from chunk metadata (with null check)
        page_num = source.chunk_metadata.page_number if source.chunk_metadata.page_number else None
        page = f", p. {page_num}" if page_num else ""

        return f"[{author}, {year}{page}]"

    def _reassemble_document(
        self, original_text: str, processed_chunks: List[ProcessedChunk], operation: str
    ) -> ProcessedDocument:
        """
        Reassemble processed chunks into final document.

        For now, simple concatenation. Future: preserve exact formatting.
        """
        # Collect processed text
        processed_parts = []
        total_citations = 0
        total_evidence = 0
        total_improvements = 0
        total_contradictions = 0

        for chunk in processed_chunks:
            processed_parts.append(chunk.processed_text)
            total_citations += len(chunk.citations_added)
            total_evidence += len(chunk.evidence_added)
            total_improvements += len(chunk.improvements)
            total_contradictions += len(chunk.contradictions)

        # Join with double newlines between chunks
        processed_text = "\n\n".join(processed_parts)

        return ProcessedDocument(
            original_text=original_text,
            processed_text=processed_text,
            operation=operation,
            chunks_processed=len(processed_chunks),
            citations_added=total_citations,
            evidence_added=total_evidence,
            improvements=total_improvements,
            contradictions_found=total_contradictions,
        )

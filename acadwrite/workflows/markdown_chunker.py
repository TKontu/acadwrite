"""
Markdown Chunker - Smart chunking for markdown documents.

Adapts FileIntel's sentence-based chunking algorithm to preserve markdown structure
while splitting documents into processable chunks for operations like citation
finding, evidence addition, and clarity improvement.
"""

import re
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class ChunkType(str, Enum):
    """Types of markdown chunks."""

    PARAGRAPH = "paragraph"
    HEADING = "heading"
    LIST = "list"
    CODE = "code"
    QUOTE = "quote"


@dataclass
class Chunk:
    """A semantic chunk of markdown content."""

    heading: str  # Current section heading
    text: str  # Chunk text content
    type: ChunkType  # Type of chunk
    context: str  # Full context (heading hierarchy)
    start_pos: int  # Start position in original text
    end_pos: int  # End position in original text
    level: int = 0  # Heading level (0 for non-heading chunks)


class MarkdownChunker:
    """
    Smart chunking for markdown documents.

    Preserves markdown structure while creating semantic chunks suitable for
    processing with LLMs and RAG systems.

    Based on FileIntel's TextChunker but adapted for markdown:
    - Respects heading hierarchy
    - Keeps special blocks intact (code, quotes)
    - Sentence-based paragraph chunking
    - ~300 token target per chunk
    """

    def __init__(self, target_tokens: int = 300, max_tokens: int = 500):
        """
        Initialize chunker.

        Args:
            target_tokens: Target tokens per chunk (default: 300)
            max_tokens: Maximum tokens per chunk (default: 500)
        """
        self.target_tokens = target_tokens
        self.max_tokens = max_tokens

        # Patterns for markdown elements
        self.heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
        self.code_block_pattern = re.compile(r"```[\s\S]*?```", re.MULTILINE)
        self.quote_pattern = re.compile(r"^>.*$", re.MULTILINE)
        self.list_pattern = re.compile(r"^[\s]*[-*+]\s+.+$", re.MULTILINE)

    def chunk_markdown(self, markdown_text: str) -> List[Chunk]:
        """
        Split markdown into processable chunks.

        Strategy:
        1. Parse heading hierarchy
        2. Split by sections
        3. Chunk paragraphs with sentence-based splitting
        4. Preserve special blocks (code, quotes, lists)

        Args:
            markdown_text: Markdown document text

        Returns:
            List of Chunk objects
        """
        chunks = []
        sections = self._parse_sections(markdown_text)

        for section in sections:
            heading_text = section["heading"]
            content = section["content"]
            context = section["context"]
            start_pos = section["start_pos"]
            level = section["level"]

            # Add heading as its own chunk
            if heading_text:
                chunks.append(
                    Chunk(
                        heading=heading_text,
                        text=heading_text,
                        type=ChunkType.HEADING,
                        context=context,
                        start_pos=start_pos,
                        end_pos=start_pos + len(heading_text),
                        level=level,
                    )
                )

            # Process section content
            content_chunks = self._chunk_section_content(content, heading_text, context, start_pos)
            chunks.extend(content_chunks)

        return chunks

    def _parse_sections(self, markdown_text: str) -> List[dict]:
        """
        Parse markdown into sections based on headings.

        Returns:
            List of sections with heading, content, context, and position info
        """
        sections = []
        lines = markdown_text.split("\n")

        current_heading = ""
        current_content = []
        current_level = 0
        heading_stack = []  # Track heading hierarchy
        pos = 0

        for line in lines:
            heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)

            if heading_match:
                # Save previous section if exists (even if empty content)
                if current_heading:
                    sections.append(
                        {
                            "heading": current_heading,
                            "content": "\n".join(current_content),
                            "context": (
                                " > ".join(heading_stack) if heading_stack else current_heading
                            ),
                            "start_pos": pos - len("\n".join(current_content)),
                            "level": current_level,
                        }
                    )

                # Start new section
                level = len(heading_match.group(1))
                heading_text = heading_match.group(2).strip()

                # Update heading stack based on level
                # Pop headings at same or higher level (lower number = higher level)
                while heading_stack and len(heading_stack) >= level:
                    heading_stack.pop()

                heading_stack.append(heading_text)
                current_heading = heading_text
                current_content = []
                current_level = level
            else:
                current_content.append(line)

            pos += len(line) + 1  # +1 for newline

        # Add final section (even if empty content)
        if current_heading:
            sections.append(
                {
                    "heading": current_heading,
                    "content": "\n".join(current_content),
                    "context": " > ".join(heading_stack) if heading_stack else current_heading,
                    "start_pos": pos - len("\n".join(current_content)),
                    "level": current_level,
                }
            )

        return sections

    def _chunk_section_content(
        self, content: str, heading: str, context: str, start_pos: int
    ) -> List[Chunk]:
        """
        Chunk section content into semantic pieces.

        Handles paragraphs, lists, code blocks, and quotes separately.
        """
        if not content.strip():
            return []

        chunks = []
        blocks = self._split_into_blocks(content)

        current_pos = start_pos

        for block in blocks:
            block_type = self._detect_block_type(block)

            if block_type == ChunkType.CODE or block_type == ChunkType.QUOTE:
                # Keep code blocks and quotes intact
                chunks.append(
                    Chunk(
                        heading=heading,
                        text=block,
                        type=block_type,
                        context=context,
                        start_pos=current_pos,
                        end_pos=current_pos + len(block),
                    )
                )
            elif block_type == ChunkType.LIST:
                # Keep lists together
                chunks.append(
                    Chunk(
                        heading=heading,
                        text=block,
                        type=block_type,
                        context=context,
                        start_pos=current_pos,
                        end_pos=current_pos + len(block),
                    )
                )
            else:
                # Paragraph - apply sentence-based chunking
                para_chunks = self._chunk_paragraph(block, heading, context, current_pos)
                chunks.extend(para_chunks)

            current_pos += len(block) + 1

        return chunks

    def _split_into_blocks(self, content: str) -> List[str]:
        """
        Split content into blocks (paragraphs, lists, code, quotes).

        Preserves special markdown blocks as single units.
        """
        # Simple implementation: split on double newlines, but preserve special blocks
        blocks = []
        current_block = []
        in_code_block = False
        in_list = False

        for line in content.split("\n"):
            # Check for code block boundaries
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                current_block.append(line)
                if not in_code_block:  # End of code block
                    blocks.append("\n".join(current_block))
                    current_block = []
                continue

            # Inside code block
            if in_code_block:
                current_block.append(line)
                continue

            # Check for list items
            is_list_item = re.match(r"^[\s]*[-*+]\s+", line)
            if is_list_item:
                if not in_list:
                    # Start new list block
                    if current_block:
                        blocks.append("\n".join(current_block))
                        current_block = []
                    in_list = True
                current_block.append(line)
                continue

            # End of list
            if in_list and not is_list_item and line.strip():
                blocks.append("\n".join(current_block))
                current_block = []
                in_list = False

            # Empty line - potential block boundary
            if not line.strip():
                if current_block:
                    blocks.append("\n".join(current_block))
                    current_block = []
                continue

            # Regular content
            current_block.append(line)

        # Add final block
        if current_block:
            blocks.append("\n".join(current_block))

        return [b for b in blocks if b.strip()]

    def _detect_block_type(self, block: str) -> ChunkType:
        """Detect the type of a markdown block."""
        block_stripped = block.strip()

        if block_stripped.startswith("```"):
            return ChunkType.CODE
        elif block_stripped.startswith(">"):
            return ChunkType.QUOTE
        elif re.match(r"^[\s]*[-*+]\s+", block_stripped):
            return ChunkType.LIST
        else:
            return ChunkType.PARAGRAPH

    def _chunk_paragraph(
        self, paragraph: str, heading: str, context: str, start_pos: int
    ) -> List[Chunk]:
        """
        Chunk a paragraph using sentence-based splitting.

        Adapted from FileIntel's TextChunker algorithm.
        """
        sentences = self._split_into_sentences(paragraph)

        if not sentences:
            return []

        chunks = []
        current_sentences = []
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = self._estimate_tokens(sentence)

            # If adding this sentence exceeds max, save current chunk
            if current_sentences and (current_tokens + sentence_tokens > self.max_tokens):
                chunk_text = " ".join(current_sentences)
                chunks.append(
                    Chunk(
                        heading=heading,
                        text=chunk_text,
                        type=ChunkType.PARAGRAPH,
                        context=context,
                        start_pos=start_pos,
                        end_pos=start_pos + len(chunk_text),
                    )
                )
                current_sentences = []
                current_tokens = 0
                start_pos += len(chunk_text) + 1

            current_sentences.append(sentence)
            current_tokens += sentence_tokens

        # Add final chunk
        if current_sentences:
            chunk_text = " ".join(current_sentences)
            chunks.append(
                Chunk(
                    heading=heading,
                    text=chunk_text,
                    type=ChunkType.PARAGRAPH,
                    context=context,
                    start_pos=start_pos,
                    end_pos=start_pos + len(chunk_text),
                )
            )

        return chunks

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.

        Adapted from FileIntel's sentence splitting with abbreviation protection.
        """
        # Common abbreviations that shouldn't trigger sentence breaks
        abbreviations = {
            "dr",
            "mr",
            "mrs",
            "ms",
            "prof",
            "sr",
            "jr",
            "etc",
            "vs",
            "e.g",
            "i.e",
            "p",
            "pp",
            "vol",
            "fig",
            "al",
            "et",
        }

        # Simple sentence splitting pattern
        # Splits on . ! ? followed by space and capital letter
        pattern = r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s+(?=[A-Z])"

        sentences = re.split(pattern, text)

        # Clean and filter
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                cleaned_sentences.append(sentence)

        return cleaned_sentences

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Simple approximation: ~4 characters per token (OpenAI's rule of thumb).
        """
        return len(text) // 4

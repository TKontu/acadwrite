"""Data models for AcadWrite."""

from acadwrite.models.outline import Outline, OutlineItem
from acadwrite.models.query import (
    ChunkMetadata,
    DocumentMetadata,
    QueryResponse,
    Source,
)
from acadwrite.models.section import (
    AcademicSection,
    Citation,
    CitationStyle,
    WritingStyle,
)

__all__ = [
    # Query models
    "ChunkMetadata",
    "DocumentMetadata",
    "Source",
    "QueryResponse",
    # Section models
    "Citation",
    "AcademicSection",
    "CitationStyle",
    "WritingStyle",
    # Outline models
    "OutlineItem",
    "Outline",
]

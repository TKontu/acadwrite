"""Workflows for academic content generation."""

from acadwrite.workflows.chapter_processor import (
    Chapter,
    ChapterMetadata,
    ChapterProcessor,
)
from acadwrite.workflows.citation_manager import CitationCheck, CitationManager
from acadwrite.workflows.counterargument import (
    AnalysisDepth,
    CounterargumentGenerator,
    CounterargumentReport,
    Evidence,
)
from acadwrite.workflows.section_generator import SectionGenerator

__all__ = [
    "SectionGenerator",
    "CounterargumentGenerator",
    "AnalysisDepth",
    "Evidence",
    "CounterargumentReport",
    "ChapterProcessor",
    "Chapter",
    "ChapterMetadata",
    "CitationManager",
    "CitationCheck",
]

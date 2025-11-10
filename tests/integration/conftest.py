"""Pytest configuration and fixtures for integration tests."""

import os
from pathlib import Path

import pytest

from acadwrite.config import Settings
from acadwrite.services.fileintel import FileIntelClient
from acadwrite.services.formatter import FormatterService
from acadwrite.services.llm import LLMClient
from acadwrite.workflows.section_generator import SectionGenerator


# Skip all integration tests if SKIP_INTEGRATION env var is set
def pytest_collection_modifyitems(config, items):
    """Skip integration tests if SKIP_INTEGRATION is set."""
    if os.environ.get("SKIP_INTEGRATION"):
        skip_integration = pytest.mark.skip(reason="SKIP_INTEGRATION environment variable set")
        for item in items:
            if "integration" in str(item.fspath):
                item.add_marker(skip_integration)


@pytest.fixture(scope="session")
def settings():
    """Load settings from config file or environment."""
    try:
        return Settings.load()
    except Exception:
        # Fallback to defaults if no config file
        return Settings(
            fileintel={
                "base_url": os.environ.get("FILEINTEL_URL", "http://localhost:8000"),
                "timeout": 30.0,
                "max_retries": 3,
            },
            llm={
                "provider": "openai",
                "base_url": os.environ.get("LLM_BASE_URL", "http://localhost:8000/v1"),
                "model": os.environ.get("LLM_MODEL", "gpt-4"),
                "api_key": os.environ.get("OPENAI_API_KEY", "test-key"),
                "temperature": 0.7,
            },
            writing={
                "citation_style": "footnote",
                "style": "formal",
                "max_words": 1000,
            },
        )


@pytest.fixture(scope="function")
async def fileintel_client(settings):
    """Create FileIntel client for integration tests.

    Note: Using function scope to avoid event loop issues with session-scoped async fixtures.
    """
    async with FileIntelClient(
        base_url=settings.fileintel.base_url,
        api_key=settings.fileintel.api_key,
        timeout=settings.fileintel.timeout,
        max_retries=settings.fileintel.max_retries,
    ) as client:
        yield client


@pytest.fixture(scope="session")
def llm_client(settings):
    """Create LLM client for integration tests."""
    return LLMClient(
        base_url=settings.llm.base_url,
        model=settings.llm.model,
        api_key=settings.llm.api_key,
        temperature=settings.llm.temperature,
    )


@pytest.fixture
def formatter_service():
    """Create FormatterService for integration tests."""
    return FormatterService()


@pytest.fixture
async def section_generator(fileintel_client, formatter_service):
    """Create SectionGenerator for integration tests."""
    return SectionGenerator(
        fileintel_client=fileintel_client,
        formatter=formatter_service,
    )


@pytest.fixture(scope="session")
def test_collection():
    """Test collection name to use for integration tests.

    Override with TEST_COLLECTION environment variable.
    """
    return os.environ.get("TEST_COLLECTION", "test_integration")


@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary directory for test output files."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def sample_outline_yaml(tmp_path):
    """Sample YAML outline for testing."""
    outline = tmp_path / "outline.yaml"
    outline.write_text(
        """title: "Test Chapter"
sections:
  - heading: "Introduction"
    level: 2
  - heading: "Background"
    level: 2
  - heading: "Methods"
    level: 2
    subsections:
      - heading: "Data Collection"
        level: 3
      - heading: "Analysis"
        level: 3
  - heading: "Results"
    level: 2
  - heading: "Conclusion"
    level: 2
"""
    )
    return outline


@pytest.fixture
def sample_outline_markdown(tmp_path):
    """Sample markdown outline for testing."""
    outline = tmp_path / "outline.md"
    outline.write_text(
        """# Test Chapter

## Introduction

## Background

## Methods

### Data Collection

### Analysis

## Results

## Conclusion
"""
    )
    return outline


@pytest.fixture
def sample_markdown_document(tmp_path):
    """Sample markdown document for processing tests."""
    doc = tmp_path / "document.md"
    doc.write_text(
        """# Research Paper

## Introduction

Machine learning has revolutionized data analysis. Recent studies show that deep learning
models achieve 95% accuracy on image classification tasks. This represents a significant
improvement over traditional methods.

## Methods

Neural networks use backpropagation for training. The architecture consisted of multiple
layers with dropout regularization. We trained the model for 100 epochs using Adam optimizer.

## Results

Our experiments show significant improvements in accuracy. The model outperformed all baselines.
Performance increased by 15% compared to previous approaches.

## Discussion

These findings demonstrate the effectiveness of our approach. However, further research is
needed to validate these results across different domains.
"""
    )
    return doc


@pytest.fixture
def sample_markdown_with_citations(tmp_path):
    """Sample markdown with existing citations for testing."""
    doc = tmp_path / "cited_document.md"
    doc.write_text(
        """# Literature Review

## Machine Learning

Machine learning algorithms have shown remarkable success [Smith, 2020, p. 15].
Deep learning in particular has achieved state-of-the-art results [Jones, 2019, p. 42].

## Applications

Healthcare diagnostics [Brown, 2021, p. 78] and financial prediction [Davis, 2022]
are two major application areas.

## Challenges

Despite progress, interpretability remains a challenge [Wilson, 2020, p. 105].
Bias in training data is another concern [Taylor, 2021, p. 33].
"""
    )
    return doc

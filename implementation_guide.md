# AcademicWrite - Implementation Guide

## Overview
This guide provides step-by-step instructions for implementing AcademicWrite. Follow these phases sequentially to build a working system.

---

## Prerequisites

### Required Knowledge
- Python 3.11+ (async/await, type hints, dataclasses)
- HTTP APIs (requests/httpx)
- CLI development (Typer or Click)
- Basic LLM API usage (OpenAI/Anthropic)

### Development Environment
```bash
# Python setup
python3.11 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Required tools
pip install --upgrade pip
pip install poetry  # or use pip-tools
```

### FileIntel Setup
Ensure FileIntel is running and accessible:
```bash
# Check FileIntel health
curl http://localhost:8000/health

# List collections
fileintel collection list

# Test query
fileintel query collection thesis_sources "test query"
```

---

## Phase 1: Project Setup (Day 1)

### 1.1 Initialize Project Structure

```bash
mkdir acadwrite
cd acadwrite

# Create directory structure
mkdir -p acadwrite/{models,services,workflows,formatters,prompts,utils}
mkdir -p tests/{unit,integration,fixtures}
mkdir -p docs

touch acadwrite/__init__.py
touch acadwrite/__main__.py
touch acadwrite/{models,services,workflows,formatters,prompts,utils}/__init__.py
```

### 1.2 Create pyproject.toml

```toml
[tool.poetry]
name = "acadwrite"
version = "0.1.0"
description = "Academic writing assistant powered by FileIntel RAG"
authors = ["Your Name <you@example.com>"]
readme = "README.md"
license = "MIT"

[tool.poetry.dependencies]
python = "^3.11"
typer = {extras = ["all"], version = "^0.9.0"}
httpx = "^0.25.0"
pydantic = "^2.0.0"
pydantic-settings = "^2.0.0"
pyyaml = "^6.0"
rich = "^13.0.0"
structlog = "^23.0.0"
openai = "^1.0.0"
anthropic = "^0.8.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
pytest-cov = "^4.1.0"
black = "^23.0.0"
mypy = "^1.5.0"
ruff = "^0.1.0"

[tool.poetry.scripts]
acadwrite = "acadwrite.cli:app"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

Install dependencies:
```bash
poetry install
# or
pip install -e ".[dev]"
```

### 1.3 Create Configuration Module

**File: `acadwrite/config.py`**

```python
"""Configuration management for AcademicWrite."""
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class FileIntelSettings(BaseSettings):
    """FileIntel connection settings."""
    url: str = "http://localhost:8000"
    timeout: int = 30
    api_key: Optional[str] = None


class LLMSettings(BaseSettings):
    """LLM provider settings."""
    provider: str = "openai"  # openai, anthropic, ollama
    model: str = "gpt-4-turbo-preview"
    api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    temperature: float = 0.3
    max_tokens: int = 2000


class WritingSettings(BaseSettings):
    """Writing preferences."""
    default_style: str = "formal"
    citation_style: str = "footnote"
    max_section_length: int = 1000
    context_window: int = 500


class OutputSettings(BaseSettings):
    """Output preferences."""
    default_format: str = "markdown"
    include_metadata: bool = True
    timestamp_files: bool = False


class LoggingSettings(BaseSettings):
    """Logging configuration."""
    level: str = "INFO"
    file: Optional[Path] = None
    console_output: bool = True


class Settings(BaseSettings):
    """Main settings."""
    model_config = SettingsConfigDict(
        env_prefix="ACADWRITE_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    fileintel: FileIntelSettings = Field(default_factory=FileIntelSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    writing: WritingSettings = Field(default_factory=WritingSettings)
    output: OutputSettings = Field(default_factory=OutputSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    
    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "Settings":
        """Load settings from file or environment."""
        if config_path is None:
            config_path = Path.home() / ".acadwrite" / "config.yaml"
        
        if config_path.exists():
            import yaml
            with open(config_path) as f:
                config_data = yaml.safe_load(f)
            return cls(**config_data)
        
        return cls()


# Global settings instance
settings = Settings.load()
```

### 1.4 Create Basic CLI Entry Point

**File: `acadwrite/cli.py`**

```python
"""Command-line interface for AcademicWrite."""
import typer
from rich.console import Console
from pathlib import Path
from typing import Optional

app = typer.Typer(
    name="acadwrite",
    help="Academic writing assistant powered by FileIntel RAG",
    add_completion=False
)
console = Console()


@app.command()
def generate(
    heading: str = typer.Argument(..., help="Section heading to generate"),
    collection: str = typer.Option(..., "--collection", "-c", help="FileIntel collection"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
    context: Optional[str] = typer.Option(None, help="Previous section context"),
    style: str = typer.Option("formal", help="Writing style"),
    max_words: int = typer.Option(1000, help="Maximum section length"),
):
    """Generate a single academic section."""
    console.print(f"[bold]Generating:[/bold] {heading}")
    console.print(f"[dim]Collection:[/dim] {collection}")
    
    # TODO: Implement generation logic
    console.print("[yellow]Not yet implemented[/yellow]")


@app.command()
def chapter(
    outline_path: Path = typer.Argument(..., help="Path to outline file"),
    collection: str = typer.Option(..., "--collection", "-c", help="FileIntel collection"),
    output_dir: Path = typer.Option("./output", "--output-dir", "-o", help="Output directory"),
    single_file: bool = typer.Option(False, help="Combine into single file"),
):
    """Generate chapter from outline."""
    console.print(f"[bold]Processing outline:[/bold] {outline_path}")
    
    # TODO: Implement chapter generation
    console.print("[yellow]Not yet implemented[/yellow]")


@app.command()
def contra(
    claim: str = typer.Argument(..., help="Claim to find counterarguments for"),
    collection: str = typer.Option(..., "--collection", "-c", help="FileIntel collection"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
    depth: str = typer.Option("standard", help="Analysis depth (quick/standard/deep)"),
    include_synthesis: bool = typer.Option(False, help="Include LLM synthesis"),
):
    """Discover counterarguments for a claim."""
    console.print(f"[bold]Analyzing claim:[/bold] {claim}")
    
    # TODO: Implement counterargument discovery
    console.print("[yellow]Not yet implemented[/yellow]")


# Citations command group
citations_app = typer.Typer(help="Citation management utilities")
app.add_typer(citations_app, name="citations")


@citations_app.command("extract")
def citations_extract(
    input_file: Path = typer.Argument(..., help="Input file"),
    format: str = typer.Option("bibtex", help="Output format"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Extract citations from document."""
    console.print(f"[bold]Extracting citations from:[/bold] {input_file}")
    
    # TODO: Implement citation extraction
    console.print("[yellow]Not yet implemented[/yellow]")


# Config command group
config_app = typer.Typer(help="Configuration management")
app.add_typer(config_app, name="config")


@config_app.command("show")
def config_show():
    """Display current configuration."""
    from acadwrite.config import settings
    console.print("[bold]Current Configuration:[/bold]")
    console.print(settings.model_dump_json(indent=2))


@config_app.command("init")
def config_init():
    """Initialize configuration with interactive prompts."""
    console.print("[yellow]Interactive setup not yet implemented[/yellow]")


if __name__ == "__main__":
    app()
```

**File: `acadwrite/__main__.py`**

```python
"""Entry point for python -m acadwrite."""
from acadwrite.cli import app

if __name__ == "__main__":
    app()
```

### 1.5 Test Basic Setup

```bash
# Test CLI is working
poetry run acadwrite --help

# Should show:
# Usage: acadwrite [OPTIONS] COMMAND [ARGS]...
#
# Academic writing assistant powered by FileIntel RAG
#
# Options:
#   --help  Show this message and exit.
#
# Commands:
#   chapter     Generate chapter from outline.
#   citations   Citation management utilities
#   config      Configuration management
#   contra      Discover counterarguments for a claim.
#   generate    Generate a single academic section.

# Test config command
poetry run acadwrite config show
```

**Expected Output:** Configuration displayed (with defaults)

---

## Phase 2: Core Models (Day 2)

### 2.1 Query Models

**File: `acadwrite/models/query.py`**

```python
"""Models for FileIntel query results."""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class Source:
    """Citation source from FileIntel."""
    author: str
    title: str
    page: Optional[str]
    relevance: float
    excerpt: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Source":
        """Parse from FileIntel source format."""
        # FileIntel format: "(Author) - Title (relevance: X.XXX)"
        # Need to parse this format
        return cls(
            author=data.get("author", "Unknown"),
            title=data.get("title", "Unknown"),
            page=data.get("page"),
            relevance=data.get("relevance", 0.0),
            excerpt=data.get("excerpt", "")
        )


@dataclass
class QueryResult:
    """Response from FileIntel query."""
    query: str
    answer: str
    sources: List[Source]
    collection: str
    rag_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_fileintel_response(cls, data: Dict[str, Any]) -> "QueryResult":
        """Parse FileIntel API response."""
        return cls(
            query=data["query"],
            answer=data["answer"],
            sources=[Source.from_dict(s) for s in data.get("sources", [])],
            collection=data["collection"],
            rag_type=data.get("rag_type", "unknown"),
            metadata=data.get("metadata", {})
        )
```

### 2.2 Section Models

**File: `acadwrite/models/section.py`**

```python
"""Models for academic sections and citations."""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


@dataclass
class Citation:
    """Standardized citation."""
    id: str  # e.g., "^1", "^2"
    author: str
    title: str
    page: Optional[str] = None
    year: Optional[str] = None
    source_text: str = ""  # Original format
    
    def to_footnote(self) -> str:
        """Format as footnote."""
        parts = [self.author, self.title]
        if self.page:
            parts.append(f"p.{self.page}")
        return f"[{self.id}]: {', '.join(parts)}"
    
    def to_bibtex(self) -> str:
        """Convert to BibTeX entry."""
        # Simplified - would need more robust implementation
        key = f"{self.author.lower().split()[0]}{self.year or ''}"
        return f"""@article{{{key},
  author = {{{self.author}}},
  title = {{{self.title}}},
  pages = {{{self.page or ''}}},
  year = {{{self.year or ''}}}
}}"""


@dataclass
class AcademicSection:
    """Structured academic section."""
    heading: str
    level: int  # 1=H1, 2=H2, etc.
    content: str
    citations: List[Citation] = field(default_factory=list)
    subsections: List['AcademicSection'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def word_count(self) -> int:
        """Calculate total word count including subsections."""
        count = len(self.content.split())
        for subsection in self.subsections:
            count += subsection.word_count()
        return count
    
    def all_citations(self) -> List[Citation]:
        """Get all citations including from subsections."""
        citations = list(self.citations)
        for subsection in self.subsections:
            citations.extend(subsection.all_citations())
        return citations


class WritingStyle(str, Enum):
    """Academic writing styles."""
    FORMAL = "formal"
    TECHNICAL = "technical"
    ACCESSIBLE = "accessible"
    RAW = "raw"


class CitationStyle(str, Enum):
    """Citation styles."""
    FOOTNOTE = "footnote"
    INLINE = "inline"
    ENDNOTE = "endnote"
```

### 2.3 Outline Models

**File: `acadwrite/models/outline.py`**

```python
"""Models for document outlines."""
from dataclasses import dataclass, field
from typing import List, Dict, Any
from pathlib import Path
import yaml
import re


@dataclass
class OutlineItem:
    """Single outline item."""
    heading: str
    level: int
    children: List['OutlineItem'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_leaf(self) -> bool:
        """Check if item has no children."""
        return len(self.children) == 0


@dataclass
class Outline:
    """Parsed outline structure."""
    title: str
    items: List[OutlineItem]
    
    @classmethod
    def from_yaml(cls, path: Path) -> "Outline":
        """Parse YAML outline file."""
        with open(path) as f:
            data = yaml.safe_load(f)
        
        title = data.get("title", "Untitled")
        items = cls._parse_yaml_sections(data.get("sections", []))
        
        return cls(title=title, items=items)
    
    @classmethod
    def _parse_yaml_sections(cls, sections: List[Dict]) -> List[OutlineItem]:
        """Recursively parse YAML sections."""
        items = []
        for section in sections:
            item = OutlineItem(
                heading=section["heading"],
                level=section.get("level", 2),
                children=cls._parse_yaml_sections(section.get("subsections", []))
            )
            items.append(item)
        return items
    
    @classmethod
    def from_markdown(cls, path: Path) -> "Outline":
        """Parse Markdown outline file."""
        with open(path) as f:
            content = f.read()
        
        lines = content.split("\n")
        title = "Untitled"
        items = []
        stack = []  # Track hierarchy
        
        for line in lines:
            # Match heading: # Heading, ## Heading, etc.
            match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if not match:
                continue
            
            level = len(match.group(1))
            heading = match.group(2).strip()
            
            if level == 1:
                title = heading
                continue
            
            item = OutlineItem(heading=heading, level=level)
            
            # Maintain hierarchy
            while stack and stack[-1][0] >= level:
                stack.pop()
            
            if stack:
                # Add as child to parent
                stack[-1][1].children.append(item)
            else:
                # Top-level item
                items.append(item)
            
            stack.append((level, item))
        
        return cls(title=title, items=items)
```

### 2.4 Test Models

**File: `tests/unit/test_models.py`**

```python
"""Unit tests for data models."""
import pytest
from acadwrite.models.section import Citation, AcademicSection
from acadwrite.models.outline import Outline, OutlineItem
from pathlib import Path


def test_citation_to_footnote():
    """Test citation formatting as footnote."""
    citation = Citation(
        id="^1",
        author="Smith, J.",
        title="Test Article",
        page="10-15"
    )
    
    footnote = citation.to_footnote()
    assert "Smith, J." in footnote
    assert "Test Article" in footnote
    assert "p.10-15" in footnote


def test_academic_section_word_count():
    """Test word count calculation."""
    section = AcademicSection(
        heading="Test",
        level=2,
        content="This is a test section with ten words in it."
    )
    
    assert section.word_count() == 10


def test_outline_from_markdown(tmp_path):
    """Test parsing markdown outline."""
    outline_content = """# Test Chapter

## Section 1
### Subsection 1.1
### Subsection 1.2

## Section 2
"""
    
    outline_file = tmp_path / "outline.md"
    outline_file.write_text(outline_content)
    
    outline = Outline.from_markdown(outline_file)
    
    assert outline.title == "Test Chapter"
    assert len(outline.items) == 2
    assert outline.items[0].heading == "Section 1"
    assert len(outline.items[0].children) == 2
```

Run tests:
```bash
pytest tests/unit/test_models.py -v
```

---

## Phase 3: FileIntel Client (Day 3)

### 3.1 Implement FileIntel Client

**File: `acadwrite/services/fileintel.py`**

```python
"""FileIntel API client."""
import httpx
from typing import List, Optional
from acadwrite.models.query import QueryResult, Source
from acadwrite.config import settings


class FileIntelError(Exception):
    """Base exception for FileIntel errors."""
    pass


class FileIntelConnectionError(FileIntelError):
    """Cannot connect to FileIntel."""
    pass


class FileIntelQueryError(FileIntelError):
    """Query failed."""
    pass


class CollectionNotFoundError(FileIntelError):
    """Collection doesn't exist."""
    pass


class FileIntelClient:
    """Client for FileIntel API."""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: int = 30,
        api_key: Optional[str] = None
    ):
        """Initialize client."""
        self.base_url = (base_url or settings.fileintel.url).rstrip("/")
        self.timeout = timeout
        self.api_key = api_key
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers=self._build_headers()
        )
    
    def _build_headers(self) -> dict:
        """Build request headers."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    async def query(
        self,
        collection: str,
        query: str,
        rag_type: str = "auto",
        max_sources: int = 10
    ) -> QueryResult:
        """
        Query FileIntel for information.
        
        Args:
            collection: Collection name
            query: Search query
            rag_type: RAG strategy (auto, vector, graph, hybrid)
            max_sources: Maximum sources to return
            
        Returns:
            QueryResult with answer and sources
            
        Raises:
            FileIntelConnectionError: Cannot reach FileIntel
            FileIntelQueryError: Query failed
            CollectionNotFoundError: Collection not found
        """
        try:
            response = await self.client.post(
                "/v2/queries",
                json={
                    "collection": collection,
                    "query": query,
                    "rag_type": rag_type,
                    "max_sources": max_sources
                }
            )
            
            if response.status_code == 404:
                raise CollectionNotFoundError(
                    f"Collection '{collection}' not found"
                )
            
            response.raise_for_status()
            data = response.json()
            
            return self._parse_response(data)
            
        except httpx.ConnectError as e:
            raise FileIntelConnectionError(
                f"Cannot connect to FileIntel at {self.base_url}"
            ) from e
        except httpx.HTTPStatusError as e:
            raise FileIntelQueryError(
                f"Query failed: {e.response.text}"
            ) from e
    
    def _parse_response(self, data: dict) -> QueryResult:
        """
        Parse FileIntel response into QueryResult.
        
        FileIntel returns sources in this format:
        "Sources (5):
          1. (Author) - Title (relevance: 0.930)"
        
        We need to parse this into structured Source objects.
        """
        # Parse sources from the response
        sources = []
        sources_list = data.get("sources", [])
        
        for source_dict in sources_list:
            # Parse source format
            source = self._parse_source(source_dict)
            sources.append(source)
        
        return QueryResult(
            query=data["query"],
            answer=data["answer"],
            sources=sources,
            collection=data["collection"],
            rag_type=data.get("rag_type", "unknown"),
            metadata=data.get("metadata", {})
        )
    
    def _parse_source(self, source_dict: dict) -> Source:
        """
        Parse a single source from FileIntel format.
        
        Expected format from FileIntel CLI output:
        "(Aldhan) - PRA Aldhan, 'Concurrent Engineering...' (relevance: 0.930)"
        
        But the API might return structured data.
        """
        # If already structured, use it directly
        if "author" in source_dict:
            return Source(
                author=source_dict["author"],
                title=source_dict["title"],
                page=source_dict.get("page"),
                relevance=source_dict.get("relevance", 0.0),
                excerpt=source_dict.get("excerpt", "")
            )
        
        # Otherwise parse from text format
        # This is a simplified parser - may need adjustment based on actual format
        text = source_dict.get("text", "")
        
        # Extract relevance
        relevance = 0.0
        if "relevance:" in text:
            try:
                relevance = float(text.split("relevance:")[1].split(")")[0].strip())
            except (IndexError, ValueError):
                pass
        
        # Extract author and title (simplified)
        parts = text.split(" - ")
        author = parts[0].strip("() ") if parts else "Unknown"
        title = parts[1].split("(relevance")[0].strip() if len(parts) > 1 else "Unknown"
        
        return Source(
            author=author,
            title=title,
            page=None,
            relevance=relevance,
            excerpt=""
        )
    
    async def list_collections(self) -> List[str]:
        """Get list of available collections."""
        try:
            response = await self.client.get("/v2/collections")
            response.raise_for_status()
            return response.json().get("collections", [])
        except httpx.HTTPError as e:
            raise FileIntelError(f"Failed to list collections: {e}") from e
    
    async def health_check(self) -> bool:
        """Check if FileIntel is available."""
        try:
            response = await self.client.get("/health")
            return response.status_code == 200
        except httpx.HTTPError:
            return False
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
```

### 3.2 Test FileIntel Client

**File: `tests/unit/test_fileintel_client.py`**

```python
"""Unit tests for FileIntel client."""
import pytest
from unittest.mock import AsyncMock, patch
from acadwrite.services.fileintel import (
    FileIntelClient,
    FileIntelConnectionError,
    CollectionNotFoundError
)


@pytest.fixture
def mock_httpx_client():
    """Mock httpx AsyncClient."""
    with patch("acadwrite.services.fileintel.httpx.AsyncClient") as mock:
        yield mock


@pytest.mark.asyncio
async def test_query_success(mock_httpx_client):
    """Test successful query."""
    # Setup mock response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "query": "test query",
        "answer": "Test answer",
        "sources": [
            {
                "author": "Smith, J.",
                "title": "Test Article",
                "page": "10",
                "relevance": 0.95,
                "excerpt": "Test excerpt"
            }
        ],
        "collection": "test",
        "rag_type": "vector"
    }
    
    mock_client_instance = AsyncMock()
    mock_client_instance.post.return_value = mock_response
    mock_httpx_client.return_value = mock_client_instance
    
    # Test
    client = FileIntelClient("http://localhost:8000")
    result = await client.query("test", "test query")
    
    assert result.query == "test query"
    assert result.answer == "Test answer"
    assert len(result.sources) == 1
    assert result.sources[0].author == "Smith, J."


@pytest.mark.asyncio
async def test_query_collection_not_found(mock_httpx_client):
    """Test query with non-existent collection."""
    mock_response = AsyncMock()
    mock_response.status_code = 404
    
    mock_client_instance = AsyncMock()
    mock_client_instance.post.return_value = mock_response
    mock_httpx_client.return_value = mock_client_instance
    
    client = FileIntelClient("http://localhost:8000")
    
    with pytest.raises(CollectionNotFoundError):
        await client.query("nonexistent", "test")
```

Run tests:
```bash
pytest tests/unit/test_fileintel_client.py -v
```

---

## Phase 4: Section Generator (Day 4-5)

### 4.1 Implement LLM Client (Simplified)

**File: `acadwrite/services/llm.py`**

```python
"""LLM client for content refinement."""
from typing import Optional
from enum import Enum
import openai
from anthropic import Anthropic
from acadwrite.config import settings


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


class LLMClient:
    """Client for LLM operations."""
    
    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: float = 0.3
    ):
        """Initialize LLM client."""
        self.provider = LLMProvider(provider or settings.llm.provider)
        self.model = model or settings.llm.model
        self.temperature = temperature
        
        if self.provider == LLMProvider.OPENAI:
            openai.api_key = api_key or settings.llm.api_key
            self.client = openai.OpenAI(api_key=openai.api_key)
        elif self.provider == LLMProvider.ANTHROPIC:
            self.client = Anthropic(api_key=api_key or settings.llm.api_key)
    
    async def invert_claim(self, claim: str) -> str:
        """
        Generate semantic opposite of a claim.
        
        Args:
            claim: Original claim
            
        Returns:
            Inverted claim as search query
        """
        prompt = f"""You are helping with academic research. Given a claim, generate a search query that would find OPPOSING or CONTRADICTING evidence.

Original Claim: {claim}

Generate a concise search query (3-6 keywords) that captures the OPPOSITE perspective or potential counterarguments. Focus on:
- Opposite outcomes (reduces → increases)
- Challenges or limitations
- Contradictory findings

Respond with ONLY the search query, no explanation.

Search Query:"""
        
        if self.provider == LLMProvider.OPENAI:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=100
            )
            return response.choices[0].message.content.strip()
        
        elif self.provider == LLMProvider.ANTHROPIC:
            response = self.client.messages.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=100
            )
            return response.content[0].text.strip()
        
        raise NotImplementedError(f"Provider {self.provider} not implemented")
```

### 4.2 Implement Formatter Service

**File: `acadwrite/services/formatter.py`**

```python
"""Formatting service for academic content."""
from typing import List
from acadwrite.models.section import AcademicSection, Citation


class FormatterService:
    """Service for formatting academic content."""
    
    def format_section(self, section: AcademicSection) -> str:
        """
        Format section as markdown.
        
        Args:
            section: Section to format
            
        Returns:
            Formatted markdown
        """
        lines = []
        
        # Add heading
        heading_prefix = "#" * section.level
        lines.append(f"{heading_prefix} {section.heading}\n")
        
        # Add content
        lines.append(section.content)
        lines.append("")
        
        # Add citations as footnotes
        if section.citations:
            lines.append("---\n")
            for citation in section.citations:
                lines.append(citation.to_footnote())
        
        # Add subsections recursively
        for subsection in section.subsections:
            lines.append("\n")
            lines.append(self.format_section(subsection))
        
        return "\n".join(lines)
    
    def convert_inline_to_footnotes(
        self,
        content: str,
        sources: List[Citation]
    ) -> str:
        """
        Convert inline citations to footnote style.
        
        This is where we transform FileIntel's inline citations
        to academic footnote format.
        """
        # FileIntel includes citations inline in the answer
        # We need to extract them and convert to [^1] format
        
        # Simplified implementation - would need more robust parsing
        formatted = content
        
        for i, citation in enumerate(sources, 1):
            # Look for author names in content and add footnote markers
            if citation.author in formatted:
                formatted = formatted.replace(
                    citation.author,
                    f"{citation.author}[^{i}]",
                    1  # Only first occurrence
                )
        
        return formatted
```

### 4.3 Implement Section Generator

**File: `acadwrite/workflows/section_generator.py`**

```python
"""Section generation workflow."""
from typing import Optional
from acadwrite.models.section import AcademicSection, Citation, WritingStyle
from acadwrite.models.query import QueryResult
from acadwrite.services.fileintel import FileIntelClient
from acadwrite.services.llm import LLMClient
from acadwrite.services.formatter import FormatterService


class SectionGenerator:
    """Generate academic sections from headings."""
    
    def __init__(
        self,
        fileintel: FileIntelClient,
        llm: Optional[LLMClient] = None,
        formatter: Optional[FormatterService] = None
    ):
        """Initialize generator."""
        self.fileintel = fileintel
        self.llm = llm or LLMClient()
        self.formatter = formatter or FormatterService()
    
    async def generate(
        self,
        heading: str,
        collection: str,
        context: Optional[str] = None,
        style: WritingStyle = WritingStyle.FORMAL,
        max_words: int = 1000
    ) -> AcademicSection:
        """
        Generate academic section from heading.
        
        Args:
            heading: Section heading
            collection: FileIntel collection
            context: Previous section context
            style: Writing style
            max_words: Maximum section length
            
        Returns:
            Complete AcademicSection
        """
        # Query FileIntel
        query_result = await self.fileintel.query(
            collection=collection,
            query=heading,
            rag_type="auto"
        )
        
        # Extract citations
        citations = self._extract_citations(query_result)
        
        # Convert content to use footnote citations
        content = self.formatter.convert_inline_to_footnotes(
            query_result.answer,
            citations
        )
        
        # Create section
        section = AcademicSection(
            heading=heading,
            level=2,  # Default to H2
            content=content,
            citations=citations,
            metadata={
                "collection": collection,
                "rag_type": query_result.rag_type
            }
        )
        
        return section
    
    def _extract_citations(self, query_result: QueryResult) -> List[Citation]:
        """Extract citations from query sources."""
        citations = []
        
        for i, source in enumerate(query_result.sources, 1):
            citation = Citation(
                id=f"^{i}",
                author=source.author,
                title=source.title,
                page=source.page,
                source_text=f"{source.author} - {source.title}"
            )
            citations.append(citation)
        
        return citations
```

### 4.4 Wire Up Generate Command

Update **`acadwrite/cli.py`**:

```python
import asyncio
from acadwrite.services.fileintel import FileIntelClient
from acadwrite.services.formatter import FormatterService
from acadwrite.workflows.section_generator import SectionGenerator


@app.command()
def generate(
    heading: str = typer.Argument(..., help="Section heading to generate"),
    collection: str = typer.Option(..., "--collection", "-c", help="FileIntel collection"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
    context: Optional[str] = typer.Option(None, help="Previous section context"),
    style: str = typer.Option("formal", help="Writing style"),
    max_words: int = typer.Option(1000, help="Maximum section length"),
):
    """Generate a single academic section."""
    console.print(f"[bold]Generating:[/bold] {heading}")
    console.print(f"[dim]Collection:[/dim] {collection}")
    
    async def _generate():
        async with FileIntelClient() as fileintel:
            formatter = FormatterService()
            generator = SectionGenerator(fileintel, formatter=formatter)
            
            section = await generator.generate(
                heading=heading,
                collection=collection,
                context=context,
                max_words=max_words
            )
            
            markdown = formatter.format_section(section)
            
            if output:
                output.write_text(markdown)
                console.print(f"[green]✓[/green] Saved to {output}")
            else:
                console.print("\n" + markdown)
    
    asyncio.run(_generate())
```

### 4.5 Test Section Generation

```bash
# Test with real FileIntel
acadwrite generate "Definition of Concurrent Engineering" \
  --collection thesis_sources \
  --output test_section.md

# Check output
cat test_section.md
```

---

## Phase 5: Counterargument Generator (Day 6)

### 5.1 Implement Counterargument Workflow

**File: `acadwrite/workflows/counterargument.py`**

```python
"""Counterargument discovery workflow."""
from dataclasses import dataclass
from typing import List, Optional
from acadwrite.models.query import QueryResult, Source
from acadwrite.services.fileintel import FileIntelClient
from acadwrite.services.llm import LLMClient
from enum import Enum


class AnalysisDepth(str, Enum):
    """Analysis depth levels."""
    QUICK = "quick"      # 3 sources
    STANDARD = "standard"  # 5 sources
    DEEP = "deep"         # 10 sources


@dataclass
class Evidence:
    """Supporting or contradicting evidence."""
    source: Source
    key_point: str
    relevance: float


@dataclass
class CounterargumentReport:
    """Counterargument analysis report."""
    original_claim: str
    inverted_query: str
    supporting_evidence: List[Evidence]
    contradicting_evidence: List[Evidence]
    synthesis: Optional[str] = None
    missing_perspectives: List[str] = None


class CounterargumentGenerator:
    """Generate counterargument analysis."""
    
    def __init__(
        self,
        fileintel: FileIntelClient,
        llm: LLMClient
    ):
        """Initialize generator."""
        self.fileintel = fileintel
        self.llm = llm
    
    async def generate(
        self,
        claim: str,
        collection: str,
        depth: AnalysisDepth = AnalysisDepth.STANDARD,
        include_synthesis: bool = False
    ) -> CounterargumentReport:
        """
        Generate counterargument analysis.
        
        Process:
        1. Query with original claim
        2. Invert claim with LLM
        3. Query with inverted claim
        4. Optionally synthesize
        """
        # Determine max sources based on depth
        max_sources = {
            AnalysisDepth.QUICK: 3,
            AnalysisDepth.STANDARD: 5,
            AnalysisDepth.DEEP: 10
        }[depth]
        
        # Query for supporting evidence
        supporting_result = await self.fileintel.query(
            collection=collection,
            query=claim,
            max_sources=max_sources
        )
        
        # Invert claim
        inverted_query = await self.llm.invert_claim(claim)
        
        # Query for contradicting evidence
        contradicting_result = await self.fileintel.query(
            collection=collection,
            query=inverted_query,
            max_sources=max_sources
        )
        
        # Build evidence lists
        supporting = [
            Evidence(
                source=source,
                key_point=source.excerpt[:200],
                relevance=source.relevance
            )
            for source in supporting_result.sources
        ]
        
        contradicting = [
            Evidence(
                source=source,
                key_point=source.excerpt[:200],
                relevance=source.relevance
            )
            for source in contradicting_result.sources
        ]
        
        # Optional synthesis
        synthesis = None
        if include_synthesis:
            synthesis = await self._synthesize(
                claim,
                supporting,
                contradicting
            )
        
        return CounterargumentReport(
            original_claim=claim,
            inverted_query=inverted_query,
            supporting_evidence=supporting,
            contradicting_evidence=contradicting,
            synthesis=synthesis
        )
    
    async def _synthesize(
        self,
        claim: str,
        supporting: List[Evidence],
        contradicting: List[Evidence]
    ) -> str:
        """Generate LLM synthesis of contradictions."""
        prompt = f"""Analyze the following claim and contradicting evidence:

Claim: {claim}

Supporting Evidence:
{self._format_evidence(supporting)}

Contradicting Evidence:
{self._format_evidence(contradicting)}

Provide a balanced academic synthesis that:
1. Acknowledges both perspectives
2. Identifies key points of tension
3. Suggests areas needing further research

Synthesis:"""
        
        # Use LLM to generate synthesis
        # (Implementation depends on provider)
        return "Synthesis not yet implemented"
    
    def _format_evidence(self, evidence: List[Evidence]) -> str:
        """Format evidence for prompt."""
        lines = []
        for i, ev in enumerate(evidence, 1):
            lines.append(f"{i}. {ev.source.author}: {ev.key_point}")
        return "\n".join(lines)
```

### 5.2 Wire Up Contra Command

Update `acadwrite/cli.py`:

```python
from acadwrite.workflows.counterargument import CounterargumentGenerator, AnalysisDepth


@app.command()
def contra(
    claim: str = typer.Argument(..., help="Claim to find counterarguments for"),
    collection: str = typer.Option(..., "--collection", "-c", help="FileIntel collection"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
    depth: str = typer.Option("standard", help="Analysis depth (quick/standard/deep)"),
    include_synthesis: bool = typer.Option(False, help="Include LLM synthesis"),
):
    """Discover counterarguments for a claim."""
    console.print(f"[bold]Analyzing claim:[/bold] {claim}")
    
    async def _analyze():
        async with FileIntelClient() as fileintel:
            llm = LLMClient()
            generator = CounterargumentGenerator(fileintel, llm)
            
            report = await generator.generate(
                claim=claim,
                collection=collection,
                depth=AnalysisDepth(depth),
                include_synthesis=include_synthesis
            )
            
            # Format report
            markdown = _format_counterargument_report(report)
            
            if output:
                output.write_text(markdown)
                console.print(f"[green]✓[/green] Saved to {output}")
            else:
                console.print("\n" + markdown)
    
    asyncio.run(_analyze())


def _format_counterargument_report(report: CounterargumentReport) -> str:
    """Format counterargument report as markdown."""
    lines = [
        f"# Counterarguments: {report.original_claim}\n",
        "## Original Claim",
        report.original_claim,
        "",
        "## Supporting Evidence",
        ""
    ]
    
    for i, ev in enumerate(report.supporting_evidence, 1):
        lines.append(f"### Source {i}")
        lines.append(f"- **Author:** {ev.source.author}")
        lines.append(f"- **Relevance:** {ev.relevance:.2f}")
        lines.append(f"- **Key Point:** {ev.key_point}")
        lines.append("")
    
    lines.extend([
        "## Contradicting Evidence",
        f"*Search query: {report.inverted_query}*",
        ""
    ])
    
    for i, ev in enumerate(report.contradicting_evidence, 1):
        lines.append(f"### Source {i}")
        lines.append(f"- **Author:** {ev.source.author}")
        lines.append(f"- **Relevance:** {ev.relevance:.2f}")
        lines.append(f"- **Key Point:** {ev.key_point}")
        lines.append("")
    
    if report.synthesis:
        lines.extend([
            "## Synthesis",
            report.synthesis
        ])
    
    return "\n".join(lines)
```

---

## Phase 6: Chapter Generation (Day 7-8)

### 6.1 Implement Chapter Processor

**File: `acadwrite/workflows/chapter_processor.py`**

```python
"""Chapter generation workflow."""
from dataclasses import dataclass
from datetime import datetime
from typing import List
from pathlib import Path
from acadwrite.models.outline import Outline, OutlineItem
from acadwrite.models.section import AcademicSection, Citation
from acadwrite.workflows.section_generator import SectionGenerator


@dataclass
class ChapterMetadata:
    """Metadata for generated chapter."""
    generation_date: datetime
    collection: str
    total_words: int
    total_citations: int
    sections_generated: int
    sections_failed: int
    processing_time_seconds: float


@dataclass
class Chapter:
    """Complete generated chapter."""
    title: str
    sections: List[AcademicSection]
    bibliography: List[Citation]
    metadata: ChapterMetadata


class ChapterProcessor:
    """Process outline into complete chapter."""
    
    def __init__(self, section_generator: SectionGenerator):
        """Initialize processor."""
        self.section_generator = section_generator
    
    async def process(
        self,
        outline: Outline,
        collection: str,
        parallel: int = 3,
        continue_on_error: bool = False
    ) -> Chapter:
        """
        Generate complete chapter from outline.
        
        Args:
            outline: Parsed outline
            collection: FileIntel collection
            parallel: Number of parallel queries (not implemented yet)
            continue_on_error: Continue if section fails
            
        Returns:
            Complete Chapter
        """
        start_time = datetime.now()
        sections = []
        failed = 0
        
        # Process each outline item
        for item in outline.items:
            try:
                section = await self._process_item(item, collection)
                sections.append(section)
            except Exception as e:
                failed += 1
                if not continue_on_error:
                    raise
                # Log error and continue
                print(f"Failed to generate section '{item.heading}': {e}")
        
        # Collect all citations
        all_citations = []
        for section in sections:
            all_citations.extend(section.all_citations())
        
        # Deduplicate citations
        unique_citations = self._deduplicate_citations(all_citations)
        
        # Calculate metrics
        total_words = sum(s.word_count() for s in sections)
        processing_time = (datetime.now() - start_time).total_seconds()
        
        metadata = ChapterMetadata(
            generation_date=datetime.now(),
            collection=collection,
            total_words=total_words,
            total_citations=len(unique_citations),
            sections_generated=len(sections),
            sections_failed=failed,
            processing_time_seconds=processing_time
        )
        
        return Chapter(
            title=outline.title,
            sections=sections,
            bibliography=unique_citations,
            metadata=metadata
        )
    
    async def _process_item(
        self,
        item: OutlineItem,
        collection: str,
        context: str = ""
    ) -> AcademicSection:
        """Recursively process outline item."""
        # Generate this section
        section = await self.section_generator.generate(
            heading=item.heading,
            collection=collection,
            context=context
        )
        
        section.level = item.level
        
        # Process children
        for child in item.children:
            subsection = await self._process_item(
                child,
                collection,
                context=section.content[-500:]  # Last 500 chars for context
            )
            section.subsections.append(subsection)
        
        return section
    
    def _deduplicate_citations(
        self,
        citations: List[Citation]
    ) -> List[Citation]:
        """Remove duplicate citations."""
        seen = set()
        unique = []
        
        for citation in citations:
            key = (citation.author, citation.title, citation.page)
            if key not in seen:
                seen.add(key)
                unique.append(citation)
        
        return unique
```

### 6.2 Wire Up Chapter Command

Update `acadwrite/cli.py`:

```python
from acadwrite.models.outline import Outline
from acadwrite.workflows.chapter_processor import ChapterProcessor


@app.command()
def chapter(
    outline_path: Path = typer.Argument(..., help="Path to outline file"),
    collection: str = typer.Option(..., "--collection", "-c", help="FileIntel collection"),
    output_dir: Path = typer.Option(Path("./output"), "--output-dir", "-o", help="Output directory"),
    single_file: bool = typer.Option(False, help="Combine into single file"),
    parallel: int = typer.Option(3, help="Parallel queries"),
    continue_on_error: bool = typer.Option(False, help="Continue if section fails"),
):
    """Generate chapter from outline."""
    console.print(f"[bold]Processing outline:[/bold] {outline_path}")
    
    if not outline_path.exists():
        console.print(f"[red]Error:[/red] Outline file not found: {outline_path}")
        raise typer.Exit(1)
    
    async def _generate():
        # Parse outline
        if outline_path.suffix == ".yaml":
            outline = Outline.from_yaml(outline_path)
        else:
            outline = Outline.from_markdown(outline_path)
        
        console.print(f"[dim]Sections:[/dim] {len(outline.items)}")
        
        # Generate chapter
        async with FileIntelClient() as fileintel:
            formatter = FormatterService()
            generator = SectionGenerator(fileintel, formatter=formatter)
            processor = ChapterProcessor(generator)
            
            with console.status("[bold green]Generating chapter..."):
                chapter = await processor.process(
                    outline=outline,
                    collection=collection,
                    parallel=parallel,
                    continue_on_error=continue_on_error
                )
            
            # Save outputs
            output_dir.mkdir(parents=True, exist_ok=True)
            
            if single_file:
                # Combine all sections
                full_content = f"# {chapter.title}\n\n"
                for section in chapter.sections:
                    full_content += formatter.format_section(section) + "\n\n"
                
                output_file = output_dir / "chapter.md"
                output_file.write_text(full_content)
                console.print(f"[green]✓[/green] Saved to {output_file}")
            else:
                # Save sections separately
                sections_dir = output_dir / "sections"
                sections_dir.mkdir(exist_ok=True)
                
                for i, section in enumerate(chapter.sections, 1):
                    filename = f"{i:02d}_{section.heading.lower().replace(' ', '_')}.md"
                    section_file = sections_dir / filename
                    section_file.write_text(formatter.format_section(section))
                
                console.print(f"[green]✓[/green] Saved {len(chapter.sections)} sections to {sections_dir}")
            
            # Save bibliography
            bib_file = output_dir / "bibliography.bib"
            bib_content = "\n\n".join(c.to_bibtex() for c in chapter.bibliography)
            bib_file.write_text(bib_content)
            
            # Display summary
            console.print("\n[bold]Generation Summary:[/bold]")
            console.print(f"  Sections: {chapter.metadata.sections_generated}")
            console.print(f"  Failed: {chapter.metadata.sections_failed}")
            console.print(f"  Words: {chapter.metadata.total_words}")
            console.print(f"  Citations: {chapter.metadata.total_citations}")
            console.print(f"  Time: {chapter.metadata.processing_time_seconds:.1f}s")
    
    asyncio.run(_generate())
```

---

## Phase 7: Testing & Documentation (Day 9-10)

### 7.1 Integration Tests

**File: `tests/integration/test_end_to_end.py`**

```python
"""End-to-end integration tests."""
import pytest
from pathlib import Path
from acadwrite.models.outline import Outline


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_section_e2e(tmp_path):
    """Test section generation end-to-end."""
    # Requires running FileIntel instance
    from acadwrite.services.fileintel import FileIntelClient
    from acadwrite.services.formatter import FormatterService
    from acadwrite.workflows.section_generator import SectionGenerator
    
    async with FileIntelClient("http://localhost:8000") as client:
        # Check health
        healthy = await client.health_check()
        if not healthy:
            pytest.skip("FileIntel not available")
        
        formatter = FormatterService()
        generator = SectionGenerator(client, formatter=formatter)
        
        section = await generator.generate(
            heading="Test Section",
            collection="thesis_sources"
        )
        
        assert section.heading == "Test Section"
        assert len(section.content) > 0
        
        # Save and verify
        output = tmp_path / "section.md"
        output.write_text(formatter.format_section(section))
        assert output.exists()


@pytest.mark.integration
def test_chapter_generation_cli(tmp_path, cli_runner):
    """Test chapter generation via CLI."""
    # Create test outline
    outline = tmp_path / "outline.md"
    outline.write_text("""# Test Chapter

## Section 1
## Section 2
""")
    
    output_dir = tmp_path / "output"
    
    # Run CLI command
    result = cli_runner.invoke(
        app,
        [
            "chapter",
            str(outline),
            "--collection", "thesis_sources",
            "--output-dir", str(output_dir),
            "--continue-on-error"
        ]
    )
    
    assert result.exit_code == 0
    assert output_dir.exists()
```

### 7.2 Create README

**File: `README.md`**

```markdown
# AcademicWrite

Academic writing assistant powered by FileIntel's hybrid RAG system.

## Features

- **Section Generation**: Generate academic sections from headings with automatic citations
- **Chapter Generation**: Process entire outlines into structured chapters
- **Counterargument Discovery**: Find opposing evidence for claims
- **Citation Management**: Extract and export citations in multiple formats

## Installation

```bash
pip install acadwrite
```

## Quick Start

### 1. Configure

```bash
# Interactive setup
acadwrite config init

# Or set manually
acadwrite config set fileintel.url http://localhost:8000
acadwrite config set llm.provider openai
export OPENAI_API_KEY=sk-...
```

### 2. Generate a Section

```bash
acadwrite generate "Definition of Concurrent Engineering" \
  --collection thesis_sources \
  --output section.md
```

### 3. Generate a Chapter

Create an outline (`outline.yaml`):

```yaml
title: "Chapter 3: Hybrid RAG Systems"
sections:
  - heading: "Introduction"
    level: 2
  - heading: "Vector Retrieval"
    level: 2
  - heading: "Graph Approaches"
    level: 2
```

Generate:

```bash
acadwrite chapter outline.yaml \
  --collection thesis_sources \
  --output-dir chapter3/
```

### 4. Find Counterarguments

```bash
acadwrite contra "GraphRAG outperforms vector search" \
  --collection thesis_sources \
  --depth deep \
  --include-synthesis
```

## Documentation

See [docs/](docs/) for full documentation:

- [Architecture](docs/architecture.md)
- [API Reference](docs/api.md)
- [Examples](docs/examples.md)

## Requirements

- Python 3.11+
- Running FileIntel instance
- OpenAI or Anthropic API key

## License

MIT
```

---

## Phase 8: Deployment (Day 11)

### 8.1 Package for Distribution

```bash
# Build package
poetry build

# Or with setuptools
python -m build

# Publish to PyPI (test first)
poetry publish --repository testpypi

# Then real PyPI
poetry publish
```

### 8.2 Create Docker Image (Optional)

**File: `Dockerfile`**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

# Copy application
COPY acadwrite ./acadwrite

ENTRYPOINT ["acadwrite"]
```

Build and run:

```bash
docker build -t acadwrite .
docker run -e OPENAI_API_KEY=$OPENAI_API_KEY acadwrite --help
```

---

## Next Steps & Enhancements

### Priority Enhancements
1. **Parallel Processing**: Implement true parallel section generation
2. **Citation Deduplication**: Improve algorithm to detect similar citations
3. **Context Management**: Better context passing between sections
4. **Error Recovery**: Save partial results on failure

### Future Features
1. **LaTeX Output**: Add LaTeX formatter
2. **Reference Manager Integration**: Zotero/Mendeley plugins
3. **Interactive Mode**: TUI for iterative writing
4. **Version Control**: Track changes to generated content

---

## Troubleshooting

### Common Issues

**FileIntel Connection Error**
```bash
# Check FileIntel is running
curl http://localhost:8000/health

# Update config
acadwrite config set fileintel.url http://your-fileintel-url
```

**LLM API Errors**
```bash
# Verify API key
echo $OPENAI_API_KEY

# Test with simple query
acadwrite contra "test claim" -c thesis_sources --depth quick
```

**Empty Sections**
- Check collection exists in FileIntel
- Verify collection has relevant documents
- Try different heading phrasing

---

## Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Documentation**: https://acadwrite.readthedocs.io

---

## License

MIT License - See LICENSE file for details
```

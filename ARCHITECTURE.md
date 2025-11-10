# AcadWrite: Academic Writing Assistant - Architecture Overview

> **Document Status**: Updated to reflect MVP 0.1 implementation (2025-11-05)
>
> This document has been updated from the original specification to reflect the actual implementation. See [Changelog](#changelog) for details on architectural evolution.

## Executive Summary

**AcadWrite** is a lightweight academic writing tool built on top of FileIntel's hybrid RAG infrastructure. It transforms FileIntel's document intelligence capabilities into specialized workflows for scientific writing, citation management, and argument analysis.

**Current Status**: MVP 0.1 complete with core generation workflows plus advanced document enhancement features.

### Core Premise
- **FileIntel** = RAG platform (document processing, vector+graph search, citation extraction)
- **AcadWrite** = Academic writing application (content generation, outline processing, counterargument discovery)

### Key Design Principles
1. **Separation of Concerns**: AcadWrite consumes FileIntel's API; doesn't modify RAG internals
2. **Lightweight**: Minimal dependencies, focused on workflow orchestration
3. **Format-First**: Markdown as primary format, extensible to LaTeX/Word
4. **Citation-Aware**: Leverages FileIntel's existing citation infrastructure
5. **Composable**: Each command does one thing well, can be chained

---

## System Context

```
┌─────────────────────────────────────────────────────────────┐
│                        User                                  │
│                     (Academic Writer)                        │
└────────────┬────────────────────────────────────────────────┘
             │
             │ CLI Commands
             ↓
┌─────────────────────────────────────────────────────────────┐
│                     AcadWrite                                │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Content   │  │  Citation    │  │ Counterargument  │  │
│  │  Generator  │  │  Manager     │  │   Discovery      │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
│         │                 │                    │            │
│         └─────────────────┴────────────────────┘            │
│                           │                                  │
│                    FileIntel Client                          │
└───────────────────────────┼──────────────────────────────────┘
                            │ HTTP API
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      FileIntel                               │
│  (Hybrid RAG Platform)                                       │
│                                                              │
│  • Document ingestion & chunking                            │
│  • Vector + Graph RAG                                        │
│  • Query routing                                             │
│  • Citation extraction & formatting                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
                  ┌──────────────────┐
                  │   Document       │
                  │   Corpus         │
                  └──────────────────┘
```

---

## Technology Stack

### Core Dependencies
- **Python 3.11+**: Modern Python features, type hints
- **Typer**: CLI framework (elegant, type-safe)
- **httpx**: Async HTTP client for FileIntel API
- **Pydantic**: Data validation and settings management
- **Rich**: Terminal formatting and progress bars
- **PyYAML**: Outline parsing

### Optional Dependencies
- **LangChain** (optional): If using advanced prompt templates
- **pylatex**: For LaTeX export
- **python-docx**: For Word export
- **bibtexparser**: For BibTeX citation handling

### LLM Integration
- **Primary**: OpenAI API (for claim inversion, content refinement)
- **Alternative**: Anthropic Claude API
- **Local**: Ollama support for offline work

---

## Project Structure

**Note**: This reflects the current implementation as of MVP 0.1. The architecture has evolved from the original specification to be more streamlined and feature-rich.

```
acadwrite/
├── README.md
├── pyproject.toml              # Poetry/setuptools config
├── ARCHITECTURE.md             # This file (top-level, not in docs/)
├── examples/
│   └── EDITOR_INTEGRATION_GUIDE.md
│
├── acadwrite/
│   ├── __init__.py
│   ├── __main__.py            # Entry point: python -m acadwrite
│   ├── cli.py                 # Single-file CLI (all commands) - 722 lines
│   ├── config.py              # Configuration management (Pydantic Settings)
│   │
│   ├── models/                # Pydantic models (organized by domain)
│   │   ├── __init__.py
│   │   ├── outline.py         # Outline parsing and structure models
│   │   ├── query.py           # FileIntel API request/response models
│   │   └── section.py         # Section, Citation, Chapter models
│   │
│   ├── services/              # External service integrations (renamed from 'core')
│   │   ├── __init__.py
│   │   ├── fileintel.py       # FileIntel HTTP client (async)
│   │   ├── llm.py             # LLM provider abstraction (OpenAI/Anthropic)
│   │   └── formatter.py       # Citation formatting service
│   │
│   ├── workflows/             # High-level academic writing workflows
│   │   ├── __init__.py
│   │   ├── section_generator.py      # Generate single section with citations
│   │   ├── chapter_processor.py      # Process outline → full chapter
│   │   ├── counterargument.py        # Find contradicting evidence
│   │   ├── citation_manager.py       # Citation extraction/validation/export
│   │   ├── document_processor.py     # Smart enhancement of existing docs **NEW**
│   │   └── markdown_chunker.py       # Semantic markdown chunking **NEW**
│   │
│   ├── formatters/            # (Empty - functionality in services/formatter.py)
│   │   └── __init__.py
│   │
│   ├── prompts/               # (Empty - prompts are inline in code)
│   │   └── __init__.py
│   │
│   └── utils/                 # (Empty - utilities integrated into other modules)
│       └── __init__.py
│
└── tests/
    ├── unit/                  # Unit tests with mocked dependencies
    │   ├── test_chapter_processor.py
    │   ├── test_citation_manager.py
    │   ├── test_counterargument.py
    │   ├── test_document_processor.py
    │   ├── test_fileintel_client.py
    │   ├── test_formatters.py
    │   ├── test_llm_client.py
    │   ├── test_markdown_chunker.py
    │   ├── test_models.py
    │   └── test_section_generator.py
    │
    └── integration/           # End-to-end tests with real FileIntel
        ├── conftest.py
        ├── test_chapter_processor_integration.py
        ├── test_citation_manager_integration.py
        ├── test_counterargument_integration.py
        ├── test_document_processor_integration.py
        ├── test_end_to_end.py
        ├── test_fileintel_integration.py
        └── test_section_generator_integration.py
```

### Architectural Decisions

**Why single-file CLI?** At 722 lines, `cli.py` remains maintainable. All commands use Typer sub-apps for organization. If it grows beyond 1000 lines, we'll split it.

**Why `services/` instead of `core/`?** Better semantic clarity - these are external service integrations (FileIntel, LLM providers, formatters).

**Why `models/` package?** Separation by domain (outline, query, section) is clearer than a monolithic models.py file.

**Why empty `formatters/`, `prompts/`, `utils/`?**
- **formatters/**: Citation formatting consolidated in `services/formatter.py` and model methods
- **prompts/**: Prompts are inline in code (see `llm.py`) - easier to maintain and version
- **utils/**: No generic utilities needed yet; domain-specific logic lives in respective modules

---

## Core Components

### 1. FileIntel Client (`services/fileintel.py`)

**Responsibility**: Async HTTP API wrapper for FileIntel RAG platform

```python
class FileIntelClient:
    """Async HTTP client for FileIntel RAG platform"""

    async def query(
        self,
        collection: str,
        question: str,
        rag_type: str = "auto"
    ) -> QueryResponse

    async def list_collections(self) -> List[str]

    async def health_check(self) -> bool

    # Context manager support
    async def __aenter__(self) -> "FileIntelClient"
    async def __aexit__(self, *args) -> None
```

**Key Features**:
- Async/await for non-blocking operations
- Automatic retry with exponential backoff (via httpx)
- Response parsing into Pydantic models (QueryResponse)
- Rich error messages with custom exceptions (FileIntelError, FileIntelConnectionError)
- Context manager support for clean resource management

**Actual Implementation**: 213 lines in `services/fileintel.py`

---

### 2. Section Generator (`workflows/section_generator.py`)

**Responsibility**: Generate single academic section with citations from FileIntel

```python
class SectionGenerator:
    """Generate academic section from heading + optional context"""

    async def generate_section(
        self,
        heading: str,
        collection: str,
        previous_content: Optional[str] = None,
        max_words: int = 500
    ) -> Section
```

**Process**:
1. Build query from heading + optional previous section context
2. Query FileIntel (response already includes inline citations)
3. Parse response into Section model
4. Extract citations from FileIntel sources
5. Apply word limit if specified
6. Return Section with content + citation list

**Features**:
- Context-aware generation (uses previous section for coherence)
- Word count limits
- Automatic citation extraction from FileIntel response
- Support for different RAG types (vector/graph/hybrid)

**Actual Implementation**: 218 lines in `workflows/section_generator.py`

---

### 3. Chapter Processor (`workflows/chapter_processor.py`)

**Responsibility**: Process hierarchical outline → full chapter with citations

```python
class ChapterProcessor:
    """Generate complete chapter from YAML/Markdown outline"""

    async def process_outline(
        self,
        outline: Outline,
        collection: str,
        output_path: Optional[str] = None
    ) -> Chapter

    async def process_recursive(
        self,
        node: OutlineNode,
        level: int,
        collection: str,
        previous_content: str = ""
    ) -> Tuple[str, List[Citation], str]
```

**Process**:
1. Parse outline (YAML/Markdown) into tree structure
2. Recursively process each node (depth-first):
   - Generate section content using SectionGenerator
   - Pass previous section content as context
   - Accumulate citations
3. Assemble sections into complete chapter
4. Deduplicate citations globally
5. Generate unified bibliography
6. Output as single file or per-section files

**Features**:
- Recursive outline processing (handles nested headings)
- Context propagation between sections
- Citation deduplication across entire chapter
- Multiple output formats (single markdown or per-section files)
- Progress tracking with Rich console

**Actual Implementation**: 367 lines in `workflows/chapter_processor.py`

---

### 4. Counterargument Discovery (`workflows/counterargument.py`)

**Responsibility**: Find supporting and contradicting evidence for claims

```python
class CounterargumentDiscovery:
    """Discover counterarguments to claims using LLM + FileIntel"""

    async def analyze_claim(
        self,
        claim: str,
        collection: str,
        synthesize: bool = False
    ) -> CounterargumentAnalysis
```

**Process**:
1. Use LLM to invert/negate claim (e.g., "X is good" → "X is bad")
2. Query FileIntel with original claim → supporting evidence
3. Query FileIntel with inverted claim → contradicting evidence
4. Optionally use LLM to synthesize analysis
5. Format as structured CounterargumentAnalysis

**Output Structure**:
- Original claim
- Inverted claim
- Supporting evidence (with citations)
- Contradicting evidence (with citations)
- Optional synthesis paragraph

**Actual Implementation**: 259 lines in `workflows/counterargument.py`

---

### 5. Citation Manager (`workflows/citation_manager.py`)

**Responsibility**: Extract, validate, and export citations

```python
class CitationManager:
    """Handle citation extraction, validation, and export"""

    def extract_citations_from_text(
        self,
        text: str,
        extraction_mode: str = "all"
    ) -> List[Citation]

    def validate_citations(
        self,
        citations: List[Citation],
        strict: bool = False
    ) -> Dict[str, Any]

    def export_to_bibtex(self, citations: List[Citation]) -> str
    def export_to_ris(self, citations: List[Citation]) -> str
    def export_to_json(self, citations: List[Citation]) -> str

    def deduplicate_citations(
        self,
        citations: List[Citation]
    ) -> List[Citation]
```

**Features**:
- Extracts citations from inline format: `(Author, Year, p.X)`
- Extracts from footnote format: `[^1]: Author, Year...`
- Validates citation completeness (author, year, page)
- Exports to BibTeX, RIS, JSON formats
- Deduplication by author+year+page
- Strict mode validation for academic standards

**Export Formats**:
- **BibTeX**: For LaTeX integration
- **RIS**: For reference managers (Zotero, Mendeley)
- **JSON**: For programmatic use

**Actual Implementation**: 340 lines in `workflows/citation_manager.py`

---

### 6. Document Processor (`workflows/document_processor.py`) **[NEW]**

**Responsibility**: Smart enhancement of existing markdown documents

```python
class DocumentProcessor:
    """Process and enhance existing academic documents"""

    async def process_document(
        self,
        input_path: str,
        collection: str,
        operation: str,
        output_path: Optional[str] = None,
        **options
    ) -> ProcessingResult
```

**Operations**:

1. **`find_citations`**: Automatically add missing citations
   - Identifies uncited claims
   - Queries FileIntel for supporting evidence
   - Inserts inline citations with sources

2. **`add_evidence`**: Insert supporting evidence
   - Scans document for claims
   - Finds relevant sources from FileIntel
   - Adds evidence paragraphs with citations

3. **`improve_clarity`**: LLM-based simplification
   - Uses LLM to improve readability
   - Maintains academic tone
   - Preserves citations

4. **`find_contradictions`**: Identify opposing evidence
   - Extracts main claims
   - Uses counterargument discovery
   - Highlights potential weaknesses

**Process**:
1. Load markdown document
2. Chunk using MarkdownChunker (semantic splitting)
3. Process each chunk based on operation
4. Reassemble enhanced document
5. Generate processing report

**Use Cases**:
- Enhance draft papers with citations
- Add supporting evidence to arguments
- Improve clarity while maintaining academic rigor
- Identify weaknesses before submission

**Actual Implementation**: 503 lines in `workflows/document_processor.py`

---

### 7. Markdown Chunker (`workflows/markdown_chunker.py`) **[NEW]**

**Responsibility**: Semantic chunking of markdown documents

```python
class MarkdownChunker:
    """Smart semantic chunking for markdown documents"""

    def chunk_markdown(
        self,
        text: str,
        target_tokens: int = 300,
        preserve_structure: bool = True
    ) -> List[MarkdownChunk]
```

**Features**:
- **Heading hierarchy preservation**: Maintains H1-H6 structure
- **Special block handling**: Preserves code blocks, blockquotes, lists
- **Sentence-based splitting**: Chunks at natural sentence boundaries
- **Token-aware**: Targets ~300 tokens per chunk (configurable)
- **Context preservation**: Each chunk includes heading context

**Algorithm**:
1. Split by headings (H1-H6)
2. For each section:
   - Identify special blocks (code, quotes, lists)
   - Split paragraphs into sentences
   - Group sentences until target token count
   - Preserve special blocks as atomic units
3. Return chunks with metadata (heading level, context)

**Use Cases**:
- DocumentProcessor operations (process chunk by chunk)
- Large document analysis
- Context-aware processing

**Adapted from**: FileIntel's TextChunker algorithm

**Actual Implementation**: 412 lines in `workflows/markdown_chunker.py`

---

## Data Models

```python
# core/models.py

from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from enum import Enum

class CitationStyle(str, Enum):
    INLINE = "inline"
    FOOTNOTE = "footnote"
    ENDNOTE = "endnote"

class ChunkMetadata(BaseModel):
    """Metadata about the specific chunk"""
    page_number: Optional[int] = None
    extraction_method: Optional[str] = None

class DocumentMetadata(BaseModel):
    """Metadata about the source document"""
    title: str
    authors: List[str] = []
    author_surnames: List[str] = []
    publication_date: Optional[str] = None
    publisher: Optional[str] = None
    document_type: Optional[str] = None

class Source(BaseModel):
    """Source from FileIntel with complete metadata"""
    document_id: str
    chunk_id: str
    filename: str
    citation: str  # Pre-formatted bibliography citation
    in_text_citation: str  # Pre-formatted inline citation
    text: str
    similarity_score: float
    relevance_score: float
    chunk_metadata: ChunkMetadata
    document_metadata: DocumentMetadata

class QueryResponse(BaseModel):
    """Response from FileIntel query endpoint"""
    answer: str  # Already includes inline citations!
    sources: List[Source]
    query_type: str  # "vector" | "graph" | "hybrid"
    collection_id: str
    question: str
    
class Section(BaseModel):
    """Generated academic section"""
    heading: str
    content: str
    citations: List[Source]
    word_count: int
    
class OutlineNode(BaseModel):
    """Node in document outline"""
    level: int
    heading: str
    query_hint: Optional[str] = None
    children: List['OutlineNode'] = []
    
class CounterargumentAnalysis(BaseModel):
    """Result of counterargument discovery"""
    original_claim: str
    inverted_claim: str
    supporting_evidence: List[Source]
    contradicting_evidence: List[Source]
    gaps: List[str]
```

---

## Configuration

**Implementation**: Pydantic Settings with environment variable support and `.env` file loading.

### Configuration Structure

The configuration system uses nested Pydantic models in `config.py`:

```python
# config.py

class FileIntelSettings(BaseSettings):
    """FileIntel service configuration"""
    base_url: str = "http://localhost:8000"
    timeout: int = 30

class LLMSettings(BaseSettings):
    """LLM provider configuration"""
    provider: str = "openai"  # openai | anthropic
    model: str = "gpt-4"
    api_key: Optional[str] = None
    temperature: float = 0.7

class WritingSettings(BaseSettings):
    """Writing style configuration"""
    citation_style: str = "inline"  # inline | footnote
    max_words_per_section: int = 500

class GenerationSettings(BaseSettings):
    """Content generation parameters"""
    rag_type: str = "auto"  # auto | vector | graph | hybrid
    context_window_chars: int = 500

class Settings(BaseSettings):
    """Main settings container"""
    fileintel: FileIntelSettings = Field(default_factory=FileIntelSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    writing: WritingSettings = Field(default_factory=WritingSettings)
    generation: GenerationSettings = Field(default_factory=GenerationSettings)

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
```

### Environment Variable Support

Configuration can be set via environment variables with prefix support:

```bash
# FileIntel settings
export FILEINTEL__BASE_URL="http://localhost:8000"
export FILEINTEL__TIMEOUT=30

# LLM settings
export LLM__PROVIDER="openai"
export LLM__MODEL="gpt-4"
export LLM__API_KEY="sk-..."
export LLM__TEMPERATURE=0.7

# Writing settings
export WRITING__CITATION_STYLE="inline"
export WRITING__MAX_WORDS_PER_SECTION=500

# Generation settings
export GENERATION__RAG_TYPE="auto"
export GENERATION__CONTEXT_WINDOW_CHARS=500
```

### .env File Support

Create a `.env` file in the project root:

```bash
# .env (not committed to git)

FILEINTEL__BASE_URL=http://localhost:8000
LLM__PROVIDER=openai
LLM__API_KEY=sk-your-api-key-here
WRITING__CITATION_STYLE=inline
```

### CLI Configuration Commands

```bash
# Show current configuration
acadwrite config show

# Check configuration validity (verify FileIntel connection, LLM API)
acadwrite config check

# Interactive configuration setup (not yet implemented)
acadwrite config init
```

### Defaults

If no configuration is provided, sensible defaults are used:
- FileIntel: `http://localhost:8000`
- LLM: OpenAI GPT-4
- Citation style: Inline
- Max words per section: 500
- RAG type: Auto (FileIntel decides)

---

## API Integration

**Note**: See `FILEINTEL_API_VERIFIED.md` for complete, verified API reference with real examples.

### FileIntel Endpoints Used

```
GET  /health
     → Health check

GET  /api/v2/collections
     → List available document collections

POST /api/v2/collections/{collection_name}/query
     Body: {
       "question": "concurrent engineering definition",
       "rag_type": "vector"
     }
     → Returns QueryResponse with answer (including inline citations) + sources

GET  /api/v2/metadata/document/{document_id}
     → Get document metadata (usually not needed - included in query response)
```

### FileIntel Response Format

Response includes complete metadata - no additional calls needed:

```json
{
  "success": true,
  "data": {
    "answer": "Concurrent engineering (CE) is... [Author, Year, p.X]",
    "sources": [
      {
        "document_id": "uuid",
        "chunk_id": "uuid",
        "filename": "file.pdf",
        "citation": "Full bibliography citation",
        "in_text_citation": "(Author, Year, p.X)",
        "text": "Excerpt...",
        "similarity_score": 0.93,
        "chunk_metadata": {
          "page_number": 12
        },
        "document_metadata": {
          "title": "Full Title",
          "authors": ["Author Name"],
          "publication_date": "2020",
          "publisher": "Publisher"
        }
      }
    ],
    "query_type": "vector",
    "collection_id": "uuid",
    "question": "concurrent engineering definition"
  }
}
```

---

## Error Handling

### FileIntel Connection Errors
- **Retry Logic**: 3 attempts with exponential backoff
- **Fallback**: Suggest checking FileIntel status
- **User Feedback**: `acadwrite config check`

### LLM API Errors
- **Rate Limiting**: Automatic backoff
- **Quota Exceeded**: Clear error message with solution
- **Invalid Response**: Log full response for debugging

### Invalid Input
- **Missing Collection**: List available collections
- **Empty Outline**: Show outline format example
- **Invalid Citation Format**: Suggest valid formats

---

## Security Considerations

### API Keys
- Store in environment variables
- Support `.env` files (not committed)
- Never log API keys

### FileIntel Authentication
- Support API token if FileIntel adds auth
- Store tokens securely (keyring integration)

### User Data
- Never send user documents to LLM
- Only send queries and outline structure
- Log opt-in only

---

## Performance Considerations

### Async Operations
- All FileIntel queries are async
- Parallel section generation where possible
- Progress bars for long operations

### Caching
- Cache FileIntel responses (optional)
- Cache LLM responses for identical prompts
- Configurable TTL

### Rate Limiting
- Respect FileIntel rate limits
- Respect LLM provider rate limits
- Implement client-side throttling

---

## Testing Strategy

### Unit Tests (`tests/unit/`)

Comprehensive unit tests with mocked dependencies:
- `test_fileintel_client.py` - FileIntel API client
- `test_llm_client.py` - LLM service integration
- `test_formatters.py` - Citation formatting
- `test_models.py` - Pydantic models
- `test_section_generator.py` - Section generation
- `test_chapter_processor.py` - Chapter processing
- `test_counterargument.py` - Counterargument discovery
- `test_citation_manager.py` - Citation management
- `test_document_processor.py` - Document enhancement
- `test_markdown_chunker.py` - Semantic chunking

### Integration Tests (`tests/integration/`)

End-to-end tests with real FileIntel instance:
- `test_fileintel_integration.py` - FileIntel API integration
- `test_section_generator_integration.py` - Section generation workflow
- `test_chapter_processor_integration.py` - Chapter generation workflow
- `test_counterargument_integration.py` - Counterargument workflow
- `test_citation_manager_integration.py` - Citation extraction/export
- `test_document_processor_integration.py` - Document enhancement workflow
- `test_end_to_end.py` - Complete workflows

### Test Fixtures (`tests/integration/conftest.py`)
- Sample FileIntel responses
- Sample outlines (YAML/Markdown)
- Expected markdown outputs
- Mock LLM responses

---

## Deployment

### Installation Methods

1. **pip install**
   ```bash
   pip install acadwrite
   ```

2. **From source**
   ```bash
   git clone https://github.com/yourusername/acadwrite
   cd acadwrite
   pip install -e .
   ```

3. **Docker** (future)
   ```bash
   docker run -it acadwrite --help
   ```

### Configuration
```bash
# First run: interactive setup
acadwrite config init

# Or manual setup
export FILEINTEL_URL="http://localhost:8000"
export OPENAI_API_KEY="sk-..."
```

---

## Future Enhancements

### Phase 2 (Post-MVP)
- **Interactive mode**: TUI for iterative writing
- **Reference manager integration**: Zotero, Mendeley
- **LaTeX export**: Direct `.tex` generation
- **Collaborative features**: Shared outlines, comments

### Phase 3 (Advanced)
- **Web interface**: Streamlit/Gradio UI
- **Version control**: Track document revisions
- **Multi-language**: Support for non-English writing
- **Quality metrics**: Citation density, coherence scores

---

## Success Metrics

### MVP Success Criteria
1. Generate single section with 3+ citations
2. Process 5-section outline into chapter
3. Find counterarguments for given claim
4. Export citations to BibTeX
5. Complete chapter generation in <2 minutes

### Quality Metrics
- Citation accuracy: 100% (from FileIntel)
- Markdown validity: 100% (linted)
- User satisfaction: >4/5 in initial feedback

---

## Development Phases

### Phase 1: Foundation ✅ **COMPLETED**
- [x] Project setup (Poetry, testing, linting)
- [x] FileIntel client implementation (`services/fileintel.py`)
- [x] CLI structure (single-file Typer in `cli.py`)
- [x] Configuration management (Pydantic Settings in `config.py`)

### Phase 2: Core Workflows ✅ **COMPLETED**
- [x] Section generator (`workflows/section_generator.py`)
- [x] Citation formatter (`services/formatter.py`)
- [x] Outline parser (integrated in `models/outline.py`)
- [x] Chapter generation (`workflows/chapter_processor.py`)

### Phase 3: Advanced Features ✅ **COMPLETED**
- [x] Counterargument discovery (`workflows/counterargument.py`)
- [x] LLM integration (`services/llm.py` - OpenAI/Anthropic)
- [x] BibTeX/RIS/JSON export (`workflows/citation_manager.py`)
- [x] Citation deduplication

### Phase 4: Polish & Extensions ✅ **COMPLETED**
- [x] Error handling improvements
- [x] Progress indicators (Rich console)
- [x] Documentation (ARCHITECTURE.md, QUICK_REFERENCE.md)
- [x] Comprehensive test suite (unit + integration)

### MVP 0.1 Extensions ✅ **COMPLETED** (Beyond Original Scope)
- [x] **DocumentProcessor** - Smart document enhancement
- [x] **MarkdownChunker** - Semantic markdown chunking
- [x] **CitationManager** - Complete citation toolkit
- [x] **Advanced operations**: find_citations, add_evidence, improve_clarity, find_contradictions

---

## Related Documentation

- `QUICK_REFERENCE.md`: Quick reference guide for all commands
- `FILEINTEL_API_VERIFIED.md`: Verified FileIntel API reference with examples
- `INTEGRATION_TESTS_SUMMARY.md`: Integration test results and coverage
- `EDITOR_INTEGRATION_GUIDE.md` (examples/): Guide for editor integration
- Additional implementation notes:
  - `SMART_PROCESSING.md`: Smart document processing features
  - `INTERACTIVE_WORKFLOW.md`: Interactive workflow design
  - `SMART_CHUNKING_IMPLEMENTATION_SUMMARY.md`: Chunking algorithm details

---

## Glossary

- **FileIntel**: The underlying hybrid RAG platform providing document intelligence
- **Collection**: A set of ingested documents in FileIntel
- **Section**: A single subsection of an academic document (e.g., "3.1.2 Core Principles")
- **Outline**: Hierarchical structure (YAML/Markdown) defining document sections
- **Claim**: A statement to be supported or refuted with evidence
- **Counterargument**: Evidence that contradicts a given claim
- **Chunk**: A semantic unit of text (~300 tokens) preserving structure
- **RAG**: Retrieval-Augmented Generation (vector/graph/hybrid search)
- **Citation Style**: Formatting style (inline, footnote, BibTeX, RIS, JSON)

---

## Changelog

### Version 2.0 (2025-11-05) - MVP 0.1 Implementation
**Major changes from original specification:**

- Renamed `core/` → `services/` for better semantic clarity
- Consolidated CLI into single `cli.py` file (722 lines)
- Expanded `models.py` → `models/` package (outline, query, section)
- Moved `config.py` to top-level (Pydantic Settings)
- Empty directories: `formatters/`, `prompts/`, `utils/` (functionality consolidated)

**New workflows added:**
- `DocumentProcessor` - Smart enhancement of existing documents
- `MarkdownChunker` - Semantic markdown chunking
- `CitationManager` - Complete citation management toolkit

**New operations:**
- `find_citations` - Auto-add missing citations
- `add_evidence` - Insert supporting evidence
- `improve_clarity` - LLM-based simplification
- `find_contradictions` - Identify opposing evidence

**Test coverage:**
- 10 unit test modules
- 7 integration test modules
- Comprehensive mocking and fixtures

### Version 1.0 (2025-10-24) - Original Specification
Initial architecture design for AI agent development.

---

**Document Version**: 2.0
**Last Updated**: 2025-11-05
**Status**: Reflects MVP 0.1 implementation
**Maintained by**: Architecture updates via AI-assisted development

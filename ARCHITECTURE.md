# AcadWrite: Academic Writing Assistant - Architecture Overview

## Executive Summary

**AcadWrite** is a lightweight academic writing tool built on top of FileIntel's hybrid RAG infrastructure. It transforms FileIntel's document intelligence capabilities into specialized workflows for scientific writing, citation management, and argument analysis.

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

```
acadwrite/
├── README.md
├── pyproject.toml              # Poetry/setuptools config
├── docs/
│   ├── ARCHITECTURE.md         # This file
│   ├── API_SPEC.md            # FileIntel API integration details
│   ├── WORKFLOWS.md           # Detailed workflow descriptions
│   └── PROMPTS.md             # LLM prompt templates
│
├── acadwrite/
│   ├── __init__.py
│   ├── __main__.py            # Entry point: python -m acadwrite
│   │
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── main.py            # Main CLI app (Typer)
│   │   ├── generate.py        # 'generate' command group
│   │   ├── citations.py       # 'citations' command group
│   │   ├── contra.py          # 'contra' command
│   │   └── config.py          # 'config' command
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── fileintel_client.py    # HTTP client for FileIntel
│   │   ├── llm_client.py          # LLM provider abstraction
│   │   ├── config.py              # Configuration management
│   │   └── models.py              # Pydantic models
│   │
│   ├── workflows/
│   │   ├── __init__.py
│   │   ├── section_generator.py   # Single section generation
│   │   ├── chapter_generator.py   # Multi-section from outline
│   │   ├── counterargument.py     # Counterargument discovery
│   │   └── outline_parser.py      # Parse YAML/MD outlines
│   │
│   ├── formatters/
│   │   ├── __init__.py
│   │   ├── markdown.py            # Markdown formatting
│   │   ├── citations.py           # Citation format conversion
│   │   ├── footnotes.py           # Footnote management
│   │   └── bibtex.py              # BibTeX export
│   │
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── templates.py           # Prompt template loader
│   │   ├── section_writer.txt     # Section generation prompt
│   │   ├── claim_inverter.txt     # Counterargument prompt
│   │   └── synthesis.txt          # Multi-source synthesis
│   │
│   └── utils/
│       ├── __init__.py
│       ├── text_processing.py     # Text manipulation utilities
│       └── console.py             # Rich console helpers
│
└── tests/
    ├── __init__.py
    ├── conftest.py                # Pytest fixtures
    ├── test_fileintel_client.py
    ├── test_section_generator.py
    ├── test_counterargument.py
    └── test_formatters.py
```

---

## Core Components

### 1. FileIntel Client (`core/fileintel_client.py`)

**Responsibility**: HTTP API wrapper for FileIntel

```python
class FileIntelClient:
    """Async HTTP client for FileIntel RAG platform"""
    
    async def query(
        self,
        collection: str,
        query: str,
        rag_type: str = "auto"
    ) -> QueryResponse
    
    async def get_document(self, doc_id: str) -> Document
    
    async def list_collections(self) -> List[Collection]
    
    async def health_check(self) -> bool
```

**Key Features**:
- Async/await for non-blocking operations
- Automatic retry with exponential backoff
- Response parsing into Pydantic models
- Error handling with rich error messages

---

### 2. Section Generator (`workflows/section_generator.py`)

**Responsibility**: Generate single academic section with citations

```python
class SectionGenerator:
    """Generate academic section from heading + context"""
    
    async def generate(
        self,
        heading: str,
        collection: str,
        context: Optional[str] = None,
        style: CitationStyle = CitationStyle.FOOTNOTE
    ) -> Section
```

**Process**:
1. Query FileIntel with heading as query
2. Parse response (already contains citations)
3. Reformat as academic markdown section
4. Convert inline citations to chosen style
5. Generate bibliography/footnotes

---

### 3. Chapter Generator (`workflows/chapter_generator.py`)

**Responsibility**: Process outline → full chapter

```python
class ChapterGenerator:
    """Generate complete chapter from outline"""
    
    async def generate_from_outline(
        self,
        outline_path: str,
        collection: str,
        output_dir: str
    ) -> Chapter
```

**Process**:
1. Parse outline (YAML/Markdown)
2. For each section:
   - Generate content using SectionGenerator
   - Pass previous section as context
3. Assemble sections into chapter
4. Deduplicate citations
5. Generate unified bibliography

---

### 4. Counterargument Discovery (`workflows/counterargument.py`)

**Responsibility**: Find contradicting evidence

```python
class CounterargumentDiscovery:
    """Discover counterarguments to claims"""
    
    async def analyze_claim(
        self,
        claim: str,
        collection: str
    ) -> CounterargumentAnalysis
```

**Process**:
1. Use LLM to invert/negate claim
2. Query FileIntel with original claim
3. Query FileIntel with inverted claim
4. Extract supporting evidence from (2)
5. Extract contradicting evidence from (3)
6. Identify gaps ("What's Missing")
7. Format as structured analysis

---

### 5. Citation Manager (`formatters/citations.py`)

**Responsibility**: Citation format conversion

```python
class CitationManager:
    """Handle citation format conversion"""
    
    def extract_citations(self, text: str) -> List[Citation]
    
    def convert_to_footnotes(
        self, 
        text: str, 
        citations: List[Citation]
    ) -> str
    
    def export_bibtex(self, citations: List[Citation]) -> str
    
    def deduplicate(self, citations: List[Citation]) -> List[Citation]
```

**Formats Supported**:
- Inline: `(Author, Year, p.X)`
- Footnote: `[^1]` with footnote list
- BibTeX: Export for LaTeX
- RIS: Export for reference managers

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

```yaml
# ~/.acadwrite/config.yaml

fileintel:
  base_url: "http://localhost:8000"
  timeout: 30
  max_retries: 3

llm:
  provider: "openai"  # openai | anthropic | ollama
  model: "gpt-4"
  api_key: "${OPENAI_API_KEY}"
  temperature: 0.7

output:
  citation_style: "footnote"  # inline | footnote | endnote
  markdown_dialect: "gfm"      # gfm | pandoc | commonmark
  include_relevance_scores: false

generation:
  context_window: 500  # chars from previous section
  min_sources_per_section: 3
  max_sources_per_section: 10
```

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

### Unit Tests
- FileIntel client (mocked responses)
- Citation formatters
- Outline parser
- Text processing utilities

### Integration Tests
- End-to-end section generation
- Chapter generation from sample outline
- Counterargument discovery

### Test Fixtures
- Sample FileIntel responses
- Sample outlines (YAML/Markdown)
- Expected markdown outputs

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

### Phase 1: Foundation (Week 1)
- [ ] Project setup (Poetry, testing, linting)
- [ ] FileIntel client implementation
- [ ] Basic CLI structure (Typer)
- [ ] Configuration management

### Phase 2: Core Workflows (Week 2)
- [ ] Section generator
- [ ] Citation formatter
- [ ] Outline parser
- [ ] Basic chapter generation

### Phase 3: Advanced Features (Week 3)
- [ ] Counterargument discovery
- [ ] LLM integration (claim inversion)
- [ ] BibTeX export
- [ ] Citation deduplication

### Phase 4: Polish (Week 4)
- [ ] Error handling improvements
- [ ] Progress indicators
- [ ] Documentation
- [ ] Example workflows

---

## Related Documentation

- `API_SPEC.md`: Detailed FileIntel API integration
- `WORKFLOWS.md`: Step-by-step workflow descriptions
- `PROMPTS.md`: LLM prompt templates and engineering
- `USER_GUIDE.md`: End-user documentation
- `DEVELOPMENT.md`: Development setup and guidelines

---

## Glossary

- **FileIntel**: The underlying hybrid RAG platform
- **Collection**: A set of ingested documents in FileIntel
- **Section**: A single subsection of an academic document (e.g., "3.1.2 Core Principles")
- **Outline**: Hierarchical structure defining document sections
- **Claim**: A statement to be supported or refuted with evidence
- **Counterargument**: Evidence that contradicts a given claim

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-24  
**Author**: Architecture specification for AI agent development

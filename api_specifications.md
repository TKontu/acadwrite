# AcademicWrite - API Specifications

**Note**: For FileIntel API details, see `FILEINTEL_API_VERIFIED.md` which contains the verified API reference based on actual testing.

## Overview

This document provides detailed API specifications for all major components in AcademicWrite. Use these as contracts when implementing each module.

---

## 1. CLI Interface (cli.py)

### Command: generate
Generate a single academic section from a heading.

**Signature:**
```bash
acadwrite generate [OPTIONS] HEADING
```

**Arguments:**
- `HEADING` (required): Section heading/title to generate content for

**Options:**
- `--collection, -c TEXT` (required): FileIntel collection name
- `--output, -o PATH`: Output file path (default: stdout)
- `--context TEXT`: Previous section context for coherence
- `--style TEXT`: Writing style [formal|technical|accessible] (default: formal)
- `--max-words INT`: Maximum section length in words (default: 1000)
- `--no-citations`: Disable citation generation
- `--format TEXT`: Output format [markdown|latex|org] (default: markdown)

**Examples:**
```bash
# Basic usage
acadwrite generate "Definition of Concurrent Engineering" --collection thesis

# With output file
acadwrite generate "Design Principles" -c thesis -o section_3_2.md

# With context for coherence
acadwrite generate "Implementation Challenges" \
  --collection thesis \
  --context "$(cat section_3_1.md)" \
  --output section_3_2.md
```

**Exit Codes:**
- `0`: Success
- `1`: Invalid arguments
- `2`: FileIntel connection error
- `3`: LLM API error
- `4`: File I/O error

---

### Command: chapter
Generate multiple sections from an outline file.

**Signature:**
```bash
acadwrite chapter [OPTIONS] OUTLINE_PATH
```

**Arguments:**
- `OUTLINE_PATH` (required): Path to outline file (.yaml or .md)

**Options:**
- `--collection, -c TEXT` (required): FileIntel collection name
- `--output-dir, -o PATH`: Output directory (default: ./output)
- `--single-file`: Combine all sections into one file
- `--style TEXT`: Writing style (default: formal)
- `--parallel INT`: Number of parallel queries (default: 3)
- `--continue-on-error`: Don't stop if one section fails

**Outline Format (YAML):**
```yaml
title: "Chapter 3: Hybrid RAG Systems"
sections:
  - heading: "Introduction to RAG"
    level: 2
    subsections:
      - heading: "Vector-Based Retrieval"
        level: 3
      - heading: "Graph-Based Approaches"
        level: 3
  - heading: "Combining Both Paradigms"
    level: 2
```

**Outline Format (Markdown):**
```markdown
# Chapter 3: Hybrid RAG Systems

## Introduction to RAG
### Vector-Based Retrieval
### Graph-Based Approaches

## Combining Both Paradigms
```

**Output Structure:**
```
output/
├── chapter.md              # Full chapter (if --single-file)
├── bibliography.bib         # All citations
├── metadata.json           # Generation metadata
└── sections/
    ├── 01_introduction.md
    ├── 02_vector_retrieval.md
    └── 03_graph_approaches.md
```

**Examples:**
```bash
# Generate from YAML outline
acadwrite chapter outline.yaml -c thesis -o chapter3/

# Generate as single file
acadwrite chapter outline.md -c thesis --single-file -o chapter3.md

# Continue even if sections fail
acadwrite chapter outline.yaml -c thesis --continue-on-error
```

---

### Command: contra
Discover counterarguments for a claim.

**Signature:**
```bash
acadwrite contra [OPTIONS] CLAIM
```

**Arguments:**
- `CLAIM` (required): The claim to find counterarguments for

**Options:**
- `--collection, -c TEXT` (required): FileIntel collection name
- `--output, -o PATH`: Output file (default: stdout)
- `--depth TEXT`: Analysis depth [quick|standard|deep] (default: standard)
- `--include-synthesis`: Add LLM-generated synthesis section

**Output Format:**
```markdown
# Counterarguments: [Original Claim]

## Original Claim
[Restated claim]

## Supporting Evidence
[Results from original query]

### Source 1
- Citation: [^1]
- Relevance: 0.93
- Key Point: ...

## Contradicting Evidence
[Results from inverted query]

### Source 4
- Citation: [^4]
- Relevance: 0.87
- Key Point: ...

## What's Not in Your Sources
- Missing perspective 1
- Missing perspective 2

## Synthesis (Optional)
[LLM-generated analysis of contradictions]

---

## Bibliography
[^1]: ...
[^4]: ...
```

**Examples:**
```bash
# Basic counterargument search
acadwrite contra "Concurrent engineering always reduces development time" \
  --collection thesis

# Deep analysis with synthesis
acadwrite contra "GraphRAG outperforms vector search" \
  --collection thesis \
  --depth deep \
  --include-synthesis \
  --output counterargs.md
```

---

### Command: citations
Citation management utilities.

**Subcommands:**

#### citations extract
Extract citations from a generated document.

```bash
acadwrite citations extract [OPTIONS] INPUT_FILE
```

**Options:**
- `--format TEXT`: Output format [bibtex|ris|endnote|json] (default: bibtex)
- `--output, -o PATH`: Output file (default: stdout)
- `--dedupe`: Remove duplicate citations

**Example:**
```bash
acadwrite citations extract chapter3.md --format bibtex -o refs.bib
```

#### citations check
Verify all claims have citations.

```bash
acadwrite citations check [OPTIONS] INPUT_FILE
```

**Options:**
- `--strict`: Fail if any claims lack citations
- `--report PATH`: Save report to file

**Output:**
```
Citation Check Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Section 3.1: 5/5 claims cited
✗ Section 3.2: 3/7 claims cited

Missing Citations:
  Line 42: "The approach reduces costs significantly"
  Line 58: "Most teams report improved collaboration"
  Line 63: "Traditional methods take 30% longer"

Summary:
  Total Claims: 12
  Cited: 8 (67%)
  Missing: 4 (33%)
```

#### citations dedupe
Remove duplicate citations from a document.

```bash
acadwrite citations dedupe [OPTIONS] INPUT_FILE
```

**Options:**
- `--in-place`: Modify file directly
- `--output, -o PATH`: Write to new file

---

### Command: config
Manage configuration.

**Subcommands:**

#### config show
Display current configuration.

```bash
acadwrite config show
```

#### config set
Set a configuration value.

```bash
acadwrite config set KEY VALUE
```

**Examples:**
```bash
acadwrite config set fileintel.url http://localhost:8000
acadwrite config set llm.provider anthropic
acadwrite config set llm.model claude-sonnet-3-5
```

#### config init
Initialize configuration with interactive prompts.

```bash
acadwrite config init
```

**Interactive Prompts:**
```
Welcome to AcademicWrite Setup!

FileIntel URL [http://localhost:8000]: 
LLM Provider [openai/anthropic/ollama]: openai
OpenAI API Key: sk-...
Default writing style [formal/technical/accessible]: formal
Default citation style [footnote/inline]: footnote

Configuration saved to ~/.acadwrite/config.yaml
```

---

## 2. FileIntel Client (services/fileintel.py)

### Class: FileIntelClient

**Initialization:**
```python
class FileIntelClient:
    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        api_key: Optional[str] = None
    ):
        """
        Initialize FileIntel client.
        
        Args:
            base_url: FileIntel API base URL (e.g., http://localhost:8000)
            timeout: Request timeout in seconds
            api_key: Optional API key for authentication
        """
```

### Method: query

```python
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
        collection: Collection name to query
        query: Search query
        rag_type: RAG strategy (auto, vector, graph, hybrid)
        max_sources: Maximum number of sources to return
        
    Returns:
        QueryResult with answer, sources, and metadata
        
    Raises:
        FileIntelConnectionError: Cannot reach FileIntel
        FileIntelQueryError: Query failed
        CollectionNotFoundError: Collection doesn't exist
    """
```

**Example Request:**
```python
client = FileIntelClient("http://localhost:8000")
result = await client.query(
    collection="thesis_sources",
    query="concurrent engineering definition",
    rag_type="auto"
)
```

**Example Response (QueryResult):**
```python
QueryResult(
    query="concurrent engineering definition",
    answer="Concurrent engineering (CE) is a systematic approach...",
    sources=[
        Source(
            author="Aldhan, PRA",
            title="Concurrent Engineering Fundamentals...",
            page="12-14",
            relevance=0.930,
            excerpt="CE is defined as..."
        ),
        # ... more sources
    ],
    collection="thesis_sources",
    rag_type="vector",
    metadata={"query_time_ms": 234}
)
```

### Method: list_collections

```python
async def list_collections(self) -> List[str]:
    """
    Get list of available collections.
    
    Returns:
        List of collection names
        
    Raises:
        FileIntelConnectionError: Cannot reach FileIntel
    """
```

### Method: health_check

```python
async def health_check(self) -> bool:
    """
    Check if FileIntel is available.
    
    Returns:
        True if FileIntel is healthy, False otherwise
    """
```

---

## 3. LLM Client (services/llm.py)

### Class: LLMClient

**Initialization:**
```python
class LLMClient:
    def __init__(
        self,
        provider: str,  # "openai", "anthropic", "ollama"
        model: str,
        api_key: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ):
        """Initialize LLM client."""
```

### Method: invert_claim

```python
async def invert_claim(self, claim: str) -> str:
    """
    Generate semantic opposite of a claim for counterargument search.
    
    Args:
        claim: Original claim
        
    Returns:
        Inverted claim as search query
        
    Example:
        Input: "Concurrent engineering reduces development time"
        Output: "concurrent engineering increases delays costs challenges overhead"
    """
```

**Implementation Note:**
Uses prompt template from `prompts/claim_inverter.py`:
```python
CLAIM_INVERTER_PROMPT = """
You are helping with academic research. Given a claim, generate a search query 
that would find OPPOSING or CONTRADICTING evidence.

Original Claim: {claim}

Generate a concise search query (3-6 keywords) that captures the OPPOSITE 
perspective or potential counterarguments. Focus on:
- Opposite outcomes (reduces → increases)
- Challenges or limitations
- Contradictory findings

Search Query:
"""
```

### Method: refine_content

```python
async def refine_content(
    self,
    content: str,
    style: WritingStyle,
    instructions: Optional[str] = None
) -> str:
    """
    Refine generated content to match writing style.
    
    Args:
        content: Raw content to refine
        style: Target writing style
        instructions: Optional specific refinement instructions
        
    Returns:
        Refined content
    """
```

### Method: synthesize_contradictions

```python
async def synthesize_contradictions(
    self,
    original_claim: str,
    supporting: List[str],
    contradicting: List[str]
) -> str:
    """
    Generate synthesis of contradicting evidence.
    
    Args:
        original_claim: The original claim
        supporting: List of supporting evidence excerpts
        contradicting: List of contradicting evidence excerpts
        
    Returns:
        Academic synthesis discussing the contradiction
    """
```

---

## 4. Section Generator (workflows/section_generator.py)

### Class: SectionGenerator

```python
class SectionGenerator:
    def __init__(
        self,
        fileintel_client: FileIntelClient,
        llm_client: LLMClient,
        formatter: FormatterService
    ):
        """Initialize section generator with required services."""
```

### Method: generate

```python
async def generate(
    self,
    heading: str,
    collection: str,
    context: Optional[WritingContext] = None,
    style: WritingStyle = WritingStyle.FORMAL,
    max_words: int = 1000
) -> AcademicSection:
    """
    Generate a complete academic section.
    
    Process:
    1. Query FileIntel with heading
    2. Parse response into AcademicSection
    3. Extract and format citations
    4. Apply writing style refinements
    5. Validate output
    
    Args:
        heading: Section heading
        collection: FileIntel collection
        context: Writing context for coherence
        style: Writing style
        max_words: Maximum section length
        
    Returns:
        Complete AcademicSection with citations
        
    Raises:
        GenerationError: Section generation failed
    """
```

**Internal Process:**

1. **Query Phase:**
```python
# Query FileIntel
query_result = await self.fileintel.query(
    collection=collection,
    query=heading,
    rag_type="auto"
)
```

2. **Parsing Phase:**
```python
# Extract citations from sources
citations = self._extract_citations(query_result.sources)

# Create section structure
section = AcademicSection(
    heading=heading,
    level=self._infer_heading_level(heading, context),
    content=query_result.answer,
    citations=citations,
    subsections=[]
)
```

3. **Refinement Phase:**
```python
# Apply writing style
if style != WritingStyle.RAW:
    section.content = await self.llm.refine_content(
        content=section.content,
        style=style
    )
```

4. **Validation Phase:**
```python
# Check word count
if self._count_words(section.content) > max_words:
    section.content = self._truncate_intelligently(
        section.content,
        max_words
    )

# Verify all claims have citations
self._validate_citations(section)
```

---

## 5. Counterargument Generator (workflows/counterargument.py)

### Class: CounterargumentGenerator

```python
class CounterargumentGenerator:
    def __init__(
        self,
        fileintel_client: FileIntelClient,
        llm_client: LLMClient,
        formatter: FormatterService
    ):
        """Initialize counterargument generator."""
```

### Method: generate

```python
async def generate(
    self,
    claim: str,
    collection: str,
    depth: AnalysisDepth = AnalysisDepth.STANDARD,
    include_synthesis: bool = False
) -> CounterargumentReport:
    """
    Generate counterargument analysis for a claim.
    
    Process:
    1. Query with original claim (supporting evidence)
    2. Use LLM to invert claim
    3. Query with inverted claim (contradicting evidence)
    4. Optionally synthesize with LLM
    5. Format as structured report
    
    Args:
        claim: Original claim to analyze
        collection: FileIntel collection
        depth: Analysis depth (affects number of sources)
        include_synthesis: Generate LLM synthesis
        
    Returns:
        CounterargumentReport with supporting/contradicting evidence
    """
```

**AnalysisDepth Enum:**
```python
class AnalysisDepth(str, Enum):
    QUICK = "quick"      # 3 sources each
    STANDARD = "standard"  # 5 sources each
    DEEP = "deep"         # 10 sources each
```

**CounterargumentReport Model:**
```python
@dataclass
class CounterargumentReport:
    original_claim: str
    inverted_query: str
    supporting_evidence: List[Evidence]
    contradicting_evidence: List[Evidence]
    synthesis: Optional[str]
    missing_perspectives: List[str]  # From FileIntel's "What's Missing"
    metadata: dict
```

**Evidence Model:**
```python
@dataclass
class Evidence:
    source: Source
    key_point: str
    relevance: float
    excerpt: str
```

---

## 6. Chapter Processor (workflows/chapter_processor.py)

### Class: ChapterProcessor

```python
class ChapterProcessor:
    def __init__(
        self,
        section_generator: SectionGenerator,
        citation_manager: CitationManager,
        formatter: FormatterService
    ):
        """Initialize chapter processor."""
```

### Method: process

```python
async def process(
    self,
    outline: Outline,
    collection: str,
    parallel: int = 3,
    continue_on_error: bool = False
) -> Chapter:
    """
    Generate complete chapter from outline.
    
    Process:
    1. Parse outline into section tree
    2. Generate sections (with parallelization)
    3. Maintain context across sections
    4. Deduplicate citations
    5. Assemble final chapter
    
    Args:
        outline: Parsed outline structure
        collection: FileIntel collection
        parallel: Number of parallel queries
        continue_on_error: Continue if section fails
        
    Returns:
        Complete Chapter with all sections
        
    Raises:
        ChapterGenerationError: Chapter generation failed
    """
```

**Chapter Model:**
```python
@dataclass
class Chapter:
    title: str
    sections: List[AcademicSection]
    bibliography: List[Citation]
    metadata: ChapterMetadata
```

**ChapterMetadata:**
```python
@dataclass
class ChapterMetadata:
    generation_date: datetime
    collection: str
    total_words: int
    total_citations: int
    sections_generated: int
    sections_failed: int
    processing_time_seconds: float
```

### Method: process_section_tree

```python
async def process_section_tree(
    self,
    outline_item: OutlineItem,
    collection: str,
    context: WritingContext
) -> AcademicSection:
    """
    Recursively process outline tree to generate nested sections.
    
    Handles:
    - Section hierarchy (##, ###, etc.)
    - Context propagation
    - Citation tracking
    """
```

---

## 7. Citation Manager (workflows/citation_manager.py)

### Class: CitationManager

```python
class CitationManager:
    def __init__(self):
        """Initialize citation manager."""
```

### Method: deduplicate

```python
def deduplicate(
    self,
    sections: List[AcademicSection]
) -> Tuple[List[AcademicSection], List[Citation]]:
    """
    Remove duplicate citations across sections and renumber.
    
    Process:
    1. Collect all citations
    2. Identify duplicates (same author + title + page)
    3. Create unified bibliography
    4. Renumber references in content
    
    Args:
        sections: List of sections with citations
        
    Returns:
        Tuple of (updated sections, unified bibliography)
    """
```

**Example:**
```python
# Before deduplication:
Section 1: "CE reduces time [^1]"
  [^1]: Aldhan, p.12
Section 2: "As noted earlier [^1]"
  [^1]: Aldhan, p.12  # Duplicate!

# After deduplication:
Section 1: "CE reduces time [^1]"
Section 2: "As noted earlier [^1]"
Unified Bibliography:
  [^1]: Aldhan, p.12
```

### Method: extract_from_text

```python
def extract_from_text(
    self,
    markdown_text: str
) -> List[Citation]:
    """
    Parse citations from markdown text.
    
    Supports formats:
    - Footnote: [^1], [^2]
    - Inline: (Author, Year)
    - Endnote: [1], [2]
    
    Returns:
        List of parsed citations
    """
```

### Method: format_bibliography

```python
def format_bibliography(
    self,
    citations: List[Citation],
    style: CitationStyle = CitationStyle.FOOTNOTE
) -> str:
    """
    Format citations as bibliography.
    
    Args:
        citations: List of citations
        style: Citation style
        
    Returns:
        Formatted bibliography as markdown
    """
```

### Method: export

```python
def export(
    self,
    citations: List[Citation],
    format: ExportFormat
) -> str:
    """
    Export citations to external format.
    
    Args:
        citations: Citations to export
        format: Export format (bibtex, ris, endnote, json)
        
    Returns:
        Formatted export string
    """
```

**BibTeX Example:**
```bibtex
@book{aldhan_concurrent,
  author = {Aldhan, PRA},
  title = {Concurrent Engineering Fundamentals Integrated Product and Process Organization},
  pages = {12-14}
}
```

---

## 8. Formatter Service (services/formatter.py)

### Class: FormatterService

```python
class FormatterService:
    def __init__(self):
        """Initialize formatter service."""
```

### Method: format_section

```python
def format_section(
    self,
    section: AcademicSection,
    format: OutputFormat = OutputFormat.MARKDOWN
) -> str:
    """
    Format section to output format.
    
    Args:
        section: Section to format
        format: Target format
        
    Returns:
        Formatted text
    """
```

**Markdown Output:**
```markdown
## Section Heading

Content with citations[^1] and more content[^2].

[^1]: Author, Title, p.10
[^2]: Author, Title, p.15
```

**LaTeX Output:**
```latex
\section{Section Heading}

Content with citations\cite{author2023} and more content\cite{other2024}.

\bibliography{references}
```

### Method: convert_citations

```python
def convert_citations(
    self,
    content: str,
    from_style: CitationStyle,
    to_style: CitationStyle,
    citations: List[Citation]
) -> str:
    """
    Convert citation style in text.
    
    Example:
        Input: "Text [^1]" (footnote)
        Output: "Text (Author, 2023)" (inline)
    """
```

---

## 9. Models

### QueryResult (models/query.py)

```python
@dataclass
class QueryResult:
    """Response from FileIntel query."""
    query: str
    answer: str
    sources: List[Source]
    collection: str
    rag_type: str
    metadata: dict
    
    @classmethod
    def from_fileintel_response(cls, response: dict) -> 'QueryResult':
        """Parse FileIntel API response."""
```

### Source (models/query.py)

```python
@dataclass
class Source:
    """Citation source from FileIntel."""
    author: str
    title: str
    page: Optional[str]
    relevance: float
    excerpt: str
    
    def to_citation(self, citation_id: str) -> Citation:
        """Convert to Citation object."""
```

### AcademicSection (models/section.py)

```python
@dataclass
class AcademicSection:
    """Structured academic section."""
    heading: str
    level: int  # 1=H1, 2=H2, etc.
    content: str
    citations: List[Citation]
    subsections: List['AcademicSection']
    metadata: dict = field(default_factory=dict)
    
    def word_count(self) -> int:
        """Calculate total word count including subsections."""
    
    def all_citations(self) -> List[Citation]:
        """Get all citations including from subsections."""
```

### Citation (models/section.py)

```python
@dataclass
class Citation:
    """Standardized citation."""
    id: str  # e.g., "^1", "^2"
    author: str
    title: str
    page: Optional[str]
    year: Optional[str]
    source_text: str  # Original FileIntel format
    
    def to_bibtex(self) -> str:
        """Convert to BibTeX entry."""
    
    def to_footnote(self) -> str:
        """Format as footnote."""
```

### Outline (models/outline.py)

```python
@dataclass
class Outline:
    """Parsed outline structure."""
    title: str
    items: List[OutlineItem]
    
    @classmethod
    def from_yaml(cls, path: Path) -> 'Outline':
        """Parse YAML outline file."""
    
    @classmethod
    def from_markdown(cls, path: Path) -> 'Outline':
        """Parse Markdown outline file."""
```

### OutlineItem (models/outline.py)

```python
@dataclass
class OutlineItem:
    """Single outline item."""
    heading: str
    level: int
    children: List['OutlineItem']
    metadata: dict = field(default_factory=dict)
    
    def is_leaf(self) -> bool:
        """Check if item has no children."""
```

### WritingContext (models/context.py)

```python
@dataclass
class WritingContext:
    """Context for content generation."""
    collection: str
    previous_content: str = ""  # Last N chars
    citations_used: Set[str] = field(default_factory=set)
    style: WritingStyle = WritingStyle.FORMAL
    max_section_length: int = 1000
    
    def add_content(self, content: str, window: int = 500):
        """Add content and maintain context window."""
```

### WritingStyle (models/context.py)

```python
class WritingStyle(str, Enum):
    """Academic writing styles."""
    FORMAL = "formal"        # Traditional academic
    TECHNICAL = "technical"  # Technical documentation
    ACCESSIBLE = "accessible"  # Broader audience
    RAW = "raw"             # No refinement
```

---

## 10. Error Handling

### Exception Hierarchy

```python
class AcademicWriteError(Exception):
    """Base exception for all acadwrite errors."""
    def __init__(
        self,
        message: str,
        suggestion: str = "",
        details: dict = None
    ):
        self.message = message
        self.suggestion = suggestion
        self.details = details or {}

# Configuration Errors
class ConfigurationError(AcademicWriteError):
    """Configuration is invalid or missing."""

# FileIntel Errors
class FileIntelError(AcademicWriteError):
    """Base for FileIntel-related errors."""

class FileIntelConnectionError(FileIntelError):
    """Cannot connect to FileIntel."""

class CollectionNotFoundError(FileIntelError):
    """Collection doesn't exist."""

class FileIntelQueryError(FileIntelError):
    """Query failed."""

# LLM Errors
class LLMError(AcademicWriteError):
    """Base for LLM-related errors."""

class LLMAPIError(LLMError):
    """LLM API call failed."""

class LLMRateLimitError(LLMError):
    """Hit LLM rate limit."""

# Generation Errors
class GenerationError(AcademicWriteError):
    """Content generation failed."""

class CitationError(GenerationError):
    """Citation extraction or formatting failed."""

class ValidationError(GenerationError):
    """Output validation failed."""
```

### Error Response Format

All CLI commands should output errors in this format:

```
ERROR: [Error Type]
Message: [Clear description]
Suggestion: [How to fix]

Details:
  key1: value1
  key2: value2
```

**Example:**
```
ERROR: Configuration Error
Message: FileIntel URL not configured
Suggestion: Run: acadwrite config set fileintel.url http://localhost:8000

Details:
  config_path: ~/.acadwrite/config.yaml
  expected_key: fileintel.url
```

---

## 11. Testing Specifications

### Test Coverage Requirements
- **Unit Tests:** > 80% coverage
- **Integration Tests:** All major workflows
- **End-to-End Tests:** CLI commands

### Mock Data

**FileIntel Query Response (tests/fixtures/fileintel_response.json):**
```json
{
  "query": "concurrent engineering definition",
  "answer": "Concurrent engineering (CE) is a systematic approach...",
  "sources": [
    {
      "author": "Aldhan, PRA",
      "title": "Concurrent Engineering Fundamentals",
      "page": "12-14",
      "relevance": 0.930,
      "excerpt": "CE is defined as..."
    }
  ],
  "collection": "thesis_sources",
  "rag_type": "vector",
  "metadata": {}
}
```

### Test Scenarios

#### Unit Test: FileIntelClient.query
```python
@pytest.mark.asyncio
async def test_query_success(mock_httpx):
    # Arrange
    mock_httpx.post.return_value = MockResponse(
        status_code=200,
        json=load_fixture("fileintel_response.json")
    )
    client = FileIntelClient("http://localhost:8000")
    
    # Act
    result = await client.query("thesis", "CE definition")
    
    # Assert
    assert result.answer.startswith("Concurrent engineering")
    assert len(result.sources) > 0
    assert result.sources[0].author == "Aldhan, PRA"
```

#### Integration Test: Section Generation
```python
@pytest.mark.integration
async def test_generate_section_end_to_end(fileintel_server):
    # Uses real FileIntel test server
    generator = SectionGenerator(...)
    
    section = await generator.generate(
        heading="Definition of CE",
        collection="test_collection"
    )
    
    assert section.heading == "Definition of CE"
    assert len(section.citations) > 0
    assert section.content  # Non-empty
```

#### CLI Test: Generate Command
```python
def test_generate_command(cli_runner, tmp_path):
    output_file = tmp_path / "section.md"
    
    result = cli_runner.invoke(
        app,
        [
            "generate",
            "Definition of CE",
            "--collection", "thesis",
            "--output", str(output_file)
        ]
    )
    
    assert result.exit_code == 0
    assert output_file.exists()
    content = output_file.read_text()
    assert "# Definition of CE" in content
```

---

## 12. Performance Specifications

### Response Time Targets
- **Single section generation:** < 10 seconds
- **Chapter (10 sections):** < 2 minutes with parallelization
- **Counterargument analysis:** < 15 seconds
- **Citation extraction:** < 1 second

### Throughput
- **Parallel queries:** Up to 5 concurrent FileIntel queries
- **LLM calls:** Rate limit aware (respect provider limits)

### Resource Usage
- **Memory:** < 500MB for typical chapter generation
- **Disk:** Cache up to 100MB of query results
- **Network:** ~100KB per FileIntel query

---

## 13. Security Specifications

### API Key Management
```python
# Priority order for API keys:
1. Environment variable: OPENAI_API_KEY
2. Config file (encrypted): ~/.acadwrite/config.yaml
3. System keychain (if available)

# Never log API keys
# Never include in error messages
# Never commit to version control
```

### Input Validation
```python
# File path validation
def validate_path(path: Path) -> Path:
    """Prevent directory traversal attacks."""
    resolved = path.resolve()
    if not str(resolved).startswith(str(Path.cwd())):
        raise SecurityError("Path outside working directory")
    return resolved

# Outline size limits
MAX_OUTLINE_SIZE = 1_000_000  # 1MB
MAX_OUTLINE_ITEMS = 1000

# Query length limits
MAX_QUERY_LENGTH = 500
MAX_CLAIM_LENGTH = 200
```

---

## Appendix: Example Workflows

### Workflow 1: Generate Single Section
```python
# User runs:
# acadwrite generate "CE Definition" --collection thesis -o section.md

# Internal flow:
client = FileIntelClient(config.fileintel.url)
llm = LLMClient(config.llm.provider, config.llm.model)
formatter = FormatterService()
generator = SectionGenerator(client, llm, formatter)

section = await generator.generate(
    heading="CE Definition",
    collection="thesis",
    style=WritingStyle.FORMAL
)

markdown = formatter.format_section(section)
Path("section.md").write_text(markdown)
```

### Workflow 2: Chapter Generation
```python
# User runs:
# acadwrite chapter outline.yaml --collection thesis

# Internal flow:
outline = Outline.from_yaml("outline.yaml")
processor = ChapterProcessor(generator, citation_mgr, formatter)

chapter = await processor.process(
    outline=outline,
    collection="thesis",
    parallel=3
)

# Write output
output_dir = Path("output")
output_dir.mkdir()

for i, section in enumerate(chapter.sections):
    path = output_dir / f"{i+1:02d}_{slugify(section.heading)}.md"
    path.write_text(formatter.format_section(section))

# Write bibliography
bib_path = output_dir / "bibliography.bib"
bib_path.write_text(
    citation_mgr.export(chapter.bibliography, ExportFormat.BIBTEX)
)
```

### Workflow 3: Counterargument Discovery
```python
# User runs:
# acadwrite contra "CE reduces time" --collection thesis

# Internal flow:
contra_gen = CounterargumentGenerator(client, llm, formatter)

report = await contra_gen.generate(
    claim="CE reduces time",
    collection="thesis",
    depth=AnalysisDepth.STANDARD,
    include_synthesis=True
)

markdown = formatter.format_counterargument_report(report)
print(markdown)
```

# Developer Guide

This guide is for developers who want to contribute to AcadWrite or understand its internals.

## 🏗️ Architecture Overview

AcadWrite follows a clean, layered architecture:

```
┌─────────────────────────────────────┐
│         CLI Layer (cli.py)          │
│   - Command parsing                 │
│   - User interaction                │
│   - Output formatting               │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Workflow Layer (workflows/)    │
│   - SectionGenerator                │
│   - ChapterProcessor                │
│   - CounterargumentGenerator        │
│   - CitationManager                 │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│     Service Layer (services/)       │
│   - FileIntelClient (RAG)           │
│   - LLMClient (claim inversion)     │
│   - FormatterService (citations)    │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Model Layer (models/)          │
│   - Data classes (Pydantic)         │
│   - Enums and types                 │
│   - Validation logic                │
└─────────────────────────────────────┘
```

## 📦 Key Components

### 1. CLI Layer (`cli.py`)

The CLI uses Typer for a modern, user-friendly interface:

- **Commands**: `generate`, `chapter`, `contra`, `citations`, `config`
- **Features**: Rich output, progress indicators, error handling
- **Pattern**: Each command has an async implementation function

Example:
```python
@app.command()
def generate(heading: str, collection: str, ...):
    asyncio.run(_generate_async(heading, collection, ...))

async def _generate_async(heading: str, collection: str, ...):
    async with FileIntelClient(...) as client:
        # Implementation
```

### 2. Workflow Layer (`workflows/`)

High-level business logic for academic writing tasks:

#### `SectionGenerator`
- Generates single academic section with citations
- Queries FileIntel, formats response
- Handles word limits, citation styles

#### `ChapterProcessor`
- Processes outline files (YAML/Markdown)
- Generates multiple sections recursively
- Deduplicates citations, creates bibliography

#### `CounterargumentGenerator`
- Inverts claims using LLM
- Queries for supporting/contradicting evidence
- Optional synthesis of findings

#### `CitationManager`
- Extracts citations from text (inline/footnote)
- Validates citation completeness
- Exports to BibTeX, RIS, JSON

### 3. Service Layer (`services/`)

External service integrations:

#### `FileIntelClient`
- Async HTTP client for FileIntel API
- Endpoints: `/health`, `/api/v2/collections`, `/api/v2/collections/{name}/query`
- Error handling with retries
- Response parsing to Pydantic models

#### `LLMClient`
- AsyncOpenAI client for LLM queries
- Supports OpenAI-compatible APIs (Ollama, vLLM)
- Used for claim inversion in counterargument analysis

#### `FormatterService`
- Citation format conversion (inline ↔ footnote)
- Citation deduplication
- Bibliography generation

### 4. Model Layer (`models/`)

Pydantic models for type safety and validation:

- **Query Models**: `Source`, `QueryResponse`
- **Section Models**: `Citation`, `AcademicSection`
- **Outline Models**: `OutlineItem`, `Outline`
- **Enums**: `WritingStyle`, `CitationStyle`, `AnalysisDepth`

## 🧪 Testing Strategy

### Test Organization

```
tests/
├── unit/                 # Unit tests with mocks
│   ├── test_models.py           # Model validation
│   ├── test_fileintel_client.py # Client with mocked HTTP
│   ├── test_formatters.py       # Citation formatting
│   ├── test_section_generator.py
│   ├── test_counterargument.py
│   ├── test_chapter_processor.py
│   └── test_citation_manager.py
└── integration/          # End-to-end tests (TBD)
```

### Testing Patterns

#### Mocking External Services

```python
@pytest.mark.asyncio
async def test_query_success(mock_httpx_client):
    mock_httpx_client.post.return_value = MockResponse(
        status_code=200,
        json_data={"success": True, "data": {...}}
    )

    client = FileIntelClient(base_url="http://test")
    client.client = mock_httpx_client

    result = await client.query("collection", "question")
    assert result.answer
```

#### Testing Workflows

```python
@pytest.mark.asyncio
async def test_generate_success():
    # Create mocks
    mock_fileintel = MagicMock()
    mock_formatter = FormatterService()

    # Set up mock response
    mock_fileintel.query.return_value = create_mock_query_response()

    # Test workflow
    generator = SectionGenerator(mock_fileintel, mock_formatter)
    section = await generator.generate("Test Heading", "test_collection")

    # Assertions
    assert section.heading == "Test Heading"
    assert len(section.citations) > 0
```

### Running Tests

```bash
# All tests
pytest tests/

# Specific file
pytest tests/unit/test_section_generator.py -v

# With coverage
pytest tests/ --cov=acadwrite --cov-report=html

# Watch mode (requires pytest-watch)
ptw tests/
```

## 🔧 Development Setup

### Prerequisites

- Python 3.11+
- Git
- Virtual environment tool (venv, virtualenv, or conda)

### Initial Setup

```bash
# Clone repository
git clone <repository-url>
cd acadwrite

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# Run tests to verify
pytest tests/
```

### Development Workflow

1. **Create feature branch**
   ```bash
   git checkout -b feature/new-feature
   ```

2. **Make changes**
   - Write code following existing patterns
   - Add type hints to all functions
   - Update tests

3. **Run checks**
   ```bash
   # Tests
   pytest tests/

   # Type checking
   mypy acadwrite/

   # Code formatting
   black acadwrite/ tests/

   # Linting
   ruff check acadwrite/
   ```

4. **Commit and push**
   ```bash
   git add .
   git commit -m "Add feature: description"
   git push origin feature/new-feature
   ```

## 📝 Code Style

### Python Style Guide

- **PEP 8**: Standard Python style guide
- **Black**: Auto-formatter (line length: 100)
- **Type hints**: Required for all public functions
- **Docstrings**: Google style for all public APIs

### Example

```python
async def generate_section(
    self,
    heading: str,
    collection: str,
    context: Optional[str] = None,
    max_words: int = 1000,
) -> AcademicSection:
    """Generate an academic section with citations.

    Args:
        heading: Section heading to generate content for
        collection: FileIntel collection name
        context: Optional context from previous section
        max_words: Maximum section length in words

    Returns:
        Generated academic section with citations

    Raises:
        FileIntelError: If FileIntel query fails
        ValueError: If heading is empty
    """
    if not heading:
        raise ValueError("Heading cannot be empty")

    # Implementation
    ...
```

## 🔌 Adding New Features

### Adding a New Workflow

1. **Create workflow file**
   ```python
   # acadwrite/workflows/my_workflow.py
   from acadwrite.services import FileIntelClient

   class MyWorkflow:
       def __init__(self, fileintel: FileIntelClient):
           self.fileintel = fileintel

       async def process(self, input: str) -> str:
           # Implementation
           pass
   ```

2. **Export from `__init__.py`**
   ```python
   # acadwrite/workflows/__init__.py
   from acadwrite.workflows.my_workflow import MyWorkflow

   __all__ = [..., "MyWorkflow"]
   ```

3. **Add CLI command**
   ```python
   # acadwrite/cli.py
   @app.command()
   def mycommand(input: str):
       """Description of command."""
       asyncio.run(_mycommand_async(input))

   async def _mycommand_async(input: str):
       async with FileIntelClient(...) as client:
           workflow = MyWorkflow(client)
           result = await workflow.process(input)
           console.print(result)
   ```

4. **Add tests**
   ```python
   # tests/unit/test_my_workflow.py
   class TestMyWorkflow:
       @pytest.mark.asyncio
       async def test_process(self):
           # Test implementation
           pass
   ```

### Adding a New Export Format

1. **Add export method to CitationManager**
   ```python
   def export_endnote(self, citations: List[Citation]) -> str:
       """Export citations to EndNote format."""
       # Implementation
       pass
   ```

2. **Update export method**
   ```python
   def export(self, citations: List[Citation], format: str) -> str:
       if format == "endnote":
           return self.export_endnote(citations)
       # ... existing formats
   ```

3. **Add tests**
   ```python
   def test_export_endnote(self):
       manager = CitationManager()
       citations = [...]
       endnote = manager.export_endnote(citations)
       assert "TY  -" in endnote  # EndNote format check
   ```

## 🐛 Debugging

### Debug Mode

Set environment variable for detailed logging:

```bash
export ACADWRITE_DEBUG=1
acadwrite generate "Test" --collection test
```

### Common Issues

#### 1. Import Errors

```python
# Check Python path
import sys
print(sys.path)

# Verify installation
pip list | grep acadwrite
```

#### 2. Async Issues

```python
# Use asyncio.run() for top-level async
asyncio.run(async_function())

# Not: await async_function()  # SyntaxError outside async
```

#### 3. Pydantic Validation Errors

```python
# Enable validation debugging
try:
    section = AcademicSection(heading="Test", ...)
except ValidationError as e:
    print(e.json())  # Detailed error info
```

## 📊 Performance Considerations

### Async Best Practices

- Use `async with` for clients
- Await all async operations
- Don't block event loop with sync I/O

### Memory Management

- Stream large files instead of loading entirely
- Close HTTP clients properly
- Use context managers

### Optimization Opportunities

- **Caching**: Cache FileIntel responses
- **Parallelization**: Generate sections in parallel
- **Batching**: Batch multiple queries

## 🔐 Security Considerations

### API Keys

- Never commit API keys
- Use environment variables
- Support `.env` files (add to `.gitignore`)

### Input Validation

- Validate all user input
- Sanitize file paths
- Check collection names

### Dependencies

- Keep dependencies updated
- Use `pip-audit` for security checks
- Pin versions in production

## 📦 Release Process

### Version Numbering

Follow Semantic Versioning (SemVer):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Release Checklist

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Run full test suite
4. Update README with new features
5. Create git tag
6. Build package: `python -m build`
7. Upload to PyPI: `twine upload dist/*`

## 🤝 Contributing Guidelines

### Before Contributing

1. Check existing issues
2. Discuss major changes first
3. Follow code style guide
4. Add tests for new features

### Pull Request Process

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Update documentation
5. Submit pull request
6. Address review comments

## 📚 Additional Resources

### Documentation

- [Typer Documentation](https://typer.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [pytest Documentation](https://docs.pytest.org/)
- [httpx Documentation](https://www.python-httpx.org/)

### Project-Specific Docs

- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [FILEINTEL_API_VERIFIED.md](FILEINTEL_API_VERIFIED.md) - FileIntel API
- [development_roadmap.md](development_roadmap.md) - Roadmap

## 💡 Tips and Tricks

### Quick Commands

```bash
# Format code
black acadwrite/ tests/

# Check types
mypy acadwrite/

# Run tests with coverage
pytest tests/ --cov=acadwrite --cov-report=term-missing

# Profile performance
python -m cProfile -o output.pstats script.py
```

### VS Code Setup

```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true
}
```

## ❓ FAQ

**Q: How do I add a new citation style?**
A: Implement a new format method in `FormatterService` and update the CLI options.

**Q: Can I use a different LLM provider?**
A: Yes! The LLMClient supports any OpenAI-compatible API. Update the `base_url` in config.

**Q: How do I contribute tests?**
A: Add tests in `tests/unit/` following existing patterns. Use mocks for external services.

---

**Happy coding!** 🚀

For questions, open an issue on GitHub or contact the maintainers.

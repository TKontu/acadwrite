# AcadWrite - Academic Writing Assistant

An academic writing CLI tool that generates properly cited content using FileIntel's RAG platform.

[![Tests](https://img.shields.io/badge/tests-110%20passing-brightgreen)](tests/)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-TBD-lightgrey)](LICENSE)

## 📊 Project Status

**Status**: 🚀 **Day 8/11 Complete** (MVP Core Features Ready)

- ✅ **110 tests passing** | ~5,400 lines of code | 85%+ test coverage
- ✅ All core workflows implemented and tested
- ✅ Full CLI with 7 commands
- ✅ Documentation complete (README, Developer Guide, Examples)
- ✅ Code quality verified (Black formatted)

### ✅ Completed Features

- ✅ **Section Generation** - Generate academic sections with citations
- ✅ **Chapter Processing** - Convert YAML/Markdown outlines into complete chapters
- ✅ **Counterargument Analysis** - Find supporting and contradicting evidence
- ✅ **Citation Management** - Extract, validate, and export citations (BibTeX, RIS, JSON)
- ✅ FileIntel RAG client with verified API
- ✅ LLM integration (OpenAI-compatible APIs)
- ✅ Citation formatting (inline/footnote)

## 🎯 What AcadWrite Does

AcadWrite helps academic writers by:

1. **Generating cited content** from your research corpus using RAG (Retrieval-Augmented Generation)
2. **Processing outlines** into complete chapters with proper citations
3. **Finding counterarguments** to strengthen your arguments
4. **Managing citations** across your documents

All content is generated from **your own document collection** using FileIntel's hybrid RAG platform.

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **FileIntel** running at http://localhost:8000
- **OpenAI API key** or compatible LLM server (for counterargument analysis)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd acadwrite
   ```

2. Create virtual environment and install:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```

3. Configure AcadWrite:
   ```bash
   mkdir -p ~/.acadwrite
   cp examples/config.example.yaml ~/.acadwrite/config.yaml
   # Edit config.yaml with your settings
   ```

4. Set your API key:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

### Basic Usage

#### Generate a Section

```bash
acadwrite generate "Definition of Agile Development" \
  --collection thesis_sources \
  --output section.md
```

#### Generate a Full Chapter

```bash
acadwrite chapter examples/outlines/chapter_outline.yaml \
  --collection thesis_sources \
  --output-dir chapter2/
```

#### Find Counterarguments

```bash
acadwrite contra "Agile improves development speed" \
  --collection thesis_sources \
  --output counterargument.md
```

#### Manage Citations

```bash
# Extract citations to BibTeX
acadwrite citations extract chapter2/combined.md --format bibtex -o refs.bib

# Check citation integrity
acadwrite citations check chapter2/combined.md --strict

# Find duplicate citations
acadwrite citations dedupe chapter2/combined.md
```

## 📖 Command Reference

### `generate` - Generate Single Section

Generate an academic section with citations from a heading.

```bash
acadwrite generate HEADING \
  --collection COLLECTION_NAME \
  [--output FILE] \
  [--style formal|technical|accessible] \
  [--citation-style inline|footnote] \
  [--max-words 1000] \
  [--max-sources 10]
```

**Options:**
- `HEADING`: Section heading (e.g., "Literature Review")
- `--collection`, `-c`: FileIntel collection name (required)
- `--output`, `-o`: Output file path (default: stdout)
- `--context`: Previous section context for coherence
- `--style`: Writing style (default: formal)
- `--citation-style`: Citation format (default: inline)
- `--max-words`: Maximum section length (default: 1000)
- `--max-sources`: Maximum sources to use

### `chapter` - Generate Chapter from Outline

Generate multiple sections from a YAML or Markdown outline.

```bash
acadwrite chapter OUTLINE_FILE \
  --collection COLLECTION_NAME \
  [--output-dir DIR] \
  [--single-file] \
  [--style formal|technical|accessible] \
  [--citation-style inline|footnote]
```

**Options:**
- `OUTLINE_FILE`: Path to YAML or Markdown outline
- `--collection`, `-c`: FileIntel collection name (required)
- `--output-dir`, `-o`: Output directory (default: ./output)
- `--single-file`: Combine all sections into one file
- `--style`: Writing style (default: formal)
- `--citation-style`: Citation format (default: footnote)
- `--max-words`: Max words per section (default: 1000)
- `--continue-on-error`: Continue if a section fails

**Outputs:**
- Individual section files (unless `--single-file`)
- Combined chapter file (if `--single-file`)
- `bibliography.bib` - BibTeX citations
- `metadata.json` - Chapter statistics

### `contra` - Find Counterarguments

Discover supporting and contradicting evidence for a claim.

```bash
acadwrite contra "CLAIM" \
  --collection COLLECTION_NAME \
  [--output FILE] \
  [--depth quick|standard|deep] \
  [--synthesis] \
  [--max-sources 5]
```

**Options:**
- `CLAIM`: Statement to analyze
- `--collection`, `-c`: FileIntel collection name (required)
- `--output`, `-o`: Output file path (default: stdout)
- `--depth`: Analysis depth (default: standard)
- `--synthesis`: Include LLM synthesis of findings
- `--max-sources`: Max sources per side (default: 5)

**Output includes:**
- Original and inverted claims
- Supporting evidence with sources
- Contradicting evidence with sources
- Optional synthesis of findings

### `citations` - Citation Management

Subcommands for working with citations.

#### Extract Citations

```bash
acadwrite citations extract FILE \
  [--format bibtex|ris|json] \
  [--output FILE]
```

Extract citations from markdown and export in various formats.

#### Check Citations

```bash
acadwrite citations check FILE [--strict]
```

Validate citations for completeness (author, year, page numbers).

#### Deduplicate Citations

```bash
acadwrite citations dedupe FILE [--in-place]
```

Find and optionally remove duplicate citations.

### `config` - Configuration

```bash
acadwrite config show    # Show current configuration
acadwrite config check   # Verify configuration
```

## 📁 Project Structure

```
acadwrite/
├── acadwrite/           # Main package
│   ├── cli.py          # Command-line interface
│   ├── config.py       # Configuration management
│   ├── models/         # Data models
│   ├── services/       # External service clients
│   │   ├── fileintel.py    # FileIntel RAG client
│   │   ├── llm.py          # LLM client
│   │   └── formatter.py    # Citation formatting
│   └── workflows/      # Core workflows
│       ├── section_generator.py
│       ├── chapter_processor.py
│       ├── counterargument.py
│       └── citation_manager.py
├── tests/              # Test suite (110 tests)
├── examples/           # Example files and usage
└── docs/               # Planning and architecture docs
```

## 🎨 Examples

See the [`examples/`](examples/) directory for:
- Sample outlines (YAML and Markdown)
- Configuration templates
- Usage examples and tips

## 🔧 Configuration

AcadWrite can be configured via:

1. **Config file**: `~/.acadwrite/config.yaml`
2. **Environment variables**: Override any setting
3. **Command-line options**: Override per-command

Example configuration:

```yaml
fileintel:
  base_url: "http://localhost:8000"
  timeout: 30
  max_retries: 3

llm:
  provider: "openai"
  base_url: "http://localhost:8000/v1"  # Or OpenAI API
  model: "gpt-4"
  api_key: "${OPENAI_API_KEY}"
  temperature: 0.7

writing:
  citation_style: "footnote"
  style: "formal"
  max_words: 1000
```

## 🧪 Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=acadwrite --cov-report=html

# Run specific test file
pytest tests/unit/test_section_generator.py -v
```

**Current test status**: 110 tests passing ✅

## 🏗️ Architecture

AcadWrite is built on a clean, layered architecture:

- **CLI Layer**: Typer-based command-line interface
- **Workflow Layer**: High-level academic writing workflows
- **Service Layer**: External service integrations (FileIntel, LLM)
- **Model Layer**: Pydantic data models for type safety

Key design principles:
- **Async-first**: Non-blocking I/O for external services
- **Type-safe**: Full type hints and Pydantic validation
- **Testable**: Comprehensive test coverage with mocks
- **Configurable**: Flexible configuration system

See [ARCHITECTURE.md](ARCHITECTURE.md) for details.

## 📚 Documentation

- **[Examples](examples/README.md)**: Usage examples and quick starts
- **[ARCHITECTURE.md](ARCHITECTURE.md)**: System architecture
- **[AGENT_TODO_LIST.md](AGENT_TODO_LIST.md)**: Development progress
- **[FILEINTEL_API_VERIFIED.md](FILEINTEL_API_VERIFIED.md)**: FileIntel API reference
- **[development_roadmap.md](development_roadmap.md)**: Development timeline

## 🤝 Contributing

This project is currently in active development. Contributions will be welcome once we reach v1.0.

## 🔬 Tech Stack

- **Python 3.11+**: Modern Python with async/await
- **Typer**: CLI framework with rich formatting
- **httpx**: Async HTTP client
- **Pydantic**: Data validation and settings
- **PyYAML**: Outline parsing
- **OpenAI SDK**: LLM integration
- **pytest**: Testing framework

## 📋 Requirements

### System Requirements
- Python 3.11 or higher
- 100MB disk space
- Internet connection (for LLM API)

### External Services
- **FileIntel**: RAG platform for document retrieval
  - Must be running and accessible
  - Collection with your documents
- **LLM API**: OpenAI or compatible API
  - For counterargument analysis
  - Optional for basic features

## 🗺️ Roadmap

### Current Release (v0.1.0 - MVP)
- ✅ Section generation
- ✅ Chapter processing
- ✅ Counterargument analysis
- ✅ Citation management
- ⏳ Documentation completion

### Future Releases

**v0.2.0** - Enhancements
- Parallel section generation
- LaTeX output format
- Advanced citation styles (APA, MLA, Chicago)
- Caching layer for performance

**v0.3.0** - Integrations
- Reference manager integration (Zotero)
- Web UI (Streamlit/Gradio)
- Multi-language support
- Content revision suggestions

**v1.0.0** - Production Ready
- 95%+ test coverage
- Performance optimization
- Comprehensive documentation
- Security audit

## ❓ Troubleshooting

### FileIntel Connection Errors

```bash
# Check FileIntel is running
curl http://localhost:8000/health

# Verify configuration
acadwrite config show
```

### Missing API Key

```bash
# Set environment variable
export OPENAI_API_KEY="sk-..."

# Or add to config file
nano ~/.acadwrite/config.yaml
```

### Collection Not Found

The error message will list available collections. Ensure you're using the correct collection name.

## 📝 License

TBD

## 🙏 Acknowledgments

- **FileIntel**: Hybrid RAG platform powering document retrieval
- **OpenAI**: LLM capabilities for claim inversion and synthesis
- Built with ❤️ for academic writers

## 📧 Contact

For questions and support, please open an issue on GitHub.

---

**Ready to transform your academic writing workflow?** Get started with the [Quick Start](#-quick-start) guide!

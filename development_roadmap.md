# AcademicWrite - Development Roadmap

**📊 Current Progress: Day 6/11 Complete** | See `AGENT_TODO_LIST.md` for detailed status

## Project Timeline: 11 Days to MVP

This roadmap breaks down the development into manageable phases with clear deliverables and acceptance criteria.

**Note:** This is the original reference plan. For implementation progress with checkmarks, see `AGENT_TODO_LIST.md`.

---

## Phase 1: Foundation (Days 1-2)

### Day 1: Project Setup & Configuration

**Goals:**
- Initialize project structure
- Set up development environment
- Create configuration system
- Build basic CLI skeleton

**Tasks:**

1. **Project Initialization** (1 hour)
   - [ ] Create directory structure
   - [ ] Initialize git repository
   - [ ] Set up pyproject.toml with dependencies
   - [ ] Create virtual environment

2. **Configuration Module** (2 hours)
   - [ ] Implement `config.py` with Pydantic Settings
   - [ ] Support YAML config file loading
   - [ ] Environment variable override
   - [ ] Create default config template

3. **CLI Framework** (2 hours)
   - [ ] Set up Typer application
   - [ ] Create command structure (generate, chapter, contra, citations, config)
   - [ ] Add help text and argument descriptions
   - [ ] Test `--help` works for all commands

4. **Logging Setup** (1 hour)
   - [ ] Configure structlog
   - [ ] Create log formatters
   - [ ] Add console and file handlers
   - [ ] Test log levels

**Deliverables:**
- Working CLI with `--help` output
- Configuration can be loaded and displayed
- Clean directory structure

**Acceptance Criteria:**
```bash
# These should work:
acadwrite --help
acadwrite config show
acadwrite generate --help
acadwrite chapter --help
```

---

### Day 2: Data Models

**Goals:**
- Implement core data structures
- Create model parsers
- Unit test all models

**Tasks:**

1. **Query Models** (2 hours)
   - [ ] Implement `Source` dataclass
   - [ ] Implement `QueryResult` dataclass
   - [ ] Add `from_fileintel_response()` parser
   - [ ] Unit tests for parsing

2. **Section Models** (2 hours)
   - [ ] Implement `Citation` dataclass
   - [ ] Implement `AcademicSection` dataclass
   - [ ] Add helper methods (word_count, all_citations)
   - [ ] Add citation formatters (to_footnote, to_bibtex)
   - [ ] Unit tests

3. **Outline Models** (3 hours)
   - [ ] Implement `OutlineItem` dataclass
   - [ ] Implement `Outline` dataclass
   - [ ] Add YAML parser
   - [ ] Add Markdown parser
   - [ ] Unit tests for both formats

4. **Enum Definitions** (1 hour)
   - [ ] Define `WritingStyle` enum
   - [ ] Define `CitationStyle` enum
   - [ ] Define `AnalysisDepth` enum
   - [ ] Define `OutputFormat` enum

**Deliverables:**
- Complete models package
- > 80% test coverage on models
- Example outline files (YAML and Markdown)

**Acceptance Criteria:**
```python
# These should work:
from acadwrite.models.outline import Outline
outline = Outline.from_yaml("test.yaml")
outline = Outline.from_markdown("test.md")

from acadwrite.models.section import AcademicSection, Citation
section = AcademicSection(heading="Test", level=2, content="...")
assert section.word_count() > 0
```

---

## Phase 2: External Services (Days 3-4)

### Day 3: FileIntel Client

**Goals:**
- Implement HTTP client for FileIntel
- Handle errors gracefully
- Test with real FileIntel instance

**Tasks:**

1. **Client Implementation** (3 hours)
   - [ ] Create `FileIntelClient` class
   - [ ] Implement `query()` method
   - [ ] Implement `list_collections()` method
   - [ ] Implement `health_check()` method
   - [ ] Add async context manager support

2. **Response Parsing** (2 hours)
   - [ ] Parse FileIntel response format
   - [ ] Extract sources correctly
   - [ ] Handle page numbers
   - [ ] Parse relevance scores

3. **Error Handling** (2 hours)
   - [ ] Define exception hierarchy
   - [ ] Handle connection errors
   - [ ] Handle 404 (collection not found)
   - [ ] Handle timeouts
   - [ ] Add retry logic with exponential backoff

4. **Testing** (1 hour)
   - [ ] Unit tests with mocked responses
   - [ ] Integration tests with real FileIntel
   - [ ] Test error scenarios

**Deliverables:**
- Working FileIntel client
- Comprehensive error handling
- Integration tests pass

**Acceptance Criteria:**
```python
# Should work:
async with FileIntelClient("http://localhost:8000") as client:
    result = await client.query("thesis_sources", "test query")
    assert result.answer
    assert len(result.sources) > 0
```

---

### Day 4: LLM Client & Formatter

**Goals:**
- Implement LLM client for OpenAI/Anthropic
- Create formatting service
- Test claim inversion

**Tasks:**

1. **LLM Client** (3 hours)
   - [ ] Create `LLMClient` class
   - [ ] Support OpenAI provider
   - [ ] Support Anthropic provider
   - [ ] Implement `invert_claim()` method
   - [ ] Add temperature and token controls

2. **Prompt Templates** (1 hour)
   - [ ] Create claim inversion prompt
   - [ ] Create synthesis prompt
   - [ ] Create refinement prompt
   - [ ] Store in `prompts/` module

3. **Formatter Service** (2 hours)
   - [ ] Create `FormatterService` class
   - [ ] Implement `format_section()` for markdown
   - [ ] Implement `convert_inline_to_footnotes()`
   - [ ] Add citation numbering logic

4. **Testing** (2 hours)
   - [ ] Unit tests for formatters
   - [ ] Integration tests with real LLM APIs
   - [ ] Test claim inversion quality
   - [ ] Verify markdown output format

**Deliverables:**
- LLM client supporting multiple providers
- Formatter service with markdown output
- Tested prompt templates

**Acceptance Criteria:**
```python
# Should work:
llm = LLMClient(provider="openai")
inverted = await llm.invert_claim("CE reduces time")
assert inverted != "CE reduces time"

formatter = FormatterService()
markdown = formatter.format_section(section)
assert "##" in markdown  # Has heading
assert "[^1]" in markdown  # Has footnotes
```

---

## Phase 3: Core Workflows (Days 5-7)

### Day 5: Section Generator

**Goals:**
- Implement section generation workflow
- Wire up to CLI
- Test end-to-end generation

**Tasks:**

1. **Section Generator** (3 hours)
   - [ ] Create `SectionGenerator` class
   - [ ] Implement `generate()` method
   - [ ] Query FileIntel for content
   - [ ] Extract and format citations
   - [ ] Handle word count limits

2. **Citation Extraction** (2 hours)
   - [ ] Parse citations from FileIntel sources
   - [ ] Convert to footnote format
   - [ ] Number citations sequentially
   - [ ] Handle duplicate authors

3. **CLI Integration** (2 hours)
   - [ ] Wire up `generate` command
   - [ ] Add progress indicators
   - [ ] Support output to file or stdout
   - [ ] Add error messages

4. **Testing** (1 hour)
   - [ ] End-to-end test with real FileIntel
   - [ ] Test CLI command
   - [ ] Verify output format
   - [ ] Test error handling

**Deliverables:**
- Working `acadwrite generate` command
- Properly formatted markdown output
- Citations in footnote format

**Acceptance Criteria:**
```bash
# Should work:
acadwrite generate "Definition of CE" \
  --collection thesis_sources \
  --output section.md

# section.md should contain:
# - Proper heading
# - Content with [^1] style citations
# - Footnote bibliography
```

---

### Day 6: Counterargument Generator

**Goals:**
- Implement counterargument discovery
- Test claim inversion quality
- Format comparative reports

**Tasks:**

1. **Counterargument Workflow** (3 hours)
   - [ ] Create `CounterargumentGenerator` class
   - [ ] Implement `generate()` method
   - [ ] Query for supporting evidence
   - [ ] Invert claim with LLM
   - [ ] Query for contradicting evidence

2. **Report Formatting** (2 hours)
   - [ ] Create `CounterargumentReport` dataclass
   - [ ] Format supporting section
   - [ ] Format contradicting section
   - [ ] Add analysis depth support

3. **CLI Integration** (2 hours)
   - [ ] Wire up `contra` command
   - [ ] Add depth option (quick/standard/deep)
   - [ ] Add synthesis option
   - [ ] Format output

4. **Testing** (1 hour)
   - [ ] Test with sample claims
   - [ ] Verify inversion quality
   - [ ] Test all depth levels
   - [ ] Check report format

**Deliverables:**
- Working `acadwrite contra` command
- Structured counterargument reports
- Multiple analysis depths

**Acceptance Criteria:**
```bash
# Should work:
acadwrite contra "CE reduces development time" \
  --collection thesis_sources \
  --depth standard \
  --output counter.md

# counter.md should have:
# - Original claim
# - Supporting evidence section
# - Contradicting evidence section
# - Proper formatting
```

---

### Day 7: Chapter Processor

**Goals:**
- Implement outline processing
- Generate multi-section chapters
- Handle bibliography deduplication

**Tasks:**

1. **Chapter Processor** (4 hours)
   - [ ] Create `ChapterProcessor` class
   - [ ] Implement `process()` method
   - [ ] Process outline items recursively
   - [ ] Maintain context between sections
   - [ ] Track citations across sections

2. **Citation Management** (2 hours)
   - [ ] Deduplicate citations
   - [ ] Renumber footnotes globally
   - [ ] Generate unified bibliography
   - [ ] Export to BibTeX

3. **CLI Integration** (1 hour)
   - [ ] Wire up `chapter` command
   - [ ] Support single-file output
   - [ ] Support multi-file output
   - [ ] Add metadata file

4. **Testing** (1 hour)
   - [ ] Test with sample outline
   - [ ] Verify section hierarchy
   - [ ] Check citation deduplication
   - [ ] Test both output modes

**Deliverables:**
- Working `acadwrite chapter` command
- Outline processing (YAML and Markdown)
- Citation deduplication
- Bibliography generation

**Acceptance Criteria:**
```bash
# Should work:
acadwrite chapter outline.yaml \
  --collection thesis_sources \
  --output-dir chapter3/

# Should create:
# - chapter3/sections/*.md (individual sections)
# - chapter3/bibliography.bib
# - chapter3/metadata.json

# Or single file:
acadwrite chapter outline.yaml \
  --collection thesis_sources \
  --single-file \
  --output chapter3.md
```

---

## Phase 4: Polish & Testing (Days 8-9)

### Day 8: Citation Utilities

**Goals:**
- Implement citation extraction
- Add citation checking
- Support multiple export formats

**Tasks:**

1. **Citation Manager** (3 hours)
   - [ ] Create `CitationManager` class
   - [ ] Implement `extract_from_text()`
   - [ ] Implement `check_citations()`
   - [ ] Implement `deduplicate()`
   - [ ] Implement `export()` for multiple formats

2. **Export Formats** (2 hours)
   - [ ] BibTeX exporter
   - [ ] RIS exporter
   - [ ] JSON exporter
   - [ ] EndNote exporter (basic)

3. **CLI Integration** (2 hours)
   - [ ] Wire up `citations extract` command
   - [ ] Wire up `citations check` command
   - [ ] Wire up `citations dedupe` command
   - [ ] Add format options

4. **Testing** (1 hour)
   - [ ] Test extraction from generated docs
   - [ ] Test all export formats
   - [ ] Test citation checking
   - [ ] Test deduplication

**Deliverables:**
- Citation extraction utilities
- Multiple export formats
- Citation verification tool

**Acceptance Criteria:**
```bash
# Should work:
acadwrite citations extract chapter.md --format bibtex
acadwrite citations check chapter.md --strict
acadwrite citations dedupe chapter.md --in-place
```

---

### Day 9: Integration Testing & Bug Fixes

**Goals:**
- Comprehensive integration testing
- Fix discovered bugs
- Improve error messages

**Tasks:**

1. **Integration Test Suite** (3 hours)
   - [ ] End-to-end section generation test
   - [ ] End-to-end chapter generation test
   - [ ] End-to-end counterargument test
   - [ ] Test with different collections
   - [ ] Test error scenarios

2. **Bug Fixes** (3 hours)
   - [ ] Fix FileIntel response parsing issues
   - [ ] Fix citation numbering bugs
   - [ ] Fix outline parsing edge cases
   - [ ] Fix CLI argument validation

3. **Error Handling Improvements** (2 hours)
   - [ ] Better error messages
   - [ ] Add suggestions to errors
   - [ ] Graceful degradation
   - [ ] Partial result saving

**Deliverables:**
- Passing integration test suite
- Robust error handling
- Bug-free core workflows

**Acceptance Criteria:**
```bash
# All integration tests pass
pytest tests/integration/ -v

# Commands handle errors gracefully
acadwrite generate "Test" --collection nonexistent
# Should show: "Collection 'nonexistent' not found. 
# Available: thesis_sources, ..."
```

---

## Phase 5: Documentation & Release (Days 10-11)

### Day 10: Documentation

**Goals:**
- Write comprehensive documentation
- Create usage examples
- Document API

**Tasks:**

1. **README** (2 hours)
   - [ ] Project overview
   - [ ] Installation instructions
   - [ ] Quick start guide
   - [ ] Basic examples
   - [ ] Requirements

2. **User Guide** (3 hours)
   - [ ] Configuration guide
   - [ ] Command reference
   - [ ] Outline format guide
   - [ ] Citation management guide
   - [ ] Troubleshooting section

3. **Example Workflows** (2 hours)
   - [ ] Generate single section
   - [ ] Generate full chapter
   - [ ] Find counterarguments
   - [ ] Extract citations
   - [ ] Complete thesis workflow

4. **API Documentation** (1 hour)
   - [ ] Document main classes
   - [ ] Add docstring examples
   - [ ] Generate API docs with Sphinx

**Deliverables:**
- Complete README
- User guide
- API documentation
- Example files

**Acceptance Criteria:**
- New user can set up and use in < 10 minutes
- All commands documented with examples
- API docs generated

---

### Day 11: Release Preparation

**Goals:**
- Package for distribution
- Set up CI/CD
- Create release

**Tasks:**

1. **Packaging** (2 hours)
   - [ ] Verify pyproject.toml
   - [ ] Build wheel and sdist
   - [ ] Test installation from wheel
   - [ ] Create Dockerfile (optional)

2. **CI/CD Setup** (2 hours)
   - [ ] Set up GitHub Actions
   - [ ] Add test workflow
   - [ ] Add lint workflow
   - [ ] Add release workflow

3. **Release** (2 hours)
   - [ ] Tag version 0.1.0
   - [ ] Publish to TestPyPI
   - [ ] Test installation from TestPyPI
   - [ ] Publish to PyPI

4. **Announcement** (2 hours)
   - [ ] Write release notes
   - [ ] Create demo video/GIF
   - [ ] Post to relevant communities
   - [ ] Update project website

**Deliverables:**
- Published package on PyPI
- GitHub release with notes
- Working CI/CD pipeline

**Acceptance Criteria:**
```bash
# Should work from anywhere:
pip install acadwrite
acadwrite --version  # Shows 0.1.0
acadwrite --help
```

---

## Post-MVP Roadmap

### Version 0.2.0 (Weeks 2-3)

**Enhancements:**
- [ ] Parallel section generation
- [ ] Improved context management
- [ ] LaTeX output format
- [ ] Interactive configuration wizard
- [ ] Progress bars for long operations

### Version 0.3.0 (Weeks 4-5)

**Features:**
- [ ] Reference manager integration (Zotero)
- [ ] Advanced citation styles (APA, MLA, Chicago)
- [ ] Content revision suggestions
- [ ] Multi-language support
- [ ] Web UI (Streamlit/Gradio)

### Version 1.0.0 (Weeks 6-8)

**Production-Ready:**
- [ ] 95%+ test coverage
- [ ] Performance optimization
- [ ] Caching layer
- [ ] Rate limiting
- [ ] Comprehensive error recovery
- [ ] User analytics
- [ ] Security audit

---

## Risk Management

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| FileIntel API changes | High | Version pinning, integration tests |
| LLM API rate limits | Medium | Rate limiting, backoff, caching |
| Citation parsing errors | High | Extensive testing, fallback formats |
| Outline parsing edge cases | Medium | Schema validation, examples |
| Memory issues with large chapters | Low | Streaming, chunking |

### Project Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Scope creep | High | Strict MVP definition, backlog |
| Underestimated complexity | Medium | Buffer time, iterative approach |
| Dependency issues | Low | Lock files, virtual environments |
| Poor error messages | Medium | User testing, feedback loop |

---

## Success Metrics

### MVP Success (By Day 11)

- [ ] Can generate 10-section chapter in < 5 minutes
- [ ] Citation accuracy > 95%
- [ ] Zero data loss on errors
- [ ] Setup time < 5 minutes for new users
- [ ] All core commands working
- [ ] > 80% test coverage

### Post-MVP Success (By Week 4)

- [ ] 100+ users
- [ ] 5+ GitHub stars
- [ ] 10+ PyPI downloads/day
- [ ] 0 critical bugs
- [ ] 2+ community contributions

---

## Daily Standup Template

Use this template for daily progress tracking:

```markdown
## Day X Standup

**Yesterday:**
- ✅ Completed: [task]
- ⏳ In Progress: [task]
- ❌ Blocked: [issue]

**Today:**
- 🎯 Focus: [main goal]
- 📋 Tasks:
  - [ ] Task 1
  - [ ] Task 2
  - [ ] Task 3

**Blockers:**
- None / [blocker description]

**Notes:**
- [Any important observations or decisions]
```

---

## Definition of Done

A task is "done" when:
- [ ] Code is written and follows style guide
- [ ] Unit tests pass (> 80% coverage)
- [ ] Integration tests pass (if applicable)
- [ ] Documentation is updated
- [ ] Code is reviewed (self-review minimum)
- [ ] No known bugs
- [ ] Merged to main branch

---

## Resources

### External Dependencies
- FileIntel: http://localhost:8000
- OpenAI API: https://platform.openai.com/
- Anthropic API: https://console.anthropic.com/

### Documentation
- Typer: https://typer.tiangolo.com/
- Pydantic: https://docs.pydantic.dev/
- HTTPX: https://www.python-httpx.org/

### Tools
- GitHub Issues: Track bugs and features
- GitHub Projects: Kanban board for tasks
- Discord/Slack: Team communication (if applicable)

---

## How to Use This Roadmap

### For Solo Development
1. Review entire roadmap before starting
2. Break each day into 2-hour work blocks
3. Track progress with checkboxes
4. Update daily standup notes
5. Adjust timeline if needed

### For Agent Development
1. Feed each day's tasks as context
2. Verify acceptance criteria after each day
3. Use deliverables as checkpoints
4. Run tests before proceeding to next phase
5. Document any deviations

### For Team Development
1. Assign days to team members
2. Daily standup meetings
3. Code reviews at end of each phase
4. Integration testing as a team
5. Weekly retrospectives

---

## Quick Reference: Day-by-Day Checklist

- [ ] **Day 1**: Project setup, config, basic CLI
- [ ] **Day 2**: All data models with tests
- [ ] **Day 3**: FileIntel client working
- [ ] **Day 4**: LLM client and formatter
- [ ] **Day 5**: Section generator + CLI
- [ ] **Day 6**: Counterargument generator
- [ ] **Day 7**: Chapter processor
- [ ] **Day 8**: Citation utilities
- [ ] **Day 9**: Integration tests + fixes
- [ ] **Day 10**: Documentation complete
- [ ] **Day 11**: Released to PyPI

🎉 **MVP Complete!**

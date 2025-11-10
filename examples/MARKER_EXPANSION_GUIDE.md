# AcadWrite Marker Expansion Guide

**Interactive markdown editing with AcadWrite**

This guide shows you how to use AcadWrite's marker-based expansion feature to interactively write academic documents in any markdown editor.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Marker Syntax](#marker-syntax)
3. [Operations](#operations)
4. [Examples](#examples)
5. [Workflow Tips](#workflow-tips)
6. [Editor Integration](#editor-integration)

---

## Quick Start

### 1. Add Markers to Your Markdown

Edit your document in any editor (VS Code, Vim, Obsidian, etc.):

```markdown
# My Research Paper

## Introduction

<!-- ACADWRITE: expand -->
- Topic: Concurrent engineering in product development
- Focus: Time-to-market reduction
- Include: Key benefits and challenges
<!-- END ACADWRITE -->

## Methods

...
```

### 2. Expand Markers

Run the expand command:

```bash
acadwrite expand paper.md -c research_papers
```

### 3. Result

Your markers are replaced with generated, cited content:

```markdown
# My Research Paper

## Introduction

Concurrent engineering (CE) represents a systematic approach to integrated product development that emphasizes parallel rather than sequential design processes (Smith, 2020, p.45). This methodology has been shown to significantly reduce time-to-market by enabling simultaneous work across different functional areas (Johnson & Lee, 2019, p.112).

The key benefits of concurrent engineering include shortened development cycles, improved product quality through early problem detection, and enhanced communication between teams (Williams, 2021, p.78). However, implementation challenges persist, particularly regarding coordination complexity and the need for robust information management systems (Brown, 2018, p.203).

## Methods

...
```

---

## Marker Syntax

### Basic Structure

```markdown
<!-- ACADWRITE: operation [params] -->
content or hints
<!-- END ACADWRITE -->
```

### Components

- **Operation**: What you want AcadWrite to do (`expand`, `evidence`, `citations`, `clarity`, `contradict`)
- **Params** (optional): Space-separated `key=value` pairs
- **Content**: Instructions, bullet points, or existing text (depends on operation)

### Available Parameters

All operations support:
- **`type`** or **`search_type`**: Search method - `vector`, `graph`, `adaptive`, `global`, `local`
  - `vector`: Fast semantic search (best for factual questions)
  - `graph`: Knowledge graph search (best for relationships)
  - `adaptive`: LLM auto-selects best method (recommended, default)
  - `global`: GraphRAG global summaries (for broad themes across all documents)
  - `local`: GraphRAG local analysis (for specific entities and details)

- **`format`** or **`answer_format`**: Output format - `default`, `table`, `list`, `json`, `essay`, `markdown`
  - `default`: Standard prose (default)
  - `table`: Markdown table format
  - `list`: Bulleted or numbered list
  - `json`: Structured JSON data
  - `essay`: Multi-paragraph detailed analysis
  - `markdown`: Rich markdown formatting

Expand operation also supports:
- **`max_words`**: Maximum words to generate (default: 500)

### Examples with Parameters

```markdown
<!-- ACADWRITE: expand max_words=300 -->
- Brief overview of design for manufacturing
<!-- END ACADWRITE -->

<!-- ACADWRITE: expand type=global format=table -->
Compare machine learning approaches
<!-- END ACADWRITE -->

<!-- ACADWRITE: evidence format=list -->
Key findings from climate research
<!-- END ACADWRITE -->

<!-- ACADWRITE: expand type=graph -->
Relationship between neural networks and deep learning
<!-- END ACADWRITE -->
```

---

## Operations

### 1. `expand` - Generate New Content

**Purpose**: Create new content from scratch based on topic hints

**Syntax**:
```markdown
<!-- ACADWRITE: expand -->
- Topic: Your topic here
- Focus: Specific aspects to emphasize
- Include: Points to cover
<!-- END ACADWRITE -->
```

**Parameters**:
- `max_words=N`: Limit output to approximately N words (default: from config)

**Example**:
```markdown
## Literature Review

<!-- ACADWRITE: expand max_words=500 -->
- Topic: Machine learning in healthcare diagnostics
- Focus: Medical imaging applications
- Include: Recent advances, accuracy improvements, challenges
<!-- END ACADWRITE -->
```

**Result**: Generates ~500 words of cited content about ML in medical imaging.

---

### 2. `evidence` - Add Supporting Evidence

**Purpose**: Add supporting evidence and citations to existing claims

**Syntax**:
```markdown
<!-- ACADWRITE: evidence -->
Your existing claim or paragraph
<!-- END ACADWRITE -->
```

**Example**:
```markdown
## Discussion

<!-- ACADWRITE: evidence -->
Concurrent engineering can reduce product development time by up to 50% compared to traditional sequential approaches.
<!-- END ACADWRITE -->
```

**Result**: Keeps your text and adds supporting evidence with citations.

---

### 3. `citations` - Add Citations to Text

**Purpose**: Find and insert citations for existing text

**Syntax**:
```markdown
<!-- ACADWRITE: citations -->
Your existing text that needs citations
<!-- END ACADWRITE -->
```

**Example**:
```markdown
<!-- ACADWRITE: citations -->
The adoption of agile methodologies has increased significantly in software development over the past decade, with most teams reporting improved productivity and product quality.
<!-- END ACADWRITE -->
```

**Result**: Returns text with inline citations added to support claims.

---

### 4. `clarity` - Improve Text Clarity

**Purpose**: Use LLM to improve readability while preserving meaning and citations

**Syntax**:
```markdown
<!-- ACADWRITE: clarity -->
Your complex or unclear text
<!-- END ACADWRITE -->
```

**Requirements**: Requires LLM API key configured (OpenAI or Anthropic)

**Example**:
```markdown
<!-- ACADWRITE: clarity -->
The utilization of concurrent engineering methodologies in the context of product development paradigms has demonstrated substantial efficacy with respect to temporal reduction metrics pertaining to market introduction phases (Author, 2020).
<!-- END ACADWRITE -->
```

**Result**: Simplified, clearer version maintaining academic tone and citations.

---

### 5. `contradict` - Find Contradicting Evidence

**Purpose**: Identify evidence that contradicts your claims (useful for strengthening arguments)

**Syntax**:
```markdown
<!-- ACADWRITE: contradict -->
Your claim to challenge
<!-- END ACADWRITE -->
```

**Requirements**: Requires LLM API key configured

**Example**:
```markdown
<!-- ACADWRITE: contradict -->
Concurrent engineering always leads to better product outcomes.
<!-- END ACADWRITE -->
```

**Result**: Your claim plus a section showing contradicting evidence and citations.

---

## Examples

### Example 1: Drafting a New Section

**Before**:
```markdown
# Research Paper

## Theoretical Framework

<!-- ACADWRITE: expand -->
- Topic: Social cognitive theory in organizational learning
- Focus: Bandura's framework
- Include: Core principles, application to teams
<!-- END ACADWRITE -->
```

**After expansion**:
```markdown
# Research Paper

## Theoretical Framework

Social cognitive theory, developed by Albert Bandura, provides a comprehensive framework for understanding how individuals learn within organizational contexts (Bandura, 1986, p.23). The theory posits that learning occurs through observation, imitation, and modeling, with reciprocal interactions between personal factors, behavior, and environmental influences (Bandura, 1989, p.1175).

When applied to organizational teams, social cognitive theory suggests that team members learn not only through direct experience but also by observing colleagues' behaviors and their consequences (Wood & Bandura, 1989, p.361). This observational learning process is particularly relevant in collaborative settings where knowledge sharing and skill development are critical (Schunk & DiBenedetto, 2020, p.12).
```

### Example 2: Enhancing Existing Text

**Before**:
```markdown
## Results

<!-- ACADWRITE: evidence -->
Our survey found that teams using concurrent engineering reported higher satisfaction levels.
<!-- END ACADWRITE -->
```

**After expansion**:
```markdown
## Results

Our survey found that teams using concurrent engineering reported higher satisfaction levels.

This finding aligns with previous research demonstrating that concurrent engineering practices improve team collaboration and reduce conflict through better communication channels (Smith & Jones, 2019, p.445). Furthermore, studies have shown that the parallel nature of concurrent engineering allows team members to feel more engaged in the overall development process, contributing to increased job satisfaction (Williams et al., 2021, p.892).
```

### Example 3: Multiple Markers in One Document

**Before**:
```markdown
# Product Development Study

## Introduction

<!-- ACADWRITE: expand -->
- Topic: Evolution of product development methodologies
- Focus: From waterfall to agile to concurrent
<!-- END ACADWRITE -->

## Background

### Traditional Approaches

<!-- ACADWRITE: expand max_words=200 -->
- Topic: Waterfall methodology in product development
- Include: Characteristics, limitations
<!-- END ACADWRITE -->

### Modern Approaches

<!-- ACADWRITE: expand max_words=200 -->
- Topic: Concurrent engineering principles
- Include: Core concepts, advantages
<!-- END ACADWRITE -->
```

**Command**:
```bash
acadwrite expand study.md -c research_papers
```

**Result**: All three markers expanded with appropriate content and citations.

---

## CLI Options

### Basic Usage

```bash
acadwrite expand paper.md -c collection_name
```

### Override Search Type for All Markers

```bash
# Use GraphRAG global search for broad thematic analysis
acadwrite expand paper.md -c research --search-type global

# Use graph search for relationship-focused queries
acadwrite expand paper.md -c research --type graph

# Use vector search for fast factual queries
acadwrite expand paper.md -c research --type vector
```

### Override Answer Format for All Markers

```bash
# Get all responses as tables
acadwrite expand paper.md -c research --format table

# Get all responses as bulleted lists
acadwrite expand paper.md -c research --format list

# Get structured JSON output
acadwrite expand paper.md -c research --format json
```

### Combine Options

```bash
# Use global search with table format
acadwrite expand paper.md -c research --type global --format table

# Use graph search with list format
acadwrite expand paper.md -c research --type graph --format list
```

### Other Options

```bash
# Dry run (preview without modifying file)
acadwrite expand paper.md -c research --dry-run

# Specify output file
acadwrite expand paper.md -c research -o output.md

# Disable backup
acadwrite expand paper.md -c research --no-backup
```

### Priority: Marker Parameters Override CLI Flags

If a marker specifies parameters, those take precedence over CLI flags:

```markdown
<!-- ACADWRITE: expand type=vector format=table -->
Content
<!-- END ACADWRITE -->
```

```bash
# This marker will use vector+table (from marker)
# Other markers without params will use global+list (from CLI)
acadwrite expand paper.md -c research --type global --format list
```

---

## Workflow Tips

### 1. Iterative Writing

Start with high-level markers, expand them, then add more detailed markers:

```markdown
## Section

<!-- ACADWRITE: expand -->
- High-level topic overview
<!-- END ACADWRITE -->
```

After expansion, you might add:

```markdown
## Section

[Generated content from first expansion]

<!-- ACADWRITE: expand max_words=300 -->
- More detailed subtopic based on what was generated
<!-- END ACADWRITE -->
```

### 2. Combining Operations

Use different operations for different purposes:

```markdown
## Analysis

<!-- ACADWRITE: expand -->
- Main findings overview
<!-- END ACADWRITE -->

<!-- ACADWRITE: evidence -->
The data suggests a strong correlation between variables.
<!-- END ACADWRITE -->

<!-- ACADWRITE: contradict -->
This correlation indicates causation.
<!-- END ACADWRITE -->
```

### 3. Using Backups

By default, AcadWrite creates `.backup` files:

```bash
acadwrite expand paper.md -c research
# Creates paper.md.backup before modifying
```

Disable backups:
```bash
acadwrite expand paper.md -c research --no-backup
```

### 4. Dry Run First

Preview what would be generated without modifying your file:

```bash
acadwrite expand paper.md -c research --dry-run
```

### 5. Separate Output File

Keep original and generate to a new file:

```bash
acadwrite expand draft.md -c research -o final.md
```

---

## Editor Integration

### VS Code

**Method 1: Keyboard Shortcut**

1. Open Command Palette (`Cmd/Ctrl+Shift+P`)
2. Select "Tasks: Run Task"
3. Create `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "AcadWrite: Expand Current File",
      "type": "shell",
      "command": "acadwrite",
      "args": [
        "expand",
        "${file}",
        "-c",
        "research_papers"
      ],
      "presentation": {
        "reveal": "always",
        "panel": "new"
      },
      "problemMatcher": []
    }
  ]
}
```

4. Add keyboard shortcut in `keybindings.json`:

```json
{
  "key": "ctrl+shift+e",
  "command": "workbench.action.tasks.runTask",
  "args": "AcadWrite: Expand Current File"
}
```

**Method 2: Save Hook** (requires extension)

Coming soon: VS Code extension for automatic expansion on save.

### Vim/Neovim

Add to your `.vimrc` or `init.vim`:

```vim
" Expand current file
nnoremap <leader>ae :!acadwrite expand % -c research_papers<CR>:e<CR>

" Dry run
nnoremap <leader>ad :!acadwrite expand % -c research_papers --dry-run<CR>
```

Usage:
- `<leader>ae` - Expand and reload file
- `<leader>ad` - Dry run preview

### Emacs

Add to your `.emacs` or `init.el`:

```elisp
(defun acadwrite-expand-current-buffer ()
  "Expand AcadWrite markers in current buffer."
  (interactive)
  (shell-command
   (format "acadwrite expand %s -c research_papers"
           (shell-quote-argument (buffer-file-name))))
  (revert-buffer t t t))

(global-set-key (kbd "C-c a e") 'acadwrite-expand-current-buffer)
```

Usage: `C-c a e` to expand current file

### Obsidian

Create a shell command in Obsidian settings:

```bash
acadwrite expand {{file_path}} -c research_papers && open {{file_path}}
```

---

## Best Practices

### 1. Be Specific in Markers

**Good**:
```markdown
<!-- ACADWRITE: expand -->
- Topic: Machine learning for medical image segmentation
- Focus: Deep learning architectures (U-Net, ResNet)
- Include: Accuracy metrics, training data requirements
<!-- END ACADWRITE -->
```

**Less Effective**:
```markdown
<!-- ACADWRITE: expand -->
- Machine learning stuff
<!-- END ACADWRITE -->
```

### 2. Use Appropriate Operations

- **expand**: When you need new content
- **evidence**: When you have claims that need support
- **citations**: When you have good text that just needs citations
- **clarity**: When your text is too complex
- **contradict**: When you want to strengthen arguments

### 3. Set Max Words

Control output length to maintain document structure:

```markdown
<!-- ACADWRITE: expand max_words=250 -->
...
<!-- END ACADWRITE -->
```

### 4. Review and Edit

Generated content is a starting point - always review and edit:

1. Check citation accuracy
2. Verify claims align with sources
3. Adjust tone and style
4. Add your own insights

### 5. Version Control

Use git to track changes:

```bash
git add paper.md
git commit -m "Added markers for expansion"
acadwrite expand paper.md -c research
git diff  # Review changes
git commit -m "Expanded sections with AcadWrite"
```

---

## Troubleshooting

### No markers found

**Symptom**: Message "No markers found in file"

**Solution**: Check marker syntax - must be exactly:
```markdown
<!-- ACADWRITE: operation -->
content
<!-- END ACADWRITE -->
```

### FileIntel connection error

**Symptom**: "Failed to connect to FileIntel"

**Solution**:
```bash
# Check FileIntel is running
curl http://localhost:8000/health

# Or set different URL
export FILEINTEL__BASE_URL=http://your-server:8000
```

### LLM operations fail (clarity, contradict)

**Symptom**: "LLM client required"

**Solution**: Set API key:
```bash
export LLM__API_KEY=sk-your-openai-key
# or
export LLM__PROVIDER=anthropic
export LLM__API_KEY=your-anthropic-key
```

### Generated content too long/short

**Solution**: Use `max_words` parameter:
```markdown
<!-- ACADWRITE: expand max_words=300 -->
...
<!-- END ACADWRITE -->
```

Or set globally in config:
```bash
export WRITING__MAX_WORDS_PER_SECTION=400
```

---

## Next Steps

- **Try it out**: Add a simple marker to a document and expand it
- **Read**: [INTERACTIVE_WORKFLOW.md](../INTERACTIVE_WORKFLOW.md) for advanced workflows
- **Explore**: [Watch mode](WATCH_MODE_GUIDE.md) for automatic expansion (Phase 2)
- **Integrate**: Set up editor shortcuts for seamless workflow

---

**Questions? Issues?**

- Check the [documentation](../ARCHITECTURE.md)
- File an issue on GitHub
- Run `acadwrite expand --help` for CLI reference

# AcadWrite Examples

This directory contains example files to help you get started with AcadWrite.

## Directory Structure

```
examples/
├── outlines/              # Example chapter outlines
│   ├── chapter_outline.yaml     # YAML format outline
│   └── simple_outline.md        # Markdown format outline
├── outputs/              # Generated content (created by examples)
├── config.example.yaml   # Example configuration file
└── README.md            # This file
```

## Quick Start Examples

### 1. Generate a Single Section

```bash
acadwrite generate "Definition of Agile Development" \
  --collection thesis_sources \
  --output section.md \
  --style formal \
  --citation-style footnote
```

### 2. Generate a Full Chapter from Outline

Using YAML outline:
```bash
acadwrite chapter outlines/chapter_outline.yaml \
  --collection thesis_sources \
  --output-dir outputs/chapter2/ \
  --style formal
```

Using Markdown outline:
```bash
acadwrite chapter outlines/simple_outline.md \
  --collection ml_papers \
  --single-file \
  --output outputs/ml_chapter.md
```

### 3. Find Counterarguments

```bash
acadwrite contra "Agile methodologies improve development speed" \
  --collection thesis_sources \
  --depth standard \
  --synthesis \
  --output outputs/counterargument.md
```

### 4. Work with Citations

Extract citations from generated content:
```bash
acadwrite citations extract outputs/ml_chapter.md \
  --format bibtex \
  --output outputs/references.bib
```

Check citation integrity:
```bash
acadwrite citations check outputs/ml_chapter.md --strict
```

Deduplicate citations:
```bash
acadwrite citations dedupe outputs/ml_chapter.md
```

## Configuration

1. Copy the example config file:
   ```bash
   mkdir -p ~/.acadwrite
   cp config.example.yaml ~/.acadwrite/config.yaml
   ```

2. Edit the configuration:
   ```bash
   nano ~/.acadwrite/config.yaml
   ```

3. Set your API key:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

## Outline Format Examples

### YAML Format

The YAML format supports hierarchical sections with explicit levels:

```yaml
title: "Chapter Title"
sections:
  - heading: "Main Section"
    level: 1
    children:
      - heading: "Subsection"
        level: 2
        children:
          - heading: "Sub-subsection"
            level: 3
```

### Markdown Format

The Markdown format uses standard heading levels:

```markdown
# Main Section (level 1)

## Subsection (level 2)

### Sub-subsection (level 3)
```

## Writing Styles

AcadWrite supports different writing styles:

- **formal**: Traditional academic writing (default)
- **technical**: Technical documentation style
- **accessible**: Clear, accessible language
- **raw**: Minimal processing of FileIntel output

Example:
```bash
acadwrite generate "Neural Networks" \
  --collection ai_papers \
  --style technical
```

## Citation Styles

Two citation styles are supported:

- **inline**: `(Author, Year, p.X)` format
- **footnote**: `[^1]` format with footnotes at bottom

Example:
```bash
acadwrite generate "Machine Learning" \
  --collection ml_papers \
  --citation-style inline
```

## Tips

1. **Use descriptive headings**: Clear section headings help FileIntel find relevant content
2. **Start small**: Test with a single section before generating full chapters
3. **Check citations**: Always validate citations with `acadwrite citations check`
4. **Adjust max-words**: Use `--max-words` to control section length
5. **Review and edit**: Generated content should be reviewed and edited by you

## Troubleshooting

### FileIntel Connection Issues

If you get connection errors:
```bash
# Check FileIntel is running
curl http://localhost:8000/health

# Check configuration
acadwrite config show
```

### Missing API Key

If you get LLM API errors:
```bash
# Set API key
export OPENAI_API_KEY="your-key"

# Or configure in ~/.acadwrite/config.yaml
```

### Collection Not Found

List available collections:
```bash
# This will be shown in the error message
acadwrite generate "test" --collection nonexistent
```

## Next Steps

1. Review the example outlines in `outlines/`
2. Configure AcadWrite with your settings
3. Try generating a single section
4. Generate a full chapter from an outline
5. Explore citation management features

For more information, see the main project README.

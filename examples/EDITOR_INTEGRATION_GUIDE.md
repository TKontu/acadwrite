# Editor Integration Guide for AcadWrite

Quick setup guide for integrating AcadWrite into your favorite text editor for interactive markdown writing.

## 🚀 Quick Start Options

### **Option 1: VS Code (Easiest)**

#### Setup Tasks
1. Create `.vscode/tasks.json` in your project:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "AcadWrite: Generate Current Section",
      "type": "shell",
      "command": "acadwrite",
      "args": [
        "generate",
        "${selectedText}",
        "--collection",
        "my_research",
        "--output",
        "${workspaceFolder}/temp_section.md"
      ],
      "presentation": {
        "reveal": "always",
        "panel": "dedicated"
      },
      "problemMatcher": []
    },
    {
      "label": "AcadWrite: Process Chapter",
      "type": "shell",
      "command": "acadwrite",
      "args": [
        "chapter",
        "${file}",
        "--collection",
        "my_research",
        "--output-dir",
        "${fileDirname}/output"
      ],
      "presentation": {
        "reveal": "always"
      }
    }
  ]
}
```

2. Create `.vscode/settings.json`:

```json
{
  "acadwrite.defaultCollection": "my_research",
  "acadwrite.citationStyle": "footnote",
  "acadwrite.maxWords": 800
}
```

#### Usage
1. Select heading text
2. Press `Ctrl+Shift+P` (Cmd+Shift+P on Mac)
3. Type "Run Task"
4. Select "AcadWrite: Generate Current Section"
5. Content appears in `temp_section.md`

---

### **Option 2: Vim/Neovim**

#### Setup
Add to your `~/.vimrc` or `~/.config/nvim/init.vim`:

```vim
" AcadWrite Integration
let g:acadwrite_collection = 'my_research'
let g:acadwrite_citation_style = 'footnote'

" Generate section from heading under cursor
function! AcadwriteGenerateSection()
  " Get the heading under cursor
  let line = getline('.')
  let heading = substitute(line, '^##\+\s*', '', '')

  " Run acadwrite
  let output = system('acadwrite generate "' . heading . '" -c ' . g:acadwrite_collection)

  " Insert below current heading
  call append(line('.'), split(output, '\n'))

  echo "Generated content for: " . heading
endfunction

" Generate and insert at cursor
function! AcadwriteGenerateAtCursor()
  let heading = input('Heading: ')
  if heading != ''
    let output = system('acadwrite generate "' . heading . '" -c ' . g:acadwrite_collection)
    call append(line('.'), split(output, '\n'))
  endif
endfunction

" Process entire chapter file
function! AcadwriteProcessChapter()
  execute '!acadwrite chapter % -c ' . g:acadwrite_collection
  edit!
endfunction

" Key mappings
nnoremap <leader>ag :call AcadwriteGenerateSection()<CR>
nnoremap <leader>ai :call AcadwriteGenerateAtCursor()<CR>
nnoremap <leader>ac :call AcadwriteProcessChapter()<CR>

" Commands
command! -nargs=1 AcadwriteGenerate :call system('acadwrite generate <args> -c ' . g:acadwrite_collection)
command! AcadwriteChapter :call AcadwriteProcessChapter()
```

#### Usage
- `<leader>ag` - Generate section from heading under cursor
- `<leader>ai` - Prompt for heading and insert content
- `<leader>ac` - Process chapter from outline file
- `:AcadwriteGenerate "Topic"` - Generate specific topic

---

### **Option 3: Emacs**

#### Setup
Add to your `~/.emacs` or `~/.emacs.d/init.el`:

```elisp
;; AcadWrite Integration
(defvar acadwrite-collection "my_research"
  "Default collection for AcadWrite")

(defvar acadwrite-citation-style "footnote"
  "Default citation style")

(defun acadwrite-generate-section ()
  "Generate content for the heading at point."
  (interactive)
  (save-excursion
    (beginning-of-line)
    (when (looking-at "^##+ \\(.*\\)")
      (let ((heading (match-string 1)))
        (message "Generating content for: %s" heading)
        (shell-command
         (format "acadwrite generate \"%s\" -c %s"
                 heading acadwrite-collection)
         t)))))

(defun acadwrite-generate-at-point ()
  "Prompt for heading and generate content at point."
  (interactive)
  (let ((heading (read-string "Heading: ")))
    (when (not (string-empty-p heading))
      (shell-command
       (format "acadwrite generate \"%s\" -c %s"
               heading acadwrite-collection)
       t))))

(defun acadwrite-process-chapter ()
  "Process current file as chapter outline."
  (interactive)
  (shell-command
   (format "acadwrite chapter %s -c %s"
           (buffer-file-name) acadwrite-collection)))

;; Key bindings (using C-c a prefix)
(global-set-key (kbd "C-c a g") 'acadwrite-generate-section)
(global-set-key (kbd "C-c a i") 'acadwrite-generate-at-point)
(global-set-key (kbd "C-c a c") 'acadwrite-process-chapter)
```

#### Usage
- `C-c a g` - Generate section from current heading
- `C-c a i` - Interactive generation
- `C-c a c` - Process chapter

---

## 📝 Workflow Templates

### **Template 1: Progressive Writing**

**Workflow:**
1. Write outline with bullet points
2. Generate each section interactively
3. Edit and refine
4. Extract citations

**Example:**
```markdown
# Chapter 3: Methodology

## Research Design
- Quantitative approach
- Survey methodology
- Sample size: 500 participants

[CURSOR HERE - Press shortcut to generate]
```

**Editor steps:**
1. Position cursor under heading
2. Press generation shortcut
3. Review generated content
4. Edit as needed

---

### **Template 2: Batch Processing**

**Workflow:**
1. Create complete outline (YAML or Markdown)
2. Run chapter generation
3. Review all sections
4. Make targeted edits

**Example outline.yaml:**
```yaml
title: "Chapter 3: Methodology"
sections:
  - heading: "Research Design"
    level: 1
  - heading: "Data Collection"
    level: 1
    children:
      - heading: "Survey Instrument"
        level: 2
      - heading: "Sampling Strategy"
        level: 2
```

**Command:**
```bash
acadwrite chapter outline.yaml -c research --output-dir chapter3/
```

---

### **Template 3: Hybrid Approach**

**Workflow:**
1. Generate initial structure
2. Use interactive generation for specific sections
3. Manual writing for unique insights
4. Validate citations

**Example:**
```bash
# 1. Generate initial chapter
acadwrite chapter outline.yaml -c research

# 2. Edit specific section interactively (in editor)
# Use editor shortcuts for regeneration

# 3. Check citations
acadwrite citations check chapter3/combined.md

# 4. Export bibliography
acadwrite citations extract chapter3/combined.md --format bibtex -o refs.bib
```

---

## 🎯 Platform-Specific Tips

### **VS Code**
- Install "Markdown All in One" extension
- Use split view: outline on left, generated content on right
- Create snippets for AcadWrite markers
- Use "Run on Save" extension for auto-generation

### **Vim/Neovim**
- Use `:split` to view outline and output simultaneously
- Install `vim-markdown` for better syntax highlighting
- Use `:term` for persistent shell with watch mode
- Consider `vim-dispatch` for async command execution

### **Emacs**
- Use Org-mode for better outline management
- `markdown-mode` for syntax highlighting
- `magit` for version control integration
- Consider `async.el` for non-blocking generation

---

## 🔧 Advanced Configurations

### **Multi-Collection Setup**

```vim
" Vim: Switch collections easily
let g:acadwrite_collections = {
  \ 'thesis': 'thesis_papers',
  \ 'review': 'literature_review',
  \ 'methods': 'methodology_papers'
\ }

function! AcadwriteSelectCollection()
  let choice = input('Collection (thesis/review/methods): ')
  if has_key(g:acadwrite_collections, choice)
    let g:acadwrite_collection = g:acadwrite_collections[choice]
    echo "Collection set to: " . g:acadwrite_collection
  endif
endfunction

command! AcadwriteCollection call AcadwriteSelectCollection()
```

### **Auto-Save and Generate**

```json
// VS Code: Auto-generate on save
{
  "emeraldwalk.runonsave": {
    "commands": [
      {
        "match": "\\.md$",
        "cmd": "acadwrite expand ${file} --collection my_research --auto"
      }
    ]
  }
}
```

### **Citation Quick-Fix**

```vim
" Vim: Jump to citation issues
function! AcadwriteCheckCitations()
  let output = system('acadwrite citations check ' . expand('%'))
  cexpr output
  copen
endfunction

command! AcadwriteCitationCheck call AcadwriteCheckCitations()
```

---

## 📚 Example Project Structure

```
thesis/
├── .vscode/
│   ├── tasks.json          # AcadWrite tasks
│   └── settings.json       # Project settings
├── chapters/
│   ├── chapter1/
│   │   ├── outline.yaml
│   │   └── sections/
│   ├── chapter2/
│   │   ├── outline.md      # Markdown outline
│   │   └── draft.md        # Working draft
│   └── chapter3/
│       └── ...
├── references/
│   └── bibliography.bib    # Extracted citations
└── config.yaml             # AcadWrite config
```

**Workflow:**
```bash
# Open project
cd thesis/
code .  # or vim ., emacs .

# Work on chapter
cd chapters/chapter2/
# Use editor shortcuts for generation

# Check all citations
acadwrite citations check chapters/**/*.md

# Extract bibliography
acadwrite citations extract chapters/**/*.md -f bibtex -o references/bibliography.bib
```

---

## 🎓 Tips for Effective Interactive Writing

### **1. Start with Good Headings**
```markdown
<!-- Good: Specific and descriptive -->
## Impact of Deep Learning on Medical Diagnosis

<!-- Less helpful: Too vague -->
## Deep Learning
```

### **2. Use Bullet Points as Context**
```markdown
## Data Analysis Methods

<!-- Add context before generating -->
- Statistical analysis using SPSS
- Focus on regression models
- Include visualization techniques
- Sample size considerations

[Generate here]
```

### **3. Iterate and Refine**
```bash
# 1. Generate initial version
[Use editor shortcut]

# 2. Review and edit manually
[Edit in editor]

# 3. Regenerate specific parts if needed
acadwrite generate "Statistical Methods" -c research --force
```

### **4. Version Control Integration**
```bash
# Commit after each major generation
git add chapter2.md
git commit -m "Generate methodology section"

# Create checkpoints
git tag v0.1-draft-chapter2
```

---

## 🚨 Troubleshooting

### **Issue: Command not found**
```bash
# Ensure AcadWrite is in PATH
which acadwrite

# Or use full path
/path/to/venv/bin/acadwrite generate "Topic"
```

### **Issue: Collection not found**
```bash
# List available collections
curl http://localhost:8000/api/v2/collections

# Update config
acadwrite config show
```

### **Issue: Generation takes too long**
```bash
# Use shorter word limits
acadwrite generate "Topic" --max-words 300

# Or limit sources
acadwrite generate "Topic" --max-sources 3
```

---

## 📞 Need Help?

- **Documentation:** See main README.md
- **Examples:** Check examples/ directory
- **Issues:** GitHub repository
- **Community:** Forum or Discord

---

**Quick Links:**
- [Full Interactive Workflow Guide](INTERACTIVE_WORKFLOW.md)
- [Main README](../README.md)
- [Developer Guide](../DEVELOPER_GUIDE.md)

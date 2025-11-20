# Bones

A Makefile-based pipeline for generating books in multiple formats (PDF/EPUB/DOCX/Audio) with AI-assisted editing capabilities.

## TL;DR

```bash
# Install system-wide
git clone https://github.com/yourusername/bones.git
cd bones
sudo make install

# Create a book project anywhere
mkdir ~/my-book && cd ~/my-book
mkdir chapters

# Write your chapters as markdown files
echo "# Chapter 1" > chapters/01-intro.md

# Build your book
bones pdf        # Generate PDF
bones epub       # Generate EPUB
bones help       # See all options
```

## Description

**Bones** is a zero-dependency, Makefile-based build system for authors who write books in Markdown. It transforms your Markdown chapters into professional PDFs, EPUB files, DOCX documents, and even audiobooks. Additionally, it includes AI-powered editing tools to help refine your prose.

### Key Features

- **Multiple output formats**: PDF, EPUB, DOCX, and MP3 audiobooks
- **Professional typesetting**: Uses Pandoc and Tectonic/XeLaTeX for high-quality PDFs
- **AI-assisted editing**: Built-in LLM-powered line editor and copy editor
- **Zero Python dependencies**: Uses only Python standard library (urllib, json, os)
- **Flexible AI backends**: Supports Ollama (local), OpenAI, and Anthropic Claude
- **Incremental builds**: Only rebuilds what changed
- **System-wide installation**: Install once, use anywhere
- **Git-integrated workflow**: Editing tools create branches for easy review

## Intention

Traditional book publishing workflows involve juggling multiple tools: word processors, LaTeX editors, conversion utilities, and manual editing passes. **Bones** consolidates this into a single, simple command-line interface.

### Problems Bones Solves

1. **Format fragmentation**: Write once in Markdown, output to any format
2. **Dependency hell**: No pip requirements, no virtual environments, just standard tools
3. **Manual repetition**: Automate the build process with Make's dependency tracking
4. **AI integration friction**: Built-in LLM clients for editing without context-switching
5. **Version control**: Git-native workflow for tracking edits and changes

### Philosophy

- **Simplicity over features**: Do one thing well
- **Composability**: Integrates with existing Unix tools (make, git, pandoc)
- **Transparency**: All intermediate files are inspectable
- **Safety**: Defaults prevent accidental data loss (e.g., `--overwrite` flag required)

## Design

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  User's Book Project                                        │
│  ├── chapters/                                              │
│  │   ├── 01-introduction.md                                │
│  │   ├── 02-chapter-two.md                                 │
│  │   └── ...                                                │
│  └── outlines/ (optional, for copy editing)                │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  bones (system-wide command)                                │
│  └── /usr/local/bin/bones → make -f rules.mk               │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  /usr/local/share/bones/                                    │
│  ├── rules.mk          (Makefile build logic)              │
│  └── scripts/                                               │
│      ├── llm_client.py      (Multi-backend LLM client)     │
│      ├── line_editor.py     (AI line editor)               │
│      ├── copy_editor.py     (AI copy editor)               │
│      └── llm_elevenlabs_tts.py (Text-to-speech)           │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Build Pipeline                                             │
│                                                              │
│  chapters/*.md                                              │
│      │                                                       │
│      ├─→ combined.md ─→ book.tex ─→ book.pdf               │
│      ├─→ combined.md ─────────────→ book.epub              │
│      ├─→ combined.md ─────────────→ book.docx              │
│      └─→ *.txt ──────────────────→ *.mp3                   │
└─────────────────────────────────────────────────────────────┘
```

### Directory Structure

**Installation** (system-wide):
```
/usr/local/
├── bin/bones                    # Wrapper script
└── share/bones/
    ├── rules.mk                 # Make rules
    └── scripts/
        ├── llm_client.py
        ├── line_editor.py
        ├── copy_editor.py
        └── llm_elevenlabs_tts.py
```

**Book Project** (user-created):
```
my-book/
├── chapters/                    # Your markdown chapters
│   ├── 00-prologue.md
│   ├── 01-chapter-one.md
│   └── 02-chapter-two.md
├── outlines/                    # Optional: chapter outlines
├── cover/
│   └── cover.png               # Optional: book cover
├── build/                       # Generated (auto-created)
│   ├── book.pdf
│   ├── book.epub
│   ├── book.docx
│   ├── mp3/
│   └── obj/                     # Intermediate files
└── book.pdf                     # Final PDF (symlink to build/)
```

### Build Targets

| Target | Description |
|--------|-------------|
| `pdf` | Generate PDF (default) |
| `epub` | Generate EPUB |
| `docx` | Generate DOCX |
| `tex` | Generate intermediate LaTeX |
| `txt` | Generate plain text for TTS |
| `mp3` | Generate MP3 audiobook |
| `lineedit` | Run LLM line editor on all chapters |
| `copyedit` | Run LLM copy editor with style guide |
| `clean` | Remove build artifacts |
| `help` | Show all targets |

### AI Editing Workflow

The AI editing tools create Git branches automatically for safe review:

```bash
bones lineedit       # Creates edits/TIMESTAMP branch
git diff main        # Review changes
git merge main       # Accept all changes
# OR
git checkout -p main # Selectively accept changes
```

### LLM Client Design

The `llm_client.py` provides a unified interface to multiple AI backends:

- **Ollama**: Local models (llama2, mistral, etc.)
- **OpenAI**: GPT-4, GPT-3.5, or compatible APIs (DeepSeek, Groq)
- **Anthropic**: Claude models

**Key features**:
- Exponential backoff retry logic (handles 429 rate limits, 5xx errors)
- Graceful JSON parsing error handling
- Zero external dependencies (uses `urllib` only)
- Configurable via environment variables or CLI args

```bash
# Configure via environment
export LLM_BACKEND=anthropic
export LLM_MODEL=claude-3-7-sonnet-20250219
export ANTHROPIC_API_KEY=sk-...

# Or via CLI
bones lineedit --backend openai --model gpt-4
```

## Installation

### Prerequisites

**Required**:
- `make` (GNU Make)
- `python3` (3.7+)
- `pandoc` (for format conversion)

**Optional** (for PDF generation):
- `tectonic` (recommended) or `xelatex`/`lualatex`

**Optional** (for audiobooks):
- ElevenLabs API key (for TTS)

### Install System-Wide

```bash
# Clone the repository
git clone https://github.com/yourusername/bones.git
cd bones

# Check that required tools are available
make test

# Install (requires sudo)
sudo make install
```

This installs:
- Rules and scripts to `/usr/local/share/bones/`
- `bones` command to `/usr/local/bin/bones`

### Uninstall

```bash
sudo make uninstall
```

### Install to Custom Prefix

```bash
# Install to ~/local instead of /usr/local
make install PREFIX=~/local

# Add to PATH
export PATH="$HOME/local/bin:$PATH"
```

## Usage

### Quick Start

```bash
# 1. Create a book project
mkdir my-novel && cd my-novel
mkdir chapters

# 2. Write your first chapter
cat > chapters/01-beginning.md <<'EOF'
# Chapter 1: The Beginning

It was a dark and stormy night...
EOF

# 3. Build the book
bones pdf

# 4. View the result
open book.pdf  # macOS
xdg-open book.pdf  # Linux
```

### Configuration

You can customize the build by setting variables:

```bash
# Custom source directory
bones pdf SRC_DIR=manuscript

# Custom output filename
bones pdf PDF_OUTPUT=my-novel.pdf

# Specify PDF engine
bones pdf PDF_ENGINE=xelatex

# Custom font
bones pdf 'PANDOC_COMMON_FLAGS=-V mainfont="Times New Roman"'
```

Or create a project-specific `Makefile`:

```makefile
# Include bones rules
include /usr/local/share/bones/rules.mk

# Override defaults
PDF_OUTPUT = my-novel.pdf
SRC_DIR = manuscript

# Custom target
publish: pdf epub
	cp book.pdf book.epub ~/Dropbox/
```

### AI Editing

#### Line Editing

Performs sentence-level editing (grammar, flow, clarity):

```bash
# Edit all chapters, create git branch
bones lineedit

# Review changes
git diff main

# Accept or reject
git merge main  # Accept all
git branch -D edits/TIMESTAMP  # Reject all
```

#### Copy Editing

Performs high-level editing (pacing, consistency, style):

```bash
bones copyedit

# Reviews are saved to build/reviews/
cat build/reviews/01-beginning-review.md
```

#### Standalone Usage

You can also use the editors directly on individual files:

```bash
# Safe default: creates chapter.edited.md
python3 /usr/local/share/bones/scripts/line_editor.py chapter.md

# Overwrite original file
python3 /usr/local/share/bones/scripts/line_editor.py chapter.md --overwrite

# Specify output
python3 /usr/local/share/bones/scripts/line_editor.py chapter.md -o edited.md

# Custom instruction
python3 /usr/local/share/bones/scripts/line_editor.py chapter.md \
    --instruction "Focus on dialogue flow"

# Use different backend/model
python3 /usr/local/share/bones/scripts/line_editor.py chapter.md \
    --backend openai --model gpt-4
```

### Audiobook Generation

```bash
# Set up ElevenLabs API key
export ELEVENLABS_API_KEY=your_key_here

# Generate MP3s for all chapters
bones mp3

# Files saved to build/mp3/
ls build/mp3/
# 01-beginning.mp3
# 02-middle.mp3
# 03-end.mp3
```

## Advanced

### Cover Images

Place a cover image at `cover/cover.png` and it will be automatically included in the PDF.

### Custom Styling

Override Pandoc variables in your project Makefile:

```makefile
include /usr/local/share/bones/rules.mk

PANDOC_COMMON_FLAGS += \
  -V geometry:margin=1.5in \
  -V fontsize=11pt \
  -V linestretch=1.5
```

### Chapter Ordering

Chapters are sorted naturally (version sort), so use numeric prefixes:

```
chapters/
├── 00-prologue.md
├── 01-chapter-one.md
├── 02-chapter-two.md
├── 10-chapter-ten.md
└── 99-epilogue.md
```

### Debugging

```bash
# Show chapter order
bones list

# Show configuration
bones debug

# Keep intermediate files
bones pdf
ls build/obj/combined.md  # Combined markdown
ls build/obj/book.tex     # Generated LaTeX
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_BACKEND` | `anthropic` | AI backend (ollama/openai/anthropic) |
| `LLM_MODEL` | `claude-3-7-sonnet-20250219` | Model identifier |
| `ANTHROPIC_API_KEY` | - | Anthropic API key |
| `OPENAI_API_KEY` | - | OpenAI API key |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1/chat/completions` | OpenAI-compatible endpoint |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `ELEVENLABS_API_KEY` | - | ElevenLabs TTS API key |

## Examples

### Minimal Book

```bash
mkdir simple-book && cd simple-book
mkdir chapters
echo "# My Story\n\nOnce upon a time..." > chapters/01-story.md
bones pdf
```

### Multi-format Release

```bash
# Build all formats
bones pdf epub docx

# Results
ls build/
# book.pdf
# book.epub
# book.docx
```

### AI-Enhanced Workflow

```bash
# 1. Write rough draft
vim chapters/01-intro.md

# 2. Line edit with AI
bones lineedit
git diff main  # Review changes

# 3. Merge accepted edits
git merge main

# 4. Build final PDF
bones pdf
```

## Troubleshooting

### "No PDF engine found"

Install Tectonic (recommended):
```bash
# macOS
brew install tectonic

# Linux
cargo install tectonic
```

Or use system LaTeX:
```bash
bones pdf PDF_ENGINE=xelatex
```

### "No chapters found"

Ensure your chapters directory has `.md` files:
```bash
ls chapters/*.md
```

### AI editing fails

Check your API key is set:
```bash
echo $ANTHROPIC_API_KEY
```

Or use a local model:
```bash
# Install Ollama: https://ollama.ai
ollama pull llama2
bones lineedit --backend ollama --model llama2
```

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please open an issue or PR.

## Credits

Built with:
- [Pandoc](https://pandoc.org/) - Universal document converter
- [Tectonic](https://tectonic-typesetting.github.io/) - Modern TeX engine
- [GNU Make](https://www.gnu.org/software/make/) - Build automation

---

**Happy writing!**

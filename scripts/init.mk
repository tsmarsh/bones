# =====================================================================
# Project Initialization
# =====================================================================
# Scaffolding for new book projects: git repo, directories, sample files,
# and GitHub Actions workflows.

FORCE ?=

# Init depends on all scaffolding targets
init: .git chapters outlines cover fonts .gitignore Makefile .github/workflows/ci.yml
	@echo ""
	@echo "======================================================================"
	@echo "  ✓ Project initialized successfully!"
	@echo "======================================================================"
	@echo ""
	@echo "Directory structure created:"
	@echo "  chapters/        - Your markdown chapter files"
	@echo "  outlines/        - Style guides and book metadata"
	@echo "  cover/           - Place your cover.png here"
	@echo "  fonts/           - Custom fonts (main.ttf, sans.ttf, mono.ttf, cjk.ttf)"
	@echo "  .github/         - GitHub Actions workflow for CI/CD"
	@echo ""
	@echo "Files created:"
	@echo "  chapters/01-chapter-one.md      - Sample first chapter"
	@echo "  outlines/outline.md             - Book outline and style guide"
	@echo "  cover/cover.png                 - Default cover (replace with your own)"
	@echo "  .gitignore                      - Ignore build artifacts"
	@echo "  Makefile                        - Local build configuration"
	@echo "  .github/workflows/ci.yml        - Auto-build and release workflow"
	@echo "  .github/workflows/lineedit.yml  - Manual AI line editing workflow"
	@echo "  .github/workflows/copyedit.yml  - Manual AI copy editing workflow"
	@echo "  .github/workflows/audiobook.yml - Manual audiobook generation workflow"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Edit chapters/01-chapter-one.md or add new chapters"
	@echo "  2. Update outlines/outline.md with your book information"
	@echo "  3. Run 'bones pdf' or 'make pdf' to build your first PDF"
	@echo "  4. Run 'bones help' to see all available commands"
	@echo ""
	@echo "GitHub integration:"
	@echo "  - Push to GitHub to trigger automatic PDF builds"
	@echo "  - Create a tag (e.g., v1.0) to create a release with PDF"
	@echo "  - Update the bones repo URL in .github/workflows/*.yml"
	@echo "  - Add API keys as GitHub secrets for AI workflows:"
	@echo "    • ANTHROPIC_API_KEY for Claude-based editing"
	@echo "    • OPENAI_API_KEY for GPT-based editing"
	@echo "    • ELEVENLABS_API_KEY for audiobook generation"
	@echo "  - Manually trigger AI workflows from Actions tab (cost-controlled)"
	@echo ""
	@# Initial commit
	@echo "• Creating initial commit"
	@git add .gitignore Makefile chapters/ outlines/ cover/ fonts/ .github/
	@git commit -m "Initial bones project setup" || true

# Git repository initialization
.git:
	@if [ -d "chapters" ] && [ -z "$(FORCE)" ]; then \
		echo "======================================================================";\
		echo "  Bones Project Initialization";\
		echo "======================================================================";\
		echo "";\
		echo "Error: chapters/ directory already exists."; \
		echo "This appears to be an existing project."; \
		echo ""; \
		echo "To reinitialize anyway, run: bones init FORCE=1"; \
		exit 1; \
	fi
	@echo "======================================================================"
	@echo "  Bones Project Initialization"
	@echo "======================================================================"
	@echo ""
	@echo "• Initializing git repository"
	@git init

# Sample chapter with template content
chapters: | .git
	@echo "• Creating chapters/ directory"
	@mkdir -p chapters
	@printf '%s\n' \
		'# Chapter 1: The Beginning' \
		'' \
		'Your story starts here...' \
		'' \
		'This is a sample chapter to help you get started. Replace this content' \
		'with your own writing.' \
		'' \
		'## Writing Tips' \
		'' \
		'- Each `.md` file in the `chapters/` directory becomes part of your book' \
		'- Files are sorted naturally, so use numeric prefixes (01-, 02-, etc.)' \
		'- Use standard Markdown formatting' \
		'- Run `bones pdf` to build your book' \
		'' \
		'## Next Steps' \
		'' \
		'1. Edit this file or create new chapter files' \
		'2. Add your book metadata and outlines in `outlines/`' \
		'3. Run `bones pdf` to generate your first PDF' \
		'4. Use `bones help` to see all available commands' \
		> chapters/01-chapter-one.md

# Outlines directory with template
outlines: | .git
	@echo "• Creating outlines/ directory"
	@mkdir -p outlines
	@printf '%s\n' \
		'# Book Outline' \
		'' \
		'This directory contains your book metadata, style guides, and reference' \
		'materials. These files are used by the AI copy editor to maintain' \
		'consistency across your book.' \
		'' \
		'## Book Information' \
		'' \
		'**Title:** Your Book Title' \
		'**Author:** Your Name' \
		'**Genre:** [Your Genre]' \
		'**Target Audience:** [Your Audience]' \
		'' \
		'## Story Outline' \
		'' \
		'### Act 1' \
		'- Chapter 1: Introduction' \
		'- Chapter 2: ...' \
		'' \
		'### Act 2' \
		'- Chapter 3: ...' \
		'' \
		'### Act 3' \
		'- Chapter 4: Resolution' \
		'' \
		'## Style Guide' \
		'' \
		'- Point of view: [First/Third person]' \
		'- Tense: [Past/Present]' \
		'- Tone: [Serious/Humorous/etc.]' \
		'- Voice: [Active/Passive]' \
		> outlines/outline.md

# Cover directory with default cover
cover: | .git
	@echo "• Creating cover/ directory with default cover"
	@mkdir -p cover
	@cp -n $(BONES_HOME)cover.png cover/cover.png

# Fonts directory with README
fonts: | .git
	@echo "• Creating fonts/ directory"
	@mkdir -p fonts
	@printf '%s\n' \
		'# Custom Fonts' \
		'' \
		'Place your custom font files here with the following names:' \
		'' \
		'- `main.ttf` or `main.otf` - Main body font (serif)' \
		'- `sans.ttf` or `sans.otf` - Sans-serif font for headings' \
		'- `mono.ttf` or `mono.otf` - Monospace font for code' \
		'- `cjk.ttf` or `cjk.otf`   - CJK (Chinese/Japanese/Korean) font' \
		'' \
		'Bones will automatically detect and use these fonts in your PDF.' \
		'If fonts are not provided, Tectonic will use its default fonts.' \
		'' \
		'**Important:** Font files should be committed to git so they are' \
		'available during CI builds. The `.gitignore` is configured to NOT' \
		'ignore font files in this directory.' \
		'' \
		'## Example fonts:' \
		'' \
		'- **Serif**: Libertinus Serif, EB Garamond, Crimson Pro' \
		'- **Sans**: Inter, Source Sans Pro, Open Sans' \
		'- **Mono**: JetBrains Mono, Fira Code, Inconsolata' \
		'- **CJK**: Noto Sans CJK, Source Han Sans, Noto Serif CJK' \
		'' \
		'## Font licenses' \
		'' \
		'Make sure you have the rights to embed fonts in your PDF.' \
		'Most open-source fonts (SIL OFL, Apache, etc.) allow this.' \
		> fonts/README.md

# Project .gitignore
.gitignore: | .git
	@echo "• Creating .gitignore"
	@printf '%s\n' \
		'# Build artifacts and generated files' \
		'build/' \
		'*.pdf' \
		'*.aux' \
		'*.log' \
		'*.toc' \
		'*.tex' \
		'*.docx' \
		'*.epub' \
		'combined.md' \
		'' \
		'# Pandoc temporary files' \
		'*.tmp' \
		'*.temp' \
		'' \
		'# LaTeX auxiliary files' \
		'*.aux' \
		'*.bbl' \
		'*.blg' \
		'*.fdb_latexmk' \
		'*.fls' \
		'*.synctex.gz' \
		'*.toc' \
		'*.out' \
		'*.nav' \
		'*.snm' \
		'*.vrb' \
		'' \
		'# Editor and IDE files' \
		'.vscode/' \
		'.idea/' \
		'*.swp' \
		'*.swo' \
		'*~' \
		'.DS_Store' \
		'Thumbs.db' \
		'' \
		'# IMPORTANT: Do NOT ignore fonts - they need to be checked in!' \
		'# fonts/*.ttf and fonts/*.otf should be committed to git' \
		> .gitignore

# Local Makefile wrapper
Makefile: | .git
	@echo "• Creating Makefile"
	@printf '%s\n' \
		'# Include bones build rules' \
		'# This allows you to use "make pdf" instead of "bones pdf"' \
		'# and customize variables for your project' \
		'' \
		'# Detect bones installation' \
		'BONES_RULES := $$(shell command -v bones >/dev/null 2>&1 && bones --print-rules 2>/dev/null || echo /usr/local/share/bones/rules.mk)' \
		'' \
		'# If bones --print-rules is not available, fall back to standard location' \
		'ifeq ($$(BONES_RULES),)' \
		'  BONES_RULES := /usr/local/share/bones/rules.mk' \
		'endif' \
		'' \
		'include $$(BONES_RULES)' \
		'' \
		'# Customize your build here (optional)' \
		'# PDF_OUTPUT = my-book.pdf' \
		'# SRC_DIR = manuscript' \
		'# PANDOC_COMMON_FLAGS += -V author="Your Name"' \
		> Makefile

# GitHub Actions workflows
.github/workflows/ci.yml: | .git
	@echo "• Creating GitHub Actions workflows"
	@mkdir -p .github/workflows
	@cp $(BONES_HOME)templates/ci.yml .github/workflows/ci.yml
	@cp $(BONES_HOME)templates/lineedit.yml .github/workflows/lineedit.yml
	@cp $(BONES_HOME)templates/copyedit.yml .github/workflows/copyedit.yml
	@cp $(BONES_HOME)templates/audiobook.yml .github/workflows/audiobook.yml

# Update existing workflows from templates
update-workflows:
	@if [ ! -d .github/workflows ]; then \
		echo "Error: .github/workflows/ directory not found."; \
		echo "Run 'bones init' first to initialize the project."; \
		exit 1; \
	fi
	@echo "• Updating GitHub Actions workflows from templates"
	@cp $(BONES_HOME)templates/ci.yml .github/workflows/ci.yml
	@cp $(BONES_HOME)templates/lineedit.yml .github/workflows/lineedit.yml
	@cp $(BONES_HOME)templates/copyedit.yml .github/workflows/copyedit.yml
	@cp $(BONES_HOME)templates/audiobook.yml .github/workflows/audiobook.yml
	@echo "✓ Workflows updated successfully"
	@echo ""
	@echo "Files updated:"
	@echo "  .github/workflows/ci.yml"
	@echo "  .github/workflows/lineedit.yml"
	@echo "  .github/workflows/copyedit.yml"
	@echo "  .github/workflows/audiobook.yml"
	@echo ""
	@echo "Review changes with: git diff .github/workflows/"

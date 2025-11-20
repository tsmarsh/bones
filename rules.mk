# ===================== Source of truth =====================
# Determine where this rules.mk file is located (for installed vs local usage)
BONES_HOME    := $(dir $(lastword $(MAKEFILE_LIST)))

SRC_DIR       ?= chapters  # canonical source directory
BUILD_DIR     ?= build
OBJ_DIR       := $(BUILD_DIR)/obj
SCRIPTS_DIR   ?= $(BONES_HOME)scripts
OUTLINES_DIR  ?= outlines

MANIFEST      := $(OBJ_DIR)/chapters.txt   # ordered list of chapter sources
DEPFILE       := $(OBJ_DIR)/combined.d     # auto deps for combined.md

# ===================== Outputs =====================
PDF_OUTPUT    ?= book.pdf
DOCX_OUTPUT   ?= $(BUILD_DIR)/book.docx
EPUB_OUTPUT   ?= $(BUILD_DIR)/book.epub
COMBINED_MD   ?= $(OBJ_DIR)/combined.md
TEX_OUTPUT    ?= $(OBJ_DIR)/book.tex
TEX_BASENAME  := $(basename $(notdir $(TEX_OUTPUT)))
PDF_BUILD     ?= $(OBJ_DIR)/$(TEX_BASENAME).pdf
COVER_JPG     ?= $(BUILD_DIR)/cover.jpg

# Text / audio
TXT_DIR       ?= $(OBJ_DIR)/txt
MP3_DIR       ?= $(BUILD_DIR)/mp3
ELEVENLABS_VOICE ?= Xb7hH8MSUJpSbSDYk0k2   # Alice - young adult female
ELEVENLABS_API_KEY ?= $(shell echo $$ELEVENLABS_API_KEY)

# ===================== Tools =====================
PANDOC        ?= pandoc
PDF_ENGINE    ?=
DETECTED_ENGINE := $(shell command -v tectonic >/dev/null 2>&1 && echo tectonic || true)
ENGINE := $(strip $(if $(PDF_ENGINE),$(PDF_ENGINE),$(DETECTED_ENGINE)))

# ===================== Pandoc flags =====================
PANDOC_COMMON_FLAGS ?= --toc
DOC_CLASS     ?= book
TOP_LEVEL_DIV ?= chapter

PANDOC_COMMON_FLAGS += \
  -V documentclass=$(DOC_CLASS) \
  --top-level-division=$(TOP_LEVEL_DIV) \
  -V fontsize=12pt \
  -V geometry:margin=1.2in \
  -V mainfont="Libertinus Serif" \
  -V sansfont="Libertinus Sans" \
  -V monofont="Libertinus Mono" \
  -V CJKmainfont="Noto Serif CJK SC" \
  -V linestretch=1.25 \
  -V indent=true \
  -V parskip=0pt \
  -V colorlinks=true \
  -V linkcolor=MidnightBlue \
  -V urlcolor=RoyalBlue \
  -V papersize=6in,9in \
  -V secnumdepth=0

COVER_HEADER := $(OBJ_DIR)/cover-header.tex

# ===================== Defaults & safety =====================
.DEFAULT_GOAL := pdf
.DELETE_ON_ERROR:
.SECONDARY: $(COMBINED_MD) $(TEX_OUTPUT) $(PDF_BUILD) $(COVER_JPG) $(COVER_HEADER)
.SECONDEXPANSION:                    # enables $$ expansion in prerequisites

# ===================== Short, descriptive targets =====================
# NOTE: these are *not* phony; they depend on actual artifacts.
CHAPTER_SOURCES := $(wildcard $(strip $(SRC_DIR))/*.md)
TXT_TARGETS := $(patsubst $(strip $(SRC_DIR))/%.md,$(TXT_DIR)/%.txt,$(CHAPTER_SOURCES))
MP3_TARGETS := $(patsubst $(TXT_DIR)/%.txt,$(MP3_DIR)/%.mp3,$(TXT_TARGETS))

pdf:  $(PDF_OUTPUT)
tex:  $(TEX_OUTPUT)
doc:  $(DOCX_OUTPUT)
epub: $(EPUB_OUTPUT)
txt:  $(TXT_TARGETS)
mp3:  $(MP3_TARGETS)

# Helper targets
.PHONY: help check-tools list clean distclean clean.mp3 lineedit copyedit

help:
	@echo "Available targets:"
	@echo "  pdf      - Build PDF (default)"
	@echo "  tex      - Generate LaTeX"
	@echo "  docx     - Build DOCX"
	@echo "  epub     - Build EPUB"
	@echo "  txt      - Generate plain text files for TTS"
	@echo "  mp3      - Generate MP3 audiobook"
	@echo "  lineedit - Run LLM line editor and save to git branch"
	@echo "  copyedit - Run LLM copy editor with style guide and save to git branch"
	@echo "  list     - Show chapter order"
	@echo "  clean    - Remove build artifacts"
	@echo ""
	@echo "Variables:"
	@echo "  SRC_DIR=$(SRC_DIR)"
	@echo "  BUILD_DIR=$(BUILD_DIR)"
	@echo "  PDF_OUTPUT=$(PDF_OUTPUT)"
	@echo "  PDF_ENGINE=$(ENGINE)"

check-tools:
	@command -v $(PANDOC) >/dev/null 2>&1 || { echo "Error: pandoc not found. Please install pandoc."; exit 1; }
	@command -v python3 >/dev/null 2>&1 || { echo "Error: python3 not found. Please install python3."; exit 1; }
	@echo "✓ All required tools found"

debug:
	@echo "SRC_DIR: $(SRC_DIR)"
	@echo "CHAPTER_SOURCES: $(CHAPTER_SOURCES)"
	@echo "TXT_TARGETS: $(TXT_TARGETS)"
	@echo "MP3_TARGETS: $(MP3_TARGETS)"

list: $(MANIFEST)
	@cat $(MANIFEST)

# ===================== Build graph =====================

# Ensure directories exist
$(BUILD_DIR) $(OBJ_DIR) $(TXT_DIR) $(MP3_DIR):
	@mkdir -p $@

# Cover image: PNG → JPEG
$(COVER_JPG): cover/cover.png | $(BUILD_DIR)
	@echo "• Converting cover → $@"
	@ffmpeg -i "$<" -q:v 2 -y "$@"

# Cover header for LaTeX
$(COVER_HEADER): $(COVER_JPG) | $(OBJ_DIR)
	@echo "• Generating cover header → $@"
	@cp -f $(COVER_JPG) $(OBJ_DIR)/cover.jpg
	@printf '%s\n' \
		'\usepackage{graphicx}' \
		'\usepackage{eso-pic}' \
		'\AtBeginDocument{' \
		'  \clearpage' \
		'  \thispagestyle{empty}' \
		'  \AddToShipoutPictureBG*{\includegraphics[width=\paperwidth,height=\paperheight]{cover.jpg}}' \
		'  \mbox{}' \
		'  \clearpage' \
		'}' \
		> $@

# Manifest: ordered chapter list (version sort)
$(MANIFEST): | $(OBJ_DIR)
	@echo "• Scanning $(SRC_DIR) → $@"
	@find $(SRC_DIR) -maxdepth 1 -name '*.md' -type f | sort -V > $@ || { echo "No chapters found in $(SRC_DIR)"; exit 1; }
	@[ -s $@ ] || { echo "No chapters found in $(SRC_DIR)"; rm -f $@; exit 1; }

# Auto-generated deps: combined.md depends on all chapters in manifest
$(DEPFILE): $(MANIFEST) | $(OBJ_DIR)
	@printf '%s: ' "$(COMBINED_MD)" > $@
	@tr '\n' ' ' < $(MANIFEST) >> $@
	@echo >> $@

# Include deps if present (first run will skip)
-include $(DEPFILE)

# Combine chapters with page breaks, in manifest order
$(COMBINED_MD): $(MANIFEST) $(DEPFILE) | $(OBJ_DIR)
	@echo "• Combining chapters → $@"
	@awk 'NR==FNR{a[NR]=$$0; n=NR; next} \
	     END{for(i=1;i<=n;i++){ \
	            system("cat \"" a[i] "\""); \
	            if(i<n) print "\n```{=latex}\n\\newpage\n```\n" \
	         }}' $(MANIFEST) /dev/null > $@.tmp
	@mv $@.tmp $@

# LaTeX from combined markdown
$(TEX_OUTPUT): $(COMBINED_MD) $(COVER_HEADER) | $(OBJ_DIR)
	@echo "• Generating LaTeX → $@"
	$(PANDOC) -s -t latex $(PANDOC_COMMON_FLAGS) --include-in-header=$(COVER_HEADER) -o $@ $(COMBINED_MD)

# PDF from TeX (tectonic preferred; otherwise run engine twice)
$(PDF_OUTPUT): $(TEX_OUTPUT)
	@echo "• Building PDF → $@"
	@if [ -z "$(ENGINE)" ]; then \
		echo "No PDF engine found. Install 'tectonic' (recommended) or set PDF_ENGINE=xelatex/lualatex."; \
		exit 2; \
	fi
	@if [ "$(ENGINE)" = "tectonic" ]; then \
		tectonic -o $(OBJ_DIR) --keep-logs --keep-intermediates $(TEX_OUTPUT); \
	else \
		$(ENGINE) -interaction=nonstopmode -halt-on-error -output-directory=$(OBJ_DIR) $(TEX_OUTPUT) && \
		$(ENGINE) -interaction=nonstopmode -halt-on-error -output-directory=$(OBJ_DIR) $(TEX_OUTPUT); \
	fi
	@cp -f $(PDF_BUILD) $(PDF_OUTPUT)

# DOCX from combined markdown
$(DOCX_OUTPUT): $(COMBINED_MD) | $(BUILD_DIR)
	@echo "• Generating DOCX → $@"
	$(PANDOC) -s $(PANDOC_COMMON_FLAGS) -o $@ $(COMBINED_MD)

# EPUB from combined markdown
$(EPUB_OUTPUT): $(COMBINED_MD) | $(BUILD_DIR)
	@echo "• Generating EPUB → $@"
	$(PANDOC) -s $(PANDOC_COMMON_FLAGS) -o $@ $(COMBINED_MD)

# ===================== TXT / MP3 pipeline (per-file, incremental) =====================

# Chapter → Plain text (pandoc)
$(strip $(TXT_DIR))/%.txt: $(strip $(SRC_DIR))/%.md | $(strip $(TXT_DIR))
	@echo "• TXT: $< → $@"
	$(PANDOC) -f markdown -t plain --wrap=none "$<" -o "$@"

# TXT → MP3 (TTS)
$(strip $(MP3_DIR))/%.mp3: $(strip $(TXT_DIR))/%.txt | $(strip $(MP3_DIR))
	@if [ -z "$(ELEVENLABS_API_KEY)" ]; then echo "Error: ELEVENLABS_API_KEY not set"; exit 1; fi
	@echo "• MP3:  $< → $@"
	python3 $(strip $(SCRIPTS_DIR))/llm_elevenlabs_tts.py "$<" "$@" --voice-id "$(ELEVENLABS_VOICE)"

# ===================== LLM Line Editing =====================
EDIT_BRANCH ?= edits/$(shell date +%Y%m%d-%H%M%S)
COPYEDIT_BRANCH ?= copyedit/$(shell date +%Y%m%d-%H%M%S)

lineedit:
	@echo "• Creating branch $(EDIT_BRANCH)"
	@git checkout -b $(EDIT_BRANCH)
	@for src in $(CHAPTER_SOURCES); do \
		python3 $(SCRIPTS_DIR)/line_editor.py "$$src" --overwrite; \
	done
	@git add $(CHAPTER_SOURCES)
	@git commit -m "LLM line edits - review before merging"
	@echo ""
	@echo "✓ Edits committed to branch $(EDIT_BRANCH)"
	@echo ""
	@echo "Review changes with:"
	@echo "  git diff main"
	@echo "  git log -p"
	@echo ""
	@echo "To accept all changes:"
	@echo "  git checkout main && git merge $(EDIT_BRANCH)"
	@echo ""
	@echo "To selectively accept changes:"
	@echo "  git checkout main"
	@echo "  git checkout -p $(EDIT_BRANCH) -- $(SRC_DIR)"
	@echo "  git commit -m 'Apply selected line edits'"
	@echo ""
	@echo "To reject:"
	@echo "  git checkout main && git branch -D $(EDIT_BRANCH)"

copyedit:
	@if [ ! -d "$(OUTLINES_DIR)" ]; then \
		echo "Error: Outlines directory not found at $(OUTLINES_DIR)"; \
		exit 1; \
	fi
	@echo "• Generating copy edit reviews"
	@for src in $(CHAPTER_SOURCES); do \
		python3 $(SCRIPTS_DIR)/copy_editor.py "$$src" --outlines-dir "$(OUTLINES_DIR)"; \
	done
	@echo ""
	@echo "✓ Reviews saved to build/reviews/"
	@echo ""
	@echo "Review the suggestions:"
	@echo "  ls build/reviews/"
	@echo "  cat build/reviews/0-prologue-review.md"

# ===================== Cleaning =====================
clean: clean.mp3
	@rm -f $(PDF_OUTPUT) $(DOCX_OUTPUT) $(EPUB_OUTPUT)
	@rm -rf $(OBJ_DIR)

clean.mp3:  ; @rm -rf $(MP3_DIR)

distclean: clean
	@rm -rf $(BUILD_DIR)
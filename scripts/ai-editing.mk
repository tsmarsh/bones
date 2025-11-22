# =====================================================================
# AI-Assisted Editing Tools
# =====================================================================
# LLM-powered line editing and copy editing for manuscript refinement.
# These tools create git branches for easy review and selective merging.

# ===================== LLM Editing =====================
LINEEDIT_BRANCH ?= lineedit/$(shell date +%Y%m%d-%H%M%S)
COPYEDIT_BRANCH ?= copyedit/$(shell date +%Y%m%d-%H%M%S)

lineedit:
	@if [ ! -d "$(OUTLINES_DIR)" ]; then \
		echo "Error: Outlines directory not found at $(OUTLINES_DIR)"; \
		exit 1; \
	fi
	@echo "• Generating line edit reviews"
	@for src in $(CHAPTER_SOURCES); do \
		python3 $(SCRIPTS_DIR)/line_editor.py "$$src" --outlines-dir "$(OUTLINES_DIR)"; \
	done
	@echo ""
	@echo "✓ Reviews saved to build/reviews/"
	@echo ""
	@echo "Review the suggestions:"
	@echo "  ls build/reviews/"
	@echo "  cat build/reviews/0-prologue-review.md"

copyedit:
	@echo "• Creating branch $(COPYEDIT_BRANCH)"
	@git checkout -b $(COPYEDIT_BRANCH)
	@for src in $(CHAPTER_SOURCES); do \
		python3 $(SCRIPTS_DIR)/copy_editor.py "$$src" --overwrite; \
	done
	@git add $(CHAPTER_SOURCES)
	@git commit -m "LLM copy edits - review before merging"
	@echo ""
	@echo "✓ Edits committed to branch $(COPYEDIT_BRANCH)"
	@echo ""
	@echo "Review changes with:"
	@echo "  git diff main"
	@echo "  git log -p"
	@echo ""
	@echo "To accept all changes:"
	@echo "  git checkout main && git merge $(COPYEDIT_BRANCH)"
	@echo ""
	@echo "To selectively accept changes:"
	@echo "  git checkout main"
	@echo "  git checkout -p $(COPYEDIT_BRANCH) -- $(SRC_DIR)"
	@echo "  git commit -m 'Apply selected copy edits'"
	@echo ""
	@echo "To reject:"
	@echo "  git checkout main && git branch -D $(COPYEDIT_BRANCH)"

# =====================================================================
# AI-Assisted Editing Tools
# =====================================================================
# LLM-powered line editing and copy editing for manuscript refinement.
# These tools create git branches for easy review and selective merging.

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

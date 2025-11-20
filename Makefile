# =====================================================================
# Bones - Makefile-based Book Pipeline
# =====================================================================
# This Makefile installs the bones system to /usr/local
#
# Usage:
#   sudo make install      - Install bones system-wide
#   sudo make uninstall    - Remove bones from system
#   make test              - Test installation without installing
#
# After installation, use bones in any directory:
#   bones pdf              - Build PDF
#   bones help             - Show available targets
#
# Or include rules.mk directly in your own Makefile:
#   include /usr/local/share/bones/rules.mk

.PHONY: help install uninstall test

# Installation paths
PREFIX       ?= /usr/local
INSTALL_DIR  := $(PREFIX)/share/bones
BIN_DIR      := $(PREFIX)/bin
BONES_BIN    := $(BIN_DIR)/bones

help:
	@echo "Bones Installer"
	@echo ""
	@echo "Targets:"
	@echo "  install     - Install bones system-wide (requires sudo)"
	@echo "  uninstall   - Remove bones from system (requires sudo)"
	@echo "  test        - Test that required tools are available"
	@echo ""
	@echo "After installation, use 'bones <target>' in any directory."
	@echo "Example: bones pdf"

install:
	@echo "Installing bones to $(PREFIX)..."
	@# Create installation directories
	@mkdir -p $(INSTALL_DIR)
	@mkdir -p $(INSTALL_DIR)/scripts
	@mkdir -p $(INSTALL_DIR)/templates
	@mkdir -p $(BIN_DIR)
	@mkdir -p $(PREFIX)/share/zsh/site-functions
	@# Copy rules and scripts
	@echo "  • Installing rules.mk → $(INSTALL_DIR)/"
	@cp -f rules.mk $(INSTALL_DIR)/rules.mk
	@echo "  • Installing scripts → $(INSTALL_DIR)/scripts/"
	@cp -f scripts/*.py $(INSTALL_DIR)/scripts/
	@chmod +x $(INSTALL_DIR)/scripts/*.py
	@echo "  • Installing templates → $(INSTALL_DIR)/templates/"
	@cp -f templates/*.yml $(INSTALL_DIR)/templates/
	@chmod 644 $(INSTALL_DIR)/templates/*.yml
	@echo "  • Installing cover.png → $(INSTALL_DIR)/"
	@cp -f cover.png $(INSTALL_DIR)/cover.png
	@echo "  • Installing zsh completion → $(PREFIX)/share/zsh/site-functions/"
	@cp -f completions/_bones $(PREFIX)/share/zsh/site-functions/_bones
	@chmod 644 $(PREFIX)/share/zsh/site-functions/_bones
	@# Create bones wrapper script
	@echo "  • Creating bones command → $(BONES_BIN)"
	@printf '%s\n' \
		'#!/bin/sh' \
		'# Bones - Makefile-based Book Pipeline' \
		'# Auto-generated wrapper script' \
		'' \
		'BONES_RULES="$(INSTALL_DIR)/rules.mk"' \
		'' \
		'if [ ! -f "$$BONES_RULES" ]; then' \
		'    echo "Error: bones rules not found at $$BONES_RULES" >&2' \
		'    exit 1' \
		'fi' \
		'' \
		'exec make -f "$$BONES_RULES" "$$@"' \
		> $(BONES_BIN)
	@chmod +x $(BONES_BIN)
	@echo ""
	@echo "✓ Installation complete!"
	@echo ""
	@echo "Usage:"
	@echo "  bones pdf       - Build PDF"
	@echo "  bones help      - Show all targets"
	@echo ""
	@echo "Shell completion:"
	@echo "  Zsh completion installed to $(PREFIX)/share/zsh/site-functions/"
	@echo "  Restart your shell or run: exec zsh"
	@echo ""
	@echo "Or include in your own Makefile:"
	@echo "  include $(INSTALL_DIR)/rules.mk"

uninstall:
	@echo "Removing bones from $(PREFIX)..."
	@rm -rf $(INSTALL_DIR)
	@rm -f $(BONES_BIN)
	@rm -f $(PREFIX)/share/zsh/site-functions/_bones
	@echo "✓ Uninstallation complete"

test:
	@echo "Checking for required tools..."
	@command -v make >/dev/null 2>&1 || { echo "  ✗ make not found"; exit 1; }
	@echo "  ✓ make"
	@command -v python3 >/dev/null 2>&1 || { echo "  ✗ python3 not found"; exit 1; }
	@echo "  ✓ python3"
	@command -v pandoc >/dev/null 2>&1 || { echo "  ✗ pandoc not found (optional but recommended)"; }
	@command -v pandoc >/dev/null 2>&1 && echo "  ✓ pandoc" || true
	@command -v tectonic >/dev/null 2>&1 || { echo "  ✗ tectonic not found (optional but recommended)"; }
	@command -v tectonic >/dev/null 2>&1 && echo "  ✓ tectonic" || true
	@echo ""
	@echo "All required tools found!"

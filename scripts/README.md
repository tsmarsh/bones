# AI-Assisted Publishing Scripts

This directory contains professional-grade scripts for AI-assisted publishing workflows.

## Scripts Overview

### **Core Scripts**
- **`llm_client.py`** - Shared LLM client with multi-backend support (ollama, openai, anthropic)
- **`line_editor.py`** - Professional line editor for fiction
- **`copy_editor.py`** - Copy editor with style guide and context awareness
- **`llm_elevenlabs_tts.py`** - Enhanced ElevenLabs TTS with intelligent chunking

### **Utility Scripts**
- **`list_elevenlabs_voices.py`** - List available ElevenLabs voices

## Usage

All scripts are designed to work with the main Makefile. Use the make targets instead of running scripts directly:

```bash
# Line editing
make lineedit          # Apply line edits to all chapters

# Copy editing
make copyedit          # Generate copy edit reviews

# Text-to-Speech
make txt               # Generate plain text files for TTS
make mp3               # Generate MP3 audiobook

# Build outputs
make pdf               # Build PDF
make docx              # Build DOCX
make epub              # Build EPUB

# Clean up
make clean             # Remove build artifacts
make clean.mp3         # Remove MP3 files
```

## Features

### **Line Editor**
- **Context-Aware** - Loads style guide and world-building from outlines/
- **Consistency Checking** - Ensures character voices and terminology match
- **Review Generation** - Creates detailed reviews with specific suggestions
- **Multi-Backend Support** - Works with Ollama, OpenAI, or Anthropic

### **Copy Editor**
- **Professional Fiction Editing** - Improves clarity, grammar, flow, and word choice
- **Voice Preservation** - Maintains author's unique style
- **Multi-Backend Support** - Works with Ollama, OpenAI, or Anthropic
- **In-Place Editing** - Directly updates chapter files

### **LLM Client**
- **Multi-Backend** - Unified interface for ollama, openai, anthropic
- **Retry Logic** - Exponential backoff for rate limiting
- **Timeout Handling** - Prevents hanging on slow requests
- **Clean API** - Simple, consistent interface

### **ElevenLabs TTS**
- **Plain Text Conversion** - Markdown → clean text for TTS
- **Error Handling** - Retry logic with exponential backoff
- **Quota Management** - Handles API limits gracefully
- **Per-Chapter Processing** - Generates individual MP3 files

## Configuration

### **Environment Variables**
```bash
# LLM Backend Configuration
export LLM_BACKEND=anthropic       # or ollama, openai
export LLM_MODEL=claude-3-7-sonnet-20250219

# Anthropic API
export ANTHROPIC_API_KEY=your_key_here

# OpenAI API (optional)
export OPENAI_BASE_URL=https://api.openai.com/v1/chat/completions
export OPENAI_API_KEY=your_key_here

# Ollama (optional)
export OLLAMA_HOST=http://localhost:11434

# ElevenLabs TTS
export ELEVENLABS_API_KEY=your_key_here
export ELEVENLABS_VOICE=Xb7hH8MSUJpSbSDYk0k2  # Alice voice
```

### **Voice Selection**
Use `list_elevenlabs_voices.py` to see available voices:
```bash
python3 scripts/list_elevenlabs_voices.py
```

## Dependencies

```bash
# Core dependencies
pip install requests

# For Ollama
ollama pull llama3.1:8b

# For OpenAI
# Set OPENAI_API_KEY environment variable
```

## Architecture

### **Shared LLM Client**
All editing scripts use a common `llm_client.py` module that provides:
- **Backend Abstraction** - Unified API across different LLM providers
- **Retry Logic** - Exponential backoff for rate limits (HTTP 429/529)
- **Timeout Handling** - 120-second timeout prevents hanging
- **Error Messages** - Clear, actionable error reporting

### **Editing Pipeline**
1. **Load Context** - Read style guide and chapter content
2. **LLM Processing** - Send to configured backend for editing/review
3. **Post-Processing** - Clean up markdown fences and formatting
4. **Output** - Write edited content or review to disk

### **TTS Pipeline**
1. **Text Extraction** - Convert markdown to plain text via Pandoc
2. **API Request** - Send to ElevenLabs with retry logic
3. **MP3 Generation** - Receive and save audio file

All scripts include comprehensive doctests and follow Python best practices.

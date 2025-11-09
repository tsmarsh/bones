# AI-Assisted Publishing Scripts

This directory contains professional-grade scripts for AI-assisted publishing workflows.

## Scripts Overview

### **Core LLM Scripts**
- **`line_editor.py`** - Professional line editor with CriticMarkup support
- **`llm_ssml_generator.py`** - LLM-powered SSML generation for speech synthesis
- **`llm_elevenlabs_tts.py`** - Enhanced ElevenLabs TTS with intelligent chunking

### **Utility Scripts**
- **`list_elevenlabs_voices.py`** - List available ElevenLabs voices

## Usage

All scripts are designed to work with the main Makefile. Use the make targets instead of running scripts directly:

```bash
# Line editing
make edit-lines        # Apply line editing
make edit-lines-diff   # Preview changes

# SSML generation
make ssml              # Generate SSML files
make ssml-audio        # Generate SSML in build/audio/

# TTS conversion
make elevenlabs-ssml   # Convert SSML to MP3

# Clean up
make clean-ssml        # Clean SSML files
make clean-ssml-audio  # Clean audio SSML files
make clean-elevenlabs-ssml  # Clean MP3 files
make clean-edited      # Clean edited files
```

## Features

### **Professional Line Editor**
- **CriticMarkup Integration** - Industry-standard tracked changes
- **Content Protection** - Preserves code, links, tables
- **LLM Intelligence** - Real AI-powered editing
- **Flexible Backends** - Ollama or OpenAI

### **LLM SSML Generator**
- **Smart Content Masking** - Protects non-prose content
- **Intelligent Chunking** - Handles long documents
- **Professional SSML** - Clean, valid markup
- **Flexible Backends** - Ollama or OpenAI

### **Enhanced ElevenLabs TTS**
- **Intelligent Chunking** - Splits long SSML automatically
- **Audio Concatenation** - Seamlessly combines chunks
- **Error Handling** - Retry logic with exponential backoff
- **Quota Management** - Handles API limits gracefully

## Configuration

### **Environment Variables**
```bash
# LLM Backend
export LLM_BACKEND=ollama          # or openai
export LLM_MODEL=llama3.1:8b       # or your preferred model

# ElevenLabs
export ELEVENLABS_API_KEY=your_key_here
export ELEVENLABS_VOICE=Xb7hH8MSUJpSbSDYk0k2  # Alice voice

# Ollama
export OLLAMA_URL=http://localhost:11434/api/generate

# OpenAI
export OPENAI_BASE_URL=https://api.openai.com/v1/chat/completions
export OPENAI_API_KEY=your_key_here
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

All scripts follow the same professional pattern:
1. **Content Masking** - Protect non-prose content from AI processing
2. **Intelligent Chunking** - Handle long documents automatically
3. **LLM Processing** - Use AI for intelligent editing and generation
4. **Error Handling** - Robust retry logic with exponential backoff
5. **Professional Output** - Clean, valid results with proper formatting

This ensures consistent, reliable operation across all AI-assisted workflows with professional-grade quality.

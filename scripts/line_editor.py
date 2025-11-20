#!/usr/bin/env python3
"""
Line Editor (LLM-assisted)

Sends full chapter to LLM for line editing and returns only the edited markdown.

Examples:
    $ python3 line_editor.py chapter.md
    $ python3 line_editor.py chapter.md --backend anthropic
    $ python3 line_editor.py chapter.md -o output.md --instruction "Focus on dialogue"
"""

import argparse
import os
import sys
from pathlib import Path

from llm_client import LLMClient, strip_markdown_fences


# -------------------- Prompts --------------------

SYSTEM_PROMPT = """You are a professional line editor for fiction.

Your task is to edit the provided chapter for:
- Clarity and concision
- Grammar and punctuation
- Sentence flow and rhythm
- Word choice and precision

Make minimal, targeted edits that improve the prose while preserving the author's voice and style.

CRITICAL: You must output ONLY the edited markdown file. Do not include:
- Explanations or commentary
- Notes about changes made
- Markdown code fences (no ```markdown)
- Any text before or after the edited content

Just output the complete edited chapter as clean markdown."""


def build_user_prompt(chapter_text: str, instruction: str = "") -> str:
    """
    Build the user prompt for line editing.

    Args:
        chapter_text: The chapter content to edit
        instruction: Optional additional editing guidance

    Returns:
        Formatted user prompt

    Examples:
        >>> prompt = build_user_prompt("# Chapter 1\\nHello world")
        >>> "Line edit the following chapter" in prompt
        True
        >>> "# Chapter 1" in prompt
        True
        >>> prompt = build_user_prompt("text", "Focus on X")
        >>> "Focus on X" in prompt
        True
    """
    if instruction:
        return f"""Additional guidance: {instruction}

Now, line edit the following chapter. Output ONLY the edited chapter as markdown, with no additional commentary:

{chapter_text}"""
    else:
        return f"""Line edit the following chapter. Output ONLY the edited chapter as markdown, with no additional commentary:

{chapter_text}"""


# -------------------- Main --------------------

def main():
    """
    Main entry point for line editor.

    Returns:
        0 on success, 1 on error
    """
    ap = argparse.ArgumentParser(description="LLM-assisted line editor")
    ap.add_argument("input_file", help="Chapter file to edit")
    ap.add_argument("-o", "--output", help="Output file (default: overwrite input)")
    ap.add_argument("--instruction", default="", help="Additional editing guidance")
    ap.add_argument("--backend", choices=["ollama","openai","anthropic"], default=os.environ.get("LLM_BACKEND","anthropic"))
    ap.add_argument("--model", default=os.environ.get("LLM_MODEL","claude-3-7-sonnet-20250219"))
    ap.add_argument("--temperature", type=float, default=0.3)
    args = ap.parse_args()

    # Read input file
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input_file}", file=sys.stderr)
        return 1

    chapter_text = input_path.read_text(encoding='utf-8')

    # Run LLM
    print(f"• Using {args.backend}/{args.model}", file=sys.stderr)
    print(f"• Line editing {input_path.name}...", file=sys.stderr)
    client = LLMClient(args.backend, args.model, args.temperature)
    edited = client.generate(SYSTEM_PROMPT, build_user_prompt(chapter_text, args.instruction))

    # Strip any potential markdown code fences the LLM might add
    edited = strip_markdown_fences(edited)

    # Write output
    output_path = Path(args.output) if args.output else input_path
    output_path.write_text(edited, encoding='utf-8')
    print(f"✓ Edited → {output_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Line Editor (LLM-assisted)

Sends full chapter to LLM for line editing and returns only the edited markdown.

Examples:
    $ python3 line_editor.py chapter.md                    # saves to chapter.edited.md
    $ python3 line_editor.py chapter.md --overwrite        # overwrites chapter.md
    $ python3 line_editor.py chapter.md -o output.md       # saves to output.md
    $ python3 line_editor.py chapter.md --instruction "Focus on dialogue"
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
    ap.add_argument("-o", "--output", help="Output file (default: input_file.edited.md)")
    ap.add_argument("--overwrite", action="store_true", help="Overwrite input file instead of creating .edited.md")
    ap.add_argument("--instruction", default="", help="Additional editing guidance")
    ap.add_argument("--backend", choices=["ollama","openai","anthropic"], default=os.environ.get("LLM_BACKEND","anthropic"))
    ap.add_argument("--model", default=os.environ.get("LLM_MODEL","claude-3-7-sonnet-20250219"))
    ap.add_argument("--temperature", type=float, default=0.3)
    args = ap.parse_args()

    # Validate argument combinations
    if args.output and args.overwrite:
        print("Error: Cannot use both -o/--output and --overwrite", file=sys.stderr)
        return 1

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

    # Determine output path with safety checks
    if args.output:
        # Explicit output file specified
        output_path = Path(args.output)
    elif args.overwrite:
        # User explicitly wants to overwrite
        output_path = input_path
    else:
        # Safe default: create .edited.md file
        stem = input_path.stem
        suffix = input_path.suffix
        output_path = input_path.with_name(f"{stem}.edited{suffix}")

    # Write output
    output_path.write_text(edited, encoding='utf-8')

    if output_path == input_path:
        print(f"✓ Edited (overwritten) → {output_path}", file=sys.stderr)
    else:
        print(f"✓ Edited → {output_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())

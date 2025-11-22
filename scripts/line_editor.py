#!/usr/bin/env python3
"""
Line Editor (LLM-assisted)

Loads context from outlines/ directory and sends full chapter to LLM for line editing.
Outputs a review with specific suggestions for improvement.

Examples:
    $ python3 line_editor.py chapter.md
    $ python3 line_editor.py chapter.md --backend anthropic
    $ python3 line_editor.py chapter.md --outlines-dir outlines -o review.md
"""

import argparse
import os
import sys
from pathlib import Path

from llm_client import LLMClient


# -------------------- Context loading --------------------

def load_context(outlines_dir: str) -> str:
    """
    Load all markdown files from outlines directory as context.

    Args:
        outlines_dir: Path to directory containing context files

    Returns:
        Combined context from all .md files

    Examples:
        >>> import tempfile
        >>> import os
        >>> tmpdir = tempfile.mkdtemp()
        >>> _ = Path(tmpdir, "test.md").write_text("# Test\\nContent")
        >>> context = load_context(tmpdir)
        >>> "# Test" in context
        True
        >>> "Content" in context
        True
        >>> import shutil
        >>> shutil.rmtree(tmpdir)
    """
    context_parts = []
    outlines_path = Path(outlines_dir)

    if not outlines_path.exists():
        return ""

    # Load all .md files in outlines directory
    for md_file in sorted(outlines_path.glob("*.md")):
        try:
            content = md_file.read_text(encoding='utf-8')
            context_parts.append(f"# Context from {md_file.name}\n\n{content}")
        except Exception as e:
            print(f"Warning: Could not read {md_file}: {e}", file=sys.stderr)

    return "\n\n---\n\n".join(context_parts)


# -------------------- Prompts --------------------

SYSTEM_PROMPT = """You are a professional line editor for fiction.

Your task is to review the provided chapter for:
- Consistency with the style guide, character voices, and world-building
- Pacing and narrative flow
- Proper use of established terminology and language patterns
- Character voice consistency
- Scene structure and emotional beats

Output a prose review with specific suggestions for improvement. For each issue:
1. Quote the relevant text
2. Explain the issue
3. Suggest a specific improvement

Be concise but thorough. Focus on the most important issues."""


def build_user_prompt(context: str, chapter_text: str) -> str:
    """
    Build the user prompt with context and chapter.

    Args:
        context: Style guide and world-building context
        chapter_text: The chapter content to review

    Returns:
        Formatted user prompt

    Examples:
        >>> prompt = build_user_prompt("Style: X", "Chapter text")
        >>> "Style: X" in prompt
        True
        >>> "Chapter text" in prompt
        True
        >>> "review the following chapter" in prompt
        True
    """
    return f"""Here is the context for this work (style guide, characters, locations, language):

{context}

---

Now, review the following chapter according to the style guide and context above. Provide specific suggestions for improvements:

{chapter_text}"""


# -------------------- Main --------------------

def main():
    """
    Main entry point for line editor.

    Returns:
        0 on success, 1 on error
    """
    ap = argparse.ArgumentParser(description="LLM-assisted line editor with style guide context")
    ap.add_argument("input_file", help="Chapter file to edit")
    ap.add_argument("-o", "--output", help="Output file (default: overwrite input)")
    ap.add_argument("--outlines-dir", default="outlines", help="Directory with style guide and context")
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

    # Load context from outlines
    print(f"• Loading context from {args.outlines_dir}/", file=sys.stderr)
    context = load_context(args.outlines_dir)

    if not context:
        print(f"Warning: No context files found in {args.outlines_dir}/", file=sys.stderr)

    # Run LLM
    print(f"• Using {args.backend}/{args.model}", file=sys.stderr)
    print(f"• Reviewing {input_path.name}...", file=sys.stderr)
    client = LLMClient(args.backend, args.model, args.temperature)
    review = client.generate(SYSTEM_PROMPT, build_user_prompt(context, chapter_text))

    # Determine output file: if no -o specified, write to build/reviews/
    if args.output:
        output_path = Path(args.output)
    else:
        reviews_dir = Path("build/reviews")
        reviews_dir.mkdir(parents=True, exist_ok=True)
        output_path = reviews_dir / f"{input_path.stem}-review.md"

    # Write review
    output_path.write_text(review.strip(), encoding='utf-8')
    print(f"✓ Review → {output_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())

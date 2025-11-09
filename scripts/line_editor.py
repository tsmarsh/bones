#!/usr/bin/env python3
"""
Line Editor (LLM-assisted)
- Sends full chapter to LLM for line editing
- Returns only the edited markdown (no commentary)
"""

import argparse
import os
import sys
import json
from pathlib import Path

# -------------------- Model client --------------------

class LLMClient:
    def __init__(self, backend: str, model: str, temperature: float = 0.3):
        self.backend = backend
        self.model = model
        self.temperature = temperature

        if backend == 'ollama':
            import urllib.request
            self._url = os.environ.get('OLLAMA_URL', 'http://localhost:11434/api/generate')
            self._post = self._ollama_post
        elif backend == 'openai':
            import urllib.request
            self._url = os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1/chat/completions')
            self._key = os.environ.get('OPENAI_API_KEY', '')
            self._post = self._openai_post
        else:
            raise ValueError("backend must be 'ollama' or 'openai'")

    def _ollama_post(self, system_prompt: str, user_prompt: str) -> str:
        import urllib.request
        payload = {
            "model": self.model,
            "prompt": f"{system_prompt}\n\n{user_prompt}",
            "stream": False,
            "options": {"temperature": self.temperature}
        }
        req = urllib.request.Request(self._url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read().decode('utf-8'))
            return data.get('response', '')

    def _openai_post(self, system_prompt: str, user_prompt: str) -> str:
        import urllib.request
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self._key}',
        }
        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        req = urllib.request.Request(self._url,
            data=json.dumps(payload).encode('utf-8'),
            headers=headers)
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read().decode('utf-8'))
            return data['choices'][0]['message']['content']

    def edit(self, system_prompt: str, user_prompt: str) -> str:
        return self._post(system_prompt, user_prompt)

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
    """Build the user prompt"""
    if instruction:
        return f"""Additional guidance: {instruction}

Now, line edit the following chapter. Output ONLY the edited chapter as markdown, with no additional commentary:

{chapter_text}"""
    else:
        return f"""Line edit the following chapter. Output ONLY the edited chapter as markdown, with no additional commentary:

{chapter_text}"""

# -------------------- Main --------------------

def main():
    ap = argparse.ArgumentParser(description="LLM-assisted line editor")
    ap.add_argument("input_file", help="Chapter file to edit")
    ap.add_argument("-o", "--output", help="Output file (default: overwrite input)")
    ap.add_argument("--instruction", default="", help="Additional editing guidance")
    ap.add_argument("--backend", choices=["ollama","openai"], default=os.environ.get("LLM_BACKEND","ollama"))
    ap.add_argument("--model", default=os.environ.get("LLM_MODEL","llama3.1"))
    ap.add_argument("--temperature", type=float, default=0.3)
    args = ap.parse_args()

    # Read input file
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input_file}", file=sys.stderr)
        return 1

    chapter_text = input_path.read_text(encoding='utf-8')

    # Run LLM
    print(f"• Line editing {input_path.name}...", file=sys.stderr)
    client = LLMClient(args.backend, args.model, args.temperature)
    edited = client.edit(SYSTEM_PROMPT, build_user_prompt(chapter_text, args.instruction))

    # Strip any potential markdown code fences the LLM might add
    edited = edited.strip()
    if edited.startswith("```markdown"):
        edited = edited[len("```markdown"):].strip()
    if edited.startswith("```"):
        edited = edited[3:].strip()
    if edited.endswith("```"):
        edited = edited[:-3].strip()

    # Write output
    output_path = Path(args.output) if args.output else input_path
    output_path.write_text(edited, encoding='utf-8')
    print(f"✓ Edited → {output_path}", file=sys.stderr)

    return 0

if __name__ == "__main__":
    sys.exit(main())

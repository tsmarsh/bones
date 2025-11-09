#!/usr/bin/env python3
"""
LLM SSML Generator (Ollama/OpenAI-compatible)
- Masks code/links/tables so only prose is processed
- Uses structured prompts for consistent SSML output
- Supports chunking for long documents
"""

import argparse, os, sys, json, re, textwrap
from dataclasses import dataclass
from typing import List, Tuple

# -------------------- Masking (reused from line_editor) --------------------

FENCE_RE = re.compile(r'```.*?```', re.S)
INLINE_CODE_RE = re.compile(r'`[^`]*`')
LINK_RE = re.compile(r'\[([^\]]+)\]\([^)]+\)')
IMG_RE = re.compile(r'!\[([^\]]*)\]\([^)]+\)')
TABLE_RE = re.compile(r'^\|.*\|\s*$', re.M)

@dataclass
class Mask:
    token: str
    payload: str

def mask_regions(s: str) -> Tuple[str, List[Mask]]:
    masks: List[Mask] = []
    def _mask(rx: re.Pattern, prefix: str):
        nonlocal s
        out, idx = [], 0
        for m in rx.finditer(s):
            out.append(s[idx:m.start()])
            token = f'@@{prefix}{len(masks)}@@'
            masks.append(Mask(token, m.group(0)))
            out.append(token)
            idx = m.end()
        out.append(s[idx:])
        s = ''.join(out)

    _mask(FENCE_RE,  'FENCE_')
    _mask(TABLE_RE,  'TABLE_')
    _mask(IMG_RE,    'IMG_')
    _mask(LINK_RE,   'LINK_')
    _mask(INLINE_CODE_RE, 'INLINE_')
    return s, masks

def unmask_regions(s: str, masks: List[Mask]) -> str:
    for m in masks:
        s = s.replace(m.token, m.payload)
    return s

# -------------------- Chunking --------------------

def split_paragraphs(md: str) -> List[str]:
    parts = md.split('\n\n')
    return parts

def approx_token_len(text: str) -> int:
    return max(1, len(text.split()))

def chunk_paragraphs(paras: List[str], max_tokens=2000) -> List[List[int]]:
    chunks, cur, budget = [], [], 0
    for i, p in enumerate(paras):
        cost = approx_token_len(p)
        if budget + cost > max_tokens and cur:
            chunks.append(cur)
            cur, budget = [], 0
        cur.append(i)
        budget += cost
    if cur:
        chunks.append(cur)
    return chunks

# -------------------- LLM Client --------------------

class LLMClient:
    def __init__(self, backend: str, model: str, temperature: float = 0.7):
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

    def _ollama_post(self, prompt: str) -> str:
        import urllib.request, json
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": self.temperature}
        }
        req = urllib.request.Request(self._url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read().decode('utf-8'))
            return data.get('response', '')

    def _openai_post(self, prompt: str) -> str:
        import urllib.request, json
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self._key}',
        }
        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": [
                {"role": "system", "content": SSML_SYS_PROMPT},
                {"role": "user", "content": prompt}
            ]
        }
        req = urllib.request.Request(self._url,
            data=json.dumps(payload).encode('utf-8'),
            headers=headers)
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read().decode('utf-8'))
            return data['choices'][0]['message']['content']

    def generate_ssml(self, text: str, chapter_name: str) -> str:
        prompt = build_ssml_prompt(text, chapter_name)
        return self._post(prompt)

# -------------------- SSML Prompts --------------------

SSML_SYS_PROMPT = """Convert narrative text to SSML for ElevenLabs text-to-speech.

CRITICAL RULES:
- Output MUST start with <speak> and end with </speak>
- NO explanations, NO comments, NO meta-text
- NO markdown (no ```, no #, no lists)
- NO prompt echoing (don't repeat instructions)
- ONLY use these tags: <break time="..."/>, <emphasis level="strong|moderate">

ALLOWED SSML:
- <break time="0.5s"/> or <break time="500ms"/> for pauses
- <emphasis level="strong">text</emphasis> for emphasis
- Plain text for everything else

DO NOT USE: <voice>, <prosody>, <say-as>, <phoneme>, or any other tags.
DO NOT EXPLAIN what you did or why.
RETURN ONLY THE SSML - nothing else."""

def build_ssml_prompt(text: str, chapter_name: str) -> str:
    return f"""Convert to SSML:

{text}"""

# -------------------- Core Pipeline --------------------

def process_with_llm(md: str, client: LLMClient, chapter_name: str) -> str:
    paras = split_paragraphs(md)
    idx_chunks = chunk_paragraphs(paras, max_tokens=2000)

    ssml_parts = []

    for i, chunk in enumerate(idx_chunks):
        block = '\n\n'.join(paras[j] for j in chunk)

        masked, masks = mask_regions(block)
        ssml_chunk = client.generate_ssml(masked, f"{chapter_name}_chunk_{i+1}")

        if not ssml_chunk.strip():
            continue

        ssml_unmasked = unmask_regions(ssml_chunk, masks)

        # Clean up the SSML response
        ssml_clean = clean_ssml_response(ssml_unmasked)

        # Remove outer speak tags from ALL chunks (we'll add one pair at the end)
        ssml_clean = ssml_clean.replace('<speak>', '').replace('</speak>', '')

        ssml_parts.append(ssml_clean)

    # Combine all parts with proper SSML structure
    final_ssml = '<speak>\n' + '\n'.join(ssml_parts) + '\n</speak>'

    # Final validation
    final_ssml = validate_ssml(final_ssml)

    return final_ssml

def validate_ssml(ssml: str) -> str:
    """Validate and fix common SSML issues"""

    # Remove all speak tags (including those with attributes) and rebuild
    ssml = re.sub(r'<speak[^>]*>', '', ssml)
    ssml = re.sub(r'</speak>', '', ssml)
    ssml = ssml.strip()

    # Check for unclosed break tags (should be self-closing)
    ssml = re.sub(r'<break\s+([^>]*[^/])>', r'<break \1/>', ssml)

    # Remove xmlns and version attributes from any remaining tags
    ssml = re.sub(r'\s+xmlns="[^"]*"', '', ssml)
    ssml = re.sub(r'\s+version="[^"]*"', '', ssml)

    # Remove any remaining invalid characters that might cause issues
    ssml = ssml.replace('\x00', '')  # null bytes

    # Wrap in single clean speak tag
    ssml = f'<speak>\n{ssml}\n</speak>'

    return ssml

def clean_ssml_response(ssml: str) -> str:
    """Clean up SSML response from LLM"""

    # Step 1: Remove markdown code fences
    ssml = re.sub(r'```[a-z]*\n?', '', ssml)
    ssml = re.sub(r'```', '', ssml)

    # Step 2: Remove HTML comments
    ssml = re.sub(r'<!--.*?-->', '', ssml, flags=re.S)

    # Step 3: Remove explanatory text blocks (often at start/end)
    # Remove common explanatory phrases
    ssml = re.sub(r'Please note that.*?$', '', ssml, flags=re.M|re.I)
    ssml = re.sub(r'Note that I.*?$', '', ssml, flags=re.M|re.I)
    ssml = re.sub(r'Also note that.*?$', '', ssml, flags=re.M|re.I)
    ssml = re.sub(r'This SSML markup includes:.*?$', '', ssml, flags=re.M|re.I)
    ssml = re.sub(r'You can adjust.*?$', '', ssml, flags=re.M|re.I)
    ssml = re.sub(r'I used different voices.*?$', '', ssml, flags=re.M|re.I)
    ssml = re.sub(r"I've added emphasis.*?$", '', ssml, flags=re.M|re.I)
    ssml = re.sub(r"I've used.*?$", '', ssml, flags=re.M|re.I)

    # Remove prompt markers (case-insensitive)
    ssml = re.sub(r'«begin»', '', ssml, flags=re.I)
    ssml = re.sub(r'«end»', '', ssml, flags=re.I)
    ssml = re.sub(r'<<begin>>', '', ssml, flags=re.I)
    ssml = re.sub(r'<<end>>', '', ssml, flags=re.I)

    # Remove markdown headings (more aggressive)
    ssml = re.sub(r'^#+\s+.*?$', '', ssml, flags=re.M)
    ssml = re.sub(r'^#[A-Za-z].*?$', '', ssml, flags=re.M)  # Catch headings without space after #

    # Remove text to convert header
    ssml = re.sub(r'^Text to convert:.*?$', '', ssml, flags=re.M|re.I)

    # Remove LLM explanatory statements (typically at start or end)
    ssml = re.sub(r"^Here's (?:your text converted|the text).*?:", '', ssml, flags=re.M|re.I)
    ssml = re.sub(r"In this case,.*", '', ssml, flags=re.S|re.I)  # Remove everything after "In this case"
    ssml = re.sub(r"I've (?:tried to follow|added|used).*", '', ssml, flags=re.S|re.I)
    ssml = re.sub(r"This (?:is just one|SSML|markup|conversion).*", '', ssml, flags=re.S|re.I)

    # Step 4: Remove focus/instructions that appear early in output
    lines = ssml.split('\n')
    cleaned_lines = []
    skip_patterns = [
        r'^\d+\.\s',  # numbered lists
        r'^#+\s',  # markdown headings
        r'^focus on:',
        r'^focus on\b',
        r'^here is',
        r'^i also',
        r'^i defined',
        r'^note:',
        r'^also,',
        r'please let me know',
        r'we can use',
        r'i assumed',
        r'if you want',
        r'this will',
        r'you can adjust',
        r'according to your',
        r'^natural speech flow',
        r'^character dialogue',
        r'^narrative pacing',
        r'^pronunciation hints',
        r'^emotional tone',
        r'^return only',
        r"i've added",
        r"i added",
    ]

    for line in lines:
        line_stripped = line.strip()
        # Skip empty lines
        if not line_stripped:
            continue
        # Skip lines matching explanatory patterns
        if any(re.match(pattern, line_stripped, re.I) for pattern in skip_patterns):
            continue
        # Skip lines that start with bullets or asterisks
        if line_stripped.startswith('*') or line_stripped.startswith('-'):
            continue
        cleaned_lines.append(line_stripped)

    ssml = '\n'.join(cleaned_lines)

    # Step 4: Remove all speak tags (we'll add one clean pair at the end)
    ssml = re.sub(r'</?speak>', '', ssml)

    # Step 5: Fix invalid tag names
    # Replace <pause> with <break> (handle both duration and milliseconds attributes)
    ssml = re.sub(r'<pause\s+duration="([^"]+)"\s*/>', r'<break time="\1"/>', ssml)
    ssml = re.sub(r'<pause\s+milliseconds="([^"]+)"\s*/>', r'<break time="\1ms"/>', ssml)

    # Replace HTML tags with plain text or remove
    ssml = re.sub(r'</?p>', '', ssml)
    ssml = re.sub(r'</?t>', '', ssml)
    ssml = re.sub(r'</?li>', '', ssml)
    ssml = re.sub(r'</?ul>', '', ssml)
    ssml = re.sub(r'</?ol>', '', ssml)
    ssml = re.sub(r'</?list>', '', ssml)
    ssml = re.sub(r'</?item>', '', ssml)
    ssml = re.sub(r'</?audio[^>]*>', '', ssml)
    ssml = re.sub(r'<strong>([^<]+)</strong>', r'<emphasis level="strong">\1</emphasis>', ssml)
    ssml = re.sub(r'</?em>', '', ssml)

    # Step 6: Remove invalid custom voice tags (keep content, remove tags)
    # Remove custom voice names that aren't standard
    ssml = re.sub(r'</?(?:RamónVoice|WolfgangVoice|ChimeVoice|AstridVoice|EchoVoice|BeaVoice)>', '', ssml)

    # Step 7: Simplify voice tags - remove nested or just strip for now
    # For ElevenLabs, we typically use a single voice, so we can remove voice tags
    ssml = re.sub(r'<voice\s+name="[^"]+">([^<]*)</voice>', r'\1', ssml)

    # Step 8: Fix prosody tags - ElevenLabs has limited support, simplify
    ssml = re.sub(r'<prosody[^>]*>([^<]*)</prosody>', r'\1', ssml)

    # Step 9: Clean up whitespace
    ssml = re.sub(r'\n\s*\n+', '\n', ssml)  # multiple blank lines to single
    ssml = ssml.strip()

    # Clean up multiple consecutive break tags (keep only first)
    ssml = re.sub(r'(<break[^>]*/>)\s*(<break[^>]*/>)+', r'\1', ssml)

    # Remove leading break tags at the start
    ssml = re.sub(r'^(\s*<break[^>]*/>\s*)+', '', ssml)

    # Step 10: Ensure proper SSML structure
    if not ssml:
        ssml = 'No content to speak.'

    # Wrap in speak tags
    ssml = f'<speak>\n{ssml}\n</speak>'

    # Step 11: Aggressive tag whitelisting - remove ALL invalid XML/SSML tags
    # Only keep: break, emphasis, and plain text
    # This is aggressive but ensures clean SSML for ElevenLabs

    # Remove XML declarations
    ssml = re.sub(r'<\?xml[^>]*\?>', '', ssml)
    ssml = re.sub(r'</?ssml>', '', ssml)

    # Remove ALL voice tags (ElevenLabs uses single voice)
    ssml = re.sub(r'<voice[^>]*>([^<]*)</voice>', r'\1', ssml)
    ssml = re.sub(r'</?voice[^>]*>', '', ssml)

    # Remove invalid pseudo-tags like <Alice voice="...">
    ssml = re.sub(r'<[A-Z][a-z]+\s+voice="[^"]*">', '', ssml)
    ssml = re.sub(r'</[A-Z][a-z]+>', '', ssml)

    # Remove narrator-style tags like <Echo's voice...>
    ssml = re.sub(r'<[^>]*voice[^>]*>', '', ssml)

    # Remove invalid tags like <says who=...>
    ssml = re.sub(r'<says[^>]*>[^<]*</says>', lambda m: m.group(0).replace('<says'+m.group(0)[5:m.group(0).find('>')]+'>','').replace('</says>',''), ssml)
    ssml = re.sub(r'</?says[^>]*>', '', ssml)

    # Remove orphaned closing tags
    ssml = re.sub(r'</(?:break|text|voice|prosody|p|t|li|audio|emphasis|Alice|Bob|Echo|Chime|greetings)[^>]*>', '', ssml)

    # Remove invalid custom tags (anything that's not break or emphasis)
    # This catches tags like <greetings>, <foo>, etc.
    # Valid SSML tags for ElevenLabs: break, emphasis (we've already stripped voice, prosody, etc.)
    ssml = re.sub(r'</?(?!break|emphasis|speak)([a-z]+)[^>]*>', '', ssml)

    # Remove empty tags
    ssml = re.sub(r'<(\w+)[^>]*>\s*</\1>', '', ssml)

    # Remove any lines that are just closing tags or fragments
    lines = ssml.split('\n')
    cleaned = [line for line in lines if not re.match(r'^\s*</[^>]+>\s*$', line)]
    ssml = '\n'.join(cleaned)

    # Final pass: keep only allowed content
    # Allowed: text, <break .../>, <emphasis>...</emphasis>
    # Everything else gets stripped

    return ssml

# -------------------- CLI --------------------

def main():
    ap = argparse.ArgumentParser(description="LLM SSML Generator")
    ap.add_argument("input_file")
    ap.add_argument("-o", "--output", help="Output SSML file")
    ap.add_argument("--backend", choices=["ollama","openai"], default=os.environ.get("LLM_BACKEND","ollama"))
    ap.add_argument("--model", default=os.environ.get("LLM_MODEL","llama3.1:8b"))
    ap.add_argument("--temperature", type=float, default=0.7)
    args = ap.parse_args()

    path = args.input_file
    chapter_name = os.path.splitext(os.path.basename(path))[0]
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    client = LLMClient(args.backend, args.model, args.temperature)
    ssml = process_with_llm(content, client, chapter_name)

    output_path = args.output or f"{chapter_name}.ssml"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ssml)
    
    print(f"✓ Generated SSML: {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())


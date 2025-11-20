#!/usr/bin/env python3
"""
Shared LLM client for line_editor and copy_editor.

Supports multiple backends: ollama, openai, anthropic
Dependency-free: Uses standard library only (urllib).
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from typing import Optional, Dict, Any


class LLMClient:
    """
    Multi-backend LLM client with unified retry logic and error handling.

    Supports:
    - ollama: Local models via Ollama
    - openai: OpenAI API (and compatible APIs like DeepSeek, Groq)
    - anthropic: Anthropic Claude API

    Examples:
        >>> client = LLMClient('anthropic', 'claude-3-7-sonnet-20250219')
        >>> isinstance(client.model, str)
        True
        >>> client = LLMClient('ollama', 'llama2')
        >>> client.backend
        'ollama'
    """

    def __init__(self, backend: str, model: str, temperature: float = 0.3):
        """
        Initialize LLM client.

        Args:
            backend: One of 'ollama', 'openai', 'anthropic'
            model: Model name/identifier
            temperature: Sampling temperature (0.0-1.0)

        Raises:
            ValueError: If backend is not supported

        Examples:
            >>> client = LLMClient('ollama', 'llama2')
            >>> client.backend
            'ollama'
            >>> client.temperature
            0.3
        """
        self.backend = backend
        self.model = model
        self.temperature = temperature

        if backend == 'ollama':
            ollama_host = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
            self._url = f"{ollama_host.rstrip('/')}/api/generate"
        elif backend == 'openai':
            self._url = os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1/chat/completions')
            self._key = os.environ.get('OPENAI_API_KEY', '')
        elif backend == 'anthropic':
            self._url = 'https://api.anthropic.com/v1/messages'
            self._key = os.environ.get('ANTHROPIC_API_KEY', '')
        else:
            raise ValueError("backend must be 'ollama', 'openai', or 'anthropic'")

    def _execute_request(self, req: urllib.request.Request, max_retries: int = 5) -> Dict[str, Any]:
        """
        Execute HTTP request with exponential backoff retry logic.
        Handles timeouts, rate limits (429), and server errors (5xx).
        """
        for attempt in range(max_retries):
            try:
                # Timeout set to 120s for long chain-of-thought reasoning
                with urllib.request.urlopen(req, timeout=120) as r:
                    return json.loads(r.read().decode('utf-8'))
            
            except urllib.error.HTTPError as e:
                # Read error body for debugging
                error_body = e.read().decode('utf-8') if e.fp else "No error details"
                
                # Retry on Rate Limit (429) or Server Error (5xx)
                if e.code == 429 or (500 <= e.code < 600):
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 2  # 2, 4, 8, 16s
                        print(f"  ⚠ API Error {e.code}, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})", file=sys.stderr)
                        time.sleep(wait_time)
                        continue
                
                # Fatal error (400, 401, 403, etc.)
                raise Exception(f"HTTP {e.code}: {error_body}")
            
            except (urllib.error.URLError, TimeoutError) as e:
                if attempt < max_retries - 1:
                    wait_time = 2
                    print(f"  ⚠ Network Error: {e}, retrying in {wait_time}s...", file=sys.stderr)
                    time.sleep(wait_time)
                    continue
                raise Exception(f"Network failed after {max_retries} attempts: {e}")
            
            except Exception as e:
                raise Exception(f"Unexpected error: {e}")
        
        raise Exception(f"Failed after {max_retries} attempts")

    def _ollama_post(self, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": f"{system_prompt}\n\n{user_prompt}",
            "stream": False,
            "options": {"temperature": self.temperature}
        }
        req = urllib.request.Request(
            self._url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        data = self._execute_request(req)
        return data.get('response', '')

    def _openai_post(self, system_prompt: str, user_prompt: str) -> str:
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
        req = urllib.request.Request(
            self._url,
            data=json.dumps(payload).encode('utf-8'),
            headers=headers
        )
        data = self._execute_request(req)
        
        try:
            return data['choices'][0]['message']['content']
        except (KeyError, IndexError):
            # Fallback for debugging unexpected API responses
            raise Exception(f"Unexpected OpenAI response format: {json.dumps(data)}")

    def _anthropic_post(self, system_prompt: str, user_prompt: str) -> str:
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': self._key,
            'anthropic-version': '2023-06-01'
        }
        payload = {
            "model": self.model,
            "max_tokens": 8192,
            "temperature": self.temperature,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt}
            ]
        }
        req = urllib.request.Request(
            self._url,
            data=json.dumps(payload).encode('utf-8'),
            headers=headers
        )
        data = self._execute_request(req)
        
        try:
            return data['content'][0]['text']
        except (KeyError, IndexError):
            raise Exception(f"Unexpected Anthropic response format: {json.dumps(data)}")

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Generate text using the configured backend.

        Args:
            system_prompt: System-level instructions
            user_prompt: User's actual prompt

        Returns:
            Model response text
        """
        if self.backend == 'ollama':
            return self._ollama_post(system_prompt, user_prompt)
        elif self.backend == 'openai':
            return self._openai_post(system_prompt, user_prompt)
        elif self.backend == 'anthropic':
            return self._anthropic_post(system_prompt, user_prompt)
        else:
            raise ValueError(f"Unknown backend: {self.backend}")


def strip_markdown_fences(text: str) -> str:
    """
    Remove markdown code fences and "Here is..." chatter that LLMs sometimes add.

    Args:
        text: Text potentially wrapped in markdown fences

    Returns:
        Text with fences removed

    Examples:
        >>> strip_markdown_fences("```markdown\\nHello\\n```")
        'Hello'
        >>> strip_markdown_fences("```\\nHello\\n```")
        'Hello'
        >>> strip_markdown_fences("Hello")
        'Hello'
        >>> strip_markdown_fences("  ```\\nHello\\n```  ")
        'Hello'
        >>> strip_markdown_fences("Here is the edited chapter:\\n```markdown\\nHello\\n```")
        'Hello'
    """
    text = text.strip()
    
    # Remove common "Here is the edited text:" prefixes
    if text.lower().startswith("here is"):
        lines = text.split('\n', 1)
        if len(lines) > 1:
            # If the first line is just chatter, check the second
            if lines[0].lower().strip().endswith(":") or "markdown" in lines[0].lower():
                text = lines[1].strip()

    # Strip fences
    if text.startswith("```markdown"):
        text = text[len("```markdown"):].strip()
    elif text.startswith("```"):
        text = text[3:].strip()
        
    if text.endswith("```"):
        text = text[:-3].strip()
        
    return text


if __name__ == "__main__":
    print("Running doctests...")
    import doctest
    doctest.testmod()
    print("Done.")

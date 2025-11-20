#!/usr/bin/env python3
"""
Shared LLM client for line_editor and copy_editor.

Supports multiple backends: ollama, openai, anthropic
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from typing import Optional


class LLMClient:
    """
    Multi-backend LLM client with retry logic.

    Supports:
    - ollama: Local models via Ollama
    - openai: OpenAI API (and compatible APIs)
    - anthropic: Anthropic Claude API

    Examples:
        >>> client = LLMClient('anthropic', 'claude-3-7-sonnet-20250219')
        >>> # Response would be generated here
        >>> isinstance(client.model, str)
        True
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
            self._post = self._ollama_post
        elif backend == 'openai':
            self._url = os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1/chat/completions')
            self._key = os.environ.get('OPENAI_API_KEY', '')
            self._post = self._openai_post
        elif backend == 'anthropic':
            self._url = 'https://api.anthropic.com/v1/messages'
            self._key = os.environ.get('ANTHROPIC_API_KEY', '')
            self._post = self._anthropic_post
        else:
            raise ValueError("backend must be 'ollama', 'openai', or 'anthropic'")

    def _ollama_post(self, system_prompt: str, user_prompt: str) -> str:
        """
        Post to Ollama API.

        Args:
            system_prompt: System-level instructions
            user_prompt: User's actual prompt

        Returns:
            Model response text
        """
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
        """
        Post to OpenAI-compatible API.

        Args:
            system_prompt: System-level instructions
            user_prompt: User's actual prompt

        Returns:
            Model response text
        """
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

    def _anthropic_post(self, system_prompt: str, user_prompt: str) -> str:
        """
        Post to Anthropic API with retry logic.

        Implements exponential backoff for rate limiting (HTTP 429/529).

        Args:
            system_prompt: System-level instructions
            user_prompt: User's actual prompt

        Returns:
            Model response text

        Raises:
            Exception: After max retries or non-retryable errors
        """
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

        # Retry logic with exponential backoff
        max_retries = 5
        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(self._url,
                    data=json.dumps(payload).encode('utf-8'),
                    headers=headers)
                with urllib.request.urlopen(req, timeout=120) as r:
                    data = json.loads(r.read().decode('utf-8'))
                    return data['content'][0]['text']
            except urllib.error.HTTPError as e:
                if e.code == 529 or e.code == 429:  # Rate limit or overloaded
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 2  # Exponential backoff: 2, 4, 8, 16 seconds
                        print(f"  Rate limited (HTTP {e.code}), retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})", file=sys.stderr)
                        time.sleep(wait_time)
                        continue
                # Read error response for better debugging
                error_body = e.read().decode('utf-8') if e.fp else "No error details"
                raise Exception(f"HTTP {e.code}: {error_body}")
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 2
                    print(f"  Error: {e}, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})", file=sys.stderr)
                    time.sleep(wait_time)
                    continue
                raise

        raise Exception(f"Failed after {max_retries} attempts")

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Generate text using the configured backend.

        Args:
            system_prompt: System-level instructions
            user_prompt: User's actual prompt

        Returns:
            Model response text

        Note:
            Requires a running backend (ollama, openai, or anthropic).
            See class docstring for backend setup.
        """
        return self._post(system_prompt, user_prompt)


def strip_markdown_fences(text: str) -> str:
    """
    Remove markdown code fences that LLMs sometimes add.

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
    """
    text = text.strip()
    if text.startswith("```markdown"):
        text = text[len("```markdown"):].strip()
    if text.startswith("```"):
        text = text[3:].strip()
    if text.endswith("```"):
        text = text[:-3].strip()
    return text


if __name__ == "__main__":
    import doctest
    doctest.testmod()

#!/usr/bin/env python3
"""
LLM ElevenLabs TTS (Enhanced)
- Handles long SSML files with intelligent chunking
- Combines audio segments seamlessly
- Supports multiple voice models
- Error handling and retry logic
"""

import argparse, os, sys, json, re, time
from dataclasses import dataclass
from typing import List, Optional
import urllib.request
import urllib.error

# -------------------- SSML Processing --------------------

def split_ssml_content(ssml_content: str, max_chars: int = 8000) -> List[str]:
    """Split SSML content into smaller chunks for processing"""
    # Remove outer speak tags for splitting
    content = ssml_content.replace('<speak>', '').replace('</speak>', '').strip()
    
    # Split by sentences (roughly)
    sentences = content.split('. ')
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk + sentence) < max_chars:
            current_chunk += sentence + ". "
        else:
            if current_chunk:
                chunks.append(f"<speak>{current_chunk.strip()}</speak>")
            current_chunk = sentence + ". "
    
    if current_chunk:
        chunks.append(f"<speak>{current_chunk.strip()}</speak>")
    
    return chunks

def clean_ssml_for_elevenlabs(ssml: str) -> str:
    """Clean SSML for ElevenLabs compatibility"""
    # Remove unsupported tags
    ssml = re.sub(r'<phoneme[^>]*>', '', ssml)
    ssml = re.sub(r'</phoneme>', '', ssml)
    ssml = re.sub(r'<say-as[^>]*>', '', ssml)
    ssml = re.sub(r'</say-as>', '', ssml)
    
    # Convert to simpler format that ElevenLabs understands
    ssml = re.sub(r'<break time="([^"]*)"[^>]*>', r'<break time="\1"/>', ssml)
    ssml = re.sub(r'<prosody rate="([^"]*)"[^>]*>', r'<prosody rate="\1">', ssml)
    ssml = re.sub(r'<emphasis level="([^"]*)"[^>]*>', r'<emphasis level="\1">', ssml)
    
    return ssml

# -------------------- ElevenLabs Client --------------------

class ElevenLabsClient:
    def __init__(self, api_key: str, voice_id: str, model_id: str = "eleven_multilingual_v2"):
        self.api_key = api_key
        self.voice_id = voice_id
        self.model_id = model_id
        self.base_url = "https://api.elevenlabs.io/v1"
        
    def generate_audio(self, text: str, max_retries: int = 3) -> Optional[bytes]:
        """Generate audio from text with retry logic"""
        url = f"{self.base_url}/text-to-speech/{self.voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        payload = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5,
                "style": 0.0,
                "use_speaker_boost": True
            }
        }
        
        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(url,
                    data=json.dumps(payload).encode('utf-8'),
                    headers=headers)
                
                with urllib.request.urlopen(req, timeout=300) as response:
                    if response.status == 200:
                        return response.read()
                    else:
                        error_text = response.read().decode('utf-8')
                        print(f"API error (attempt {attempt + 1}): {response.status}")
                        print(f"Response: {error_text}")
                        
                        # Check for specific errors
                        if "quota_exceeded" in error_text:
                            print("Quota exceeded. Please wait or upgrade your plan.")
                            return None
                        elif "max_character_limit_exceeded" in error_text:
                            print("Character limit exceeded. Text too long.")
                            return None
                            
            except urllib.error.HTTPError as e:
                print(f"HTTP error (attempt {attempt + 1}): {e.code}")
                if e.code == 401:
                    print("Authentication failed. Check your API key.")
                    return None
                elif e.code == 429:
                    print("Rate limited. Waiting before retry...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
            except urllib.error.URLError as e:
                print(f"Network error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
            except Exception as e:
                print(f"Unexpected error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
        
        return None

# -------------------- Audio Processing --------------------

def combine_audio_chunks(chunks: List[bytes]) -> bytes:
    """Combine multiple audio chunks into single MP3"""
    # Simple concatenation - in production you might want to use pydub
    # for proper audio merging with fade-in/fade-out
    return b''.join(chunks)

def estimate_audio_duration(text: str) -> float:
    """Rough estimate of audio duration in seconds"""
    # Average speaking rate: ~150 words per minute
    words = len(text.split())
    return (words / 150) * 60

# -------------------- Core Pipeline --------------------

def process_ssml_to_mp3(ssml_file: str, output_file: str, client: ElevenLabsClient) -> bool:
    """Process SSML file to MP3 with intelligent chunking"""
    
    # Read SSML file
    with open(ssml_file, 'r', encoding='utf-8') as f:
        ssml_content = f.read()
    
    # Clean SSML for ElevenLabs
    cleaned_ssml = clean_ssml_for_elevenlabs(ssml_content)
    
    # Check if content is too long
    if len(cleaned_ssml) > 8000:
        print(f"SSML content too long ({len(cleaned_ssml)} chars), splitting into chunks...")
        chunks = split_ssml_content(cleaned_ssml)
        print(f"Split into {len(chunks)} chunks")
        
        # Process each chunk
        audio_chunks = []
        for i, chunk in enumerate(chunks):
            print(f"Processing chunk {i+1}/{len(chunks)}...")
            audio_data = client.generate_audio(chunk)
            
            if audio_data:
                audio_chunks.append(audio_data)
                print(f"✓ Chunk {i+1} generated ({len(audio_data)} bytes)")
            else:
                print(f"✗ Failed to process chunk {i+1}")
                return False
        
        # Combine audio chunks
        if audio_chunks:
            combined_audio = combine_audio_chunks(audio_chunks)
            with open(output_file, 'wb') as f:
                f.write(combined_audio)
            print(f"✓ Generated: {output_file}")
            return True
        else:
            return False
    else:
        # Single chunk processing
        print(f"Processing single chunk ({len(cleaned_ssml)} chars)...")
        audio_data = client.generate_audio(cleaned_ssml)
        
        if audio_data:
            with open(output_file, 'wb') as f:
                f.write(audio_data)
            print(f"✓ Generated: {output_file}")
            return True
        else:
            return False

# -------------------- CLI --------------------

def main():
    ap = argparse.ArgumentParser(description="LLM ElevenLabs TTS")
    ap.add_argument("ssml_file", help="Input SSML file")
    ap.add_argument("output_file", help="Output MP3 file")
    ap.add_argument("--voice-id", default=os.environ.get("ELEVENLABS_VOICE", "Xb7hH8MSUJpSbSDYk0k2"))
    ap.add_argument("--model-id", default="eleven_multilingual_v2")
    ap.add_argument("--api-key", help="ElevenLabs API key (or set ELEVENLABS_API_KEY)")
    args = ap.parse_args()

    # Get API key
    api_key = args.api_key or os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        print("Error: ElevenLabs API key not provided")
        print("Set ELEVENLABS_API_KEY environment variable or use --api-key")
        return 1

    # Create client
    client = ElevenLabsClient(api_key, args.voice_id, args.model_id)
    
    # Process file
    success = process_ssml_to_mp3(args.ssml_file, args.output_file, client)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())


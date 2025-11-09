#!/usr/bin/env python3
"""
List available ElevenLabs voices
"""

import requests
import os
import sys

def list_voices(api_key):
    """List all available ElevenLabs voices"""
    url = "https://api.elevenlabs.io/v1/voices"
    headers = {
        "Accept": "application/json",
        "xi-api-key": api_key
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            voices = response.json()
            print("Available ElevenLabs voices:")
            print("-" * 50)
            for voice in voices['voices']:
                print(f"Name: {voice['name']}")
                print(f"ID: {voice['voice_id']}")
                print(f"Category: {voice.get('category', 'N/A')}")
                print("-" * 30)
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error: {e}")

def main():
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        print("Error: ELEVENLABS_API_KEY environment variable not set")
        sys.exit(1)
    
    list_voices(api_key)

if __name__ == '__main__':
    main()


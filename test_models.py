#!/usr/bin/env python3
"""Test which Claude models are available with the API key"""

from anthropic import Anthropic
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('ANTHROPIC_API_KEY')
if not api_key:
    print("❌ No ANTHROPIC_API_KEY found in environment")
    exit(1)

print(f"✓ API key found (starts with: {api_key[:15]}...)")
client = Anthropic(api_key=api_key)

# List of models to try
models_to_try = [
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-20240620", 
    "claude-3-5-sonnet",
    "claude-3-sonnet-20240229",
    "claude-3-opus-20240229",
    "claude-3-haiku-20240307"
]

print("\nTesting available models...\n")
working_model = None

for model in models_to_try:
    try:
        msg = client.messages.create(
            model=model,
            max_tokens=5,
            messages=[{"role": "user", "content": "hi"}]
        )
        print(f"✅ {model} - WORKS!")
        working_model = model
        break
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg or "not_found" in error_msg:
            print(f"❌ {model} - Not found (404)")
        elif "401" in error_msg or "authentication" in error_msg.lower():
            print(f"🔒 {model} - Authentication error (401)")
            break
        else:
            print(f"⚠️  {model} - Error: {error_msg[:80]}")

if working_model:
    print(f"\n✓ Recommended model: {working_model}")
else:
    print("\n❌ No working models found. Please check your API key and account access.")


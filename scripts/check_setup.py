"""Smoke test: is Python, the .env file, and the Gemini API key working?

    python scripts/check_setup.py
"""

import sys

from llm_qa.config import DEFAULT_MODEL, get_api_key, mask
from llm_qa.llm_client import GeminiClient

print(f"Python  : {sys.version.split()[0]}")
print(f"Model   : {DEFAULT_MODEL}")

key = get_api_key()
if not key:
    sys.exit("API key: NOT FOUND -> copy .env.example to .env and set GEMINI_API_KEY")
print(f"API key : {mask(key)}")

response = GeminiClient().generate("Balas hanya dengan satu kata: OK", temperature=0)
print(f"Answer  : {response.text.strip()!r}")
print(f"Latency : {response.latency_s}s")
print(f"Tokens  : input={response.input_tokens} output={response.output_tokens} thinking={response.thinking_tokens}")
print("\nSetup OK")

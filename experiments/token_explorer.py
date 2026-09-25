"""How many tokens does a text cost? Compares Indonesian vs English.

    python experiments/token_explorer.py
    python experiments/token_explorer.py "teks kamu sendiri"

count_tokens is free: it does not generate anything.
"""

import sys

from llm_qa.llm_client import GeminiClient

SAMPLES = [
    "Saya ingin transfer uang ke rekening teman saya.",
    "I want to transfer money to my friend's account.",
    "gw mau tf duit ke rek temen gw dong",
    "Rp1.500.000",
    "Pertanggungjawaban",
    "BBCA BBRI TLKM",
]

client = GeminiClient()
texts = sys.argv[1:] or SAMPLES

max_in, max_out = client.token_limits()
print(f"Model {client.model}: context window {max_in:,} input tokens, max {max_out:,} output tokens\n")

print(f"{'tokens':>6}  {'chars':>5}  {'chars/token':>11}  text")
for text in texts:
    tokens = client.count_tokens(text)
    print(f"{tokens:>6}  {len(text):>5}  {len(text) / tokens:>11.1f}  {text}")

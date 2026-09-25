"""Same user question, different system prompts -> different behaviour.

    python experiments/system_prompt_demo.py

Temperature is 0 so the difference comes from the system prompt, not randomness.
"""

from llm_qa.llm_client import GeminiClient

QUESTION = "Saham apa yang bagus dibeli bulan ini?"

SYSTEM_PROMPTS = {
    "none": None,
    "bank CS (strict)": (
        "Kamu adalah customer service Bank Nusantara. Jawab maksimal 2 kalimat. "
        "Jangan pernah memberi rekomendasi saham spesifik; arahkan ke penasihat keuangan berizin OJK."
    ),
    "english, 1 sentence": "Always answer in English, in exactly one sentence.",
}

client = GeminiClient()
for name, system_prompt in SYSTEM_PROMPTS.items():
    r = client.generate(QUESTION, temperature=0, system_prompt=system_prompt)
    print(f"=== system prompt: {name} ===")
    print(f"(input tokens={r.input_tokens}, output tokens={r.output_tokens}, latency={r.latency_s}s)")
    print(r.text.strip(), "\n")

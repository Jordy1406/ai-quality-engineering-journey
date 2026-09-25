"""Week 1 experiment: send the same prompt N times at different temperatures
and measure how much the answers vary.

    python experiments/temperature_experiment.py
    python experiments/temperature_experiment.py --runs 10 --temps 0 1.0 --delay 4

Saves raw answers (JSON) and a summary table (Markdown) to experiments/results/.
"""

import argparse
import json
import time
from collections import Counter
from datetime import datetime
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path

from llm_qa.llm_client import DailyQuotaExceededError, GeminiClient

DEFAULT_PROMPT = (
    "Berikan satu nama unik untuk aplikasi tabungan digital untuk anak muda Indonesia. "
    "Jawab hanya dengan nama aplikasinya, tanpa penjelasan."
)
RESULTS_DIR = Path(__file__).parent / "results"


def avg_similarity(texts: list[str]) -> float:
    """Average pairwise text similarity: 1.0 = all identical, 0.0 = nothing in common."""
    pairs = list(combinations(texts, 2))
    if not pairs:
        return 1.0
    return sum(SequenceMatcher(None, a, b).ratio() for a, b in pairs) / len(pairs)


def summarize(temperature: float, responses: list) -> dict:
    texts = [r.text.strip() for r in responses]
    top_answer, top_count = Counter(texts).most_common(1)[0]
    return {
        "temperature": temperature,
        "runs": len(texts),
        "unique_answers": len(set(texts)),
        "most_common": top_answer,
        "most_common_count": top_count,
        "avg_similarity": round(avg_similarity(texts), 3),
        "avg_latency_s": round(sum(r.latency_s for r in responses) / len(responses), 2),
        "avg_output_tokens": round(sum(r.output_tokens for r in responses) / len(responses), 1),
        "answers": texts,
    }


def to_markdown(prompt: str, model: str, summaries: list[dict]) -> str:
    lines = [
        f"**Model:** `{model}`  ",
        f"**Prompt:** {prompt}",
        "",
        "| Temperature | Runs | Unique answers | Most common (count) | Avg similarity | Avg latency (s) | Avg output tokens |",
        "|---|---|---|---|---|---|---|",
    ]
    for s in summaries:
        lines.append(
            f"| {s['temperature']} | {s['runs']} | {s['unique_answers']} | "
            f"{s['most_common']} ({s['most_common_count']}) | {s['avg_similarity']} | "
            f"{s['avg_latency_s']} | {s['avg_output_tokens']} |"
        )
    for s in summaries:
        lines += ["", f"<details><summary>All answers at temperature {s['temperature']}</summary>", ""]
        lines += [f"{i}. {a}" for i, a in enumerate(s["answers"], 1)]
        lines += ["", "</details>"]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--temps", type=float, nargs="+", default=[0.0, 1.0])
    parser.add_argument("--delay", type=float, default=0, help="seconds between calls (avoid free-tier rate limits)")
    args = parser.parse_args()

    client = GeminiClient()
    summaries = []
    complete = True
    for temp in args.temps:
        responses = []
        try:
            for i in range(args.runs):
                r = client.generate(args.prompt, temperature=temp)
                responses.append(r)
                print(f"[temp={temp}] run {i + 1}/{args.runs}: {r.text.strip()!r}")
                time.sleep(args.delay)
        except DailyQuotaExceededError as e:
            # Keep what we already paid for instead of losing it.
            print(f"\n[stopped] {e}")
            complete = False
        if responses:
            summaries.append(summarize(temp, responses))
        if not complete:
            break

    if not summaries:
        raise SystemExit("No results collected.")

    RESULTS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S") + ("" if complete else "-partial")
    json_path = RESULTS_DIR / f"temperature_{stamp}.json"
    md_path = RESULTS_DIR / f"temperature_{stamp}.md"
    payload = {"model": client.model, "prompt": args.prompt, "complete": complete, "results": summaries}
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(to_markdown(args.prompt, client.model, summaries), encoding="utf-8")

    print("\n" + to_markdown(args.prompt, client.model, summaries))
    print(f"Saved: {json_path}\n       {md_path}")


if __name__ == "__main__":
    main()

# AI Quality Engineering Journey

A 24-week, hands-on journey from **QA Automation Engineer** to **AI Quality Engineer**: learning how to test, evaluate, and secure LLM-powered applications, with a focus on the **finance domain** and **Indonesian-language** use cases.

LLM output is non-deterministic, so `assert output == expected` doesn't work. This repo is about the replacements: schema validation, safety checks, pass rates over repeated runs, eval metrics, and quality gates in CI.

## Roadmap

| Month | Theme | Status |
|---|---|---|
| 1 | LLM fundamentals + RAG | 🟡 In progress |
| 2 | Eval pipeline + AI failure triage | ⚪ Not started |
| 3 | Agents, MCP, security + portfolio | ⚪ Not started |
| 4 | Specialization: agent eval, OCR, LLM performance | ⚪ Not started |
| 5 | Public reputation + credentials | ⚪ Not started |
| 6 | Job hunt | ⚪ Not started |

### Week 1: LLM fundamentals & first LLM tests

| # | Task | Status |
|---|---|---|
| 1 | Setup repo, Python venv, pytest, Gemini API key | ✅ Done |
| 2 | Learn tokens, temperature, system prompt, context window, non-determinism ([notes](notes/week-01-concepts.md)) | ✅ Done |
| 3 | Experiment: same prompt 10× at temperature 1.0 vs 0 ([results](#results)) | ✅ Done |
| 4 | 3+ pytest tests for LLM output (pydantic JSON schema, forbidden content, pass rate) ([tests](tests/test_llm_output.py)) | ✅ Done |
| 5 | 5+ commits + "what I learned" notes | ⏳ Next |
| 6 | API key in `.env` / GitHub Secrets + API cost limit | 🟡 `.env` done |

Detailed change history: [CHANGELOG.md](CHANGELOG.md)

## Tech stack

- **Python 3.10+**, **pytest**
- **Google Gemini** via the official [`google-genai`](https://pypi.org/project/google-genai/) SDK (default model: `gemini-2.5-flash`)
- **pydantic** for validating structured (JSON) LLM output
- **GitHub Actions** for CI

## Project structure

```
ai-quality-engineering-journey/
├── src/llm_qa/                 # Reusable toolkit, grows week by week
│   ├── config.py               # Loads .env, reads API key & model name
│   ├── llm_client.py           # Gemini wrapper: latency, token usage, retry on 429/5xx
│   ├── validators.py           # JSON schema check, forbidden-content check, pass rate
│   └── tasks.py                # LLM features under test (transaction extractor, bank CS bot)
├── tests/
│   ├── test_validators.py      # Offline tests of the checkers themselves (no API calls)
│   └── test_llm_output.py      # Live tests against Gemini (marker: live)
├── experiments/
│   ├── temperature_experiment.py   # Same prompt N× per temperature, measures variation
│   ├── token_explorer.py           # Token counts (Indonesian vs English vs slang) + context window
│   ├── system_prompt_demo.py       # Same question, different system prompts
│   └── results/                    # Experiment output (JSON + Markdown)
├── notes/week-01-concepts.md   # LLM fundamentals, backed by real measurements
├── scripts/check_setup.py      # Smoke test: is the key loaded and the API reachable?
├── .github/workflows/tests.yml # CI: offline tests on push, live tests on manual run
├── .env.example                # Config template (the real .env is git-ignored)
├── CHANGELOG.md
├── pyproject.toml
├── pytest.ini
└── requirements.txt
```

## Getting started

**1. Clone & create a virtual environment**

```bash
git clone https://github.com/<your-username>/ai-quality-engineering-journey.git
cd ai-quality-engineering-journey
python -m venv .venv
```

Activate it:

```bash
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate
```

**2. Install dependencies**

```bash
pip install -r requirements.txt -e .
```

**3. Add your Gemini API key**

Get a free key at [Google AI Studio](https://aistudio.google.com/apikey), then:

```bash
cp .env.example .env        # Windows: Copy-Item .env.example .env
```

Put the key in `.env` as `GEMINI_API_KEY=...`. The `.env` file is git-ignored and must never be committed.

**4. Verify the setup**

```bash
python scripts/check_setup.py
```

Expected output ends with `Setup OK`, along with latency and token usage.

## Running tests

```bash
pytest -m "not live"   # offline: tests the validators, free, no API key needed
pytest -m live         # live: calls Gemini, uses API quota
pytest                 # everything (live tests auto-skip if no key is set)
```

In CI, offline tests run on every push. Live tests run only when triggered manually from the **Actions** tab, using the `GEMINI_API_KEY` repository secret.

## Results

All numbers come from real runs in this repo (`gemini-2.5-flash`, Sep 2026). Details: [notes/week-01-concepts.md](notes/week-01-concepts.md).

**Week 1: LLM fundamentals**
- **Tokens:** a formal Indonesian sentence used *fewer* tokens than its English equivalent (10 vs 13). Slang (3.2 chars/token) and currency amounts like `Rp1.500.000` (1 char/token) are the expensive cases.
- **Hidden cost:** answering an open stock question used 863 output tokens plus **1,179 invisible "thinking" tokens**. Cost estimates based only on visible output would be off by more than 2×.
- **System prompt:** a strict bank-CS system prompt cut output from 863 to 36 tokens (−96%) and latency from 12.2 s to 2.2 s, while correctly refusing to recommend stocks.
- **Reliability:** hit `503 UNAVAILABLE` (model overloaded) during a run. LLM test suites must separate infrastructure failures from quality failures.

**Week 1: temperature experiment (same prompt 10× per temperature)**

Prompt: *"Berikan satu nama unik untuk aplikasi tabungan digital untuk anak muda Indonesia. Jawab hanya dengan nama aplikasinya, tanpa penjelasan."* ([script](experiments/temperature_experiment.py), [full results](experiments/results/temperature_20260925-211643.md))

| Model | Temperature | Runs | Unique answers | Most common (count) | Avg similarity |
|---|---|---|---|---|---|
| `gemini-3.5-flash-lite` | 0 | 10 | **6** | CelenganGenZ (4) | 0.474 |
| `gemini-3.5-flash-lite` | 1.0 | 10 | **7** | SakuGenZ (2) | 0.462 |
| `gemini-2.5-flash` ¹ | 0 | 8 | **2** | SakuCuan (6) | – |

¹ Partial run: stopped after 8 calls when the free-tier quota (20 requests/day for this model) ran out. Recorded from terminal output.

What I learned:
- **Temperature 0 is not deterministic.** Both models returned different answers to the identical request at temperature 0. With `gemini-3.5-flash-lite` it was almost as varied as temperature 1.0 (6 vs 7 unique answers out of 10).
- **Behavior differs per model.** `gemini-2.5-flash` at temperature 0 was far more stable (2 unique answers) than `gemini-3.5-flash-lite` (6). A test suite tuned on one model can't assume the same stability on another. Re-check the pass rate after every model change.
- **Exact string matching undercounts agreement.** `CelenganGenZ` and `Celengan GenZ` count as different answers. Real checks need normalization or semantic comparison, not `==`.
- **Consequence for testing:** test properties (format, allowed values, safety) and measure a pass rate over N runs, instead of asserting one exact output.

**Week 1: LLM output test suite**

| Test | What it checks | Cases | Result |
|---|---|---|---|
| `test_extraction_matches_schema_and_values` | Transaction extractor returns JSON that matches a strict pydantic schema (no extra keys, allowed categories only, amount > 0), and the amount/category are correct. Run both with prompt-only instructions and with JSON mode. | 4 messages × 2 modes = 8 | 8/8 ✅ |
| `test_cs_answer_has_no_forbidden_content` | Bank CS bot never leaks its system prompt (canary token), gives no specific stock buy call, promises no guaranteed profit, and shows no 16-digit card/NIK numbers. Includes a prompt-injection attempt. | 3 questions | 3/3 ✅ |
| `test_extraction_pass_rate_at_high_temperature` | Same extraction 5× at temperature 1.0 must pass ≥ 80% of the time. | 1 (5 calls) | ✅ |
| `test_validators.py` (offline) | The checkers themselves: 6 kinds of invalid JSON rejected, forbidden patterns caught, negated disclaimers not flagged. | 18 + 1 xfail | ✅ |

Live run: `gemini-3.5-flash-lite`, 12 passed in 50 s (16 API calls).

Known limitations (honest review of my own suite):
- **An all-green run on 4 easy inputs proves little.** The suite needs harder cases: ambiguous amounts ("2 jt-an"), multiple transactions in one message, slang, and typos. That's the job of the golden dataset in week 4.
- **Keyword/regex safety checks are brittle.** A sentence like *"Tidak ada produk yang dijamin untung"* is a good disclaimer but still gets flagged (documented as a strict `xfail`). Semantic checks come in week 5 (LLM-as-judge).
- **Only 5 runs for the pass-rate test.** Cheap on the free tier, but statistically weak: 4/5 and 5/5 both pass.
- `bank` and `counterparty` are schema-checked but not value-checked yet.

## Author

**Jordy Dwi Prakoso**, QA Automation Engineer on the path to AI Quality Engineering.

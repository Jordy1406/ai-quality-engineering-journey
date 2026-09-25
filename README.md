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
| 2 | Learn tokens, temperature, system prompt, context window, non-determinism | ⏳ Next |
| 3 | Experiment: same prompt 10× at temperature 1.0 vs 0 | ⚪ |
| 4 | 3+ pytest tests for LLM output (pydantic JSON schema, forbidden content, pass rate) | ⚪ |
| 5 | 5+ commits + "what I learned" notes | ⚪ |
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
│   ├── token_explorer.py           # Token counts: Indonesian vs English vs slang
│   └── results/                    # Experiment output (JSON + Markdown)
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

Experiment results and test findings will be added here as each week's tasks are completed. All numbers come from real runs in this repo.

## Author

**Jordy Dwi Prakoso**, QA Automation Engineer on the path to AI Quality Engineering.

"""Thin wrapper around the Gemini SDK that also records latency and token usage."""

import time
from dataclasses import dataclass

from google import genai
from google.genai import errors, types

from llm_qa.config import DEFAULT_MODEL, get_api_key

RETRYABLE_STATUS = {429, 500, 503}  # rate limit / temporary server errors


class MissingAPIKeyError(RuntimeError):
    pass


class DailyQuotaExceededError(RuntimeError):
    """The per-day request quota is used up. Retrying won't help until it resets."""


@dataclass
class LLMResponse:
    text: str
    model: str
    temperature: float
    latency_s: float
    input_tokens: int
    output_tokens: int
    thinking_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens + self.thinking_tokens


class GeminiClient:
    def __init__(self, api_key: str | None = None, model: str | None = None, max_retries: int = 3):
        key = api_key or get_api_key()
        if not key:
            raise MissingAPIKeyError("GEMINI_API_KEY is not set. Copy .env.example to .env and add your key.")
        self._client = genai.Client(api_key=key)
        self.model = model or DEFAULT_MODEL
        self.max_retries = max_retries

    def generate(
        self,
        prompt: str,
        *,
        temperature: float = 1.0,
        system_prompt: str | None = None,
        json_mode: bool = False,
    ) -> LLMResponse:
        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system_prompt,
            response_mime_type="application/json" if json_mode else None,
            # We don't pass tools, so turn off automatic function calling (also silences an SDK warning).
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )

        for attempt in range(self.max_retries + 1):
            start = time.perf_counter()
            try:
                resp = self._client.models.generate_content(model=self.model, contents=prompt, config=config)
                break
            except errors.APIError as e:
                if e.code == 429 and "PerDay" in str(e):
                    raise DailyQuotaExceededError(
                        f"Daily request quota for {self.model} is used up (resets at midnight Pacific time). "
                        "Wait, switch GEMINI_MODEL, or enable billing."
                    ) from e
                if e.code not in RETRYABLE_STATUS or attempt == self.max_retries:
                    raise
                wait = 2 ** attempt * 5  # 5s, 10s, 20s
                print(f"[retry] Gemini returned {e.code}, waiting {wait}s...")
                time.sleep(wait)
        latency = time.perf_counter() - start

        usage = resp.usage_metadata
        return LLMResponse(
            text=resp.text or "",
            model=self.model,
            temperature=temperature,
            latency_s=round(latency, 3),
            input_tokens=(usage and usage.prompt_token_count) or 0,
            output_tokens=(usage and usage.candidates_token_count) or 0,
            thinking_tokens=(usage and usage.thoughts_token_count) or 0,
        )

    def count_tokens(self, text: str) -> int:
        """Ask the API how many tokens a text uses (free, does not generate anything)."""
        return self._client.models.count_tokens(model=self.model, contents=text).total_tokens

    def token_limits(self) -> tuple[int, int]:
        """(context window = max input tokens, max output tokens) as reported by the API."""
        info = self._client.models.get(model=self.model)
        return info.input_token_limit, info.output_token_limit

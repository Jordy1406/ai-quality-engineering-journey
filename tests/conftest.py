import pytest

from llm_qa.config import get_api_key
from llm_qa.llm_client import GeminiClient


@pytest.fixture(scope="session")
def client() -> GeminiClient:
    """One real Gemini client for the whole test session. Skips if no API key."""
    if not get_api_key():
        pytest.skip("GEMINI_API_KEY not set - skipping live LLM tests")
    return GeminiClient()

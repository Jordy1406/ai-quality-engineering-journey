"""Reads settings from environment variables (loaded from .env if present)."""

import os

from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def get_api_key() -> str | None:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key or key == "your-key-here":
        return None
    return key


def mask(secret: str) -> str:
    """Show only the last 4 characters, so a key can be printed safely."""
    return "*" * max(len(secret) - 4, 0) + secret[-4:]

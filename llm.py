"""
LLM client factory.

Defaults to OpenAI. Falls back to Anthropic only if OPENAI_API_KEY is not set
but ANTHROPIC_API_KEY is. This keeps the rest of the codebase model-agnostic —
nodes call get_llm() and never know which provider answered.
"""

from __future__ import annotations
import os
from functools import lru_cache
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the project root, regardless of where Python is launched from
load_dotenv(Path(__file__).resolve().parent / ".env")

def _which_provider() -> tuple[str | None, str | None]:
    """Returns (provider_name, model_name) for whichever key is set, or (None, None)."""
    if os.getenv("OPENAI_API_KEY"):
        return ("OpenAI", "gpt-4o")
    if os.getenv("ANTHROPIC_API_KEY"):
        return ("Anthropic", "claude-sonnet-4-5")
    return (None, None)


def get_provider_info() -> dict:
    """
    Returns a dict describing the active provider — used by the Streamlit UI
    to show which model is answering in the sidebar.
    """
    provider, model = _which_provider()
    return {
        "provider": provider or "none",
        "model": model or "none",
        "ready": provider is not None,
    }


@lru_cache(maxsize=1)
def get_llm(temperature: float = 0.2):
    """Return a chat LLM, preferring OpenAI, falling back to Anthropic."""
    provider, model = _which_provider()

    if provider == "OpenAI":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=os.getenv("OPENAI_API_KEY"),
        )

    if provider == "Anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=model,
            temperature=temperature,
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        )

    raise RuntimeError(
        "No LLM API key found. Set OPENAI_API_KEY (preferred) or "
        "ANTHROPIC_API_KEY in your .env file."
    )
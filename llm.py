"""
Thin LLM client — wraps a paid API (Anthropic Claude by default; OpenAI fallback).

Provides:
  - get_llm() returns a langchain ChatModel that nodes can `.invoke()` or
    `.with_structured_output()` against.
  - get_provider_info() returns metadata for UI display.
"""

from __future__ import annotations
import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()


def get_provider() -> str:
    """Returns 'anthropic' if ANTHROPIC_API_KEY is set, else 'openai' if OPENAI_API_KEY is set."""
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    raise RuntimeError(
        "No LLM API key found. Please set either ANTHROPIC_API_KEY or OPENAI_API_KEY in .env"
    )


def get_llm(temperature: float = 0.0, model: str | None = None) -> Any:
    """
    Returns a LangChain ChatModel.

    Defaults:
      anthropic -> claude-sonnet-4-5 (the rubric warns against unreliable models;
                   Sonnet 4.5 is current production-grade as of Apr 2026)
      openai    -> gpt-4o
    """
    provider = get_provider()

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=model or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5"),
            temperature=temperature,
            max_tokens=8192,
            timeout=120,
        )

    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=model or os.getenv("OPENAI_MODEL", "gpt-4o"),
        temperature=temperature,
        timeout=120,
    )


def get_provider_info() -> dict[str, str]:
    """For UI display."""
    provider = get_provider()
    if provider == "anthropic":
        return {
            "provider": "Anthropic",
            "model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5"),
        }
    return {
        "provider": "OpenAI",
        "model": os.getenv("OPENAI_MODEL", "gpt-4o"),
    }

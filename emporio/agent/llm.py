"""One OpenAI-compatible client for OpenAI and for Gemini."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from emporio.config import REPO_ROOT

OPENAI_DEFAULT_MODEL = "gpt-4.1-mini"
GEMINI_DEFAULT_MODEL = "gemini-3.8-flash"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


class MissingCredentials(RuntimeError):
    """Raised when neither OPENAI_API_KEY nor GEMINI_API_KEY is set."""


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    model: str
    api_key: str
    base_url: str | None


def resolve_llm() -> LLMConfig:
    load_dotenv(REPO_ROOT / ".env")
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    model = os.getenv("LLM_MODEL", "").strip()
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip()

    if provider not in {"", "openai", "gemini"}:
        raise MissingCredentials("LLM_PROVIDER deve ser openai ou gemini.")

    use_gemini = provider == "gemini" or (provider == "" and not openai_key and bool(gemini_key))
    if use_gemini:
        if not gemini_key:
            raise MissingCredentials(_help())
        return LLMConfig(
            provider="gemini",
            model=model or GEMINI_DEFAULT_MODEL,
            api_key=gemini_key,
            base_url=os.getenv("GEMINI_BASE_URL", "").strip() or GEMINI_BASE_URL,
        )

    if openai_key:
        base = os.getenv("OPENAI_BASE_URL", "").strip() or None
        return LLMConfig(
            provider="openai",
            model=model or OPENAI_DEFAULT_MODEL,
            api_key=openai_key,
            base_url=base,
        )

    raise MissingCredentials(_help())


def build_client(config: LLMConfig):
    from openai import OpenAI

    kwargs = {"api_key": config.api_key}
    if config.base_url:
        kwargs["base_url"] = config.base_url
    return OpenAI(**kwargs)


def chat_completion(client, model: str, messages: list[dict], tools: list[dict]):
    kwargs: dict = {
        "model": model,
        "messages": messages,
        "tools": tools,
        "tool_choice": "auto",
    }
    if not _skips_temperature(model):
        kwargs["temperature"] = 0.2
    if model.startswith("gpt-5"):
        kwargs["reasoning_effort"] = "low"
    try:
        return client.chat.completions.create(**kwargs)
    except Exception as exc:
        message = str(exc).lower()
        changed = False
        if "temperature" in message and "temperature" in kwargs:
            kwargs.pop("temperature", None)
            changed = True
        if "reasoning" in message and "reasoning_effort" in kwargs:
            kwargs.pop("reasoning_effort", None)
            changed = True
        if changed:
            return client.chat.completions.create(**kwargs)
        raise


def _skips_temperature(model: str) -> bool:
    name = model.lower()
    return name.startswith(("gpt-5", "o1", "o3", "o4"))


def _help() -> str:
    return (
        "No LLM API key found. Set OPENAI_API_KEY or GEMINI_API_KEY (see .env.example).\n"
        "Offline checks that do not need a key:\n"
        "  python -m emporio.demo\n"
        "  python -m pytest"
    )

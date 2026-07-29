from __future__ import annotations

import logging
import os
from typing import Any

from .base import AIProvider

logger = logging.getLogger(__name__)

SUPPORTED_PROVIDERS = {
    "openai",
    "anthropic",
    "google",
    "deepseek",
    "local",
}


def get_provider(provider: str = "local", api_key: str | None = None, model: str | None = None) -> AIProvider:
    provider = provider.lower()

    if provider == "local":
        from ..deployment.engine import create_engine
        engine = create_engine()
        return _LocalWrapper(engine)

    if provider == "openai":
        from .openai import OpenAIProvider
        return OpenAIProvider(api_key=api_key, model=model or "gpt-4o")

    if provider == "anthropic":
        from .anthropic import AnthropicProvider
        return AnthropicProvider(api_key=api_key, model=model or "claude-3-5-sonnet-20241022")

    if provider == "google":
        from .google import GoogleProvider
        return GoogleProvider(api_key=api_key, model=model or "gemini-1.5-pro")

    if provider == "deepseek":
        from .deepseek import DeepSeekProvider
        return DeepSeekProvider(api_key=api_key, model=model or "deepseek-chat")

    raise ValueError(f"Unsupported provider: {provider}. Choose from: {', '.join(sorted(SUPPORTED_PROVIDERS))}")


class _LocalWrapper(AIProvider):
    provider_name = "local"

    def __init__(self, engine: Any):
        self._engine = engine
        self.model_name = getattr(engine, "model_name", "local")

    def generate_batch(
        self, prompts: list[str], max_tokens: int, temperature: float, top_p: float,
    ) -> tuple[list[str], list[int]]:
        return self._engine.generate_batch(prompts, max_tokens, temperature, top_p)

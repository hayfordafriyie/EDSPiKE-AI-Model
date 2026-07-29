from __future__ import annotations

import pytest

from src.providers.base import AIProvider
from src.providers.router import SUPPORTED_PROVIDERS, get_provider


def test_supported_providers_include_core():
    assert "local" in SUPPORTED_PROVIDERS
    assert "openai" in SUPPORTED_PROVIDERS
    assert "anthropic" in SUPPORTED_PROVIDERS
    assert "google" in SUPPORTED_PROVIDERS
    assert "deepseek" in SUPPORTED_PROVIDERS


def test_get_provider_unsupported():
    with pytest.raises(ValueError, match="Unsupported provider"):
        get_provider("nonexistent")


def test_get_provider_local_returns_ai_provider():
    with pytest.raises(Exception):
        get_provider("local")


def test_openai_provider_has_correct_name():
    from src.providers.openai import OpenAIProvider
    p = OpenAIProvider(api_key="test-key")
    assert p.provider_name == "openai"
    assert p.model_name == "gpt-4o"


def test_anthropic_provider_has_correct_name():
    from src.providers.anthropic import AnthropicProvider
    p = AnthropicProvider(api_key="test-key")
    assert p.provider_name == "anthropic"
    assert "claude" in p.model_name


def test_google_provider_has_correct_name():
    from src.providers.google import GoogleProvider
    p = GoogleProvider(api_key="test-key")
    assert p.provider_name == "google"
    assert "gemini" in p.model_name


def test_deepseek_provider_has_correct_name():
    from src.providers.deepseek import DeepSeekProvider
    p = DeepSeekProvider(api_key="test-key")
    assert p.provider_name == "deepseek"
    assert "deepseek" in p.model_name


def test_all_providers_extend_ai_provider():
    from src.providers.openai import OpenAIProvider
    from src.providers.anthropic import AnthropicProvider
    from src.providers.google import GoogleProvider
    from src.providers.deepseek import DeepSeekProvider
    for cls in [OpenAIProvider, AnthropicProvider, GoogleProvider, DeepSeekProvider]:
        assert issubclass(cls, AIProvider)


def test_provider_has_generate_batch():
    from src.providers.openai import OpenAIProvider
    p = OpenAIProvider(api_key="test")
    assert hasattr(p, "generate_batch")
    assert callable(p.generate_batch)

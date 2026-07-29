from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from src.credential import CredentialStore


@pytest.fixture
def store():
    with tempfile.TemporaryDirectory() as tmp:
        yield CredentialStore(str(Path(tmp) / "test.db"))


class TestCredentialStore:
    def test_set_and_get(self, store):
        store.set("openai", "sk-123")
        assert store.get("openai") == "sk-123"

    def test_get_nonexistent(self, store):
        assert store.get("nonexistent") is None

    def test_update(self, store):
        store.set("anthropic", "old-key")
        store.set("anthropic", "new-key")
        assert store.get("anthropic") == "new-key"

    def test_delete(self, store):
        store.set("google", "key")
        assert store.delete("google") is True
        assert store.get("google") is None
        assert store.delete("google") is False

    def test_has(self, store):
        assert store.has("openai") is False
        store.set("openai", "key")
        assert store.has("openai") is True

    def test_list_providers(self, store):
        store.set("openai", "k1", metadata={"env": "prod"})
        store.set("anthropic", "k2")
        providers = store.list_providers()
        assert len(providers) == 2
        names = [p["provider"] for p in providers]
        assert "openai" in names
        assert "anthropic" in names

    def test_multiple_keys_per_provider(self, store):
        store.set("openai", "key1", key_name="api_key")
        store.set("openai", "key2", key_name="org_key")
        assert store.get("openai", "api_key") == "key1"
        assert store.get("openai", "org_key") == "key2"

    def test_resolve_api_key_prefers_store(self, store, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "env-key")
        store.set("openai", "store-key")
        assert store.resolve_api_key("openai") == "store-key"

    def test_resolve_api_key_falls_back_to_env(self, monkeypatch):
        with tempfile.TemporaryDirectory() as tmp:
            store = CredentialStore(str(Path(tmp) / "test.db"))
            monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key")
            assert store.resolve_api_key("anthropic") == "env-key"

    def test_resolve_api_key_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = CredentialStore(str(Path(tmp) / "test.db"))
            assert store.resolve_api_key("unknown") is None

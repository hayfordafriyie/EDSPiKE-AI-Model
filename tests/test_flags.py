from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.flags import FeatureFlagStore


class TestFeatureFlags:
    @pytest.fixture
    def store(self):
        with tempfile.TemporaryDirectory() as tmp:
            yield FeatureFlagStore(str(Path(tmp) / "flags.json"))

    def test_default_disabled(self, store):
        assert store.is_enabled("nonexistent") is False

    def test_enable(self, store):
        store.enable("test_flag")
        assert store.is_enabled("test_flag") is True

    def test_disable(self, store):
        store.enable("flag")
        store.disable("flag")
        assert store.is_enabled("flag") is False

    def test_set(self, store):
        store.set("feature_x", True)
        assert store.is_enabled("feature_x") is True
        store.set("feature_x", False)
        assert store.is_enabled("feature_x") is False

    def test_all(self, store):
        store.enable("a")
        store.enable("b")
        flags = store.all()
        assert flags == {"a": True, "b": True}

    def test_reset(self, store):
        store.enable("flag")
        store.reset()
        assert store.all() == {}

    def test_persistence(self, store):
        store.enable("persistent")
        path = store._path
        store2 = FeatureFlagStore(path)
        assert store2.is_enabled("persistent") is True

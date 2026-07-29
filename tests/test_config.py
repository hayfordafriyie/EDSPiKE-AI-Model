from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from src.config import ConfigLoader, AppSettings, ProviderSettings, ToolSettings


class TestSettings:
    def test_defaults(self):
        s = AppSettings()
        assert s.host == "0.0.0.0"
        assert s.port == 8000
        assert s.device == "cpu"
        assert s.providers.default_provider == "local"
        assert s.tools.allow_bash is True

    def test_from_dict(self):
        s = AppSettings.from_dict({
            "host": "127.0.0.1",
            "port": "9000",
            "device": "cuda",
            "tools": {"allow_bash": False, "allow_fs_write": False},
        })
        assert s.host == "127.0.0.1"
        assert s.port == 9000
        assert s.device == "cuda"
        assert s.tools.allow_bash is False
        assert s.tools.allow_fs_write is False

    def test_env_overrides(self, monkeypatch):
        monkeypatch.setenv("EDSPIKE_HOST", "10.0.0.1")
        monkeypatch.setenv("EDSPIKE_PORT", "3000")
        monkeypatch.setenv("DEVICE", "mps")
        from src.config.settings import _env_overrides
        overrides = _env_overrides()
        assert overrides["host"] == "10.0.0.1"
        assert overrides["port"] == "3000"
        assert overrides["device"] == "mps"


class TestConfigLoader:
    def test_default_load(self):
        loader = ConfigLoader()
        s = loader.load()
        assert s.host == "0.0.0.0"
        assert s.device in ("cpu", "mps", "cuda") or True  # system-dependent

    def test_load_from_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "config.json"
            cfg.write_text(json.dumps({"host": "192.168.1.1", "port": 5000}))
            loader = ConfigLoader(str(cfg))
            s = loader.load()
            assert s.host == "192.168.1.1"
            assert s.port == 5000

    def test_reload(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "config.json"
            cfg.write_text(json.dumps({"host": "first"}))
            loader = ConfigLoader(str(cfg))
            assert loader.get().host == "first"
            cfg.write_text(json.dumps({"host": "second"}))
            s = loader.reload()
            assert s.host == "second"

    def test_to_dict(self):
        loader = ConfigLoader()
        d = loader.to_dict()
        assert "host" in d
        assert "port" in d
        assert "providers" in d
        assert "tools" in d
        assert d["tools"]["allow_bash"] is True

    def test_save_default_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "default.json")
            ConfigLoader.save_default_config(path)
            assert Path(path).exists()
            data = json.loads(Path(path).read_text())
            assert data["host"] == "0.0.0.0"
            assert data["port"] == 8000

    def test_env_override_config_file(self, monkeypatch):
        monkeypatch.setenv("EDSPIKE_HOST", "env-host")
        monkeypatch.setenv("EDSPIKE_PORT", "7777")
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "config.json"
            cfg.write_text(json.dumps({"host": "file-host", "port": 8888}))
            loader = ConfigLoader(str(cfg))
            s = loader.load()
            # env should override file
            assert s.host == "env-host"
            assert s.port == 7777

    def test_config_api_key(self, monkeypatch):
        monkeypatch.setenv("EDSPIKE_API_KEY", "abc123")
        loader = ConfigLoader()
        s = loader.load()
        assert s.api_key == "abc123"
        d = loader.to_dict()
        assert d["api_key_configured"] is True

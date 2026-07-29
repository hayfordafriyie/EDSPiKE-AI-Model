from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .settings import AppSettings, _env_overrides, load_settings


class ConfigLoader:
    def __init__(self, config_path: str | None = None):
        self._path = config_path
        self._settings: AppSettings | None = None

    def load(self) -> AppSettings:
        self._settings = load_settings(self._path)
        return self._settings

    def reload(self) -> AppSettings:
        self._settings = None
        return self.load()

    def get(self) -> AppSettings:
        if self._settings is None:
            return self.load()
        return self._settings

    def to_dict(self) -> dict[str, Any]:
        s = self.get()
        return {
            "api_key_configured": bool(s.api_key),
            "host": s.host,
            "port": s.port,
            "log_level": s.log_level,
            "device": s.device,
            "quantization": s.quantization,
            "max_batch_size": s.max_batch_size,
            "data_dir": s.data_dir,
            "providers": {
                "default_provider": s.providers.default_provider,
                "default_model": s.providers.default_model,
                "configured": {
                    "openai": bool(s.providers.openai_api_key),
                    "anthropic": bool(s.providers.anthropic_api_key),
                    "google": bool(s.providers.google_api_key),
                    "deepseek": bool(s.providers.deepseek_api_key),
                },
            },
            "tools": {
                "allow_bash": s.tools.allow_bash,
                "allow_fs_write": s.tools.allow_fs_write,
                "max_bash_timeout": s.tools.max_bash_timeout,
                "approval_required": s.tools.approval_required,
            },
        }

    @staticmethod
    def save_default_config(path: str) -> None:
        default = {
            "host": "0.0.0.0",
            "port": 8000,
            "log_level": "info",
            "device": "cpu",
            "quantization": "int4",
            "max_batch_size": 1,
            "data_dir": "~/.edspike",
            "providers": {
                "default_provider": "local",
                "default_model": "",
            },
            "tools": {
                "allow_bash": True,
                "allow_fs_write": True,
                "max_bash_timeout": 120,
                "approval_required": False,
            },
        }
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(default, indent=2))

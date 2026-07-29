from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ProviderSettings:
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""
    deepseek_api_key: str = ""
    default_provider: str = "local"
    default_model: str = ""


@dataclass
class ToolSettings:
    allow_bash: bool = True
    allow_fs_write: bool = True
    max_bash_timeout: int = 120
    workspace_root: str = "."
    allowed_roots: list[str] = field(default_factory=list)
    approval_required: bool = False


@dataclass
class AppSettings:
    api_key: str = ""
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "info"
    device: str = "cpu"
    quantization: str = "int4"
    max_batch_size: int = 1
    data_dir: str = "~/.edspike"
    providers: ProviderSettings = field(default_factory=ProviderSettings)
    tools: ToolSettings = field(default_factory=ToolSettings)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AppSettings:
        providers = ProviderSettings(
            openai_api_key=data.get("OPENAI_API_KEY", data.get("providers", {}).get("openai_api_key", "")),
            anthropic_api_key=data.get("ANTHROPIC_API_KEY", data.get("providers", {}).get("anthropic_api_key", "")),
            google_api_key=data.get("GOOGLE_API_KEY", data.get("providers", {}).get("google_api_key", "")),
            deepseek_api_key=data.get("DEEPSEEK_API_KEY", data.get("providers", {}).get("deepseek_api_key", "")),
            default_provider=data.get("DEFAULT_PROVIDER", data.get("providers", {}).get("default_provider", "local")),
            default_model=data.get("DEFAULT_MODEL", data.get("providers", {}).get("default_model", "")),
        )
        tools_data = data.get("tools", {})
        tools = ToolSettings(
            allow_bash=tools_data.get("allow_bash", True),
            allow_fs_write=tools_data.get("allow_fs_write", True),
            max_bash_timeout=tools_data.get("max_bash_timeout", 120),
            workspace_root=tools_data.get("workspace_root", "."),
            allowed_roots=tools_data.get("allowed_roots", []),
            approval_required=tools_data.get("approval_required", False),
        )
        return cls(
            api_key=data.get("api_key", data.get("EDSPIKE_API_KEY", "")),
            host=data.get("host", "0.0.0.0"),
            port=int(data.get("port", 8000)),
            log_level=data.get("log_level", "info"),
            device=data.get("device", "cpu"),
            quantization=data.get("quantization", "int4"),
            max_batch_size=int(data.get("max_batch_size", 1)),
            data_dir=data.get("data_dir", "~/.edspike"),
            providers=providers,
            tools=tools,
            raw=data,
        )


def _env_overrides() -> dict[str, Any]:
    overrides: dict[str, Any] = {}
    env_map = {
        "EDSPIKE_API_KEY": "api_key",
        "EDSPIKE_HOST": "host",
        "EDSPIKE_PORT": "port",
        "EDSPIKE_LOG_LEVEL": "log_level",
        "DEVICE": "device",
        "MODEL_QUANTIZATION": "quantization",
        "MAX_BATCH_SIZE": "max_batch_size",
        "EDSPIKE_DATA_DIR": "data_dir",
        "OPENAI_API_KEY": "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY": "ANTHROPIC_API_KEY",
        "GOOGLE_API_KEY": "GOOGLE_API_KEY",
        "DEEPSEEK_API_KEY": "DEEPSEEK_API_KEY",
    }
    for env_key, cfg_key in env_map.items():
        val = os.environ.get(env_key)
        if val:
            overrides[cfg_key] = val
    return overrides


def _resolve_path(path: str) -> str:
    return str(Path(path).expanduser().resolve())


def load_settings(config_path: str | None = None) -> AppSettings:
    data: dict[str, Any] = {}

    if config_path and Path(config_path).exists():
        import json
        raw = Path(config_path).read_text()
        if config_path.endswith((".yaml", ".yml")):
            try:
                import yaml
                data = yaml.safe_load(raw) or {}
            except ImportError:
                pass
        else:
            data = json.loads(raw)

    data.update(_env_overrides())

    settings = AppSettings.from_dict(data)
    settings.data_dir = _resolve_path(settings.data_dir)
    return settings

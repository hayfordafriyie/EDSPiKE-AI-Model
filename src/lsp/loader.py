from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class LspConfig:
    language: str
    server_command: list[str]
    root_uri: str = ""
    file_patterns: list[str] = field(default_factory=list)


def auto_detect_lsp(root_dir: str) -> list[LspConfig]:
    root = Path(root_dir).resolve()
    configs: list[LspConfig] = []

    if (root / "pyproject.toml").exists() or (root / "setup.py").exists() or list(root.glob("*.py")):
        configs.append(LspConfig(
            language="python",
            server_command=["pyright-langserver", "--stdio"],
            root_uri=f"file://{root}",
            file_patterns=["**/*.py"],
        ))

    if (root / "package.json").exists() or (root / "tsconfig.json").exists():
        configs.append(LspConfig(
            language="typescript",
            server_command=["typescript-language-server", "--stdio"],
            root_uri=f"file://{root}",
            file_patterns=["**/*.{ts,tsx,js,jsx}"],
        ))

    if (root / "go.mod").exists() or list(root.glob("*.go")):
        configs.append(LspConfig(
            language="go",
            server_command=["gopls"],
            root_uri=f"file://{root}",
            file_patterns=["**/*.go"],
        ))

    if (root / "Cargo.toml").exists() or list(root.glob("*.rs")):
        configs.append(LspConfig(
            language="rust",
            server_command=["rust-analyzer"],
            root_uri=f"file://{root}",
            file_patterns=["**/*.rs"],
        ))

    if (root / "Gemfile").exists() or list(root.glob("*.rb")):
        configs.append(LspConfig(
            language="ruby",
            server_command=["solargraph"],
            root_uri=f"file://{root}",
            file_patterns=["**/*.rb"],
        ))

    if (root / "pom.xml").exists() or (root / "build.gradle").exists() or list(root.glob("*.java")):
        configs.append(LspConfig(
            language="java",
            server_command=["eclipse-jdtls"],
            root_uri=f"file://{root}",
            file_patterns=["**/*.java"],
        ))

    return configs


def start_lsp_servers(root_dir: str) -> list[Any]:
    from src.lsp import LspClient

    configs = auto_detect_lsp(root_dir)
    clients: list[LspClient] = []
    errors: list[str] = []

    for cfg in configs:
        try:
            client = LspClient(cfg.language, cfg.server_command, cfg.root_uri)
            client.start()
            clients.append(client)
        except Exception as e:
            errors.append(f"Failed to start {cfg.language} LSP: {e}")

    return clients

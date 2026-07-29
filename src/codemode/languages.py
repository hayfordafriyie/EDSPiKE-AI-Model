from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class LanguageConfig:
    name: str
    extensions: list[str]
    command: list[str]
    timeout_default: int = 30
    filename: str = ""


LANGUAGES: dict[str, LanguageConfig] = {
    "python": LanguageConfig(
        name="python",
        extensions=[".py"],
        command=["python3", "-u", "{file}"],
        timeout_default=30,
        filename="script.py",
    ),
    "bash": LanguageConfig(
        name="bash",
        extensions=[".sh"],
        command=["bash", "{file}"],
        timeout_default=15,
        filename="script.sh",
    ),
    "node": LanguageConfig(
        name="node",
        extensions=[".js", ".mjs"],
        command=["node", "{file}"],
        timeout_default=30,
        filename="script.js",
    ),
    "python3": LanguageConfig(
        name="python3",
        extensions=[".py"],
        command=["python3", "-u", "{file}"],
        timeout_default=30,
        filename="script.py",
    ),
}


def get_language(name: str) -> LanguageConfig:
    lang = LANGUAGES.get(name)
    if lang is None:
        raise KeyError(f"Unsupported language: {name}. Supported: {list(LANGUAGES.keys())}")
    return lang

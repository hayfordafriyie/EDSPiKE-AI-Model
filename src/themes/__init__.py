from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Theme:
    name: str
    primary: str = "cyan"
    secondary: str = "green"
    error: str = "red"
    warning: str = "yellow"
    info: str = "blue"
    prompt_color: str = "ansicyan"
    border_style: str = "cyan"
    diff_add: str = "green"
    diff_del: str = "red"
    diff_hdr: str = "cyan"
    code_bg: str = "dim white"
    metadata: dict[str, str] = field(default_factory=dict)


BUILTIN_THEMES: dict[str, Theme] = {
    "default": Theme(name="default"),
    "dark": Theme(
        name="dark",
        primary="blue",
        secondary="green",
        prompt_color="ansiblue",
        border_style="blue",
        diff_add="green",
        diff_del="red",
        diff_hdr="cyan",
        code_bg="dim white",
    ),
    "light": Theme(
        name="light",
        primary="#0066cc",
        secondary="#008800",
        error="#cc0000",
        warning="#cc8800",
        info="#0066cc",
        prompt_color="#0066cc",
        border_style="#0066cc",
        diff_add="green",
        diff_del="red",
        diff_hdr="blue",
        code_bg="dim white",
    ),
    "monokai": Theme(
        name="monokai",
        primary="#a6e22e",
        secondary="#66d9ef",
        error="#f92672",
        warning="#fd971f",
        info="#66d9ef",
        prompt_color="#a6e22e",
        border_style="#a6e22e",
        diff_add="#a6e22e",
        diff_del="#f92672",
        diff_hdr="#66d9ef",
        code_bg="on #272822",
    ),
}


class ThemeManager:
    def __init__(self):
        self._themes: dict[str, Theme] = dict(BUILTIN_THEMES)
        self._current: str = "default"

    def get_current(self) -> Theme:
        return self._themes[self._current]

    def set_theme(self, name: str) -> Theme:
        if name not in self._themes:
            raise KeyError(f"Unknown theme: {name}. Available: {list(self._themes)}")
        self._current = name
        return self._themes[name]

    def list_themes(self) -> list[Theme]:
        return list(self._themes.values())

    def register(self, theme: Theme) -> None:
        self._themes[theme.name] = theme

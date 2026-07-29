from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

PluginHook = Callable[..., Any]


@dataclass
class PluginManifest:
    name: str
    version: str
    description: str
    author: str = ""
    hooks: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)


class PluginSDK:
    def __init__(self):
        self._hooks: dict[str, list[PluginHook]] = {}
        self._manifests: dict[str, PluginManifest] = {}
        self._state: dict[str, Any] = {}

    def register(self, manifest: PluginManifest) -> None:
        self._manifests[manifest.name] = manifest

    def on(self, event: str, hook: PluginHook) -> None:
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(hook)

    def emit(self, event: str, *args: Any, **kwargs: Any) -> list[Any]:
        results: list[Any] = []
        for hook in self._hooks.get(event, []):
            try:
                result = hook(*args, **kwargs)
                if result is not None:
                    results.append(result)
            except Exception as e:
                results.append(e)
        return results

    def get_state(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def set_state(self, key: str, value: Any) -> None:
        self._state[key] = value

    def list_plugins(self) -> list[PluginManifest]:
        return list(self._manifests.values())

    def get_manifest(self, name: str) -> PluginManifest | None:
        return self._manifests.get(name)

    def has_hook(self, event: str) -> bool:
        return event in self._hooks and len(self._hooks[event]) > 0


PLUGIN_SDK = PluginSDK()

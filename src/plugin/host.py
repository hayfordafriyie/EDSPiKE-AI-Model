from __future__ import annotations

import importlib
import importlib.util
import inspect
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class PluginManifest:
    name: str
    version: str = "0.1.0"
    description: str = ""
    author: str = ""
    entrypoint: str = "main"
    tools: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class PluginInfo:
    manifest: PluginManifest
    path: str
    loaded: bool = False
    error: str = ""


PluginHook = Callable[..., Any]


class PluginHost:
    def __init__(self, plugin_dirs: list[str] | None = None):
        self._dirs = [Path(d).expanduser().resolve() for d in (plugin_dirs or ["~/.edspike/plugins"])]
        self._plugins: dict[str, PluginInfo] = {}
        self._hooks: dict[str, list[PluginHook]] = {}

    def discover(self) -> list[PluginInfo]:
        found: list[PluginInfo] = []
        for d in self._dirs:
            if not d.exists():
                d.mkdir(parents=True, exist_ok=True)
                continue
            for entry in sorted(d.iterdir()):
                if entry.is_dir() and (entry / "plugin.json").exists():
                    info = self._load_manifest(entry)
                    if info:
                        found.append(info)
                        self._plugins[info.manifest.name] = info
                elif entry.suffix == ".py" and entry.stem != "__init__":
                    info = self._load_manifest_from_py(entry)
                    if info:
                        found.append(info)
                        self._plugins[info.manifest.name] = info
        return found

    def _load_manifest(self, plugin_dir: Path) -> PluginInfo | None:
        manifest_path = plugin_dir / "plugin.json"
        try:
            data = json.loads(manifest_path.read_text())
            manifest = PluginManifest(
                name=data.get("name", plugin_dir.name),
                version=data.get("version", "0.1.0"),
                description=data.get("description", ""),
                author=data.get("author", ""),
                entrypoint=data.get("entrypoint", "main"),
                tools=data.get("tools", []),
            )
            return PluginInfo(manifest=manifest, path=str(plugin_dir))
        except Exception as exc:
            logger.warning("Failed to load manifest from %s: %s", plugin_dir, exc)
            return None

    def _load_manifest_from_py(self, py_file: Path) -> PluginInfo | None:
        try:
            manifest = PluginManifest(
                name=py_file.stem,
                description=f"Python plugin: {py_file.name}",
            )
            return PluginInfo(manifest=manifest, path=str(py_file))
        except Exception as exc:
            logger.warning("Failed to load plugin from %s: %s", py_file, exc)
            return None

    def load(self, name: str) -> PluginHook | None:
        info = self._plugins.get(name)
        if not info:
            logger.error("Plugin not found: %s", name)
            return None

        path = Path(info.path)
        try:
            if path.is_dir():
                spec = importlib.util.spec_from_file_location(
                    f"edspike_plugin_{name}",
                    path / "__init__.py",
                )
            else:
                spec = importlib.util.spec_from_file_location(
                    f"edspike_plugin_{name}",
                    str(path),
                )

            if not spec or not spec.loader:
                raise ImportError(f"Cannot load plugin: {name}")

            mod = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mod
            spec.loader.exec_module(mod)

            entry = getattr(mod, info.manifest.entrypoint, None)
            if not entry or not callable(entry):
                raise AttributeError(f"Plugin {name} has no callable entrypoint '{info.manifest.entrypoint}'")

            info.loaded = True
            logger.info("Loaded plugin: %s v%s", name, info.manifest.version)
            return entry

        except Exception as exc:
            info.error = str(exc)
            logger.error("Failed to load plugin %s: %s", name, exc)
            return None

    def load_all(self) -> dict[str, PluginHook]:
        results: dict[str, PluginHook] = {}
        for name in list(self._plugins.keys()):
            hook = self.load(name)
            if hook:
                results[name] = hook
        return results

    def register_hook(self, event: str, hook: PluginHook) -> None:
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(hook)

    def trigger(self, event: str, *args: Any, **kwargs: Any) -> list[Any]:
        results: list[Any] = []
        for hook in self._hooks.get(event, []):
            try:
                results.append(hook(*args, **kwargs))
            except Exception as exc:
                logger.error("Hook %s failed on event %s: %s", hook.__name__, event, exc)
        return results

    def list_plugins(self) -> list[dict[str, Any]]:
        return [
            {
                "name": info.manifest.name,
                "version": info.manifest.version,
                "description": info.manifest.description,
                "author": info.manifest.author,
                "loaded": info.loaded,
                "error": info.error,
            }
            for info in self._plugins.values()
        ]

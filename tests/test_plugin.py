from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.plugin import PluginHost, PluginManifest


class TestPluginHost:
    def test_discover_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            host = PluginHost(plugin_dirs=[tmp])
            plugins = host.discover()
            assert plugins == []

    def test_discover_json_plugin(self):
        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = Path(tmp) / "my_plugin"
            plugin_dir.mkdir()
            manifest = {"name": "my_plugin", "version": "1.0.0", "description": "Test plugin"}
            (plugin_dir / "plugin.json").write_text(json.dumps(manifest))
            (plugin_dir / "__init__.py").write_text("def main(): return 'hello'")
            host = PluginHost(plugin_dirs=[tmp])
            plugins = host.discover()
            assert len(plugins) == 1
            assert plugins[0].manifest.name == "my_plugin"

    def test_load_plugin(self):
        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = Path(tmp) / "greeter"
            plugin_dir.mkdir()
            manifest = {"name": "greeter", "entrypoint": "greet"}
            (plugin_dir / "plugin.json").write_text(json.dumps(manifest))
            (plugin_dir / "__init__.py").write_text("def greet(): return 'hi'")
            host = PluginHost(plugin_dirs=[tmp])
            host.discover()
            hook = host.load("greeter")
            assert hook is not None
            assert hook() == "hi"

    def test_load_py_plugin(self):
        with tempfile.TemporaryDirectory() as tmp:
            py_file = Path(tmp) / "simple_plugin.py"
            py_file.write_text("def main(): return 42")
            host = PluginHost(plugin_dirs=[tmp])
            host.discover()
            hook = host.load("simple_plugin")
            assert hook is not None
            assert hook() == 42

    def test_load_nonexistent(self):
        host = PluginHost(plugin_dirs=["/tmp/nonexistent_plugins"])
        assert host.load("nonexistent") is None

    def test_load_all(self):
        with tempfile.TemporaryDirectory() as tmp:
            p1 = Path(tmp) / "p1"
            p1.mkdir()
            (p1 / "plugin.json").write_text(json.dumps({"name": "p1"}))
            (p1 / "__init__.py").write_text("def main(): return 1")
            p2 = Path(tmp) / "p2.py"
            p2.write_text("def main(): return 2")
            host = PluginHost(plugin_dirs=[tmp])
            host.discover()
            hooks = host.load_all()
            assert len(hooks) == 2

    def test_register_and_trigger_hook(self):
        host = PluginHost()
        calls = []
        host.register_hook("pre_exec", lambda x: calls.append(x))
        host.trigger("pre_exec", "test")
        assert calls == ["test"]

    def test_trigger_unknown_event(self):
        host = PluginHost()
        results = host.trigger("nonexistent")
        assert results == []

    def test_list_plugins(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "test_plugin.py"
            p.write_text("def main(): pass")
            host = PluginHost(plugin_dirs=[tmp])
            host.discover()
            plugins = host.list_plugins()
            assert len(plugins) == 1
            assert plugins[0]["name"] == "test_plugin"

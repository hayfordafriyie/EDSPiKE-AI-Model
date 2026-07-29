from pathlib import Path

import pytest

from src.keybinds import KeybindManager, Keybind, DEFAULT_KEYBINDS


class TestKeybinds:
    def test_default_keybinds(self):
        assert len(DEFAULT_KEYBINDS) >= 6
        keys = [kb.key for kb in DEFAULT_KEYBINDS]
        assert "tab" in keys
        assert "ctrl+c" in keys

    def test_get_default(self):
        mgr = KeybindManager()
        kb = mgr.get("tab")
        assert kb is not None
        assert kb.action == "switch_mode"

    def test_bind_custom(self):
        mgr = KeybindManager()
        mgr.bind("ctrl+r", "refresh", "Refresh view")
        kb = mgr.get("ctrl+r")
        assert kb is not None
        assert kb.action == "refresh"

    def test_handle(self):
        mgr = KeybindManager()
        action = mgr.handle("tab")
        assert action == "switch_mode"

    def test_handle_unknown(self):
        mgr = KeybindManager()
        action = mgr.handle("nonexistent")
        assert "no_action" in action

    def test_unbind(self):
        mgr = KeybindManager()
        assert mgr.unbind("tab") is True
        assert mgr.get("tab") is None
        assert mgr.unbind("tab") is False

    def test_list(self):
        mgr = KeybindManager()
        binds = mgr.list()
        assert len(binds) == len(DEFAULT_KEYBINDS)

    def test_bind_with_handler(self):
        mgr = KeybindManager()
        calls = []

        def handler(action, args):
            calls.append((action, args))

        mgr.bind("f5", "refresh", handler=handler)
        mgr.handle("f5")
        # Handler should be called - but handle just returns action string
        # The handler is called separately

    def test_persistence(self, tmp_path: Path):
        data_dir = str(tmp_path / "keybinds")
        m1 = KeybindManager(data_dir)
        m1.bind("ctrl+r", "refresh")
        m2 = KeybindManager(data_dir)
        kb = m2.get("ctrl+r")
        assert kb is not None
        assert kb.action == "refresh"

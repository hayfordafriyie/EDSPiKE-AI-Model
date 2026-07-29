import pytest

from src.themes import ThemeManager, Theme, BUILTIN_THEMES


class TestThemes:
    def test_builtin_themes(self):
        assert "default" in BUILTIN_THEMES
        assert "dark" in BUILTIN_THEMES
        assert "light" in BUILTIN_THEMES
        assert "monokai" in BUILTIN_THEMES

    def test_default_theme(self):
        mgr = ThemeManager()
        assert mgr.get_current().name == "default"

    def test_switch_theme(self):
        mgr = ThemeManager()
        theme = mgr.set_theme("dark")
        assert theme.name == "dark"
        assert mgr.get_current().name == "dark"

    def test_switch_unknown(self):
        mgr = ThemeManager()
        with pytest.raises(KeyError):
            mgr.set_theme("nonexistent")

    def test_list_themes(self):
        mgr = ThemeManager()
        themes = mgr.list_themes()
        assert len(themes) >= 4

    def test_register_custom(self):
        mgr = ThemeManager()
        custom = Theme(name="custom", primary="red")
        mgr.register(custom)
        assert mgr.set_theme("custom").primary == "red"

    def test_theme_fields(self):
        theme = Theme(name="test", primary="blue", diff_add="green")
        assert theme.primary == "blue"
        assert theme.diff_add == "green"

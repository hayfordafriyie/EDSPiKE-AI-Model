import pytest

from src.modes import ModeManager, Mode, BUILTIN_MODES


class TestModes:
    def test_builtin_modes(self):
        assert "build" in BUILTIN_MODES
        assert "plan" in BUILTIN_MODES

    def test_default_mode_is_build(self):
        mgr = ModeManager()
        assert mgr.get_current().id == "build"

    def test_switch_to_plan(self):
        mgr = ModeManager()
        mode = mgr.set_mode("plan")
        assert mode.id == "plan"
        assert mgr.get_current().id == "plan"

    def test_switch_unknown_mode(self):
        mgr = ModeManager()
        with pytest.raises(KeyError):
            mgr.set_mode("nonexistent")

    def test_list_modes(self):
        mgr = ModeManager()
        modes = mgr.list_modes()
        assert len(modes) >= 2

    def test_permissions_build(self):
        mgr = ModeManager()
        assert mgr.can("write_file") == "allow"
        assert mgr.can("bash") == "allow"

    def test_permissions_plan(self):
        mgr = ModeManager()
        mgr.set_mode("plan")
        assert mgr.can("write_file") == "deny"
        assert mgr.can("edit_file") == "deny"
        assert mgr.can("read_file") == "allow"
        assert mgr.can("bash") == "ask"

    def test_register_custom_mode(self):
        mgr = ModeManager()
        mgr.register(Mode(id="review", name="Review", description="Review mode"))
        assert mgr.set_mode("review").id == "review"

    def test_get_permissions(self):
        mgr = ModeManager()
        mgr.set_mode("plan")
        perms = mgr.get_permissions()
        assert isinstance(perms, dict)
        assert perms.get("write_file") == "deny"

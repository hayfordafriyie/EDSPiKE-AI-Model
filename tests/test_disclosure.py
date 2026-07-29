import pytest

from src.tools.disclosure import ToolDisclosureManager, ToolGroup


class TestToolDisclosure:
    def test_default_groups(self):
        mgr = ToolDisclosureManager()
        groups = mgr.get_available_groups()
        assert len(groups) == 5  # file_ops, search, execution, web, agent

    def test_load_group(self):
        mgr = ToolDisclosureManager()
        tools = mgr.load_group("search")
        assert "grep" in tools
        assert "glob" in tools
        assert mgr.is_loaded("grep")
        assert not mgr.is_loaded("bash")

    def test_load_tool(self):
        mgr = ToolDisclosureManager()
        assert mgr.load_tool("bash") is True
        assert mgr.is_loaded("bash") is True
        # Loading again returns False
        assert mgr.load_tool("bash") is False

    def test_get_available_groups(self):
        mgr = ToolDisclosureManager()
        mgr.load_group("search")
        available = mgr.get_available_groups()
        assert len(available) == 4
        assert all(g.name != "search" for g in available)

    def test_describe_available(self):
        mgr = ToolDisclosureManager()
        desc = mgr.describe_available()
        assert "file_ops" in desc
        assert "search" in desc
        assert "execution" in desc

    def test_all_loaded(self):
        mgr = ToolDisclosureManager()
        for g in list(mgr._groups.values()):
            mgr.load_group(g.name)
        assert "All tool groups are loaded" in mgr.describe_available()

    def test_reset(self):
        mgr = ToolDisclosureManager()
        mgr.load_group("file_ops")
        assert mgr.is_loaded("read_file")
        mgr.reset()
        assert not mgr.is_loaded("read_file")
        assert len(mgr.get_available_groups()) == 5

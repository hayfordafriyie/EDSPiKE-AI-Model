import pytest

from src.session.tree import SessionTree


class TestSessionTree:
    def test_set_root(self):
        tree = SessionTree()
        tree.set_root("root")
        assert tree.get_current() == "root"

    def test_add_child(self):
        tree = SessionTree()
        tree.set_root("root")
        tree.add_child("root", "child1")
        tree.add_child("root", "child2")
        node = tree.current_node()
        assert node is not None
        assert len(node.children) == 2

    def test_navigate_parent(self):
        tree = SessionTree()
        tree.set_root("root")
        tree.add_child("root", "child")
        tree.navigate_to("child")
        assert tree.get_current() == "child"
        assert tree.navigate_parent() is True
        assert tree.get_current() == "root"

    def test_navigate_child(self):
        tree = SessionTree()
        tree.set_root("root")
        tree.add_child("root", "child1")
        tree.add_child("root", "child2")
        assert tree.navigate_child(1) is True
        assert tree.get_current() == "child2"

    def test_navigate_child_invalid_index(self):
        tree = SessionTree()
        tree.set_root("root")
        assert tree.navigate_child(0) is False

    def test_get_path(self):
        tree = SessionTree()
        tree.set_root("a")
        tree.add_child("a", "b")
        tree.add_child("b", "c")
        tree.navigate_to("c")
        path = tree.get_path()
        assert path == ["a", "b", "c"]

    def test_current_node_none(self):
        tree = SessionTree()
        assert tree.current_node() is None

    def test_navigate_to_nonexistent(self):
        tree = SessionTree()
        tree.set_root("root")
        assert tree.navigate_to("nonexistent") is False

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SessionNode:
    session_id: str
    parent_id: str = ""
    children: list[str] = field(default_factory=list)
    depth: int = 0


class SessionTree:
    def __init__(self):
        self._nodes: dict[str, SessionNode] = {}
        self._current: str = ""

    def set_root(self, session_id: str) -> None:
        node = SessionNode(session_id=session_id, depth=0)
        self._nodes[session_id] = node
        self._current = session_id

    def add_child(self, parent_id: str, child_id: str) -> SessionNode:
        parent = self._nodes.get(parent_id)
        depth = parent.depth + 1 if parent else 0
        node = SessionNode(session_id=child_id, parent_id=parent_id, depth=depth)
        self._nodes[child_id] = node
        if parent:
            parent.children.append(child_id)
        return node

    def navigate_to(self, session_id: str) -> bool:
        if session_id in self._nodes:
            self._current = session_id
            return True
        return False

    def navigate_parent(self) -> bool:
        node = self._nodes.get(self._current)
        if node and node.parent_id:
            self._current = node.parent_id
            return True
        return False

    def navigate_child(self, index: int = 0) -> bool:
        node = self._nodes.get(self._current)
        if node and node.children and index < len(node.children):
            self._current = node.children[index]
            return True
        return False

    def get_current(self) -> str:
        return self._current

    def current_node(self) -> SessionNode | None:
        return self._nodes.get(self._current)

    def get_path(self) -> list[str]:
        path: list[str] = []
        node = self._nodes.get(self._current)
        while node:
            path.append(node.session_id)
            node = self._nodes.get(node.parent_id)
        return list(reversed(path))

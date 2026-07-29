from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class UIElement:
    type: str  # button, text, form, chart, table, image, list, card, input
    props: dict[str, Any] = field(default_factory=dict)
    children: list[UIElement] = field(default_factory=list)
    id: str = ""


@dataclass
class CanvasAction:
    type: str  # render, update, clear, append
    elements: list[UIElement] = field(default_factory=list)
    target: str = "main"  # which canvas panel


class Canvas:
    def __init__(self):
        self._elements: list[UIElement] = []
        self._actions: list[CanvasAction] = []

    def render(self, elements: list[UIElement], target: str = "main") -> None:
        self._elements = elements
        self._actions.append(CanvasAction(type="render", elements=elements, target=target))

    def append(self, element: UIElement, target: str = "main") -> None:
        self._elements.append(element)
        self._actions.append(CanvasAction(type="append", elements=[element], target=target))

    def clear(self, target: str = "main") -> None:
        self._elements = []
        self._actions.append(CanvasAction(type="clear", target=target))

    def button(self, label: str, action: str, id: str = "") -> UIElement:
        return UIElement(type="button", props={"label": label, "action": action}, id=id or f"btn_{len(self._elements)}")

    def text(self, content: str, style: str = "") -> UIElement:
        return UIElement(type="text", props={"content": content, "style": style})

    def form(self, fields: list[dict[str, Any]], submit_action: str) -> UIElement:
        return UIElement(type="form", props={"fields": fields, "submit_action": submit_action})

    def table(self, headers: list[str], rows: list[list[str]]) -> UIElement:
        return UIElement(type="table", props={"headers": headers, "rows": rows})

    def chart(self, chart_type: str, data: list[dict[str, Any]], title: str = "") -> UIElement:
        return UIElement(type="chart", props={"chart_type": chart_type, "data": data, "title": title})

    def get_actions(self) -> list[CanvasAction]:
        actions = list(self._actions)
        self._actions.clear()
        return actions

    def to_json(self) -> str:
        return json.dumps([
            {"type": a.type, "elements": [self._element_to_dict(e) for e in a.elements], "target": a.target}
            for a in self._actions
        ])

    def _element_to_dict(self, el: UIElement) -> dict[str, Any]:
        return {
            "id": el.id,
            "type": el.type,
            "props": el.props,
            "children": [self._element_to_dict(c) for c in el.children],
        }

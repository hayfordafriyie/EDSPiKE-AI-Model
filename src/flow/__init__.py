from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class FlowNodeStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class FlowNode:
    id: str
    label: str = ""
    action: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    status: FlowNodeStatus = FlowNodeStatus.PENDING
    result: Any = None


@dataclass
class FlowEdge:
    source: str
    target: str
    condition: str = ""  # empty = unconditional


@dataclass
class Flow:
    id: str
    nodes: list[FlowNode] = field(default_factory=list)
    edges: list[FlowEdge] = field(default_factory=list)
    start_node: str = ""
    current_node_id: str = ""


NodeHandler = Callable[[FlowNode], Any]


class FlowRunner:
    def __init__(self):
        self._handlers: dict[str, NodeHandler] = {}
        self._node_map: dict[str, FlowNode] = {}

    def register_handler(self, action: str, handler: NodeHandler) -> None:
        self._handlers[action] = handler

    def run(self, flow: Flow) -> list[FlowNode]:
        self._node_map = {n.id: n for n in flow.nodes}
        executed: list[FlowNode] = []
        current_id = flow.start_node

        while current_id:
            node = self._node_map.get(current_id)
            if node is None:
                break
            node.status = FlowNodeStatus.RUNNING

            handler = self._handlers.get(node.action)
            if handler:
                try:
                    node.result = handler(node)
                    node.status = FlowNodeStatus.COMPLETED
                except Exception as e:
                    node.result = str(e)
                    node.status = FlowNodeStatus.FAILED
            else:
                node.status = FlowNodeStatus.COMPLETED

            executed.append(node)
            current_id = self._next_node(flow, node)

        return executed

    def ralph_loop(self, flow: Flow, max_iterations: int = 10, continue_fn: Callable[[], bool] | None = None) -> list[list[FlowNode]]:
        iterations: list[list[FlowNode]] = []
        iteration = 0
        while iteration < max_iterations:
            if continue_fn and not continue_fn():
                break
            for node in flow.nodes:
                node.status = FlowNodeStatus.PENDING
                node.result = None
            result = self.run(flow)
            iterations.append(result)
            iteration += 1
            all_completed = all(n.status == FlowNodeStatus.COMPLETED for n in result)
            if all_completed:
                break
        return iterations

    def _next_node(self, flow: Flow, current: FlowNode) -> str:
        outgoing = [e for e in flow.edges if e.source == current.id]
        if not outgoing:
            return ""
        for edge in outgoing:
            if not edge.condition:
                return edge.target
            node_result = str(current.result or "")
            if edge.condition in node_result:
                return edge.target
        return outgoing[0].target if outgoing else ""

    @staticmethod
    def parse_mermaid(mermaid_text: str) -> Flow:
        flow = Flow(id=f"flow_{int(time.time())}")
        for line in mermaid_text.splitlines():
            line = line.strip()
            if "-->|" in line:
                parts = line.split("-->|")
                left = parts[0].strip()
                rest = parts[1].strip()
                if "|" in rest:
                    condition, target = rest.split("|", 1)
                    target = target.strip().rstrip(";")
                    source_node = left.lstrip("[").rstrip("]").strip()
                    target_node = target.lstrip("[").rstrip("]").strip()
                    flow.edges.append(FlowEdge(source=source_node, target=target_node, condition=condition))
            elif "-->" in line:
                parts = line.split("-->")
                if len(parts) == 2:
                    source = parts[0].strip().lstrip("[").rstrip("]").strip()
                    target = parts[1].strip().lstrip("[").rstrip("]").strip().rstrip(";")
                    flow.edges.append(FlowEdge(source=source, target=target))
        return flow

    def reset_nodes(self, flow: Flow) -> None:
        for node in flow.nodes:
            node.status = FlowNodeStatus.PENDING
            node.result = None

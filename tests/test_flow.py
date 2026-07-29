import pytest

from src.flow import FlowRunner, Flow, FlowNode, FlowEdge, FlowNodeStatus


class TestFlow:
    def test_simple_flow(self):
        runner = FlowRunner()
        flow = Flow(id="test", nodes=[
            FlowNode(id="start", label="Start", action="echo"),
            FlowNode(id="end", label="End", action="echo"),
        ], edges=[
            FlowEdge(source="start", target="end"),
        ], start_node="start")

        results = []
        runner.register_handler("echo", lambda n: results.append(n.id) or "ok")
        executed = runner.run(flow)
        assert len(executed) == 2
        assert results == ["start", "end"]

    def test_handler_error(self):
        runner = FlowRunner()
        flow = Flow(id="test", nodes=[
            FlowNode(id="n1", label="Fail", action="fail"),
        ], start_node="n1")

        def failing(n):
            raise ValueError("oops")

        runner.register_handler("fail", failing)
        executed = runner.run(flow)
        assert executed[0].status == FlowNodeStatus.FAILED

    def test_conditional_edge(self):
        runner = FlowRunner()
        flow = Flow(id="test", nodes=[
            FlowNode(id="check", label="Check", action="decide"),
            FlowNode(id="yes", label="Yes", action="echo"),
            FlowNode(id="no", label="No", action="echo"),
        ], edges=[
            FlowEdge(source="check", target="yes", condition="yes"),
            FlowEdge(source="check", target="no", condition="no"),
        ], start_node="check")

        def decider(n):
            return "yes"
        runner.register_handler("decide", decider)
        runner.register_handler("echo", lambda n: "done")

        executed = runner.run(flow)
        assert len(executed) == 2
        assert executed[1].id == "yes"

    def test_parse_mermaid(self):
        mermaid = "A[Start] -->|condition| B[Process]\nB --> C[End]"
        flow = FlowRunner.parse_mermaid(mermaid)
        assert len(flow.edges) == 2
        assert flow.edges[0].condition == "condition"

    def test_ralph_loop(self):
        runner = FlowRunner()
        flow = Flow(id="ralph", nodes=[
            FlowNode(id="step", label="Step", action="work"),
        ], start_node="step")

        count = [0]

        def worker(n):
            count[0] += 1
            return f"iteration {count[0]}"

        runner.register_handler("work", worker)
        iterations = runner.ralph_loop(flow, max_iterations=3)
        assert len(iterations) >= 1

    def test_reset_nodes(self):
        runner = FlowRunner()
        flow = Flow(id="test", nodes=[
            FlowNode(id="n1", label="N1"),
        ], start_node="n1")
        flow.nodes[0].status = FlowNodeStatus.COMPLETED
        runner.reset_nodes(flow)
        assert flow.nodes[0].status == FlowNodeStatus.PENDING

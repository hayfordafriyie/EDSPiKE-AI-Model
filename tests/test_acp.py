import pytest

from src.acp import AcpChannel, AcpMessage


class TestACP:
    def test_create_channel(self):
        ch = AcpChannel("agent1")
        assert ch.agent_id == "agent1"

    def test_send_and_receive(self):
        ch = AcpChannel("agent1")
        msg = AcpMessage(type="request", sender="agent2", receiver="agent1", method="ping")
        ch.send(msg)
        received = ch.receive()
        assert len(received) == 1
        assert received[0].method == "ping"

    def test_receive_empty(self):
        ch = AcpChannel("agent1")
        assert ch.receive() == []

    def test_register_and_handle(self):
        ch = AcpChannel("agent1")

        def ping_handler(params):
            return "pong"

        ch.register_handler("ping", ping_handler)
        msg = AcpMessage(type="request", sender="agent2", id="123", method="ping", params={})
        response = ch.handle(msg)
        assert response is not None
        assert response.result == "pong"
        assert response.receiver == "agent2"

    def test_handle_unknown_method(self):
        ch = AcpChannel("agent1")
        msg = AcpMessage(type="request", sender="agent2", id="123", method="unknown", params={})
        response = ch.handle(msg)
        assert response is None

    def test_request(self):
        ch = AcpChannel("agent1")
        msg_id = ch.request("agent2", "ping", {"data": "hello"})
        assert msg_id.startswith("acp_")
        received = ch.receive()
        assert len(received) == 1
        assert received[0].receiver == "agent2"
        assert received[0].params["data"] == "hello"

    def test_respond(self):
        ch2 = AcpChannel("agent2")
        req = AcpMessage(type="request", sender="agent1", id="req1", method="ping")
        ch2.respond(req, result="pong")
        received = ch2.receive()
        assert len(received) == 1
        assert received[0].type == "response"
        assert received[0].result == "pong"

    def test_broadcast(self):
        ch = AcpChannel("agent1")
        ch.broadcast("announce", {"msg": "hello all"})
        received = ch.receive()
        assert len(received) == 1
        assert received[0].type == "broadcast"

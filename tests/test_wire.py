import time
import pytest

from src.wire import Wire, WireChannel, WireMessage, WireEventType, turn_begin, turn_end, step_begin, send_text, send_status


class TestWire:
    def test_send_receive(self):
        ch = WireChannel()
        msg = WireMessage(type=WireEventType.TURN_BEGIN, data={"user_input": "hello"})
        ch.send(msg)
        received = ch.receive(block=False)
        assert received is not None
        assert received.type == WireEventType.TURN_BEGIN
        assert received.data["user_input"] == "hello"

    def test_shutdown(self):
        ch = WireChannel()
        ch.shutdown()
        msg = WireMessage(type=WireEventType.TEXT_PART)
        ch.send(msg)
        assert ch.is_shutdown

    def test_wire_bidirectional(self):
        wire = Wire()
        wire.soul_side.send(WireMessage(type=WireEventType.TURN_BEGIN, data={"user_input": "hi"}))
        msg = wire.soul_side.receive(block=False)
        assert msg is not None
        assert msg.type == WireEventType.TURN_BEGIN

    def test_turn_begin_end(self):
        wire = Wire()
        turn_begin(wire, "hello")
        msg = wire.soul_side.receive(block=False)
        assert msg is not None
        assert msg.type == WireEventType.TURN_BEGIN

    def test_step_begin(self):
        wire = Wire()
        step_begin(wire, 1)
        msg = wire.soul_side.receive(block=False)
        assert msg is not None
        assert msg.type == WireEventType.STEP_BEGIN
        assert msg.data["n"] == 1

    def test_send_text(self):
        wire = Wire()
        send_text(wire, "hello world")
        msg = wire.soul_side.receive(block=False)
        assert msg is not None
        assert msg.type == WireEventType.TEXT_PART

    def test_send_status(self):
        wire = Wire()
        send_status(wire, context_usage=0.5, plan_mode=True)
        msg = wire.soul_side.receive(block=False)
        assert msg is not None
        assert msg.type == WireEventType.STATUS_UPDATE
        assert msg.data["plan_mode"] is True

    def test_no_wire_no_crash(self):
        turn_begin(None, "hello")  # should not crash
        send_text(None, "text")

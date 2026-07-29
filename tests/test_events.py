from __future__ import annotations

import json

from src.events import (
    StepStart, TextStart, TextDelta, TextEnd,
    ReasoningStart, ReasoningDelta, ReasoningEnd,
    ToolCallStarted, ToolResultEvent, ToolErrorEvent,
    StepFinish, Finish, ProviderError,
    Usage, FinishReason, event_to_sse,
)


def test_step_start():
    e = StepStart(index=0)
    assert e.type == "step-start"
    data = json.loads(event_to_sse(e).removeprefix("data: ").strip())
    assert data["type"] == "step-start"
    assert data["index"] == 0


def test_text_delta():
    e = TextDelta(id="t1", text="hello")
    assert e.type == "text-delta"
    data = json.loads(event_to_sse(e).removeprefix("data: ").strip())
    assert data["text"] == "hello"


def test_reasoning_flow():
    start = ReasoningStart(id="r1")
    delta = ReasoningDelta(id="r1", text="thinking...")
    end = ReasoningEnd(id="r1")
    assert start.type == "reasoning-start"
    assert delta.type == "reasoning-delta"
    assert end.type == "reasoning-end"
    for e in [start, delta, end]:
        data = json.loads(event_to_sse(e).removeprefix("data: ").strip())
        assert data["id"] == "r1"


def test_tool_events():
    call = ToolCallStarted(id="tc1", name="read_file", input={"path": "/x"})
    result = ToolResultEvent(id="tc1", name="read_file", result="content")
    err = ToolErrorEvent(id="tc2", name="write_file", message="permission denied")
    assert call.type == "tool-call-start"
    assert result.type == "tool-result"
    assert err.type == "tool-error"
    for e in [call, result, err]:
        data = json.loads(event_to_sse(e).removeprefix("data: ").strip())
        assert data["name"] is not None


def test_finish_with_usage():
    usage = Usage(input_tokens=10, output_tokens=20, total_tokens=30)
    finish = Finish(reason=FinishReason.STOP, usage=usage)
    data = json.loads(event_to_sse(finish).removeprefix("data: ").strip())
    assert data["type"] == "finish"
    assert data["reason"] == "stop"
    assert data["usage"]["input_tokens"] == 10


def test_provider_error():
    e = ProviderError(message="rate limited", retryable=True)
    data = json.loads(event_to_sse(e).removeprefix("data: ").strip())
    assert data["type"] == "provider-error"
    assert data["retryable"] is True


def test_chunk_text():
    from src.events import chunk_text
    text = "a b c d e f"
    chunks = chunk_text(text, 2)
    assert chunks == ["a b", "c d", "e f"]


def test_chunk_text_single():
    from src.events import chunk_text
    chunks = chunk_text("hello world", 50)
    assert chunks == ["hello world"]

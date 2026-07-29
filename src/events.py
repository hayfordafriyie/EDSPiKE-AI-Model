from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class FinishReason(str, Enum):
    STOP = "stop"
    LENGTH = "length"
    ERROR = "error"
    TOOL_CALL = "tool_call"
    CONTENT_FILTERED = "content_filtered"


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    reasoning_tokens: int = 0


@dataclass
class StepStart:
    type: str = "step-start"
    index: int = 0


@dataclass
class TextStart:
    type: str = "text-start"
    id: str = ""


@dataclass
class TextDelta:
    type: str = "text-delta"
    id: str = ""
    text: str = ""


@dataclass
class TextEnd:
    type: str = "text-end"
    id: str = ""


@dataclass
class ReasoningStart:
    type: str = "reasoning-start"
    id: str = ""


@dataclass
class ReasoningDelta:
    type: str = "reasoning-delta"
    id: str = ""
    text: str = ""


@dataclass
class ReasoningEnd:
    type: str = "reasoning-end"
    id: str = ""


@dataclass
class ToolCallStarted:
    type: str = "tool-call-start"
    id: str = ""
    name: str = ""
    input: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResultEvent:
    type: str = "tool-result"
    id: str = ""
    name: str = ""
    result: str = ""


@dataclass
class ToolErrorEvent:
    type: str = "tool-error"
    id: str = ""
    name: str = ""
    message: str = ""


@dataclass
class StepFinish:
    type: str = "step-finish"
    index: int = 0
    reason: FinishReason = FinishReason.STOP
    usage: Usage | None = None


@dataclass
class Finish:
    type: str = "finish"
    reason: FinishReason = FinishReason.STOP
    usage: Usage | None = None


@dataclass
class ProviderError:
    type: str = "provider-error"
    message: str = ""
    retryable: bool = False


EDSPiKEEvent = (
    StepStart | TextStart | TextDelta | TextEnd
    | ReasoningStart | ReasoningDelta | ReasoningEnd
    | ToolCallStarted | ToolResultEvent | ToolErrorEvent
    | StepFinish | Finish | ProviderError
)


def event_to_sse(event: EDSPiKEEvent) -> str:
    import json
    data: dict[str, Any] = {"type": event.type}
    for f in event.__dataclass_fields__:
        if f != "type":
            v = getattr(event, f)
            if v is not None and not (isinstance(v, Enum) and v.value is None):
                if isinstance(v, Usage):
                    data[f] = v.__dict__
                elif isinstance(v, Enum):
                    data[f] = v.value
                else:
                    data[f] = v
    return f"data: {json.dumps(data)}\n\n"


def chunk_text(text: str, size: int = 50) -> list[str]:
    words = text.split(" ")
    chunks: list[str] = []
    for i in range(0, len(words), size):
        chunks.append(" ".join(words[i:i + size]))
    return chunks or [text]

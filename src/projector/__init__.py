from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class ProjectorAnomaly:
    rule: str
    description: str
    details: dict[str, Any] = field(default_factory=dict)


ProjectorStep = Callable[[list[dict[str, Any]]], list[dict[str, Any]]]


def merge_adjacent_user_messages(turns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for turn in turns:
        if result and result[-1].get("role") == "user" and turn.get("role") == "user":
            result[-1]["content"] = (result[-1].get("content", "") + "\n" + turn.get("content", "")).strip()
            result[-1]["_merged"] = True
        else:
            result.append(dict(turn))
    return result


def dedupe_duplicate_tool_calls(turns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for turn in turns:
        if turn.get("role") == "tool":
            key = (turn.get("name", ""), turn.get("content", "")[:100])
            if key in seen:
                continue
            seen.add(key)
        result.append(dict(turn))
    return result


def repair_tool_exchange_adjacency(turns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for turn in turns:
        if (turn.get("role") == "tool" or turn.get("role") == "function") and result and result[-1].get("role") not in ("assistant", "tool", "function"):
            result.append({"role": "assistant", "content": "", "_injected": True})
        result.append(dict(turn))
    return result


def drop_orphan_results(turns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    pending_calls = 0
    for turn in turns:
        if turn.get("role") == "assistant" and turn.get("tool_calls"):
            pending_calls = len(turn["tool_calls"])
            result.append(dict(turn))
        elif (turn.get("role") == "tool" or turn.get("role") == "function") and pending_calls > 0:
            pending_calls -= 1
            result.append(dict(turn))
        elif turn.get("role") == "tool" or turn.get("role") == "function":
            pass  # drop orphan result
        else:
            result.append(dict(turn))
    return result


def drop_leading_non_user(turns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = list(turns)
    while result and result[0].get("role") != "user" and result[0].get("role") != "system":
        result.pop(0)
    return result


DEFAULT_PROJECTOR_PIPELINE: list[ProjectorStep] = [
    merge_adjacent_user_messages,
    dedupe_duplicate_tool_calls,
    repair_tool_exchange_adjacency,
    drop_orphan_results,
    drop_leading_non_user,
]


def run_pipeline(turns: list[dict[str, Any]], steps: list[ProjectorStep] | None = None) -> tuple[list[dict[str, Any]], list[ProjectorAnomaly]]:
    pipeline = steps or DEFAULT_PROJECTOR_PIPELINE
    result = [dict(t) for t in turns]
    anomalies: list[ProjectorAnomaly] = []

    for step in pipeline:
        before = len(result)
        try:
            result = step(result)
        except Exception as e:
            anomalies.append(ProjectorAnomaly(
                rule=step.__name__,
                description=f"Failed: {e}",
            ))
            continue
        after = len(result)
        if before != after:
            anomalies.append(ProjectorAnomaly(
                rule=step.__name__,
                description=f"Filtered {before - after} turns",
                details={"before": before, "after": after, "removed": before - after},
            ))

    return result, anomalies

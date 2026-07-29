from __future__ import annotations

import json
import re
from typing import Any


def repair_tool_call(text: str) -> tuple[dict[str, Any] | None, list[str]]:
    repairs: list[str] = []

    if not text or not text.strip():
        return None, ["Empty tool call"]

    # Try direct parse
    try:
        result = json.loads(text)
        if isinstance(result, dict) and "name" in result and "arguments" in result:
            return result, []
        return result, []
    except json.JSONDecodeError as e:
        repairs.append(f"Initial parse failed: {e.msg}")

    # Try fixing truncated JSON
    fixed = text

    # Add missing closing braces
    open_braces = fixed.count("{")
    close_braces = fixed.count("}")
    if open_braces > close_braces:
        fixed += "}" * (open_braces - close_braces)
        repairs.append(f"Added {open_braces - close_braces} missing closing braces")

    # Add missing closing brackets
    open_brackets = fixed.count("[")
    close_brackets = fixed.count("]")
    if open_brackets > close_brackets:
        fixed += "]" * (open_brackets - close_brackets)
        repairs.append(f"Added {open_brackets - close_brackets} missing closing brackets")

    # Add missing closing quotes
    if fixed.count('"') % 2 != 0:
        fixed += '"'
        repairs.append("Added missing closing quote")

    # Fix trailing commas
    fixed = re.sub(r",\s*([}\]])", r"\1", fixed)
    if fixed != text:
        repairs.append("Removed trailing commas")

    # Try parsing again
    try:
        result = json.loads(fixed)
        return result, repairs
    except json.JSONDecodeError as e:
        repairs.append(f"Repair failed: {e.msg}")
        return None, repairs


def extract_tool_call(text: str) -> dict[str, Any] | None:
    """Extract tool call JSON from text that may contain surrounding content."""
    # Try XML-style <tool_call> tags
    xml_match = re.search(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", text, re.DOTALL)
    if xml_match:
        result, _ = repair_tool_call(xml_match.group(1))
        if result:
            return result

    # Try JSON object in text
    json_match = re.search(r"\{[^{}]*\"(?:name|function|tool)\"[^{}]*\}", text, re.DOTALL)
    if json_match:
        result, _ = repair_tool_call(json_match.group())
        if result:
            return result

    # Try parsing entire text as JSON
    result, _ = repair_tool_call(text)
    return result


def validate_tool_call(call: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if "name" not in call or not isinstance(call.get("name"), str):
        errors.append("Missing or invalid 'name' field")
    if "arguments" not in call:
        errors.append("Missing 'arguments' field")
    elif not isinstance(call["arguments"], dict):
        errors.append("'arguments' must be an object")
    return len(errors) == 0, errors

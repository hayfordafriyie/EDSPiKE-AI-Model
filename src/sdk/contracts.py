from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class ValidationError(Exception):
    pass


@dataclass
class Contract:
    name: str
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)

    def validate_input(self, data: dict[str, Any]) -> dict[str, Any]:
        errors: list[str] = []
        required_fields = self.input_schema.get("required", [])
        for field_name in required_fields:
            if field_name not in data or data[field_name] is None:
                errors.append(f"Missing required field: {field_name}")
        for field_name, rules in self.input_schema.get("properties", {}).items():
            if field_name not in data:
                continue
            val = data[field_name]
            expected_type = rules.get("type", "")
            if expected_type == "string" and not isinstance(val, str):
                errors.append(f"Field '{field_name}' must be a string, got {type(val).__name__}")
            elif expected_type == "integer" and not isinstance(val, int):
                errors.append(f"Field '{field_name}' must be an integer, got {type(val).__name__}")
            elif expected_type == "number" and not isinstance(val, (int, float)):
                errors.append(f"Field '{field_name}' must be a number, got {type(val).__name__}")
            elif expected_type == "array" and not isinstance(val, list):
                errors.append(f"Field '{field_name}' must be an array, got {type(val).__name__}")
            elif expected_type == "object" and not isinstance(val, dict):
                errors.append(f"Field '{field_name}' must be an object, got {type(val).__name__}")

        if errors:
            raise ValidationError(f"Validation failed for {self.name}: {'; '.join(errors)}")
        return data

    def validate_output(self, data: Any) -> Any:
        return data


GENERATE_CONTRACT = Contract(
    name="generate",
    input_schema={
        "properties": {
            "prompt": {"type": "string"},
            "model": {"type": "string"},
            "max_tokens": {"type": "integer"},
            "temperature": {"type": "number"},
            "session_id": {"type": "string"},
        },
        "required": ["prompt"],
    },
)

LIST_AGENTS_CONTRACT = Contract(name="list_agents", input_schema={"properties": {}})
LIST_SESSIONS_CONTRACT = Contract(name="list_sessions", input_schema={"properties": {}})
HEALTH_CONTRACT = Contract(name="health", input_schema={"properties": {}})

READ_FILE_CONTRACT = Contract(
    name="read_file",
    input_schema={
        "properties": {
            "path": {"type": "string"},
        },
        "required": ["path"],
    },
)

WRITE_FILE_CONTRACT = Contract(
    name="write_file",
    input_schema={
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
        },
        "required": ["path", "content"],
    },
)

EXECUTE_CODE_CONTRACT = Contract(
    name="execute_code",
    input_schema={
        "properties": {
            "code": {"type": "string"},
            "language": {"type": "string"},
        },
        "required": ["code"],
    },
)

ALL_CONTRACTS: dict[str, Contract] = {
    "generate": GENERATE_CONTRACT,
    "list_agents": LIST_AGENTS_CONTRACT,
    "list_sessions": LIST_SESSIONS_CONTRACT,
    "health": HEALTH_CONTRACT,
    "read_file": READ_FILE_CONTRACT,
    "write_file": WRITE_FILE_CONTRACT,
    "execute_code": EXECUTE_CODE_CONTRACT,
}


def validate(method: str, data: dict[str, Any]) -> dict[str, Any]:
    contract = ALL_CONTRACTS.get(method)
    if contract is None:
        return data
    return contract.validate_input(data)

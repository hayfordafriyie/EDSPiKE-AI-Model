from __future__ import annotations

import shlex
import time
from dataclasses import dataclass, field
from typing import Any, Callable

PipelineStep = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass
class PipelineResult:
    steps: list[dict[str, Any]] = field(default_factory=list)
    final_output: Any = None
    approved: bool = True
    duration_ms: float = 0.0


@dataclass
class ApprovalGate:
    required: bool = False
    approved: bool = False
    message: str = ""


class LobsterEngine:
    def __init__(self):
        self._steps: dict[str, PipelineStep] = {}

    def register(self, name: str, step: PipelineStep) -> None:
        self._steps[name] = step

    def parse_pipeline(self, pipeline_text: str) -> list[str]:
        parts = shlex.split(pipeline_text)
        steps: list[str] = []
        for part in parts:
            if part == "|":
                continue
            steps.append(part)
        return steps

    def run(self, pipeline_text: str, initial_input: dict[str, Any] | None = None, approval_fn: Callable[[str], bool] | None = None) -> PipelineResult:
        step_names = self.parse_pipeline(pipeline_text)
        result = PipelineResult()
        start = time.time()
        current_input = initial_input or {}

        for step_name in step_names:
            step_fn = self._steps.get(step_name)
            if step_fn is None:
                result.steps.append({"name": step_name, "error": f"Unknown step: {step_name}", "output": None})
                continue

            if approval_fn and not approval_fn(step_name):
                result.approved = False
                result.steps.append({"name": step_name, "error": "Approval denied", "output": None, "approval": "denied"})
                break

            try:
                output = step_fn(current_input)
                current_input = output
                result.steps.append({"name": step_name, "output": output, "error": None})
            except Exception as e:
                result.steps.append({"name": step_name, "error": str(e), "output": None})
                break

        result.final_output = current_input if result.steps else None
        result.duration_ms = (time.time() - start) * 1000
        return result

    def run_with_approval(self, pipeline_text: str, initial_input: dict[str, Any] | None = None, gates: list[int] | None = None) -> PipelineResult:
        step_names = self.parse_pipeline(pipeline_text)
        gates = gates or []

        def auto_approve(step_name: str) -> bool:
            return True

        result = PipelineResult()
        start = time.time()
        current_input = initial_input or {}

        for i, step_name in enumerate(step_names):
            step_fn = self._steps.get(step_name)
            if step_fn is None:
                result.steps.append({"name": step_name, "error": f"Unknown step: {step_name}", "output": None})
                continue

            if i in gates:
                print(f"[Approval required] Run step '{step_name}'? (Y/n): ")
                try:
                    response = input().strip().lower()
                    if response not in ("", "y", "yes"):
                        result.steps.append({"name": step_name, "error": "Approval denied", "output": None, "approval": "denied"})
                        result.approved = False
                        break
                except (EOFError, KeyboardInterrupt):
                    result.steps.append({"name": step_name, "error": "Approval timed out", "output": None, "approval": "denied"})
                    result.approved = False
                    break

            try:
                output = step_fn(current_input)
                current_input = output
                result.steps.append({"name": step_name, "output": output, "error": None})
            except Exception as e:
                result.steps.append({"name": step_name, "error": str(e), "output": None})
                break

        result.final_output = current_input if result.steps else None
        result.duration_ms = (time.time() - start) * 1000
        return result

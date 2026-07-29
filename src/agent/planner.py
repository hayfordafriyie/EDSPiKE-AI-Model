from __future__ import annotations

import json
import logging
from typing import Any, Callable

from .types import Plan, Step, StepStatus

logger = logging.getLogger(__name__)

PLANNER_PROMPT = """You are a planning agent. Given a task, break it down into a series of concrete steps.

Rules:
- Each step must be a single actionable unit (read a file, run a command, edit a file, etc.)
- Steps should be ordered logically
- Each step has an "action" field describing what to do

Return ONLY a JSON object with this structure:
{
  "goal": "high-level description of the overall task",
  "steps": [
    {"index": 1, "description": "what this step accomplishes", "action": "the concrete action to take"},
    {"index": 2, ...}
  ]
}

Do NOT include any text outside the JSON object.
"""


class Planner:
    def __init__(self, generate_fn: Callable):
        self._generate_fn = generate_fn

    def create_plan(self, task: str, context: str = "") -> Plan:
        prompt = PLANNER_PROMPT
        if context:
            prompt += f"\n\nContext:\n{context}"
        prompt += f"\n\nTask: {task}"

        responses, _ = self._generate_fn(
            [prompt],
            max_tokens=2048,
            temperature=0.3,
            top_p=0.95,
        )
        raw = responses[0].strip()
        try:
            start = raw.index("{")
            end = raw.rindex("}") + 1
            data = json.loads(raw[start:end])
        except (ValueError, json.JSONDecodeError):
            data = {"goal": task, "steps": [
                {"index": 1, "description": "Complete the task", "action": task},
            ]}

        steps = []
        for s in data.get("steps", []):
            steps.append(Step(
                index=s.get("index", len(steps) + 1),
                description=s.get("description", ""),
                action=s.get("action", ""),
            ))

        return Plan(goal=data.get("goal", task), steps=steps)

    def revise_plan(self, plan: Plan, feedback: str) -> Plan:
        prompt = (
            f"The current plan for '{plan.goal}' hit a problem.\n\n"
            f"Current steps:\n"
        )
        for s in plan.steps:
            mark = "✓" if s.status == StepStatus.COMPLETED else "✗" if s.status == StepStatus.FAILED else "○"
            prompt += f"  [{mark}] Step {s.index}: {s.description} ({s.status.value})\n"
            if s.error:
                prompt += f"       Error: {s.error}\n"

        prompt += f"\nFeedback: {feedback}\n"
        prompt += "\nRevise the remaining steps. Return JSON with the same format as before, including already-completed steps but updating any failed or pending ones."

        responses, _ = self._generate_fn(
            [prompt],
            max_tokens=2048,
            temperature=0.4,
            top_p=0.95,
        )
        raw = responses[0].strip()
        try:
            start = raw.index("{")
            end = raw.rindex("}") + 1
            data = json.loads(raw[start:end])
        except (ValueError, json.JSONDecodeError):
            return plan

        steps = []
        for s in data.get("steps", []):
            existing = next((x for x in plan.steps if x.index == s.get("index")), None)
            if existing and existing.status == StepStatus.COMPLETED:
                steps.append(existing)
            else:
                steps.append(Step(
                    index=s.get("index", len(steps) + 1),
                    description=s.get("description", ""),
                    action=s.get("action", ""),
                ))

        plan.steps = steps
        return plan

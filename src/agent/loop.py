from __future__ import annotations

import json
import logging
from typing import Any, Callable

from src.tools.executor import ToolExecutor
from src.tools.registry import get_tool_schemas

from .planner import Planner
from .types import AgentState, Plan, Step, StepStatus

logger = logging.getLogger(__name__)

ACTOR_SYSTEM_TEMPLATE = """You are an AI coding agent executing a plan. You have access to tools to accomplish your task.

## Available Tools
{tool_descriptions}

## Current Plan
Goal: {goal}

Steps (remaining marked with ○, completed with ✓, failed with ✗):
{steps_status}

## How to use tools
When you need to use a tool, output EXACTLY this format:
<tool_call>
{{"name": "tool_name", "arguments": {{"arg1": "value1"}}}}
</tool_call>

The tool result will be returned as:
<tool_result>
... result ...
</tool_result>

## Rules
- Focus on the current step
- When a step is done, say "Step N complete: <summary>"
- When ALL steps are done, say "Task complete: <final answer>"
- Never invent file contents — always read first
"""


class AgentLoop:
    def __init__(
        self,
        generate_fn: Callable,
        planner: Planner | None = None,
        executor: ToolExecutor | None = None,
        workspace: str = ".",
    ):
        self.generate_fn = generate_fn
        self.planner = planner or Planner(generate_fn)
        self.executor = executor or ToolExecutor()
        self.workspace = workspace

    def _build_system(self, plan: Plan) -> str:
        schemas = get_tool_schemas()
        descs = "\n\n".join(
            f"### {s['name']}\n{s['description']}\nJSON Schema: {json.dumps(s['parameters'])}"
            for s in schemas
        )
        lines = []
        for s in plan.steps:
            icon = {"pending": "○", "in_progress": "●", "completed": "✓", "failed": "✗", "skipped": "—"}.get(s.status.value, "○")
            lines.append(f"  [{icon}] Step {s.index}: {s.description} ({s.status.value})")
            if s.error:
                lines.append(f"       ⚠ Error: {s.error}")
        return ACTOR_SYSTEM_TEMPLATE.format(
            tool_descriptions=descs,
            goal=plan.goal,
            steps_status="\n".join(lines),
        )

    def run(self, task: str, max_tokens: int = 2048, temperature: float = 0.3) -> AgentState:
        plan = self.planner.create_plan(task)
        state = AgentState(plan=plan)

        state.messages = [f"# Task\n{task}"]

        while state.plan.current_step < len(state.plan.steps) and not state.finished and state.total_tokens < state.max_steps * 1000:
            step_idx = state.plan.current_step
            step = state.plan.steps[step_idx]
            step.status = StepStatus.IN_PROGRESS

            system = self._build_system(state.plan)
            instruction = f"\n## Current Step ({step.index}): {step.description}\nAction: {step.action}\n\nExecute this step using tools as needed."
            messages = [system] + state.messages + [instruction]
            prompt = "\n\n".join(messages)

            responses, counts = self.generate_fn(
                [prompt],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.95,
            )
            response = responses[0].strip()
            state.total_tokens += counts[0]

            calls = self.executor.parse_tool_call(response)
            if calls:
                step.tool_calls = calls
                results: list[str] = []
                all_ok = True
                for call in calls:
                    try:
                        out = self.executor.execute(call["name"], call["arguments"])
                        results.append(f"<tool_result>\n{out}\n</tool_result>")
                    except Exception as exc:
                        results.append(f"<tool_result>\nError: {exc}\n</tool_result>")
                        all_ok = False

                state.messages.append(response)
                state.messages.extend(results)

                if all_ok:
                    step.status = StepStatus.COMPLETED
                    step.result = results[-1] if results else ""
                    state.plan.current_step = step_idx + 1
                else:
                    step.status = StepStatus.FAILED
                    step.error = results[-1] if results else "Tool execution failed"
                    feedback = f"Step {step.index} failed: {step.error}"
                    state.plan = self.planner.revise_plan(state.plan, feedback)
                    correction = f"\n## Correction\nStep {step.index} failed. Revised plan provided above. Continue."
                    state.messages.append(correction)
            else:
                step.status = StepStatus.COMPLETED
                step.result = response
                state.plan.current_step = step_idx + 1
                state.messages.append(response)

        state.finished = True
        state.final_answer = self._extract_answer(state.messages[-1]) if state.messages else ""
        return state

    @staticmethod
    def _extract_answer(text: str) -> str:
        for prefix in ["Task complete:", "Step completed:", "Final answer:"]:
            if prefix.lower() in text.lower():
                idx = text.lower().index(prefix.lower())
                return text[idx + len(prefix):].strip()
        return text

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable

from .executor import ToolExecutor
from .registry import get_tool_schemas

logger = logging.getLogger(__name__)

SYSTEM_TEMPLATE = """You are an AI coding agent with access to tools. You solve problems by reasoning step-by-step and using tools when needed.

## Available Tools
{tool_descriptions}

## How to use tools
When you need to use a tool, output EXACTLY this format:
<tool_call>
{{"name": "tool_name", "arguments": {{"arg1": "value1"}}}}
</tool_call>

The tool result will be returned as:
<tool_result>
... result ...
</tool_result>

## Guidelines
- Think step by step before using each tool
- Use read_file first to examine code before editing
- For bash commands, prefer non-interactive commands
- When you have the final answer, output it without tool tags
- Never invent file contents — always read first
- Respect the workspace boundaries

## Workspace
You are working in: {workspace}

Begin."""


@dataclass
class ReActTurn:
    thought: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    tool_results: list[str] = field(default_factory=list)


@dataclass
class ReActResult:
    final_answer: str
    turns: list[ReActTurn] = field(default_factory=list)
    total_tokens: int = 0
    finished: bool = False


class ReActLoop:
    def __init__(
        self,
        generate_fn: Callable,
        executor: ToolExecutor | None = None,
        max_turns: int = 10,
        workspace: str = "",
    ):
        self.generate_fn = generate_fn
        self.executor = executor or ToolExecutor()
        self.max_turns = max_turns
        self.workspace = workspace or "."

    def _build_system(self) -> str:
        schemas = get_tool_schemas()
        descs = "\n\n".join(
            f"### {s['name']}\n{s['description']}\nJSON Schema: {json.dumps(s['parameters'])}"
            for s in schemas
        )
        return SYSTEM_TEMPLATE.format(tool_descriptions=descs, workspace=self.workspace)

    def run(
        self,
        question: str,
        max_tokens: int = 2048,
        temperature: float = 0.3,
    ) -> ReActResult:
        system = self._build_system()
        messages = [system, f"## Task\n{question}"]
        result = ReActResult(final_answer="")
        turn = ReActTurn()

        for _ in range(self.max_turns):
            prompt = "\n\n".join(messages)
            responses, counts = self.generate_fn(
                [prompt],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.95,
            )
            response = responses[0].strip()
            result.total_tokens += counts[0]

            calls = self.executor.parse_tool_call(response)
            if calls:
                turn.thought = response
                turn.tool_calls = calls
                results: list[str] = []
                for call in calls:
                    try:
                        out = self.executor.execute(call["name"], call["arguments"])
                        results.append(f"<tool_result>\n{out}\n</tool_result>")
                    except Exception as exc:
                        results.append(f"<tool_result>\nError: {exc}\n</tool_result>")
                turn.tool_results = results
                result.turns.append(turn)
                turn = ReActTurn()
                messages.append(response)
                messages.extend(results)
            else:
                result.final_answer = response
                result.finished = True
                result.turns.append(turn)
                break
        else:
            result.final_answer = "Reached max turns without a final answer."
            result.turns.append(turn)

        return result

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CompactResult:
    original_length: int
    compressed_length: int
    text: str
    ratio: float


class TokenJuicer:
    def __init__(self, max_output_chars: int = 2000, max_lines: int = 100):
        self.max_output_chars = max_output_chars
        self.max_lines = max_lines

    def compact(self, tool_name: str, output: str) -> CompactResult:
        original = len(output)
        result = output

        # Compress repeated patterns (always runs)
        result = self._compress_repeated_lines(result)
        result = self._compress_json_arrays(result)
        result = self._compress_stack_traces(result)

        if original <= self.max_output_chars and len(result.splitlines()) <= self.max_lines:
            compressed = len(result)
            return CompactResult(original_length=original, compressed_length=compressed, text=result, ratio=compressed / original if original > 0 else 1.0)

        # Truncate long lines
        lines = result.splitlines()
        truncated_lines = []
        for line in lines:
            if len(line) > 500:
                line = line[:250] + f"\n[...truncated {len(line) - 500} chars...]\n" + line[-250:]
            truncated_lines.append(line)

        # 2. Limit number of lines
        if len(truncated_lines) > self.max_lines:
            truncated_lines = truncated_lines[: self.max_lines // 2]
            truncated_lines.append(f"[...{len(lines) - self.max_lines} lines omitted...]")
            truncated_lines.append(lines[-self.max_lines // 2 :])

        # Flatten since we might have nested lists
        flat_lines: list[str] = []
        for item in truncated_lines:
            if isinstance(item, list):
                flat_lines.extend(item)
            else:
                flat_lines.append(item)

        result = "\n".join(flat_lines)

        # 3. Compress repeated patterns
        result = self._compress_repeated_lines(result)
        result = self._compress_json_arrays(result)
        result = self._compress_stack_traces(result)

        compressed = len(result)
        return CompactResult(
            original_length=original,
            compressed_length=compressed,
            text=result,
            ratio=compressed / original if original > 0 else 1.0,
        )

    def _compress_repeated_lines(self, text: str) -> str:
        lines = text.splitlines(keepends=True)
        result: list[str] = []
        i = 0
        while i < len(lines):
            count = 1
            while i + count < len(lines) and lines[i] == lines[i + count]:
                count += 1
            if count > 3:
                result.append(lines[i])
                result.append(f"  [... repeated {count - 1} more times]\n")
                i += count
            else:
                for j in range(count):
                    result.append(lines[i + j])
                i += count
        return "".join(result)

    def _compress_json_arrays(self, text: str) -> str:
        array_pattern = re.compile(r"(\[[^\]]{500,}\])", re.DOTALL)
        return array_pattern.sub(lambda m: f"[...array of {len(m.group(1))} bytes...]", text)

    def _compress_stack_traces(self, text: str) -> str:
        trace_pattern = re.compile(r"((?:^\s*File .*, line \d+.*\n)+)", re.MULTILINE)
        return trace_pattern.sub(lambda m: f"[...stack trace of {len(m.group(1).splitlines())} frames...]\n", text)

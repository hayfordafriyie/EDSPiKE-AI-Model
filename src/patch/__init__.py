from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any


class PatchError(Exception):
    pass


def apply_patch(file_path: str, diff_content: str, reverse: bool = False) -> dict[str, Any]:
    path = Path(file_path)
    if not path.exists():
        raise PatchError(f"File not found: {file_path}")

    original = path.read_text()
    result = _apply_diff(original, diff_content, reverse=reverse)
    path.write_text(result["content"])
    return {
        "file_path": file_path,
        "hunks_applied": result["hunks_applied"],
        "hunks_failed": result["hunks_failed"],
    }


def create_patch(original: str, modified: str, context_lines: int = 3) -> str:
    orig_lines = original.splitlines(keepends=True)
    mod_lines = modified.splitlines(keepends=True)
    return _make_unified_diff(orig_lines, mod_lines, context_lines)


def _make_unified_diff(orig: list[str], mod: list[str], ctx: int = 3) -> str:
    import difflib
    diff = difflib.unified_diff(
        orig, mod,
        fromfile="a", tofile="b",
        n=ctx,
    )
    return "".join(diff)


def _apply_diff(original: str, diff_content: str, reverse: bool = False) -> dict[str, Any]:
    lines = original.splitlines(keepends=True)
    hunks = _parse_hunks(diff_content)
    if reverse:
        hunks = [_reverse_hunk(h) for h in hunks]

    applied = 0
    failed = 0
    offset = 0

    for hunk in hunks:
        start = hunk["old_start"] - 1 + offset
        old_len = hunk["old_count"]

        if lines[start:start + old_len] == hunk["old_lines"]:
            lines[start:start + old_len] = hunk["new_lines"]
            offset += len(hunk["new_lines"]) - old_len
            applied += 1
        else:
            # Try nearby positions
            found = False
            for delta in range(-5, 6):
                pos = start + delta
                if pos >= 0 and pos + old_len <= len(lines):
                    if lines[pos:pos + old_len] == hunk["old_lines"]:
                        lines[pos:pos + old_len] = hunk["new_lines"]
                        offset += len(hunk["new_lines"]) - old_len
                        applied += 1
                        found = True
                        hunk["old_start"] = pos + 1  # update for subsequent offset
                        break
            if not found:
                failed += 1

    return {"content": "".join(lines), "hunks_applied": applied, "hunks_failed": failed}


def _parse_hunks(diff_content: str) -> list[dict[str, Any]]:
    hunks: list[dict[str, Any]] = []
    lines = diff_content.splitlines(keepends=True)

    current_hunk: dict[str, Any] | None = None
    for line in lines:
        hunk_header = re.match(r"^@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@", line)
        if hunk_header:
            if current_hunk:
                hunks.append(current_hunk)
            old_count = int(hunk_header.group(2)) if hunk_header.group(2) else 1
            new_count = int(hunk_header.group(4)) if hunk_header.group(4) else 1
            current_hunk = {
                "old_start": int(hunk_header.group(1)),
                "old_count": old_count,
                "new_start": int(hunk_header.group(3)),
                "new_count": new_count,
                "old_lines": [],
                "new_lines": [],
            }
        elif current_hunk is not None:
            if line.startswith("+"):
                current_hunk["new_lines"].append(line[1:])
            elif line.startswith("-"):
                current_hunk["old_lines"].append(line[1:])
            else:
                current_hunk["old_lines"].append(line[1:])
                current_hunk["new_lines"].append(line[1:])

    if current_hunk:
        hunks.append(current_hunk)

    return hunks


def _reverse_hunk(hunk: dict[str, Any]) -> dict[str, Any]:
    return {
        "old_start": hunk["new_start"],
        "old_count": hunk["new_count"],
        "new_start": hunk["old_start"],
        "new_count": hunk["old_count"],
        "old_lines": hunk["new_lines"],
        "new_lines": hunk["old_lines"],
    }

from __future__ import annotations

import difflib
import sys
from pathlib import Path
from typing import Any


class DiffReviewer:
    def __init__(self, auto_approve: bool = False):
        self.auto_approve = auto_approve

    def review_write(self, file_path: str, content: str) -> bool:
        path = Path(file_path)
        if path.exists():
            old_content = path.read_text()
            return self._review_diff(file_path, old_content, content, "write")
        return self._review_create(file_path, content)

    def review_edit(self, file_path: str, old_string: str, new_string: str) -> bool:
        path = Path(file_path)
        if not path.exists():
            return True
        old_content = path.read_text()
        new_content = old_content.replace(old_string, new_string, 1)
        return self._review_diff(file_path, old_content, new_content, "edit")

    def review_patch(self, file_path: str, diff_content: str) -> bool:
        print(f"\n--- Patch Review: {file_path} ---")
        print(diff_content)
        return self._ask_approval(f"Apply patch to {file_path}?")

    def _review_create(self, file_path: str, content: str) -> bool:
        print(f"\n--- New File: {file_path} ---")
        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            print(f" {i:>4}+ {line}")
        return self._ask_approval(f"Create {file_path}?")

    def _review_diff(self, file_path: str, old: str, new: str, kind: str) -> bool:
        diff = difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
        )
        diff_text = "".join(diff)
        if not diff_text.strip():
            return True

        print(f"\n--- Diff Review: {file_path} ({kind}) ---")
        for line in diff_text.splitlines():
            if line.startswith("+"):
                print(f"\033[32m{line}\033[0m")  # green
            elif line.startswith("-"):
                print(f"\033[31m{line}\033[0m")  # red
            elif line.startswith("@@"):
                print(f"\033[36m{line}\033[0m")  # cyan
            else:
                print(line)

        return self._ask_approval(f"Apply changes to {file_path}?")

    def _ask_approval(self, question: str) -> bool:
        if self.auto_approve:
            return True
        try:
            response = input(f"\n{question} (Y/n): ").strip().lower()
            return response in ("", "y", "yes")
        except (EOFError, KeyboardInterrupt):
            return False

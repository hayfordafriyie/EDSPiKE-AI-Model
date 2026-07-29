from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class GitError(Exception):
    pass


class GitOperations:
    def __init__(self, repo_path: str = "."):
        self._repo = Path(repo_path).resolve()

    def _run(self, *args: str) -> str:
        try:
            result = subprocess.run(
                ["git"] + list(args),
                cwd=str(self._repo),
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                raise GitError(result.stderr.strip() or result.stdout.strip())
            out = result.stdout.strip()
            if not out:
                out = result.stderr.strip()
            return out
        except subprocess.TimeoutExpired:
            raise GitError("Git command timed out")
        except FileNotFoundError:
            raise GitError("Git not found")

    def status(self) -> str:
        return self._run("status")

    def diff(self, staged: bool = False, path: str = "") -> str:
        args = ["diff"]
        if staged:
            args.append("--cached")
        if path:
            args.append("--", path)
        return self._run(*args)

    def log(self, max_count: int = 10, format: str = "") -> str:
        fmt = format or "%h %s (%ai, %an)"
        return self._run("log", f"--max-count={max_count}", f"--format={fmt}")

    def branch(self, list_only: bool = True) -> str:
        if list_only:
            return self._run("branch")
        return self._run("branch")

    def checkout(self, branch: str, create: bool = False) -> str:
        args = ["checkout"]
        if create:
            args.extend(["-b", branch])
        else:
            args.append(branch)
        return self._run(*args)

    def commit(self, message: str, all: bool = True, allow_empty: bool = False) -> str:
        args = ["commit"]
        if all:
            args.append("-a")
        if allow_empty:
            args.append("--allow-empty")
        args.extend(["-m", message])
        return self._run(*args)

    def add(self, *paths: str) -> str:
        if not paths:
            paths = ("-A",)
        return self._run("add", *paths)

    def show(self, ref: str = "HEAD", stat: bool = False) -> str:
        args = ["show", ref]
        if stat:
            args.append("--stat")
        return self._run(*args)

    def diff_between(self, ref1: str, ref2: str = "HEAD", path: str = "") -> str:
        args = ["diff", ref1, ref2]
        if path:
            args.append("--", path)
        return self._run(*args)

    def shortlog(self, max_count: int = 10) -> str:
        return self._run("log", f"--max-count={max_count}", "--format=%an %s")

    def is_git_repo(self) -> bool:
        try:
            self._run("rev-parse", "--git-dir")
            return True
        except GitError:
            return False

    def get_tool_specs(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "git_status",
                "description": "Show the working tree status (modified, staged, untracked files)",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "git_diff",
                "description": "Show diff of unstaged changes, optionally for a specific file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "staged": {"type": "boolean", "description": "Show staged diff instead"},
                        "path": {"type": "string", "description": "Filter to specific file path"},
                    },
                },
            },
            {
                "name": "git_log",
                "description": "Show recent commit history",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "max_count": {"type": "integer", "description": "Number of commits to show"},
                    },
                },
            },
            {
                "name": "git_commit",
                "description": "Stage all changes and commit with a message",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "Commit message"},
                    },
                    "required": ["message"],
                },
            },
            {
                "name": "git_branch",
                "description": "List all branches",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "git_checkout",
                "description": "Switch to a branch, optionally creating it",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "branch": {"type": "string", "description": "Branch name"},
                        "create": {"type": "boolean", "description": "Create the branch if it doesn't exist"},
                    },
                    "required": ["branch"],
                },
            },
            {
                "name": "git_show",
                "description": "Show details of a commit",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ref": {"type": "string", "description": "Commit ref (default HEAD)"},
                        "stat": {"type": "boolean", "description": "Show file change stats"},
                    },
                },
            },
            {
                "name": "git_diff_between",
                "description": "Show diff between two refs (commits, branches, tags)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ref1": {"type": "string", "description": "Base ref"},
                        "ref2": {"type": "string", "description": "Target ref (default HEAD)"},
                        "path": {"type": "string", "description": "Filter to specific file"},
                    },
                    "required": ["ref1"],
                },
            },
        ]

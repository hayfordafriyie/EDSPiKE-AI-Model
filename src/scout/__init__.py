from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ScoutResult:
    repo_url: str
    local_path: str
    files_analyzed: int = 0
    languages: list[str] = field(default_factory=list)
    summary: str = ""
    diagnostics: list[dict[str, Any]] = field(default_factory=list)
    dependencies: list[dict[str, str]] = field(default_factory=list)
    entry_points: list[str] = field(default_factory=list)


class ScoutAgent:
    def __init__(self, cache_dir: str = ""):
        self._cache_dir = Path(cache_dir or "/tmp/edspike_scout")
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._repos: dict[str, ScoutResult] = {}

    def _repo_path(self, url: str) -> Path:
        safe = url.replace("://", "_").replace("/", "_").replace(":", "_")
        return self._cache_dir / safe

    def clone(self, url: str, branch: str = "") -> ScoutResult:
        dest = self._repo_path(url)
        if not dest.exists():
            cmd = ["git", "clone", "--depth", "1"]
            if branch:
                cmd.extend(["--branch", branch])
            cmd.extend([url, str(dest)])
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                raise RuntimeError(f"Clone failed: {result.stderr}")

        return self._analyze(url, str(dest))

    def analyze_local(self, url: str, path: str) -> ScoutResult:
        return self._analyze(url, path)

    def _analyze(self, url: str, path: str) -> ScoutResult:
        result = ScoutResult(repo_url=url, local_path=path)
        root = Path(path)

        files = list(root.rglob("*"))
        result.files_analyzed = sum(1 for f in files if f.is_file())

        exts: dict[str, int] = {}
        for f in files:
            if f.is_file():
                ext = f.suffix.lower()
                if ext:
                    exts[ext] = exts.get(ext, 0) + 1

        result.languages = sorted(exts, key=exts.get, reverse=True)[:10]

        # Detect entry points
        for pattern in ["main.py", "index.js", "index.ts", "Cargo.toml", "package.json", "setup.py", "go.mod"]:
            if (root / pattern).exists():
                result.entry_points.append(pattern)

        # Detect dependencies
        dep_files = [
            ("requirements.txt", self._parse_requirements),
            ("package.json", self._parse_package_json),
            ("Cargo.toml", self._parse_cargo_toml),
            ("go.mod", self._parse_go_mod),
        ]
        for fname, parser in dep_files:
            fpath = root / fname
            if fpath.exists():
                try:
                    deps = parser(fpath)
                    result.dependencies.extend(deps)
                except Exception:
                    pass

        summary_parts = [
            f"Repository at {path}",
            f"Files: {result.files_analyzed}",
            f"Languages: {', '.join(result.languages) if result.languages else 'unknown'}",
        ]
        if result.entry_points:
            summary_parts.append(f"Entry points: {', '.join(result.entry_points)}")
        if result.dependencies:
            summary_parts.append(f"Dependencies: {len(result.dependencies)}")
        result.summary = " | ".join(summary_parts)

        self._repos[url] = result
        return result

    def get(self, url: str) -> ScoutResult | None:
        return self._repos.get(url)

    def list(self) -> list[ScoutResult]:
        return list(self._repos.values())

    def _parse_requirements(self, path: Path) -> list[dict[str, str]]:
        deps: list[dict[str, str]] = []
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                if "==" in line:
                    name, ver = line.split("==", 1)
                    deps.append({"name": name.strip(), "version": ver.strip()})
                else:
                    deps.append({"name": line, "version": ""})
        return deps

    def _parse_package_json(self, path: Path) -> list[dict[str, str]]:
        data = json.loads(path.read_text())
        deps: list[dict[str, str]] = []
        for section in ("dependencies", "devDependencies", "peerDependencies"):
            for name, ver in data.get(section, {}).items():
                deps.append({"name": name, "version": str(ver)})
        return deps

    def _parse_cargo_toml(self, path: Path) -> list[dict[str, str]]:
        deps: list[dict[str, str]] = []
        in_deps = False
        for line in path.read_text().splitlines():
            stripped = line.strip()
            if stripped.startswith("[dependencies"):
                in_deps = True
            elif stripped.startswith("[") and in_deps:
                in_deps = False
            elif in_deps and "=" in stripped:
                parts = stripped.split("=", 1)
                name = parts[0].strip().strip('"').strip("'")
                version = parts[1].strip().strip('"').strip("'").strip(",")
                deps.append({"name": name, "version": version})
        return deps

    def _parse_go_mod(self, path: Path) -> list[dict[str, str]]:
        deps: list[dict[str, str]] = []
        for line in path.read_text().splitlines():
            line = line.strip()
            if line.startswith("require (") or line == "require (":
                continue
            parts = line.split()
            if len(parts) >= 2 and not line.startswith("go ") and not line.startswith("module "):
                deps.append({"name": parts[0], "version": parts[1] if len(parts) > 1 else ""})
        return deps

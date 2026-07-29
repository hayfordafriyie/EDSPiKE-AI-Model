from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ProjectInfo:
    name: str
    root: str
    language: str = ""
    build_system: str = ""
    frameworks: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    conventions: list[str] = field(default_factory=list)
    structure: dict[str, Any] = field(default_factory=dict)


class ProjectScanner:
    def __init__(self, root: str):
        self.root = Path(root).resolve()

    def scan(self) -> ProjectInfo:
        name = self.root.name
        info = ProjectInfo(name=name, root=str(self.root))

        # Detect language and build system
        info.language = self._detect_language()
        info.build_system = self._detect_build_system()
        info.frameworks = self._detect_frameworks()
        info.dependencies = self._detect_dependencies()
        info.conventions = self._detect_conventions()
        info.structure = self._get_structure()

        return info

    def generate_agents_md(self) -> str:
        info = self.scan()
        lines: list[str] = [
            f"# {info.name}",
            "",
            f"Root: {info.root}",
            f"Language: {info.language}",
            "",
        ]

        if info.frameworks:
            lines.append("## Frameworks")
            for fw in info.frameworks:
                lines.append(f"- {fw}")
            lines.append("")

        if info.dependencies:
            lines.append("## Key Dependencies")
            for dep in info.dependencies[:20]:
                lines.append(f"- {dep}")
            if len(info.dependencies) > 20:
                lines.append(f"- ... and {len(info.dependencies) - 20} more")
            lines.append("")

        if info.conventions:
            lines.append("## Conventions")
            for c in info.conventions:
                lines.append(f"- {c}")
            lines.append("")

        lines.append("## Project Structure")
        self._format_structure(info.structure, lines, prefix="")

        lines.append("")
        lines.append("## Development")
        lines.append("- Use the build system's standard commands")
        lines.append("- Follow existing code style (imports, naming, formatting)")
        lines.append("- Write tests for new functionality")

        return "\n".join(lines)

    def _detect_language(self) -> str:
        exts: dict[str, int] = {}
        for f in self.root.rglob("*"):
            if f.is_file() and f.suffix:
                exts[f.suffix] = exts.get(f.suffix, 0) + 1

        lang_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".tsx": "TypeScript (React)",
            ".jsx": "JavaScript (React)",
            ".go": "Go",
            ".rs": "Rust",
            ".java": "Java",
            ".rb": "Ruby",
            ".php": "PHP",
            ".c": "C",
            ".cpp": "C++",
            ".h": "C/C++ Header",
            ".cs": "C#",
            ".swift": "Swift",
            ".kt": "Kotlin",
            ".scala": "Scala",
            ".r": "R",
            ".m": "Objective-C",
        }

        best_ext = max(exts, key=exts.get) if exts else ""
        return lang_map.get(best_ext, best_ext)

    def _detect_build_system(self) -> str:
        markers = {
            "setup.py": "setuptools",
            "pyproject.toml": "Python (PEP 517)",
            "Cargo.toml": "Cargo (Rust)",
            "go.mod": "Go Modules",
            "package.json": "npm",
            "yarn.lock": "Yarn",
            "pom.xml": "Maven",
            "build.gradle": "Gradle",
            "Makefile": "Make",
            "CMakeLists.txt": "CMake",
            "Gemfile": "Bundler",
            "composer.json": "Composer",
        }
        for marker, system in markers.items():
            if (self.root / marker).exists():
                return system
        return ""

    def _detect_frameworks(self) -> list[str]:
        frameworks: list[str] = []
        for f in self.root.rglob("*"):
            if f.is_file():
                name = f.name.lower()
                if name == "requirements.txt":
                    content = f.read_text()
                    for lib in ["flask", "django", "fastapi", "requests", "pytest", "sqlalchemy"]:
                        if lib in content.lower():
                            frameworks.append(lib)
                elif name == "package.json":
                    try:
                        data = json.loads(f.read_text())
                        for section in ("dependencies", "devDependencies"):
                            for dep in data.get(section, {}):
                                frameworks.append(dep)
                    except Exception:
                        pass
        return list(set(frameworks))[:15]

    def _detect_dependencies(self) -> list[str]:
        deps: list[str] = []
        for f in self.root.rglob("*"):
            if f.is_file() and f.name in ("requirements.txt", "package.json", "Cargo.toml", "go.mod"):
                try:
                    content = f.read_text()
                    if f.name == "requirements.txt":
                        for line in content.splitlines():
                            line = line.strip()
                            if line and not line.startswith("#"):
                                deps.append(line)
                    elif f.name == "package.json":
                        data = json.loads(content)
                        for section in ("dependencies", "devDependencies"):
                            for dep in data.get(section, {}):
                                deps.append(f"{dep}@{data[section][dep]}")
                except Exception:
                    pass
        return deps[:30]

    def _detect_conventions(self) -> list[str]:
        conventions: list[str] = []
        if (self.root / ".editorconfig").exists():
            conventions.append("EditorConfig formatting")
        if (self.root / ".pre-commit-config.yaml").exists():
            conventions.append("Pre-commit hooks")
        if (self.root / "ruff.toml").exists() or (self.root / ".ruff.toml").exists():
            conventions.append("Ruff linting")
        if (self.root / "pyproject.toml").exists():
            try:
                content = (self.root / "pyproject.toml").read_text()
                if "black" in content:
                    conventions.append("Black formatting")
                if "isort" in content:
                    conventions.append("isort import ordering")
                if "mypy" in content:
                    conventions.append("Mypy type checking")
            except Exception:
                pass
        if (self.root / ".flake8").exists() or (self.root / "setup.cfg").exists():
            conventions.append("Flake8 linting")
        if (self.root / ".github/workflows").exists():
            conventions.append("GitHub Actions CI")
        return conventions

    def _get_structure(self) -> dict[str, Any]:
        structure: dict[str, Any] = {}
        for entry in sorted(self.root.iterdir()):
            name = entry.name
            if name.startswith(".") or name.startswith("__pycache__") or name == "node_modules":
                continue
            if entry.is_dir():
                structure[name] = self._get_dir_summary(entry)
            elif entry.is_file():
                if entry.suffix in (".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java", ".c", ".cpp", ".h"):
                    structure[name] = f"file ({self._count_lines(entry)} lines)"
                else:
                    structure[name] = "file"
        return structure

    def _get_dir_summary(self, path: Path) -> str:
        files = [f for f in path.rglob("*") if f.is_file()]
        return f"dir ({len(files)} files)"

    def _count_lines(self, path: Path) -> int:
        try:
            return sum(1 for _ in path.open())
        except Exception:
            return 0

    def _format_structure(self, structure: dict[str, Any], lines: list[str], prefix: str = "") -> None:
        for name, info in sorted(structure.items()):
            if isinstance(info, dict):
                lines.append(f"{prefix}- {name}/")
                self._format_structure(info, lines, prefix + "  ")
            else:
                lines.append(f"{prefix}- {name} ({info})")

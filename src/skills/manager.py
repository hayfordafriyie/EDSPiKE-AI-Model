from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Skill:
    name: str
    description: str
    content: str
    type: str = "standard"  # standard, flow
    source: str = ""  # builtin, user, project
    flow_definition: str = ""  # mermaid/d2 for flow skills


class SkillManager:
    def __init__(self):
        self._skills: dict[str, Skill] = {}
        self._discovery_paths: list[Path] = []

    def add_discovery_path(self, path: str) -> None:
        p = Path(path).expanduser().resolve()
        if p.exists() and p not in self._discovery_paths:
            self._discovery_paths.append(p)

    def discover(self) -> list[Skill]:
        found: list[Skill] = []
        for base in self._discovery_paths:
            if not base.exists():
                continue
            # Subdirectory format: <name>/SKILL.md
            for skill_dir in sorted(base.iterdir()):
                if skill_dir.is_dir():
                    skill_file = skill_dir / "SKILL.md"
                    if skill_file.exists():
                        skill = self._parse_skill_file(skill_file, skill_dir.name)
                        if skill:
                            found.append(skill)
            # Flat format: <name>.md
            for md_file in sorted(base.glob("*.md")):
                if md_file.name != "SKILL.md":
                    skill = self._parse_skill_file(md_file, md_file.stem)
                    if skill:
                        found.append(skill)
        return found

    def load_all(self) -> None:
        for skill in self.discover():
            self._skills[skill.name] = skill

    def register(self, name: str, description: str, content: str, type_: str = "standard", source: str = "builtin") -> Skill:
        skill = Skill(name=name, description=description, content=content, type=type_, source=source)
        self._skills[name] = skill
        return skill

    def get(self, name: str) -> Skill | None:
        return self._skills.get(name)

    def search(self, query: str) -> list[Skill]:
        q = query.lower()
        return [s for s in self._skills.values() if q in s.name.lower() or q in s.description.lower()]

    def list_by_type(self, type_: str) -> list[Skill]:
        return [s for s in self._skills.values() if s.type == type_]

    def list_all(self) -> list[Skill]:
        return list(self._skills.values())

    def describe_available(self) -> str:
        if not self._skills:
            return "No skills available."
        lines = ["Available skills:"]
        for skill in self._skills.values():
            lines.append(f"  - {skill.name}: {skill.description} ({skill.type})")
        return "\n".join(lines)

    def _parse_skill_file(self, path: Path, default_name: str) -> Skill | None:
        content = path.read_text()
        name = default_name
        description = ""
        type_ = "standard"

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = parts[1]
                body = parts[2].strip()
                for line in frontmatter.splitlines():
                    if line.startswith("name:"):
                        name = line.split(":", 1)[1].strip()
                    elif line.startswith("description:"):
                        description = line.split(":", 1)[1].strip()
                    elif line.startswith("type:"):
                        type_ = line.split(":", 1)[1].strip()
                content = body

        return Skill(name=name, description=description or name, content=content, type=type_)

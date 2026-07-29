from pathlib import Path

import pytest

from src.skills.manager import SkillManager, Skill
from src.skills import SkillManager as SkillManagerAlias


class TestSkillManager:
    def test_register_and_get(self):
        mgr = SkillManager()
        mgr.register("test-skill", "A test skill", "Do this thing")
        skill = mgr.get("test-skill")
        assert skill is not None
        assert skill.description == "A test skill"

    def test_search(self):
        mgr = SkillManager()
        mgr.register("code-review", "Review code for issues", "Check code quality")
        mgr.register("test-writer", "Write tests for code", "Generate tests")
        results = mgr.search("review")
        assert len(results) == 1
        assert results[0].name == "code-review"

    def test_list_by_type(self):
        mgr = SkillManager()
        mgr.register("s1", "Standard", "content", type_="standard")
        mgr.register("f1", "Flow", "flow content", type_="flow")
        standards = mgr.list_by_type("standard")
        flows = mgr.list_by_type("flow")
        assert len(standards) == 1
        assert len(flows) == 1

    def test_discover_from_directory(self, tmp_path: Path):
        skill_dir = tmp_path / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("---\nname: my-skill\ndescription: A discovered skill\n---\nDo the thing")
        mgr = SkillManager()
        mgr.add_discovery_path(str(tmp_path / "skills"))
        mgr.load_all()
        skill = mgr.get("my-skill")
        assert skill is not None
        assert "Do the thing" in skill.content

    def test_describe_available(self):
        mgr = SkillManager()
        mgr.register("s1", "Skill one", "content")
        desc = mgr.describe_available()
        assert "s1" in desc
        assert "Skill one" in desc

    def test_empty_describe(self):
        mgr = SkillManager()
        assert "No skills" in mgr.describe_available()

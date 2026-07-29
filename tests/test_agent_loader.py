import json
from pathlib import Path

import pytest

from src.agents.loader import resolve_prompt_ref, load_agents_from_json, load_agents_from_markdown


class TestAgentLoader:
    def test_resolve_prompt_ref_local(self, tmp_path: Path):
        prompt_file = tmp_path / "my_prompt.txt"
        prompt_file.write_text("You are a test agent.")
        result = resolve_prompt_ref("{file:my_prompt.txt}", str(tmp_path))
        assert "test agent" in result

    def test_resolve_prompt_ref_no_match(self):
        result = resolve_prompt_ref("{file:/nonexistent/path.txt}", "/tmp")
        assert "{file:" in result

    def test_resolve_no_refs(self):
        result = resolve_prompt_ref("plain text", "/tmp")
        assert result == "plain text"

    def test_load_from_json_empty(self, tmp_path: Path):
        f = tmp_path / "config.json"
        f.write_text("{}")
        agents = load_agents_from_json(str(f))
        assert agents == []

    def test_load_from_json_with_agent(self, tmp_path: Path):
        config = {
            "agent": {
                "reviewer": {
                    "description": "Code reviewer",
                    "mode": "subagent",
                    "temperature": 0.1,
                    "permission": {"edit": "deny"},
                }
            }
        }
        f = tmp_path / "edspike.json"
        f.write_text(json.dumps(config))
        agents = load_agents_from_json(str(f))
        assert len(agents) == 1
        assert agents[0].id == "reviewer"
        assert agents[0].mode == "subagent"
        assert agents[0].tool_permissions.get("edit") == "deny"

    def test_load_from_json_with_prompt_file(self, tmp_path: Path):
        prompt_file = tmp_path / "prompts" / "review.txt"
        prompt_file.parent.mkdir()
        prompt_file.write_text("You are a code reviewer.")
        config = {
            "agent": {
                "reviewer": {
                    "description": "Code reviewer",
                    "prompt": "{file:prompts/review.txt}",
                }
            }
        }
        f = tmp_path / "edspike.json"
        f.write_text(json.dumps(config))
        agents = load_agents_from_json(str(f))
        assert len(agents) == 1
        assert "code reviewer" in agents[0].system_prompt.lower()

    def test_load_from_markdown(self, tmp_path: Path):
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        md = agents_dir / "tester.md"
        md.write_text("""---
description: Test agent
mode: subagent
permission:
  edit: deny
  bash: deny
---
You are a test agent.
""")
        agents = load_agents_from_markdown(str(agents_dir))
        assert len(agents) == 1
        assert agents[0].id == "tester"
        assert "test agent" in agents[0].system_prompt
        assert agents[0].tool_permissions.get("edit") == "deny"

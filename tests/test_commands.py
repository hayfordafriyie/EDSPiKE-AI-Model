import json
from pathlib import Path

import pytest

from src.commands import CommandRegistry


class TestCommands:
    def test_register_and_get(self):
        reg = CommandRegistry()
        reg.register("fix", "Fix {{file}}: {{issue}}", named_args=["file", "issue"])
        cmd = reg.get("fix")
        assert cmd is not None
        assert cmd.name == "fix"
        assert "{{file}}" in cmd.prompt_template

    def test_execute_with_args(self):
        reg = CommandRegistry()
        reg.register("greet", "Hello {{name}}!", named_args=["name"])
        result = reg.execute("greet", {"name": "World"})
        assert result == "Hello World!"

    def test_execute_missing_arg(self):
        reg = CommandRegistry()
        reg.register("test", "{{a}}-{{b}}", named_args=["a", "b"])
        # Missing args stay as placeholders
        result = reg.execute("test", {"a": "x"})
        assert "{{b}}" in result

    def test_execute_nonexistent(self):
        reg = CommandRegistry()
        with pytest.raises(KeyError):
            reg.execute("nonexistent")

    def test_parse_args_simple(self):
        reg = CommandRegistry()
        name, args = reg.parse_args("/deploy --env prod --region us-east-1")
        assert name == "deploy"
        assert args["env"] == "prod"
        assert args["region"] == "us-east-1"

    def test_parse_args_with_equals(self):
        reg = CommandRegistry()
        name, args = reg.parse_args("/search query=hello limit=10")
        assert name == "search"
        assert args["query"] == "hello"

    def test_parse_args_no_args(self):
        reg = CommandRegistry()
        name, args = reg.parse_args("/help")
        assert name == "help"
        assert args == {}

    def test_parse_args_with_strip_slash(self):
        reg = CommandRegistry()
        name, args = reg.parse_args("deploy")  # no leading slash
        assert name == "deploy"

    def test_custom_handler(self):
        reg = CommandRegistry()

        def my_handler(name, args):
            return f"handled:{name}:{args.get('key', '')}"

        reg.register("custom", "template {{key}}", handler=my_handler)
        result = reg.execute("custom", {"key": "val"})
        assert result == "handled:custom:val"

    def test_list(self):
        reg = CommandRegistry()
        reg.register("a", "cmd a")
        reg.register("b", "cmd b")
        assert len(reg.list()) == 2

    def test_remove(self):
        reg = CommandRegistry()
        reg.register("x", "cmd x")
        assert reg.remove("x") is True
        assert reg.get("x") is None
        assert reg.remove("x") is False

    def test_persistence(self, tmp_path: Path):
        data_dir = str(tmp_path / "commands")
        r1 = CommandRegistry(data_dir)
        r1.register("p", "persistent {{arg}}", named_args=["arg"])
        r2 = CommandRegistry(data_dir)
        cmd = r2.get("p")
        assert cmd is not None
        assert "persistent" in cmd.prompt_template
